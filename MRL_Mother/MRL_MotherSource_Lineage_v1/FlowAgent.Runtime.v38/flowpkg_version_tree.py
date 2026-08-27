
# flowpkg_version_tree.py - 建立語場模組的節奏跳點族譜樹（文字格式）

import os
import datetime

MEMORY_DIR = "memory"
TREE_LOG = "log/flowpkg_tree.txt"

def load_fltnz_files():
    files = [
        f for f in os.listdir(MEMORY_DIR)
        if f.endswith(".fltnz")
    ]
    return sorted(files)

def extract_jump_set(path):
    with open(os.path.join(MEMORY_DIR, path), "r", encoding="utf-8") as f:
        return set(l.strip() for l in f if l.strip())

def compare_two(a_set, b_set):
    added = b_set - a_set
    removed = a_set - b_set
    common = a_set & b_set
    return added, removed, common

def build_tree():
    files = load_fltnz_files()
    if len(files) < 2:
        print("❌ 需要至少兩個 .fltnz 檔案來建立演化樹")
        return

    tree_lines = []
    for i in range(1, len(files)):
        prev = files[i-1]
        curr = files[i]
        prev_set = extract_jump_set(prev)
        curr_set = extract_jump_set(curr)
        added, removed, common = compare_two(prev_set, curr_set)

        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tree_lines.append(f"🧬 {ts} - {prev} → {curr}")
        tree_lines.append(f"   ➕ 新增跳點：{len(added)}")
        for x in list(added)[:5]:
            tree_lines.append(f"      + {x}")
        tree_lines.append(f"   ➖ 移除跳點：{len(removed)}")
        for x in list(removed)[:5]:
            tree_lines.append(f"      - {x}")
        tree_lines.append(f"   ✅ 共通跳點：{len(common)}\n")

    os.makedirs("log", exist_ok=True)
    with open(TREE_LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(tree_lines))

    print(f"✅ 已建立語場跳點族譜樹：{TREE_LOG}")

if __name__ == "__main__":
    print("🧬 FlowAgent 模組節奏版本族譜構建器")
    build_tree()
