
# flowpkg_diff_tracker.py - 模組語場異動比對工具：比對兩份 .fltnz 檔案的差異跳點

import os

def read_lines(path):
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def compare_fltnz(path1, path2):
    if not os.path.exists(path1) or not os.path.exists(path2):
        print("❌ 檔案不存在")
        return

    lines1 = set(read_lines(path1))
    lines2 = set(read_lines(path2))

    only_in_1 = sorted(lines1 - lines2)
    only_in_2 = sorted(lines2 - lines1)
    common = sorted(lines1 & lines2)

    print(f"🔍 比對結果：")
    print(f"  ✅ 共通語場跳點：{len(common)}")
    print(f"  ➖ 僅存在於 {os.path.basename(path1)}：{len(only_in_1)}")
    for l in only_in_1[:10]:
        print(f"     - {l}")
    print(f"  ➕ 僅存在於 {os.path.basename(path2)}：{len(only_in_2)}")
    for l in only_in_2[:10]:
        print(f"     + {l}")
    if len(only_in_1) > 10 or len(only_in_2) > 10:
        print("  ...")

if __name__ == "__main__":
    print("🧠 模組封裝跳點演化比對器")
    p1 = input("請輸入第一份 fltnz 檔案路徑：").strip()
    p2 = input("請輸入第二份 fltnz 檔案路徑：").strip()
    compare_fltnz(p1, p2)
