import os
import json

def scan_collected(base_dir="collected"):
    results = []
    if not os.path.exists(base_dir):
        print("[✘] 沒有 collected 資料夾")
        return results

    for group in os.listdir(base_dir):
        path = os.path.join(base_dir, group)
        if not os.path.isdir(path):
            continue
        for fname in os.listdir(path):
            if fname.endswith(".json"):
                full = os.path.join(path, fname)
                try:
                    with open(full, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        results.append(data)
                except:
                    continue
    return results

def export_jsonl(data, out_path="exported_dataset.jsonl"):
    with open(out_path, "w", encoding="utf-8") as f:
        for item in data:
            record = {
                "input": item.get("input", ""),
                "fltnz": " ".join(item.get("fltnz", []))
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"📤 已成功匯出語場語料集：{out_path}")

if __name__ == "__main__":
    data = scan_collected()
    if data:
        export_jsonl(data)
    else:
        print("⚠️ 沒有可用資料可以匯出。")
