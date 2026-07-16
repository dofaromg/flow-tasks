# origin_signature: MrLiouWord
from .base_particle import BaseParticle
class ModuleParticle(BaseParticle):
    def __init__(self, name, exports=None, imports=None):
        super().__init__(f"module:{name}", "module")
        self.name = name
        self.exports = exports or []
        self.imports = imports or []
    def to_dict(self):
        d = super().to_dict()
        d.update({"name": self.name, "exports": self.exports, "imports": self.imports})
        return d
