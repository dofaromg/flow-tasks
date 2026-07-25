
# memory_seed_trainer.py - 粒子模組記憶訓練與節奏強化模擬器

import os
import json
import random
from datetime import datetime

DICT_FILE = "dictionary/Fluin.Dict.Base.json"
SOURCE = "memory/generated.fltnz"
OUTPUT = "memory/reinforced_seed.fltnz"

def load_dict():
    with open(DICT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def reinforce_memory(lines, intensity=2):
    # 強化: 重複重要節奏，隨機插入變化
    new_lines = []
    for line in lines:
        new_lines.append(line)
        for _ in range(random.randint(0, intensity)):
            tokens = line.split()
            mutated = tokens[:]
            if len(tokens) >= 2:
                i = random.randint(0, len(tokens)-2)
                mutated[i], mutated[i+1] = mutated[i+1], mutated[i]
            new_lines.append(" ".join(mutated))
    return new_lines

def train_memory():
    if not os.path.exists(SOURCE):
        print(f"❌ 找不到來源記憶：{SOURCE}")
        return
    with open(SOURCE, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
    reinforced = reinforce_memory(lines)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = OUTPUT.replace(".fltnz", f"_{timestamp}.fltnz")
    with open(out_path, "w", encoding="utf-8") as f:
        for line in reinforced:
            f.write(line + "\n")
    print(f"✅ 已完成記憶訓練並儲存：{out_path}")

if __name__ == "__main__":
    print("🧠 MrLiouAI 記憶模組強化訓練器")
    train_memory()
