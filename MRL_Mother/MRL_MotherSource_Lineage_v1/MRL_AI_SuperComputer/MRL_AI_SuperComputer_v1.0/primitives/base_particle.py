# origin_signature: MrLiouWord
import hashlib, time
ORIGIN = "MrLiouWord"
class BaseParticle:
    def __init__(self, content, particle_type="base"):
        self.id = f"p.{hashlib.md5(str(content).encode()).hexdigest()[:8]}"
        self.content = content
        self.type = particle_type
        self.created = time.time()
        self.origin_signature = ORIGIN
        self.simhash = int(hashlib.sha256(str(content).encode()).hexdigest()[:16], 16)
    def to_dict(self):
        return {"id": self.id, "content": self.content, "type": self.type, "simhash": hex(self.simhash), "origin_signature": self.origin_signature}
    def merge(self, other):
        return BaseParticle(f"{self.content}+{other.content}", f"{self.type}.merged")
    def clone(self):
        return BaseParticle(self.content, self.type)
