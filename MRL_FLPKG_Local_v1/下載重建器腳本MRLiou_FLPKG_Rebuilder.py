#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRLiou FLPKG Rebuilder — 粒子封包建構 / 檢視 / 解包
指令：
  1) 建包（把資料夾打成 .flpkg.zip，並生成 manifest.json、index.md）：
     python3 下載重建器腳本MRLiou_FLPKG_Rebuilder.py build <src_dir> --out out.flpkg.zip
  2) 檢視（列出封包內檔案與每個 .flpnz 的第一行）：
     python3 下載重建器腳本MRLiou_FLPKG_Rebuilder.py inspect out.flpkg.zip
  3) 解包（還原到目錄）：
     python3 下載重建器腳本MRLiou_FLPKG_Rebuilder.py extract out.flpkg.zip --dst restored_dir

特性：
  - 自動生成 manifest.json（檔名、大小、sha1、mime、第一行摘要）。
  - 對 .flpnz/.fltnz 嘗試讀第一行，輸出 index.md，便於人類閱讀。
  - 完全本地執行，安全、可追蹤。
"""
import argparse
import hashlib
import io
import json
import mimetypes
import zipfile
from pathlib import Path

def sha1_bytes(b: bytes) -> str:
    import hashlib
    h = hashlib.sha1()
    h.update(b)
    return h.hexdigest()

def first_line_text(b: bytes) -> str:
    try:
        s = b.decode('utf-8', errors='ignore').splitlines()
        return s[0].strip() if s else ''
    except Exception:
        return ''

def build(src_dir: Path, out_zip: Path):
    src_dir = src_dir.resolve()
    out_zip = out_zip.resolve()
    manifest = {"root": str(src_dir), "files": []}

    with zipfile.ZipFile(out_zip, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(src_dir.rglob('*')):
            if not p.is_file():
                continue
            rel = p.relative_to(src_dir).as_posix()
            data = p.read_bytes()
            z.writestr(rel, data)

            mime, _ = mimetypes.guess_type(p.name)
            mime = mime or 'application/octet-stream'
            entry = {
                "path": rel,
                "size": len(data),
                "sha1": sha1_bytes(data),
                "mime": mime,
            }
            if p.suffix.lower() in {'.flpnz', '.fltnz', '.txt', '.md'}:
                entry["preview"] = first_line_text(data)
            manifest["files"].append(entry)

        # 同時寫入 manifest.json 與 index.md
        manifest_bytes = json.dumps(manifest, ensure_ascii=False, indent=2).encode('utf-8')
        z.writestr('manifest.json', manifest_bytes)

        # 簡單索引
        index_lines = ["# FLPKG Index", ""]
        for e in manifest["files"]:
            preview = e.get("preview","")
            index_lines.append(f"- {e['path']}  ({e['size']} bytes, sha1:{e['sha1'][:8]}…)  {preview}")
        z.writestr('index.md', "\n".join(index_lines).encode('utf-8'))

    print(f"[OK] 已建包 → {out_zip}")

def inspect(zip_path: Path):
    with zipfile.ZipFile(zip_path, 'r') as z:
        names = z.namelist()
        print(f"[INFO] 檔案數：{len(names)}")
        if 'manifest.json' in names:
            manifest = json.loads(z.read('manifest.json').decode('utf-8', errors='ignore'))
        else:
            manifest = None
        # 列印摘要
        for name in names:
            if name.endswith('/'):
                continue
            b = z.read(name)
            info = {
                "name": name,
                "size": len(b),
                "sha1": sha1_bytes(b)[:8]
            }
            if name.lower().endswith(('.flpnz','.fltnz','.txt','.md')):
                info["preview"] = first_line_text(b)
            print(json.dumps(info, ensure_ascii=False))

        if manifest:
            print("\n[manifest preview]")
            print(json.dumps(manifest, ensure_ascii=False, indent=2))

def extract(zip_path: Path, dst_dir: Path):
    dst_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(dst_dir)
    print(f"[OK] 已解包 → {dst_dir.resolve()}")

def main():
    ap = argparse.ArgumentParser(description="MRLiou FLPKG 重建器")
    sub = ap.add_subparsers(dest='cmd', required=True)

    b = sub.add_parser('build', help='將資料夾打包成 .flpkg.zip')
    b.add_argument('src', type=str, help='來源資料夾')
    b.add_argument('--out', type=str, default='out.flpkg.zip', help='輸出封包檔名')

    i = sub.add_parser('inspect', help='檢視封包內容')
    i.add_argument('zip', type=str, help='.flpkg.zip 路徑')

    e = sub.add_parser('extract', help='解包封包到資料夾')
    e.add_argument('zip', type=str, help='.flpkg.zip 路徑')
    e.add_argument('--dst', type=str, default='restored', help='輸出資料夾')

    args = ap.parse_args()
    if args.cmd == 'build':
        build(Path(args.src), Path(args.out))
    elif args.cmd == 'inspect':
        inspect(Path(args.zip))
    elif args.cmd == 'extract':
        extract(Path(args.zip), Path(args.dst))

if __name__ == '__main__':
    main()