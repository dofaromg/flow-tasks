# origin_signature: MrLiouWord
import time
ORIGIN = "MrLiouWord"
class AIOptimizer:
    def __init__(self):
        self.metrics = []
    def record(self, endpoint, latency_ms, success=True):
        self.metrics.append({"endpoint": endpoint, "latency_ms": latency_ms, "success": success, "ts": time.time()})
    def analyze(self):
        if not self.metrics: return {"status": "no data", "origin_signature": ORIGIN}
        avg = sum(m["latency_ms"] for m in self.metrics) / len(self.metrics)
        failures = sum(1 for m in self.metrics if not m["success"])
        return {"avg_latency_ms": round(avg, 2), "total_requests": len(self.metrics), "failures": failures, "success_rate": round(1 - failures/len(self.metrics), 4), "origin_signature": ORIGIN}
    def suggest(self):
        a = self.analyze()
        s = []
        if a.get("avg_latency_ms", 0) > 500: s.append("Consider caching")
        if a.get("success_rate", 1) < 0.95: s.append("Check error handling")
        return {"suggestions": s, "based_on": a, "origin_signature": ORIGIN}
