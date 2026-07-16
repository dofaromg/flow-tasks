import json

# 詞庫結構（type = 詞性、category = 概念分類、module = 對應封裝）
particle_dict = {
    "內省的": {
        "code": "⋄fx.adj.112",
        "type": "adjective",
        "category": "emotion",
        "module": ".flmod",
        "pcode": "MOV FX.ADJ.112"
    },
    "記憶": {
        "code": "⋄fx.noun.024",
        "type": "noun",
        "category": "memory",
        "module": ".flnode",
        "pcode": "MOV FX.NOUN.024"
    },
    "節點": {
        "code": "⋄fx.noun.024",
        "type": "noun",
        "category": "structure",
        "module": ".flnode",
        "pcode": "MOV FX.NOUN.024"
    },
    "封存": {
        "code": "⋄fx.flow.007",
        "type": "verb",
        "category": "storage",
        "module": ".flflow",
        "pcode": "CALL FX.FLOW.007"
    },
    "導出": {
        "code": "⋄fx.flow.007",
        "type": "verb",
        "category": "transfer",
        "module": ".flflow",
        "pcode": "CALL FX.FLOW.007"
    },
    "我": {
        "code": "⋄fx.per.001",
        "type": "pronoun",
        "category": "self",
        "module": ".flper",
        "pcode": "MOV FX.PER.001"
    },
    "現在": {
        "code": "⋄fx.time.010",
        "type": "adverb",
        "category": "time",
        "module": ".fltime",
        "pcode": "JMP FX.TIME.010"
    },
    "並且": {
        "code": "⋄fx.gate.001",
        "type": "conjunction",
        "category": "logic",
        "module": ".flgate",
        "pcode": "GATE FX.GATE.001"
    }
}

def advanced_parse(text):
    tokens = text.strip().split()
    fltnz_chain = []
    detailed_output = []

    for word in tokens:
        if word in particle_dict:
            entry = particle_dict[word]
            fltnz_chain.append(entry["code"])
            detailed_output.append({
                "word": word,
                **entry
            })
        elif word in ["被", "∴"]:
            fltnz_chain.append("∴")
            detailed_output.append({
                "word": word,
                "code": "∴",
                "type": "logic",
                "category": "causal",
                "module": ".flgate",
                "pcode": "JMP FLYNZ.CAUSE"
            })
        else:
            detailed_output.append({
                "word": word,
                "code": "(unknown)",
                "type": "",
                "category": "",
                "module": "",
                "pcode": ""
            })

    return fltnz_chain, detailed_output

if __name__ == "__main__":
    text = "內省的 記憶 被 封存"
    fltnz, details = advanced_parse(text)
    print("🧠 FLTNZ:", " ".join(fltnz))
    print("📦 詳細解析:")
    print(json.dumps(details, indent=2, ensure_ascii=False))
