import json
from collections import Counter
from typing import List

def load_structure(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def extract_codes(structure: List[dict]):
    return [entry["code"] for entry in structure if entry["code"] not in ("(unknown)", "")]

def score_overlap(codes1, codes2):
    counter1 = Counter(codes1)
    counter2 = Counter(codes2)
    common = set(codes1) & set(codes2)
    score = sum(min(counter1[c], counter2[c]) for c in common)
    return score / max(len(codes1), len(codes2), 1)

def can_resonate(file1, file2, threshold=0.4):
    s1 = load_structure(file1)
    s2 = load_structure(file2)
    codes1 = extract_codes(s1)
    codes2 = extract_codes(s2)
    print(f"🧬 模組1 語素：{codes1}")
    print(f"🧬 模組2 語素：{codes2}")
    score = score_overlap(codes1, codes2)
    print(f"🔁 共振相似度分數：{score:.2f}")
    return score >= threshold

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("用法：python resonance_test.py file1.json file2.json")
        sys.exit(1)

    f1, f2 = sys.argv[1], sys.argv[2]
    result = can_resonate(f1, f2)
    print("✅ 可以共振！" if result else "⛔ 無法共振。")
