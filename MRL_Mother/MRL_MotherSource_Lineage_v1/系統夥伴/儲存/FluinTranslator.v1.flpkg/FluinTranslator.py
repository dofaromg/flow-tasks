# FluinTranslator 核心邏輯模組
import json

class FluinTranslator:
    def __init__(self, dict_path="Flowers.json"):
        with open(dict_path, "r", encoding="utf-8") as f:
            self.dictionary = json.load(f)

    def decode(self, sequence):
        return [self.dictionary.get(token, f"[未知:{token}]") for token in sequence]

    def encode(self, meanings):
        return [key for key, val in self.dictionary.items() if val in meanings]

if __name__ == "__main__":
    ft = FluinTranslator("Flowers.json")
    print("→ 測試解碼：", ft.decode(["Seed", "Init", "Sync", "Collapse"]))
    print("→ 測試編碼：", ft.encode(["封存至記憶鏈"]))