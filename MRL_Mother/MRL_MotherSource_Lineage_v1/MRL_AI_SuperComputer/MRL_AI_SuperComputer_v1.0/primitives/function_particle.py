# origin_signature: MrLiouWord
from .base_particle import BaseParticle
class FunctionParticle(BaseParticle):
    def __init__(self, name, params=None, body=""):
        super().__init__(f"fn:{name}", "function")
        self.name = name
        self.params = params or []
        self.body = body
    def to_dict(self):
        d = super().to_dict()
        d.update({"name": self.name, "params": self.params, "body_len": len(self.body)})
        return d
