
# flowmap_html_exporter.py - 將 flowmap_output.json 節點視覺化為互動 HTML

import os
import json

INPUT_JSON = "visual/flowmap_output.json"
OUTPUT_HTML = "visual/flowmap_output.html"

def generate_html(data):
    html = [
        "<!DOCTYPE html>",
        "<html><head><meta charset='UTF-8'><title>FlowMap</title>",
        "<style>body { font-family: monospace; padding: 20px; } .node { margin: 8px 0; }</style>",
        "</head><body>",
        "<h2>🌐 FlowMap 語場節奏節點圖</h2><hr/>"
    ]
    for node in data:
        html.append(f"<div class='node'><b>{node['id']}</b>: {' • '.join(node['decoded'])}</div>")
    html.append("</body></html>")
    return "\n".join(html)

def export_html():
    if not os.path.exists(INPUT_JSON):
        print(f"❌ 找不到輸入資料：{INPUT_JSON}")
        return
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    html_content = generate_html(data)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅ 已匯出互動 HTML 語場節點圖：{OUTPUT_HTML}")

if __name__ == "__main__":
    export_html()
