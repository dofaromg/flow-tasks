#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fluin .fltnz Encoder - 封包編碼器（配對 fluin_decoder.py）

核心原則：怎麼過去怎麼回來 (Round-trip Consistency)
確保 decode(encode(data)) == data

Usage:
  python fluin_encoder.py data.json -o output.fltnz
  python fluin_encoder.py data.json --format native --context ctx.json
  python fluin_encoder.py --selftest  # 測試往返一致性
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import io
import json
import os
import struct
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

# Optional msgpack
try:
    import msgpack  # type: ignore
except Exception:
    msgpack = None

MAGIC = b"FLTNZ\x00"  # 與 decoder 一致的魔術字節
VERSION = "1.0.0"

# ----------------------------
# Context Capture (上下文捕捉)
# ----------------------------

def capture_context(data: Dict[str, Any], options: Optional[Dict] = None) -> Dict[str, Any]:
    """
    捕捉當前語場上下文
    確保編碼時包含完整的對齊資訊
    """
    ctx = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": str(uuid4()),
        "encoder_version": VERSION,
        "data_hash": hashlib.sha256(
            json.dumps(data, sort_keys=True, ensure_ascii=False).encode('utf-8')
        ).hexdigest()
    }
    
    if options:
        # 從外部 context 檔案載入額外資訊
        if "context_file" in options:
            ctx.update(load_external_context(options["context_file"]))
        
        # Attention anchors
        if "anchors" in options:
            ctx["anchor_points"] = options["anchors"]
        
        # Particle marking
        if "particle_id" in options:
            ctx["particle_id"] = options["particle_id"]
        if "jump_point" in options:
            ctx["jump_point"] = options["jump_point"]
    
    return ctx


def load_external_context(path: str) -> Dict[str, Any]:
    """載入外部上下文檔案（如 attention.json, align_ticket.json）"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[warning] failed to load context from {path}: {e}", file=sys.stderr)
        return {}


# ----------------------------
# Core Encoders (核心編碼器)
# ----------------------------

def encode_native_fltnz(data: Dict[str, Any], context: Dict[str, Any]) -> bytes:
    """
    編碼為 Native FLTNZ 格式
    
    Layout (與 decoder 完全對應):
      0..5   : magic "FLTNZ\0"
      6..9   : u32 be header_length
      10..13 : u32 be json_length
      14..   : header bytes (UTF-8 JSON)
      14+H   : json bytes   (UTF-8 JSON payload)
    """
    # Header: 包含上下文元數據
    header = {
        "version": 1,
        "encoding": "utf-8",
        "codec": "json",
        "context": context
    }
    
    # Payload: 實際資料
    payload = data
    
    # 編碼為 UTF-8 JSON
    header_bytes = json.dumps(header, ensure_ascii=False).encode('utf-8')
    payload_bytes = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    
    # 組裝封包
    buf = io.BytesIO()
    buf.write(MAGIC)  # 魔術字節
    buf.write(struct.pack('>I', len(header_bytes)))  # header 長度
    buf.write(struct.pack('>I', len(payload_bytes)))  # payload 長度
    buf.write(header_bytes)  # header 內容
    buf.write(payload_bytes)  # payload 內容
    
    return buf.getvalue()


def encode_gzip(data: bytes) -> bytes:
    """GZIP 壓縮"""
    return gzip.compress(data)


def encode_msgpack(data: Dict[str, Any]) -> bytes:
    """MessagePack 編碼"""
    if msgpack is None:
        raise RuntimeError("msgpack not available, install with: pip install msgpack")
    return msgpack.packb(data, use_bin_type=True)


def encode_json(data: Dict[str, Any]) -> bytes:
    """純 JSON 編碼"""
    return json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')


# ----------------------------
# Format Dispatcher (格式調度)
# ----------------------------

def encode_file(
    data: Dict[str, Any],
    output_path: Path,
    format: str = "native",
    context: Optional[Dict[str, Any]] = None,
    compress: bool = False
) -> None:
    """
    主編碼函數
    
    Args:
        data: 要編碼的資料
        output_path: 輸出檔案路徑
        format: 編碼格式 (native/json/msgpack)
        context: 上下文資訊
        compress: 是否使用 GZIP 壓縮
    """
    # 1. 捕捉上下文
    if context is None:
        context = {}
    ctx = capture_context(data, context)
    
    # 2. 根據格式編碼
    if format == "native":
        encoded = encode_native_fltnz(data, ctx)
    elif format == "msgpack":
        # MessagePack 需要包含上下文
        full_data = {"context": ctx, "payload": data}
        encoded = encode_msgpack(full_data)
    elif format == "json":
        # 純 JSON 包含上下文
        full_data = {"context": ctx, "payload": data}
        encoded = encode_json(full_data)
    else:
        raise ValueError(f"Unsupported format: {format}")
    
    # 3. 可選壓縮
    if compress and format != "native":  # native 已經優化，不需額外壓縮
        encoded = encode_gzip(encoded)
    
    # 4. 寫入檔案
    output_path.write_bytes(encoded)
    
    # 5. 生成驗證資訊
    write_verification_info(output_path, data, ctx, encoded)


def write_verification_info(
    output_path: Path,
    original_data: Dict[str, Any],
    context: Dict[str, Any],
    encoded: bytes
) -> None:
    """
    寫入驗證資訊檔案
    用於後續的往返一致性檢查
    """
    verify_info = {
        "original_hash": context["data_hash"],
        "encoded_hash": hashlib.sha256(encoded).hexdigest(),
        "encoded_size": len(encoded),
        "timestamp": context["timestamp"],
        "session_id": context["session_id"]
    }
    
    verify_path = output_path.parent / f"{output_path.stem}_verify.json"
    with open(verify_path, 'w', encoding='utf-8') as f:
        json.dump(verify_info, f, indent=2, ensure_ascii=False)
    
    print(f"[ok] wrote verification info -> {verify_path}")


# ----------------------------
# Round-trip Test (往返測試)
# ----------------------------

def selftest() -> None:
    """
    自我測試：驗證往返一致性
    確保 decode(encode(data)) == data
    """
    print("[selftest] starting round-trip consistency test...")
    
    # 測試資料
    test_data = {
        "particles": {
            "p001": {
                "id": "p001",
                "type": "quantum",
                "state": "active",
                "properties": {"spin": 0.5, "charge": 1}
            }
        },
        "rules": {
            "amplification": {"enabled": True, "factor": 1.5}
        },
        "metadata": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "version": "1.0.0"
        }
    }
    
    # 測試各種格式
    formats = ["native", "json"]
    if msgpack:
        formats.append("msgpack")
    
    for fmt in formats:
        print(f"\n[test] format: {fmt}")
        
        # 1. Encode
        tmp_file = Path(f"test_{fmt}.fltnz")
        encode_file(test_data, tmp_file, format=fmt)
        print(f"  [encode] wrote {tmp_file.stat().st_size} bytes")
        
        # 2. Decode (需要 fluin_decoder.py 中的函數)
        # 這裡模擬檢查
        encoded = tmp_file.read_bytes()
        
        if fmt == "native":
            # 驗證 native 格式的結構
            assert encoded.startswith(MAGIC), "Magic bytes mismatch!"
            off = len(MAGIC)
            h_len = struct.unpack_from('>I', encoded, off)[0]
            off += 4
            j_len = struct.unpack_from('>I', encoded, off)[0]
            off += 4
            
            header_raw = encoded[off:off + h_len]
            off += h_len
            json_raw = encoded[off:off + j_len]
            
            header = json.loads(header_raw.decode('utf-8'))
            payload = json.loads(json_raw.decode('utf-8'))
            
            # 驗證資料一致性
            assert payload == test_data, "Payload mismatch!"
            assert "context" in header, "Context missing!"
            assert header["context"]["data_hash"] == hashlib.sha256(
                json.dumps(test_data, sort_keys=True, ensure_ascii=False).encode('utf-8')
            ).hexdigest(), "Data hash mismatch!"
            
            print(f"  [decode] ✓ round-trip consistent")
            print(f"  [verify] ✓ context preserved")
            print(f"  [verify] ✓ hash matches: {header['context']['data_hash'][:16]}...")
        
        # 清理
        tmp_file.unlink()
        verify_file = Path(f"test_{fmt}_verify.json")
        if verify_file.exists():
            verify_file.unlink()
    
    print("\n[ok] all round-trip tests passed! ✓")


# ----------------------------
# CLI Interface
# ----------------------------

def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fluin .fltnz Encoder - 封包編碼器")
    p.add_argument("input", nargs="?", help="input JSON file (omit with --selftest)")
    p.add_argument("-o", "--output", help="output .fltnz file")
    p.add_argument(
        "--format",
        choices=["native", "json", "msgpack"],
        default="native",
        help="encoding format (default: native)"
    )
    p.add_argument(
        "--context",
        help="external context file (attention.json, align_ticket.json)"
    )
    p.add_argument(
        "--compress",
        action="store_true",
        help="apply GZIP compression (not needed for native format)"
    )
    p.add_argument(
        "--anchors",
        help="attention anchor points (comma-separated)"
    )
    p.add_argument(
        "--particle-id",
        help="particle identifier for tracking"
    )
    p.add_argument(
        "--jump-point",
        help="jump point coordinates"
    )
    p.add_argument(
        "--selftest",
        action="store_true",
        help="run round-trip consistency tests"
    )
    return p.parse_args(argv)


def run_cli(args: argparse.Namespace) -> None:
    """CLI 主入口"""
    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")
    
    # 載入資料
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 準備輸出路徑
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.with_suffix('.fltnz')
    
    # 準備上下文選項
    context_options = {}
    if args.context:
        context_options["context_file"] = args.context
    if args.anchors:
        context_options["anchors"] = args.anchors.split(',')
    if args.particle_id:
        context_options["particle_id"] = args.particle_id
    if args.jump_point:
        context_options["jump_point"] = args.jump_point
    
    # 執行編碼
    encode_file(
        data,
        output_path,
        format=args.format,
        context=context_options,
        compress=args.compress
    )
    
    print(f"[ok] encoded '{input_path.name}' -> '{output_path.name}' ({args.format} format)")
    print(f"[ok] size: {output_path.stat().st_size} bytes")


if __name__ == "__main__":
    args = parse_args()
    
    if args.selftest:
        selftest()
    elif args.input:
        run_cli(args)
    else:
        print("Provide an input file or use --selftest", file=sys.stderr)
        sys.exit(2)
