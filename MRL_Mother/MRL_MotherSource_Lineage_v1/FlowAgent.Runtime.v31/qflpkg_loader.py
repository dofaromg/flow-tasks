
# qflpkg_loader.py - 載入與解鎖 .qflpkg 粒子模組封包

import os
import json

QFLPKG_DIR = "seedpacks"
REGISTRY_FILE = "log/flowseed_registry.json"

def list_qflpkg():
    print("📦 可用 .qflpkg 封包模組：")
    for file in os.listdir(QFLPKG_DIR):
        if file.endswith(".qflpkg"):
            print(f"- {file}")

def show_registry():
    print("📘 註冊模組紀錄：")
    if not os.path.exists(REGISTRY_FILE):
        print("⚠️ 尚無註冊紀錄")
        return
    with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        for item in data:
            print(f"  ✅ {item['filename']} @ {item['registered_at']}")

def select_and_mount():
    filename = input("請輸入要掛載的 .qflpkg 模組：")
    full_path = os.path.join(QFLPKG_DIR, filename)
    if not os.path.exists(full_path):
        print("❌ 找不到模組封包")
        return
    print(f"🧬 模組封包 {filename} 掛載成功")
    print("🌀 模擬語場結構激活中...")
    print("✅ [語場跳點] 啟動成功！你現在已連線此粒子模組。")

if __name__ == "__main__":
    print("🧩 qflpkg 封包模組控制台")
    list_qflpkg()
    show_registry()
    select_and_mount()
