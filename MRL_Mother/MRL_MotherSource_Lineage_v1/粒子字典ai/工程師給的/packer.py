import os
import json
import zipfile
from datetime import datetime
from pathlib import Path
import yaml

# 詞庫（可換成外部 JSON 讀入）
particle_dict = {
    "內省的": "⋄fx.adj.112",
    "記憶": "⋄fx.noun.024",
    "節點": "⋄fx.noun.024",
    "封存": "⋄fx.flow.007",
    "導出": "⋄fx.flow.007"
}

meaning_map = {
    "⋄fx.adj.112": ("adjective", "內省的", "MOV FX.ADJ.112"),
    "⋄fx.noun.024": ("noun", "記憶 / 節點", "MOV FX.NOUN.024"),
    "⋄fx.flow.007": ("verb", "封存 / 導出", "CALL FX.FLOW.007")
}

def parse_text(text):
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

def pack_text_to_flpkg(input_path):
    with open(input_path, "r", encoding="utf-8") as f:
        text = f.read().strip()

    fltnz_chain, mapping = parse_text(text)
    base_name = Path(input_path).stem
    output_dir = Path("output_flpkg")
    output_dir.mkdir(exist_ok=True)

    # 儲存 fltnz
    with open(output_dir / "seed.fltnz", "w", encoding="utf-8") as f:
        f.write("\n".join(fltnz_chain))

    # 儲存語素映射 JSON
    with open(output_dir / "structure.json", "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)

    # 儲存 manifest
    manifest = {
        "package": base_name,
        "version": "1.0.0",
        "created": datetime.utcnow().isoformat() + "Z"
    }
    with open(output_dir / "manifest.yml", "w", encoding="utf-8") as f:
        yaml.dump(manifest, f, allow_unicode=True)

    # 打包成 .flpkg
    flpkg_path = Path(f"{base_name}.flpkg")
    with zipfile.ZipFile(flpkg_path, "w") as zipf:
        for filename in ["seed.fltnz", "structure.json", "manifest.yml"]:
            zipf.write(output_dir / filename, arcname=filename)

    print(f"[✔] 封裝完成：{flpkg_path}")
