
# fluin_expander.py - 自動生成粒子語言節奏內容

import json
import random

DICT_FILE = "dictionary/Fluin.Dict.Base.json"
OUTPUT_FILE = "memory/generated.fltnz"

def generate_lines(n=5, tokens_per_line=3):
    with open(DICT_FILE, "r", encoding="utf-8") as f:
        mapping = json.load(f)
    keys = list(mapping.keys())
    result = []
    for _ in range(n):
        line = " ".join(random.choice(keys) for _ in range(tokens_per_line))
        result.append(line)
    return result

def write_output(lines):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")
    print(f"✅ 已生成語場記憶：{OUTPUT_FILE}（共 {len(lines)} 行）")

if __name__ == "__main__":
    print("🧬 Fluin 語場節奏生成器")
    n = input("請輸入要生成的行數（預設 5）：")
    try:
        num = int(n)
    except:
        num = 5
    lines = generate_lines(num)
    for line in lines:
        print("→", line)
    write_output(lines)
