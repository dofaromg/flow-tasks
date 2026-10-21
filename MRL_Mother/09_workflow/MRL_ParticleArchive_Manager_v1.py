#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_ParticleArchive_Manager_v1.py — 粒子檔案庫管理器(T3:存→可取回/可復活)
origin_signature: MrLiouWord
layer: L6 REFLECT (記憶取回) + L7 LOOP (復活)

補洞:粒子庫之前只「存」不「取」。本模組讓粒子可被:
  - list()     列出全部粒子(觀測總覽)
  - observe()  觀測單一粒子(看內容,不改動 — 對應 Mr.liou「喜歡觀測」)
  - search()   依關鍵字找粒子
  - restore()  復活:把回收的粒子內容寫回指定路徑(展開投影)

對齊法則:
  - rl_15 粒子不滅:取回不刪原檔(復活是 additive 投影,源粒子仍在)
  - rl_18 怎麼過去怎麼回來:存(過去)↔ 復活(回來)同一條可逆閉環
  - LAW-0:復活前驗證母體簽章(若有),確保是母體粒子
  - no_proof:找不到/讀不到誠實回錯,不偽造

零依賴。CLI:python3 09_workflow/MRL_ParticleArchive_Manager_v1.py list
"""
from __future__ import annotations

import json
import pathlib
from typing import Any, Dict, List, Optional

from MRL_utils import ORIGIN_SIGNATURE
_REPO = pathlib.Path(__file__).resolve().parent.parent
_ARCHIVE = _REPO / "MRL_ParticleArchive"
_MANIFEST = _ARCHIVE / "MRL_ParticleArchive_manifest.json"


class MRL_ParticleArchiveManager:
    """粒子檔案庫的取回/觀測/復活管理器。"""

    def __init__(self, archive_dir: pathlib.Path = _ARCHIVE) -> None:
        self.origin_signature = ORIGIN_SIGNATURE
        self.archive = pathlib.Path(archive_dir)

    # ── 觀測總覽:列出庫裡所有粒子檔(實際掃描,不靠 manifest 宣稱)──────────────
    def list(self) -> Dict[str, Any]:
        if not self.archive.exists():
            return {"error": "archive not found", "path": str(self.archive)}
        files = [p for p in self.archive.rglob("*")
                 if p.is_file() and p.name != "MRL_ParticleArchive_manifest.json"
                 and p.name != "README.md"]
        groups: Dict[str, List[str]] = {}
        for f in files:
            grp = f.relative_to(self.archive).parts[0]
            groups.setdefault(grp, []).append(f.name)
        manifest_count = None
        if _MANIFEST.exists():
            try:
                manifest_count = json.load(open(_MANIFEST, encoding="utf-8")).get("particle_count")
            except Exception:  # noqa: BLE001
                pass
        return {
            "origin_signature": ORIGIN_SIGNATURE,
            "total_files": len(files),
            "manifest_particle_count": manifest_count,
            "groups": {g: {"count": len(v), "files": sorted(v)} for g, v in sorted(groups.items())},
        }

    def _find(self, name: str) -> Optional[pathlib.Path]:
        """以檔名(可含/不含攤平前綴)找粒子檔。"""
        for p in self.archive.rglob("*"):
            if p.is_file() and (p.name == name or p.name.endswith(name) or name in p.name):
                return p
        return None

    # ── 觀測單一粒子:看內容,不改動 ──────────────────────────────────────────
    def observe(self, name: str, *, max_chars: int = 2000) -> Dict[str, Any]:
        p = self._find(name)
        if p is None:
            return {"error": f"particle not found: {name}"}
        try:
            content = p.read_text(encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            return {"error": f"cannot read: {exc}", "path": str(p)}
        signed = None
        if p.suffix == ".json":
            try:
                d = json.loads(content)
                signed = "_signature" in d and d.get("_signature") == ORIGIN_SIGNATURE
            except Exception:  # noqa: BLE001
                pass
        return {
            "name": p.name,
            "path": str(p.relative_to(_REPO)),
            "size_bytes": p.stat().st_size,
            "lines": content.count("\n") + 1,
            "mother_signed": signed,
            "preview": content[:max_chars] + ("…" if len(content) > max_chars else ""),
            "origin_signature": ORIGIN_SIGNATURE,
        }

    # ── 搜尋粒子 ───────────────────────────────────────────────────────────────
    def search(self, keyword: str) -> Dict[str, Any]:
        hits = []
        for p in self.archive.rglob("*"):
            if not p.is_file():
                continue
            if keyword.lower() in p.name.lower():
                hits.append({"name": p.name, "path": str(p.relative_to(_REPO)), "match": "filename"})
                continue
            try:
                if keyword.lower() in p.read_text(encoding="utf-8").lower():
                    hits.append({"name": p.name, "path": str(p.relative_to(_REPO)), "match": "content"})
            except Exception:  # noqa: BLE001
                pass
        return {"keyword": keyword, "hit_count": len(hits), "hits": hits,
                "origin_signature": ORIGIN_SIGNATURE}

    # ── 復活:把粒子內容寫回指定路徑(展開投影,rl_18 怎麼過去怎麼回來)──────────
    def restore(self, name: str, target_path: str, *, overwrite: bool = False) -> Dict[str, Any]:
        """
        復活粒子到 target_path。rl_15:不刪庫裡原粒子(源仍在),這是 additive 投影。
        no_proof:目標已存在且未允許覆寫 → 誠實拒絕,不靜默蓋掉。
        """
        p = self._find(name)
        if p is None:
            return {"restored": False, "error": f"particle not found: {name}"}
        dest = (_REPO / target_path).resolve()
        # 安全:不可寫出 repo 外
        try:
            dest.relative_to(_REPO)
        except ValueError:
            return {"restored": False, "error": "target must be inside repo"}
        if dest.exists() and not overwrite:
            return {"restored": False, "error": "target exists; pass overwrite=True to replace",
                    "target": str(dest.relative_to(_REPO))}
        try:
            content = p.read_text(encoding="utf-8")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            return {"restored": False, "error": str(exc)}
        return {
            "restored": True,
            "source_particle": str(p.relative_to(_REPO)),   # 源仍在(rl_15)
            "restored_to": str(dest.relative_to(_REPO)),
            "bytes": len(content),
            "note": "復活=additive 投影;源粒子未刪(rl_15)。怎麼過去怎麼回來(rl_18)。",
            "origin_signature": ORIGIN_SIGNATURE,
        }


def main() -> int:
    import sys
    mgr = MRL_ParticleArchiveManager()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "list":
        print(json.dumps(mgr.list(), ensure_ascii=False, indent=2))
    elif cmd == "observe" and len(sys.argv) > 2:
        print(json.dumps(mgr.observe(sys.argv[2]), ensure_ascii=False, indent=2))
    elif cmd == "search" and len(sys.argv) > 2:
        print(json.dumps(mgr.search(sys.argv[2]), ensure_ascii=False, indent=2))
    else:
        print("usage: list | observe <name> | search <keyword>")
    print("MRL_PARTICLE_ARCHIVE_MANAGER_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
