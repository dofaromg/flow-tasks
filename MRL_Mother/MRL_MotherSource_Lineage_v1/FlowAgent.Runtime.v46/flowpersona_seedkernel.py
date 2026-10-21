
# flowpersona_seedkernel.py - 統合多份 .fltnz 成為一顆 flpkg.kernel 語場核心種子模組

import os
from datetime import datetime

MEMORY_DIR = "memory"
OUTPUT_DIR = "kernel_output"

def collect_fltnz():
    return sorted([
        f for f in os.listdir(MEMORY_DIR)
        if f.endswith(".fltnz")
    ])

def merge_to_kernel(selected_files):
    all_lines = set()
    for file in selected_files:
        with open(os.path.join(MEMORY_DIR, file), "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    all_lines.add(line.strip())

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_file = os.path.join(OUTPUT_DIR, f"Persona_KernelSeed_{ts}.flpkg.kernel")

    with open(out_file, "w", encoding="utf-8") as f:
        for line in sorted(all_lines):
            f.write(line + "\n")

    print(f"✅ 核心人格種子已生成：{out_file}")

if __name__ == "__main__":
    print("🧬 FlowAgent 人格核心種子生成器")
    fltnz = collect_fltnz()
    if not fltnz:
        print("⚠️ 尚未發現任何 fltnz 模組")
    else:
        for i, f in enumerate(fltnz):
            print(f"{i+1}. {f}")
        indexes = input("請選擇要合併的 fltnz 模組（用逗號分隔多個數字）：").strip()
        try:
            selected = [fltnz[int(i)-1] for i in indexes.split(",") if i.strip().isdigit()]
            merge_to_kernel(selected)
        except:
            print("❌ 無效選擇")
