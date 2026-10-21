
# fluin_decoder.py - 粒子語法 → 人類語句轉換器

import json

DICT_FILE = "dictionary/Fluin.Dict.Base.json"

def decode_fltnz(file_path):
    with open(DICT_FILE, "r", encoding="utf-8") as f:
        mapping = json.load(f)
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for line in lines:
        tokens = line.strip().split()
        result = [mapping.get(t, "[?]") for t in tokens]
        print("→", " ".join(result))

if __name__ == "__main__":
    print("🔎 Fluin 解碼器")
    path = input("請輸入 .fltnz 檔案路徑：")
    decode_fltnz(path)
