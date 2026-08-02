
# mrliouai_console.py - MrLiouAI 總模組 CLI 控制台

import os

OPTIONS = {
    "1": ("列出已註冊模組", "qflpkg_loader.py"),
    "2": ("封裝最新合併語場", "flpkg_autopack.py"),
    "3": ("還原封包為 fltnz", "flpkg_unpacker.py"),
    "4": ("比對語場差異", "qflpkg_diff.py"),
    "5": ("合併語場節奏", "qflpkg_diffmerge.py"),
    "6": ("批次註冊所有 qflpkg", "qflpkg_manager.py"),
    "7": ("啟動人格掛載 CLI", "persona_manager.py"),
    "8": ("模組記憶融合模擬", "fusion_engine.py"),
    "9": ("語場自動生成器", "fluin_expander.py"),
    "10": ("語句 → 粒子 編碼器", "fluin_encoder.py"),
    "11": ("粒子 → 語句 解碼器", "fluin_decoder.py"),
    "12": ("語法節奏檢查器", "fluin_syntax_checker.py")
}

def run_script(script_name):
    if not os.path.exists(script_name):
        print(f"❌ 找不到模組：{script_name}")
    else:
        os.system(f"python3 {script_name}")

def menu():
    while True:
        print("\n🌀 MrLiouAI CLI 控制台")
        for key, (label, _) in OPTIONS.items():
            print(f"{key}. {label}")
        print("0. 離開")
        choice = input("請輸入選項：").strip()
        if choice == "0":
            break
        elif choice in OPTIONS:
            _, script = OPTIONS[choice]
            run_script(script)
        else:
            print("❌ 無效選項")

if __name__ == "__main__":
    menu()
