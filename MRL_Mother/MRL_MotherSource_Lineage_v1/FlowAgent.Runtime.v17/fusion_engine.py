
# fusion_engine.py - MrLiouAI 人格融合模擬器

import os
import json

MEMORY_DIR = "memory"
MERGED_MEMORY_FILE = "memory/FusedPersona.Memory.json"

def load_memories(memory_files):
    merged = []
    for mfile in memory_files:
        path = os.path.join(MEMORY_DIR, mfile)
        if not os.path.exists(path):
            print(f"⚠️ 找不到記憶檔案：{mfile}")
            continue
        if path.endswith(".json"):
            with open(path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    merged.extend(data)
                    print(f"✅ 載入：{mfile}（節點：{len(data)}）")
                except:
                    print(f"❌ 格式錯誤：{mfile}")
        else:
            with open(path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
                merged.extend(lines)
                print(f"✅ 載入：{mfile}（行數：{len(lines)}）")
    return merged

def save_merged_memory(data):
    with open(MERGED_MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"🧠 已儲存融合記憶：{MERGED_MEMORY_FILE}（共 {len(data)} 條）")

def simulate_conflicts(data):
    print("🌀 模擬人格記憶節奏衝突點...")
    keywords = {}
    for i, d in enumerate(data):
        if isinstance(d, str):
            tokens = d.split()
        elif isinstance(d, dict):
            tokens = d.get("text", "").split()
        else:
            continue
        for t in tokens:
            if t in keywords:
                keywords[t] += 1
            else:
                keywords[t] = 1
    repeated = {k: v for k, v in keywords.items() if v > 2}
    if repeated:
        print("⚠️ 偵測到潛在節奏詞衝突：")
        for k, v in repeated.items():
            print(f"  🔁 {k} 出現 {v} 次")
    else:
        print("✅ 無明顯語場衝突，節奏融合穩定")

if __name__ == "__main__":
    print("🔬 MrLiouAI 人格記憶融合模擬器")
    files = input("請輸入要融合的記憶檔案名稱（以逗號分隔）:
> ").split(",")
    memory_data = load_memories([f.strip() for f in files])
    simulate_conflicts(memory_data)
    save_merged_memory(memory_data)
