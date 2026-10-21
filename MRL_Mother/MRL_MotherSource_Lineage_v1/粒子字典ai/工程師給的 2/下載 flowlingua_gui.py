import streamlit as st
import json

st.set_page_config(page_title="FlowLingua 翻譯器", layout="centered")

# 詞庫（簡化內嵌）
particle_dict = {
    "內省的": "⋄fx.adj.112",
    "記憶": "⋄fx.noun.024",
    "節點": "⋄fx.noun.024",
    "封存": "⋄fx.flow.007",
    "導出": "⋄fx.flow.007",
    "激烈的": "⋄fx.adj.305",
    "衝突": "⋄fx.noun.091",
    "轉變": "⋄fx.flow.018",
    "我": "⋄fx.per.001",
    "現在": "⋄fx.time.010",
    "並且": "⋄fx.gate.001"
}

meaning_map = {
    "⋄fx.adj.112": ("adjective", "內省的", "MOV FX.ADJ.112"),
    "⋄fx.noun.024": ("noun", "記憶 / 節點", "MOV FX.NOUN.024"),
    "⋄fx.flow.007": ("verb", "封存 / 導出", "CALL FX.FLOW.007"),
    "⋄fx.adj.305": ("adjective", "激烈的", "MOV FX.ADJ.305"),
    "⋄fx.noun.091": ("noun", "衝突", "MOV FX.NOUN.091"),
    "⋄fx.flow.018": ("verb", "產生 / 轉變", "CALL FX.FLOW.018"),
    "⋄fx.per.001": ("pronoun", "我", "MOV FX.PER.001"),
    "⋄fx.time.010": ("adverb", "現在", "JMP FX.TIME.010"),
    "⋄fx.gate.001": ("conjunction", "並且", "GATE FX.GATE.001")
}

def parse_sentence(text):
    tokens = text.strip().split()
    fltnz_chain = []
    mapping = []

    for word in tokens:
        code = particle_dict.get(word)
        if code:
            fltnz_chain.append(code)
            type_, zh, pcode = meaning_map.get(code, ("", "", ""))
            mapping.append({
                "word": word,
                "code": code,
                "type": type_,
                "zh": zh,
                "pcode": pcode
            })
        elif word in ["被", "∴"]:
            fltnz_chain.append("∴")
        else:
            mapping.append({
                "word": word,
                "code": "(unknown)",
                "type": "",
                "zh": "",
                "pcode": ""
            })
    return fltnz_chain, mapping

st.title("🧠 FlowLingua 粒子翻譯器 (v0.1)")
text_input = st.text_input("輸入自然語句（中文）：", value="內省的 記憶 被 導出")

if st.button("翻譯為 FLTNZ"):
    fltnz, mapping = parse_sentence(text_input)
    st.subheader("🔡 FLTNZ 結構語句")
    st.code(" ".join(fltnz), language="plaintext")

    st.subheader("🔎 結構映射")
    st.json(mapping)

    # 檔案下載
    st.download_button("下載 .fltnz", data="\n".join(fltnz), file_name="output_result.fltnz")
    st.download_button("下載 .json 結構", data=json.dumps(mapping, indent=2, ensure_ascii=False), file_name="output_map.json")
