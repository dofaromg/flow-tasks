#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# origin_signature: MrLiouWord
# layer: L6 REFLECT / 分析入口腳本
from modules.FluinAnalyzer import analyze_entry

print("Fluin Memory Analyzer")
log_path = "logs/flmem.log"
entries = []
with open(log_path, encoding="utf-8") as f:
    for line in f:
        try:
            entries.append(eval(line.strip()))
        except:
            pass

for e in entries:
    analysis = analyze_entry(e)
    print(f"- [{analysis['type']}] {e['content']} / Keywords: {analysis['keywords']}")