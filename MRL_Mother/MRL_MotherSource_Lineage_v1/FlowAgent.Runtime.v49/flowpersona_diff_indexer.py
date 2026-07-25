
# flowpersona_diff_indexer.py - 比對兩顆 fltnz 模組人格差異

import difflib
import os

def load_fltnz(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.readlines()

def compare_fltnz(path1, path2):
    a = load_fltnz(path1)
    b = load_fltnz(path2)
    d = difflib.unified_diff(a, b, fromfile=path1, tofile=path2)
    print("".join(d))

if __name__ == "__main__":
    print("🧠 MrLiouAI 人格模組差異比對工具")
    path1 = input("請輸入第一顆 .fltnz 路徑：").strip()
    path2 = input("請輸入第二顆 .fltnz 路徑：").strip()

    if not os.path.exists(path1) or not os.path.exists(path2):
        print("❌ 找不到檔案，請確認路徑正確")
    else:
        print("🔍 差異比較結果：")
        compare_fltnz(path1, path2)
