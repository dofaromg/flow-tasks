# origin_signature: MrLiouWord
from .base_particle import BaseParticle
class ClassParticle(BaseParticle):
    def __init__(self, name, methods=None, properties=None):
        super().__init__(f"class:{name}", "class")
        self.name = name
        self.methods = methods or []
        self.properties = properties or []
    def to_dict(self):
        d = super().to_dict()
        d.update({"name": self.name, "methods": self.methods, "properties": self.properties})
        return d
