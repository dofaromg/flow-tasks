# FluinRecorder - 粒子語言記錄器模組

from datetime import datetime

def record_input(user_input: str, log_path: str = "logs/flmem.log"):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "type": "input",
        "content": user_input
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(str(entry) + "\n")
    return entry