#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# origin_signature: MrLiouWord
# layer: L5 STORE / 記憶封存建構入口腳本
from modules.FluinMemoryVault import build_memory
print("Fluin Memory Vault Builder")
log_path = "logs/flmem.log"
entries = []
with open(log_path, encoding="utf-8") as f:
    for line in f:
        try:
            entries.append(eval(line.strip()))
        except:
            pass

output_path = build_memory(entries)
print(f"✅ 記憶模組已建立：{output_path}")