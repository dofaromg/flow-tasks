
# fluin_syntax_checker.py - Fluin 粒子語法節奏檢查器

import json

DICT_FILE = "dictionary/Fluin.Dict.Base.json"

def check_syntax(file_path):
    with open(DICT_FILE, "r", encoding="utf-8") as f:
        mapping = json.load(f)
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    valid = set(mapping.keys())
    for idx, line in enumerate(lines, 1):
        tokens = line.strip().split()
        unknown = [t for t in tokens if t not in valid]
        if unknown:
            print(f"❌ 第 {idx} 行無效粒子：{', '.join(unknown)}")
        else:
            print(f"✅ 第 {idx} 行語法正確")

if __name__ == "__main__":
    print("🧪 Fluin 語法結構檢查器")
    path = input("請輸入 .fltnz 檔案路徑：")
    check_syntax(path)
