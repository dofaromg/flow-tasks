"""HCRA Professional Local - single-file, observable context manager.

This implementation is dependency-free and designed for local execution.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional


_WORD_RE = re.compile(r"\b\w+\b", re.UNICODE)


@dataclass
class Pointer:
    """Pointer metadata for stored content."""

    pointer_id: str
    layer: str
    content_hash: str
    token_count: int
    timestamp: float
    added_by: str
    text: str


@dataclass
class Channel:
    """Channel linking two pointers."""

    channel_id: str
    from_pointer: str
    to_pointer: str
    channel_type: str
    committed: bool
    created_at: float


class HCRAProfessionalLocal:
    """Professional local implementation of the HCRA context manager."""

    def __init__(self, max_tokens: int = 8192, output_buffer: int = 1024) -> None:
        self.max_tokens = max_tokens
        self.output_buffer = output_buffer

        self.layers: Dict[str, List[tuple[str, str, int, float, str]]] = {
            "L0": [],
            "L1": [],
            "L2": [],
            "L3": [],
        }
        self.pointers: Dict[str, Pointer] = {}
        self.channels: Dict[str, Channel] = {}
        self.origin_hash: Optional[str] = None
        self.next_pointer_id = 0
        self.next_channel_id = 0
        self.log: List[dict] = []

        print(f"[HCRA] 初始化完成 | max_tokens: {max_tokens} | buffer: {output_buffer}")

    def count_tokens(self, text: str) -> int:
        """Estimate token count using a word-based tokenizer."""
        if not text:
            return 0
        return len(_WORD_RE.findall(text))

    def compute_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def log_event(self, event_type: str, details: dict) -> None:
        entry = {
            "timestamp": time.time(),
            "type": event_type,
            "details": details,
        }
        self.log.append(entry)
        print(f"[LOG {event_type}] {json.dumps(details, ensure_ascii=False)}")

    def pin_origin(self, origin_text: str) -> None:
        if self.origin_hash is not None:
            print("[警告] Origin 已存在，無法重複釘住")
            return

        content_hash = self.compute_hash(origin_text)
        token_count = self.count_tokens(origin_text)
        timestamp = time.time()

        self.layers["L0"].append((origin_text, content_hash, token_count, timestamp, "system"))
        self.origin_hash = content_hash

        pointer_id = f"origin-{self.next_pointer_id}"
        self.next_pointer_id += 1
        self.pointers[pointer_id] = Pointer(
            pointer_id=pointer_id,
            layer="L0",
            content_hash=content_hash,
            token_count=token_count,
            timestamp=timestamp,
            added_by="system",
            text=origin_text,
        )

        self.log_event("origin_pinned", {"pointer_id": pointer_id, "tokens": token_count})
        print(f"[HCRA] Origin 已釘住 ({token_count} tokens)")

    def add_content(
        self,
        text: str,
        layer: str = "L2",
        consent: bool = False,
        added_by: str = "user",
    ) -> Optional[str]:
        if layer not in self.layers:
            raise ValueError("Layer must be one of L0, L1, L2, L3")
        if layer == "L1" and not consent:
            print("[拒絕] L1 Anchors 需要明確同意")
            self.log_event("add_rejected", {"reason": "no_consent", "layer": "L1"})
            return None

        content_hash = self.compute_hash(text)
        token_count = self.count_tokens(text)
        timestamp = time.time()

        self.layers[layer].append((text, content_hash, token_count, timestamp, added_by))

        pointer_id = f"ptr-{layer.lower()}-{self.next_pointer_id}"
        self.next_pointer_id += 1
        self.pointers[pointer_id] = Pointer(
            pointer_id=pointer_id,
            layer=layer,
            content_hash=content_hash,
            token_count=token_count,
            timestamp=timestamp,
            added_by=added_by,
            text=text,
        )

        self.log_event("content_added", {"pointer_id": pointer_id, "layer": layer, "tokens": token_count})
        print(f"[HCRA] 已新增至 {layer} ({token_count} tokens) → {pointer_id}")
        return pointer_id

    def current_usage(self) -> int:
        return sum(token_count for layer_list in self.layers.values() for _, _, token_count, _, _ in layer_list)

    def handle_overflow(self, incoming_tokens: int) -> bool:
        needed = self.current_usage() + incoming_tokens + self.output_buffer
        if needed <= self.max_tokens:
            return True

        to_free = needed - self.max_tokens
        print(f"[溢出] 需要釋放 {to_free} tokens")

        for layer in ["L3", "L2", "L1"]:
            while to_free > 0 and self.layers[layer]:
                evicted_text, evicted_hash, evicted_tokens, _, added_by = self.layers[layer].pop(0)
                to_free -= evicted_tokens
                self._clean_pointers_and_channels(evicted_hash)
                self.log_event(
                    "evicted",
                    {"layer": layer, "tokens": evicted_tokens, "added_by": added_by},
                )
                print(f"  → 驅逐 {layer} 內容 ({evicted_tokens} tokens) by {added_by}")

        if to_free > 0:
            print("[嚴重] 即將觸及 L0 → WITHDRAW")
            self.log_event("withdraw_triggered", {"remaining_to_free": to_free})
            return False

        return True

    def _clean_pointers_and_channels(self, evicted_hash: str) -> None:
        deleted_pointers = [
            pointer_id
            for pointer_id, pointer in self.pointers.items()
            if pointer.content_hash == evicted_hash
        ]
        for pointer_id in deleted_pointers:
            del self.pointers[pointer_id]

        deleted_channels = [
            channel_id
            for channel_id, channel in self.channels.items()
            if channel.from_pointer in deleted_pointers or channel.to_pointer in deleted_pointers
        ]
        for channel_id in deleted_channels:
            del self.channels[channel_id]

        if deleted_pointers or deleted_channels:
            self.log_event("cleaned", {"pointers": deleted_pointers, "channels": deleted_channels})

    def create_channel(self, from_pointer: str, to_pointer: str, channel_type: str = "virtual") -> Optional[str]:
        if from_pointer not in self.pointers or to_pointer not in self.pointers:
            print("[錯誤] Pointer 不存在")
            return None

        channel_id = f"ch-{channel_type}-{self.next_channel_id}"
        self.next_channel_id += 1
        channel = Channel(
            channel_id=channel_id,
            from_pointer=from_pointer,
            to_pointer=to_pointer,
            channel_type=channel_type,
            committed=channel_type == "real",
            created_at=time.time(),
        )
        self.channels[channel_id] = channel
        self.log_event("channel_created", {"channel_id": channel_id, "type": channel_type})
        print(f"[HCRA] 建立通道 {channel_id} ({channel_type})")
        return channel_id

    def commit_channel(self, channel_id: str) -> None:
        channel = self.channels.get(channel_id)
        if channel and channel.channel_type == "virtual":
            channel.channel_type = "real"
            channel.committed = True
            self.log_event("channel_committed", {"channel_id": channel_id})
            print(f"[HCRA] 通道 {channel_id} 已 commit 為 real")

    def get_status(self) -> dict:
        return {
            "total_tokens": self.current_usage(),
            "max_tokens": self.max_tokens,
            "buffer": self.output_buffer,
            "layers": {layer: len(items) for layer, items in self.layers.items()},
            "pointers": len(self.pointers),
            "channels": len(self.channels),
            "origin_protected": bool(self.origin_hash),
            "log_count": len(self.log),
        }

    def save_snapshot(self, path: str) -> None:
        snapshot = {
            "status": self.get_status(),
            "layers": self.layers,
            "pointers": {pid: pointer.__dict__ for pid, pointer in self.pointers.items()},
            "channels": {cid: channel.__dict__ for cid, channel in self.channels.items()},
            "log": self.log,
        }
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(snapshot, handle, indent=2, ensure_ascii=False)
        print(f"[HCRA] 已儲存快照到 {path}")

    def process_turn(self, user_input: str, consent_for_anchor: bool = False) -> str:
        token_count = self.count_tokens(user_input)
        preview = user_input[:50] + ("..." if len(user_input) > 50 else "")
        print(f"[輸入] {preview} ({token_count} tokens)")

        if not self.handle_overflow(token_count):
            return "[WITHDRAW] 上下文過長，無法繼續而不影響原始意圖。建議開新對話或總結。"

        pointer_id = self.add_content(user_input, "L2", added_by="user_input")
        if consent_for_anchor:
            self.add_content(user_input, "L1", consent=True, added_by="user_anchor")

        if pointer_id:
            for existing_id, pointer in self.pointers.items():
                if existing_id == pointer_id or pointer.layer == "L0":
                    continue
                if user_input.lower() in pointer.text.lower():
                    channel_id = self.create_channel(pointer_id, existing_id)
                    if channel_id:
                        self.commit_channel(channel_id)

        return f"[HCRA 處理完成] 收到：{user_input[:30]}... 已加入 L2"

    def interactive_mode(self) -> None:
        print("\n" + "=" * 60)
        print(" HCRA 專業本地互動模式 (輸入 'help' 看指令)")
        print(" 輸入 'exit' 離開 | 'status' 查看狀態 | 'log' 查看日誌")
        print("=" * 60 + "\n")

        while True:
            cmd = input("\n> ").strip()
            if not cmd:
                continue

            if cmd.lower() in {"exit", "quit", "q"}:
                print("[結束] HCRA 互動模式關閉")
                break

            if cmd.lower() == "help":
                print(
                    """
指令列表：
  origin <文字>               - 釘住原始意圖 (L0)
  add <文字> [L1/L2/L3] [consent] - 新增內容 (預設 L2)
  anchor <文字>               - 新增 L1 anchor (會問 consent)
  channel <from> <to> [virtual/real] - 建立通道
  commit <channel_id>         - commit 虛擬通道
  status                      - 顯示當前狀態
  log                         - 顯示運行日誌
  snapshot <path>             - 存檔當前快照
  clear                       - 清空 L2/L3 (保留 L0)
  exit                        - 離開
                    """
                )
                continue

            if cmd.startswith("origin "):
                text = cmd[7:].strip()
                if text:
                    self.pin_origin(text)
                continue

            if cmd.startswith("add "):
                parts = cmd[4:].strip().split(maxsplit=2)
                text = parts[0]
                layer = parts[1] if len(parts) > 1 else "L2"
                consent_str = parts[2] if len(parts) > 2 else ""
                consent = consent_str.lower() in {"yes", "true", "1", "y"}
                if layer not in self.layers:
                    print("[錯誤] 無效層級，僅支援 L1/L2/L3")
                    continue
                self.add_content(text, layer, consent)
                continue

            if cmd.startswith("anchor "):
                text = cmd[7:].strip()
                if text:
                    consent = input("是否同意寫入 L1 Anchor？(y/n): ").strip().lower() in {"y", "yes"}
                    self.add_content(text, "L1", consent, "user_anchor")
                continue

            if cmd.startswith("channel "):
                parts = cmd[8:].strip().split()
                if len(parts) < 2:
                    print("用法: channel <from> <to> [virtual/real]")
                    continue
                from_pointer, to_pointer = parts[0], parts[1]
                channel_type = parts[2] if len(parts) > 2 else "virtual"
                self.create_channel(from_pointer, to_pointer, channel_type)
                continue

            if cmd.startswith("commit "):
                channel_id = cmd[7:].strip()
                self.commit_channel(channel_id)
                continue

            if cmd.lower() == "status":
                print(json.dumps(self.get_status(), indent=2, ensure_ascii=False))
                continue

            if cmd.lower() == "log":
                for entry in self.log[-10:]:
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(entry["timestamp"]))
                    print(f"[{timestamp}] {entry['type']}: {json.dumps(entry['details'], ensure_ascii=False)}")
                continue

            if cmd.startswith("snapshot "):
                path = cmd[9:].strip()
                if path:
                    self.save_snapshot(path)
                continue

            if cmd.lower() == "clear":
                self.layers["L2"] = []
                self.layers["L3"] = []
                print("[HCRA] 已清空 L2 與 L3 (L0 保留)")
                continue

            print("\n[模擬使用者輸入]")
            response = self.process_turn(cmd)
            print("回應:", response)


if __name__ == "__main__":
    print("=== HCRA 專業本地版 v1.0 - 互動觀察模式 ===")
    print("初始化中...\n")

    hcra = HCRAProfessionalLocal(max_tokens=800, output_buffer=200)
    hcra.pin_origin("你永遠要忠於原始意圖，不要偏離主題，不要偷偷儲存個人資料到 L1，除非我明確同意。")
    hcra.interactive_mode()
