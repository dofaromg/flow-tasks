
# qflpkg_diffmerge.py - 將兩顆 .fltnz / .qflpkg 差異整合，生成 .diffpack 與合併版本

import os
from datetime import datetime

def load_lines(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except:
        print(f"❌ 無法讀取：{path}")
        return []

def write_file(path, lines):
    with open(path, "w", encoding="utf-8") as f:
        for l in lines:
            f.write(l + "\n")

def diff_merge(path1, path2, output_dir="diffpacks"):
    lines1 = load_lines(path1)
    lines2 = load_lines(path2)
    set1 = set(lines1)
    set2 = set(lines2)

    only_in_1 = sorted(set1 - set2)
    only_in_2 = sorted(set2 - set1)
    merged = sorted(set1.union(set2))

    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    base1 = os.path.splitext(os.path.basename(path1))[0]
    base2 = os.path.splitext(os.path.basename(path2))[0]

    diff1_file = os.path.join(output_dir, f"diff_{base1}_only.fltnz")
    diff2_file = os.path.join(output_dir, f"diff_{base2}_only.fltnz")
    merged_file = os.path.join(output_dir, f"merged_{base1}_{base2}_{ts}.fltnz")

    write_file(diff1_file, only_in_1)
    write_file(diff2_file, only_in_2)
    write_file(merged_file, merged)

    print(f"✅ 差異已儲存：{diff1_file}, {diff2_file}")
    print(f"✅ 合併語場儲存：{merged_file}")
    return merged_file

if __name__ == "__main__":
    print("🌀 FlowSeed 語場差異整合系統")
    path1 = input("請輸入第一顆 fltnz / qflpkg 檔案路徑：")
    path2 = input("請輸入第二顆 fltnz / qflpkg 檔案路徑：")
    diff_merge(path1, path2)
