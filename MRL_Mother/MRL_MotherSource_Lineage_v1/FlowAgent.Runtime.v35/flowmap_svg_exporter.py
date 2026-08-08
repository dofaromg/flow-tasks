
# flowmap_svg_exporter.py - 將語場 JSON 節點圖轉為 SVG 節奏可視化圖

import os
import json

INPUT_JSON = "visual/flowmap_output.json"
OUTPUT_SVG = "visual/flowmap_output.svg"

def generate_svg(data):
    node_height = 40
    padding = 20
    width = 800
    height = padding + len(data) * node_height + padding

    svg_elements = []
    svg_elements.append(f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">')
    svg_elements.append('<style>text { font-family: monospace; font-size: 14px; }</style>')

    for i, node in enumerate(data):
        y = padding + i * node_height
        text = " • ".join(node["decoded"])
        svg_elements.append(f'<text x="20" y="{y + 20}">{node["id"]}: {text}</text>')

    svg_elements.append('</svg>')
    return "\n".join(svg_elements)

def export_svg():
    if not os.path.exists(INPUT_JSON):
        print(f"❌ 無法找到 JSON：{INPUT_JSON}")
        return

    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    svg_content = generate_svg(data)
    with open(OUTPUT_SVG, "w", encoding="utf-8") as f:
        f.write(svg_content)

    print(f"✅ 已匯出語場節奏 SVG：{OUTPUT_SVG}")

if __name__ == "__main__":
    export_svg()
