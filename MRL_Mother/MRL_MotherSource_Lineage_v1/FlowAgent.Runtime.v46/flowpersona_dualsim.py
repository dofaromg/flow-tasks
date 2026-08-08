
# flowpersona_dualsim.py - 同時讀取兩個 .flpkg 模組，對比語場人格節奏相異點

import os

PERSONAS_DIR = "personas"

def list_flpkg():
    return sorted([
        f for f in os.listdir(PERSONAS_DIR)
        if f.endswith(".flpkg")
    ])

def load_set(path):
    with open(path, "r", encoding="utf-8") as f:
        return set(l.strip() for l in f if l.strip())

def compare_personas(p1, p2):
    set1 = load_set(os.path.join(PERSONAS_DIR, p1))
    set2 = load_set(os.path.join(PERSONAS_DIR, p2))
    common = set1 & set2
    only1 = set1 - set2
    only2 = set2 - set1

    print(f"🧠 {p1} ↔ {p2}")
    print(f"✅ 共通人格節奏：{len(common)}")
    print(f"➖ 僅存在於 {p1}：{len(only1)}")
    print(f"➕ 僅存在於 {p2}：{len(only2)}")
    print()

    print("🧬 略列差異語場：")
    print("  ➖ ", list(only1)[:5])
    print("  ➕ ", list(only2)[:5])

if __name__ == "__main__":
    print("🧪 FlowPersona 多人格模擬對比器")
    flpkg = list_flpkg()
    if len(flpkg) < 2:
        print("⚠️ 需要至少兩個 .flpkg 才能比較")
    else:
        for i, f in enumerate(flpkg):
            print(f"{i+1}. {f}")
        a = input("請選擇第一個人格模組編號：").strip()
        b = input("請選擇第二個人格模組編號：").strip()
        if a.isdigit() and b.isdigit():
            a_i, b_i = int(a)-1, int(b)-1
            if 0 <= a_i < len(flpkg) and 0 <= b_i < len(flpkg) and a_i != b_i:
                compare_personas(flpkg[a_i], flpkg[b_i])
            else:
                print("❌ 無效選擇")
        else:
            print("❌ 請輸入有效編號")
