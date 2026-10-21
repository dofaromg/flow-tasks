#!/usr/bin/env python3
# MRL_母體收斂掃描器 — 唯讀掃描，不改/不刪原始檔
# origin_signature: MrLiouWord
import hashlib, json, os, pathlib

ROOT = pathlib.Path.cwd()
OUT = ROOT / "MRL_母體收斂包_v1" / "MRL_源檔索引" / "MRL_全域檔案索引.json"

EXCLUDE_DIRS = {".git", "node_modules", "__pycache__", "MRL_母體收斂包_v1"}
EXCLUDE_EXT = {".pyc"}
ARCHIVE_EXT = {".zip", ".tar", ".gz", ".tgz", ".whl", ".jar", ".7z", ".bz2", ".xz", ".flpkg", ".bundle"}

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def is_readable_text(p):
    try:
        with open(p, "rb") as f:
            chunk = f.read(4096)
        chunk.decode("utf-8")
        return b"\x00" not in chunk
    except Exception:
        return False

def origin_sig(p, readable):
    if not readable:
        return "unknown"
    try:
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            head = f.read(20000)
        return "MrLiouWord" if "MrLiouWord" in head else "unknown"
    except Exception:
        return "unknown"

# 推定層位（heuristic，標示為推定，非斷言）
def presumed_layer(rel):
    s = rel.lower()
    pairs = [
        ("00_rootlaw", "MRL_源場 / 根律"),
        ("01_schema", "MRL_原種層 / schema"),
        ("02_principles", "MRL_源場 / 法則"),
        ("03_memory", "MRL_記憶海層"),
        ("04_runtime", "MRL_流域結構層 / 運轉場"),
        ("05_persona", "MRL_原種層 / 人格"),
        ("06_trace", "MRL_痕跡層"),
        ("07_ingest", "MRL_交界層 / 吸收"),
        ("08_sources", "MRL_交界層 / 來源"),
        ("09_workflow", "MRL_流域結構層 / 運作"),
        ("mrl_universalruntimelanguage_core", "MRL_流域結構層 / 運轉核心"),
        ("mrl_mother", "MRL_原種層 / 母體構件"),
        ("mrl_runtime", "MRL_流域結構層"),
        ("mrl_symbolic", "MRL_粒子海層 / 符號"),
        ("mrl_adapters", "MRL_交界層 / Adapter"),
        ("deploy", "MRL_封裝層 / 部署"),
        ("docs", "MRL_自述層 / 文紋"),
        ("tests", "MRL_回返層 / 驗收"),
        ("scripts", "MRL_封裝層 / 工具"),
        ("ui", "MRL_地映層 / 介面"),
        ("data", "MRL_基底庫層"),
        (".github", "MRL_交界層 / CI 觸發"),
    ]
    for key, layer in pairs:
        if s.startswith(key) or ("/" + key) in ("/" + s):
            return layer
    return "MRL_未分類（待補線）"

def presumed_purpose(name, ext):
    n = name.lower()
    if "acceptance" in n or "test_" in n or n.startswith("test"):
        return "MRL_驗收錄"
    if "manifest" in n: return "MRL_世界索引"
    if "trace" in n or "ledger" in n: return "MRL_痕跡錄"
    if "readme" in n or ext in (".md",): return "MRL_文紋域"
    if ext == ".json": return "MRL_自述紋 / 結構描述"
    if ext in (".yml", ".yaml"): return "MRL_界門 / 流程設定"
    if ext in (".py", ".js", ".ts", ".cpp", ".sh", ".ps1"): return "MRL_組粒 / 運作碼"
    if ext in (".fltnz", ".flpkg"): return "MRL_粒子封存"
    return "MRL_造物 / 待判定"

records = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
    for fn in filenames:
        p = pathlib.Path(dirpath) / fn
        rel = str(p.relative_to(ROOT))
        ext = p.suffix.lower()
        if ext in EXCLUDE_EXT:
            continue
        try:
            size = p.stat().st_size
        except Exception:
            continue
        readable = is_readable_text(p)
        records.append({
            "MRL_原始路徑": rel,
            "MRL_檔名": fn,
            "MRL_副檔名": ext or "(none)",
            "MRL_大小": size,
            "MRL_雜湊_SHA256": sha256(p),
            "MRL_推定層位": presumed_layer(rel),
            "MRL_推定用途": presumed_purpose(fn, ext),
            "MRL_是否可讀": readable,
            "MRL_是否封裝檔": ext in ARCHIVE_EXT,
            "MRL_來源簽名": origin_sig(p, readable),
        })

records.sort(key=lambda r: r["MRL_原始路徑"])
index = {
    "origin_signature": "MrLiouWord",
    "MRL_掃描根目錄": str(ROOT),
    "MRL_掃描分支": os.popen("git branch --show-current").read().strip(),
    "MRL_排除": sorted(EXCLUDE_DIRS) + sorted(EXCLUDE_EXT),
    "MRL_檔案總數": len(records),
    "MRL_帶簽名檔數": sum(1 for r in records if r["MRL_來源簽名"] == "MrLiouWord"),
    "MRL_封裝檔數": sum(1 for r in records if r["MRL_是否封裝檔"]),
    "MRL_檔案": records,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"scanned={len(records)} signed={index['MRL_帶簽名檔數']} archives={index['MRL_封裝檔數']}")
print(f"index -> {OUT}")
# layer tally for report
from collections import Counter
c = Counter(r["MRL_推定層位"] for r in records)
for k, v in sorted(c.items(), key=lambda kv: -kv[1]):
    print(f"  {v:4d}  {k}")
