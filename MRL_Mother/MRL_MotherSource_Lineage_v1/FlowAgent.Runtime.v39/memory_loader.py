
# memory_loader.py - MrLiouAI 記憶結構還原器

import os

def restore_memory():
    mem_dir = "memory"
    print("🧠 [記憶還原器啟動]")
    if not os.path.exists(mem_dir):
        print("❌ memory 資料夾不存在")
        return
    files = os.listdir(mem_dir)
    if not files:
        print("⚠️ 無記憶封存模組")
    for f in files:
        print(f"📦 還原記憶模組：{f}")

if __name__ == "__main__":
    restore_memory()
