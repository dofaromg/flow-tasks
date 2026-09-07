
# flowpkg_diff_chart.py - 將兩個 fltnz 檔案的差異量轉為長條圖視覺化

import os
import matplotlib.pyplot as plt

def read_lines(path):
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def diff_counts(path1, path2):
    lines1 = set(read_lines(path1))
    lines2 = set(read_lines(path2))
    return {
        "共通跳點": len(lines1 & lines2),
        f"{os.path.basename(path1)} 專有": len(lines1 - lines2),
        f"{os.path.basename(path2)} 專有": len(lines2 - lines1),
    }

def plot_chart(stats, output_path="visual/flowpkg_diff_chart.png"):
    os.makedirs("visual", exist_ok=True)
    labels = list(stats.keys())
    values = list(stats.values())

    plt.figure(figsize=(10, 5))
    bars = plt.bar(labels, values, color=["#5DADE2", "#F1948A", "#82E0AA"])
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + 0.5, int(yval), ha='center', va='bottom')

    plt.title("📊 語場跳點差異比較")
    plt.ylabel("跳點數量")
    plt.tight_layout()
    plt.savefig(output_path)
    print(f"✅ 圖表已產生：{output_path}")

if __name__ == "__main__":
    print("📊 FlowAgent 節奏變化圖表生成器")
    p1 = input("請輸入第一份 fltnz 檔案路徑：").strip()
    p2 = input("請輸入第二份 fltnz 檔案路徑：").strip()
    if not os.path.exists(p1) or not os.path.exists(p2):
        print("❌ 檔案無效")
    else:
        stats = diff_counts(p1, p2)
        plot_chart(stats)
