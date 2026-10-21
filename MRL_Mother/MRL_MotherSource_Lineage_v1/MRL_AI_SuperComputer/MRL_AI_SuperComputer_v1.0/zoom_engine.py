# origin_signature: MrLiouWord
# ZoomEngine — Four-level particle zoom with golden ratio scaling

ORIGIN = "MrLiouWord"
GOLDEN = 1.618

class ZoomLevel:
    MICRO = "micro"
    CORE = "core"
    MACRO = "macro"
    ABSTRACT = "abstract"
    ALL = [MICRO, CORE, MACRO, ABSTRACT]

class ZoomEngine:
    def __init__(self):
        self.current_level = ZoomLevel.CORE
        self.history = []
        self.projection_mode = "semantic"
    def zoom_to(self, level, particles=None):
        if level not in ZoomLevel.ALL:
            return {"error": f"invalid level, use {ZoomLevel.ALL}"}
        prev = self.current_level
        self.current_level = level
        idx = ZoomLevel.ALL.index(level)
        scale = GOLDEN ** idx
        result = {"level": level, "previous": prev, "scale": round(scale, 4),
                  "projection": self.projection_mode, "origin_signature": ORIGIN}
        if particles:
            result["visible"] = [p for p in particles if p.get("layer", 0) <= idx + 2]
            result["hidden"] = [p for p in particles if p.get("layer", 0) > idx + 2]
            result["visible_count"] = len(result["visible"])
            result["hidden_count"] = len(result["hidden"])
        self.history.append({"from": prev, "to": level, "scale": scale})
        return result
    def get_state(self):
        return {"current_level": self.current_level, "projection": self.projection_mode,
                "history_count": len(self.history), "origin_signature": ORIGIN}
