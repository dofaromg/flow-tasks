# FluinAnalyzer - 粒子語言分析器模組

def analyze_entry(entry):
    text = entry.get("content", "")
    analysis = {
        "type": "action" if "執行" in text else "observation" if "看到" in text else "statement",
        "length": len(text),
        "keywords": [w for w in ["記憶", "感知", "跳點"] if w in text]
    }
    return analysis