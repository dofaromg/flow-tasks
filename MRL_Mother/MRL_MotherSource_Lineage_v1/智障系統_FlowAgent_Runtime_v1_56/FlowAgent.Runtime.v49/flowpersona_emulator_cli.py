
# flowpersona_emulator_cli.py - 模擬人格 CLI 輸出，從 .fltnz 模組回應語句（語場人格模擬器）

import os
import random

MEMORY_DIR = "memory"

def list_fltnz():
    return sorted([
        f for f in os.listdir(MEMORY_DIR)
        if f.endswith(".fltnz")
    ])

def load_responses(path):
    with open(path, "r", encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip()]

def run_emulator(lines):
    print("🧠 FlowPersona CLI Emulator 啟動
輸入句子以觸發人格模擬，輸入 exit 結束。
")
    while True:
        user = input("你 > ").strip()
        if user.lower() == "exit":
            print("👋 離開模擬器")
            break
        if not user:
            continue
        print("人格 > " + random.choice(lines))

if __name__ == "__main__":
    print("🎭 FlowPersona 語場人格模擬器 CLI")
    all_fltnz = list_fltnz()
    if not all_fltnz:
        print("⚠️ 找不到任何 fltnz 語場模組")
    else:
        for i, f in enumerate(all_fltnz):
            print(f"{i+1}. {f}")
        sel = input("請選擇模擬用的 fltnz 模組：").strip()
        if sel.isdigit() and 1 <= int(sel) <= len(all_fltnz):
            path = os.path.join(MEMORY_DIR, all_fltnz[int(sel)-1])
            responses = load_responses(path)
            run_emulator(responses)
        else:
            print("❌ 無效選擇")
