# MRLiou 粒子語言管線共用常數
# Shared constants for the particle language pipeline system

from typing import List, Dict

# 核心管線步驟序列 / Core pipeline step sequence
PIPELINE_STEPS: List[str] = ["structure", "mark", "flow", "recurse", "store"]

# 步驟說明映射 / Step explanation mapping
STEP_EXPLANATIONS: Dict[str, str] = {
    "structure": "定義輸入資料結構",
    "mark": "建立邏輯跳點標記",
    "flow": "轉換為流程結構節奏",
    "recurse": "遞歸展開為細部結構",
    "store": "封存至邏輯記憶模組"
}

# 標準壓縮格式 / Standard compressed format
COMPRESSED_SEED = "SEED(X) = STORE(RECURSE(FLOW(MARK(STRUCTURE(X)))))"
