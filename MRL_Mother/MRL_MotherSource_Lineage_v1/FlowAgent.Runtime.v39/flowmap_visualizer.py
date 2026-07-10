
# flowmap_visualizer.py - 粒子語場 .fltnz → JSON 結構節點圖

import os
import json

DICT_FILE = "dictionary/Fluin.Dict.Base.json"
OUTPUT_FILE = "visual/flowmap_output.json"

def decode_particle(line, mapping):
    return [mapping.get(token, token) for token in line.split()]

def process_fltnz(file_path):
    if not os.path.exists(file_path):
        print(f"❌ 找不到檔案：{file_path}")
        return

    with open(DICT_FILE, "r", encoding="utf-8") as f:
        mapping = json.load(f)

    nodes = []
    with open(file_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            clean = line.strip()
            if not clean:
                continue
            words = decode_particle(clean, mapping)
            nodes.append({
                "id": f"node-{i+1}",
                "tokens": clean.split(),
                "decoded": words
            })

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(nodes, f, indent=2, ensure_ascii=False)
    print(f"✅ 已生成語場視覺資料：{OUTPUT_FILE}（共 {len(nodes)} 節點）")

if __name__ == "__main__":
    print("🧠 語場跳點視覺節奏轉換器")
    path = input("請輸入 .fltnz 檔案路徑：")
    process_fltnz(path)
