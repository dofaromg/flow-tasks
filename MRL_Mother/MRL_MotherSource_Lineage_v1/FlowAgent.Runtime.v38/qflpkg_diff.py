
# qflpkg_diff.py - 比對兩顆 .qflpkg 粒子模組封包的內容差異（以 fltnz 為準）

def load_lines(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except:
        print(f"❌ 無法讀取：{path}")
        return []

def diff_lines(a, b):
    set_a = set(a)
    set_b = set(b)
    only_in_a = sorted(set_a - set_b)
    only_in_b = sorted(set_b - set_a)
    return only_in_a, only_in_b

if __name__ == "__main__":
    print("🧬 FlowSeed 粒子模組差異比對工具")
    path1 = input("請輸入第一顆 .qflpkg（或 fltnz 檔）路徑：")
    path2 = input("請輸入第二顆 .qflpkg（或 fltnz 檔）路徑：")

    lines1 = load_lines(path1)
    lines2 = load_lines(path2)

    if lines1 and lines2:
        a_diff, b_diff = diff_lines(lines1, lines2)
        print(f"✅ 差異比對完成")
        print(f"📂 只存在於 {path1} 的節奏：")
        for l in a_diff:
            print("  ➖", l)
        print(f"📂 只存在於 {path2} 的節奏：")
        for l in b_diff:
            print("  ➕", l)
