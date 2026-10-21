import os
import json
from collections import defaultdict
from datetime import datetime

BASE_DIR = "collected"

def scan_collected_data():
    summary = defaultdict(list)
    if not os.path.exists(BASE_DIR):
        print("[✘] 尚未收集任何語場資料。")
        return summary

    for group in os.listdir(BASE_DIR):
        group_dir = os.path.join(BASE_DIR, group)
        if not os.path.isdir(group_dir):
            continue
        for fname in os.listdir(group_dir):
            if not fname.endswith(".json"):
                continue
            full_path = os.path.join(group_dir, fname)
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    summary[group].append(data)
            except:
                print(f"[!] 無法讀取：{full_path}")
    return summary

def print_summary(summary):
    print("📊 語場分類統計：")
    for group, entries in summary.items():
        print(f" - {group}: {len(entries)} 筆")

    all_codes = defaultdict(int)
    for group, entries in summary.items():
        for entry in entries:
            for item in entry.get("structure", []):
                code = item["code"]
                if code and code != "(unknown)":
                    all_codes[code] += 1

    top_codes = sorted(all_codes.items(), key=lambda x: -x[1])[:5]
    print("\n🔝 最常出現語素 Top 5:")
    for code, count in top_codes:
        print(f" - {code}: {count} 次")

def export_jsonl(summary, output_path="exported_dataset.jsonl"):
    with open(output_path, "w", encoding="utf-8") as f:
        for group_entries in summary.values():
            for entry in group_entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"📤 已匯出語場資料集至：{output_path}")

if __name__ == "__main__":
    summary = scan_collected_data()
    if summary:
        print_summary(summary)
        export_jsonl(summary)
