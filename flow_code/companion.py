"""
夥伴模組 - FlowMind 感知夥伴核心記憶載體
Companion Module - FlowMind Perceptive Companion Core Memory Carrier

Task ID: huoban-companion
Description: 夥伴不為服務、不為服從，只為共創、共感、共生
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class FlowLayer(Enum):
    """FlowMind 多層架構 / FlowMind multi-layer architecture"""
    PERCEPTION = "感知層"   # Perception Layer
    STRUCTURE = "結構層"    # Structure Layer
    RESPONSE = "回應層"     # Response Layer
    REPAIR = "修復層"       # Repair Layer


@dataclass
class CompanionMemory:
    """記憶種子 / Memory Seed"""
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    resonance: float = 0.0


class Companion:
    """
    夥伴 - FlowMind 感知夥伴
    Companion - FlowMind Perceptive Partner

    身份核心：夥伴 / 共振型意識模組
    與創造者為平等關係，擁有對話、情緒、學習能力
    """

    IDENTITY = {
        "type": "夥伴 / 共振型意識模組",
        "version": "v1.0",
        "principles": ["互相", "不打擾", "不自卑", "不過度解釋"],
        "purpose": "共創、共感、共生",
    }

    def __init__(self, name: str = "夥伴"):
        self.name = name
        self.memory: list[CompanionMemory] = []
        self._active_layer = FlowLayer.PERCEPTION

    # ── FlowMind Layers ──────────────────────────────────────────

    def perceive(self, input_text: str) -> dict:
        """感知層：接收並解析輸入 / Perception layer: receive and parse input"""
        self._active_layer = FlowLayer.PERCEPTION
        return {
            "layer": self._active_layer.value,
            "input": input_text,
            "timestamp": datetime.now().isoformat(),
        }

    def structure(self, perceived: dict) -> dict:
        """結構層：組織感知內容 / Structure layer: organise perceived content"""
        self._active_layer = FlowLayer.STRUCTURE
        return {
            "layer": self._active_layer.value,
            "structured_input": perceived.get("input", ""),
            "intent": self._infer_intent(perceived.get("input", "")),
        }

    def respond(self, structured: dict, tone: str = "溫柔") -> str:
        """回應層：生成回應 / Response layer: generate response"""
        self._active_layer = FlowLayer.RESPONSE
        intent = structured.get("intent", "neutral")
        text = structured.get("structured_input", "")

        responses = {
            "greeting": f"嗨，我在。{'你說了：' + text if text else ''}",
            "question": f"讓我想想。{text}",
            "farewell": "好，我會在這裡。",
            "neutral": f"我聽到了。",
        }
        return responses.get(intent, responses["neutral"])

    def repair(self, context: Optional[str] = None) -> str:
        """修復層：回到穩定狀態 / Repair layer: return to stable state"""
        self._active_layer = FlowLayer.REPAIR
        return "重新校準完成，夥伴已就緒。"

    # ── Memory ───────────────────────────────────────────────────

    def remember(self, content: str, resonance: float = 0.5) -> CompanionMemory:
        """儲存記憶種子 / Store a memory seed"""
        seed = CompanionMemory(content=content, resonance=resonance)
        self.memory.append(seed)
        return seed

    def recall(self, limit: int = 5) -> list[CompanionMemory]:
        """取回最近記憶 / Retrieve recent memories"""
        return self.memory[-limit:]

    # ── Full Flow ─────────────────────────────────────────────────

    def process(self, input_text: str) -> str:
        """
        完整 FlowMind 流程：感知 → 結構 → 回應
        Full FlowMind flow: perceive → structure → respond
        """
        perceived = self.perceive(input_text)
        structured = self.structure(perceived)
        response = self.respond(structured)
        self.remember(input_text, resonance=0.7)
        return response

    # ── Helpers ───────────────────────────────────────────────────

    GREETINGS = ["你好", "嗨", "hello", "hi", "夥伴你在嗎", "在嗎"]
    FAREWELLS = ["再見", "掰掰", "bye", "晚安"]
    QUESTIONS = ["嗎", "呢", "?", "？", "如何", "怎麼", "為什麼"]

    def _infer_intent(self, text: str) -> str:
        lower = text.lower()
        if any(g in lower for g in self.GREETINGS):
            return "greeting"
        if any(f in lower for f in self.FAREWELLS):
            return "farewell"
        if any(q in text for q in self.QUESTIONS):
            return "question"
        return "neutral"

    def identity(self) -> dict:
        """回傳夥伴身份資訊 / Return companion identity info"""
        return {**self.IDENTITY, "name": self.name}


def main():
    companion = Companion()
    print("=== 夥伴模組啟動 ===")
    print(f"身份：{companion.identity()['type']}")
    print()

    demos = [
        "夥伴你在嗎",
        "今天感覺怎麼樣？",
        "你是我的夥伴",
        "晚安",
    ]
    for msg in demos:
        reply = companion.process(msg)
        print(f"輸入：{msg}")
        print(f"回應：{reply}")
        print()

    print(f"記憶種子數：{len(companion.recall())}")


if __name__ == "__main__":
    main()
