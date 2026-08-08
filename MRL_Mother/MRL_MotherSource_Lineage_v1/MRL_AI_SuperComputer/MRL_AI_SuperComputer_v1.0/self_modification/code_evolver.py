# origin_signature: MrLiouWord
import json, os, time
ORIGIN = "MrLiouWord"
class CodeEvolver:
    def __init__(self, log_dir=None):
        self.log_dir = log_dir or os.path.dirname(__file__)
        self.mutations = []
    def propose(self, target, mutation_type, description):
        entry = {"target": target, "type": mutation_type, "description": description, "timestamp": time.time(), "status": "proposed", "origin_signature": ORIGIN}
        self.mutations.append(entry)
        return entry
    def apply(self, index):
        if 0 <= index < len(self.mutations):
            self.mutations[index]["status"] = "applied"
            return self.mutations[index]
        return {"error": "invalid index"}
    def log(self):
        return {"mutations": self.mutations, "count": len(self.mutations), "origin_signature": ORIGIN}
