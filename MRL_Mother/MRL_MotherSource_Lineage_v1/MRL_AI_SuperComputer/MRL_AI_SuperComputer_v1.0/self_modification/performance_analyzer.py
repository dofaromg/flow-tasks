# origin_signature: MrLiouWord
import time, os
ORIGIN = "MrLiouWord"
class PerformanceAnalyzer:
    def __init__(self):
        self.snapshots = []
    def snapshot(self):
        try:
            import psutil
            cpu, mem = psutil.cpu_percent(), psutil.virtual_memory().percent
        except ImportError:
            cpu, mem = -1, -1
        s = {"cpu_percent": cpu, "memory_percent": mem, "ts": time.time(), "origin_signature": ORIGIN}
        self.snapshots.append(s)
        return s
    def trend(self, last_n=10):
        r = self.snapshots[-last_n:]
        if not r: return {"status": "no data"}
        return {"snapshots": len(r), "avg_cpu": round(sum(s["cpu_percent"] for s in r)/len(r), 2), "avg_mem": round(sum(s["memory_percent"] for s in r)/len(r), 2), "origin_signature": ORIGIN}
