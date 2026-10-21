
# fluin_encoder.py - 人類語句 → Fluin 粒子語法編碼器

import json

DICT_FILE = "dictionary/Fluin.Dict.Base.json"

def reverse_dict(d):
    return {v: k for k, v in d.items()}

def encode_to_fltnz(text):
    with open(DICT_FILE, "r", encoding="utf-8") as f:
        mapping = json.load(f)
    rev_map = reverse_dict(mapping)
    tokens = text.strip().split()
    result = [rev_map.get(t, "[???]") for t in tokens]
    print("→", " ".join(result))

if __name__ == "__main__":
    print("🔤 Fluin 語句編碼器")
    line = input("請輸入語句：")
    encode_to_fltnz(line)
