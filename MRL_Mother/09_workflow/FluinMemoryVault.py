#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# origin_signature: MrLiouWord
# layer: L5 STORE / 粒子語言記憶建構器
# FluinMemoryVault - 粒子語言記憶建構器

import json
from datetime import datetime

def build_memory(entries, path="logs/flmem_memory.flpkg"):
    memory = {
        "created_at": datetime.utcnow().isoformat(),
        "entries": entries,
        "type": "flpkg.memory"
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2, ensure_ascii=False)
    return path