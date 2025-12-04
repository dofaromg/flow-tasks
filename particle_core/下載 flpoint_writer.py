import json
from pathlib import Path
from datetime import datetime

def write_flpoint(
    label,
    position,
    code,
    visible_text,
    temperature=None,
    emotion_color=None,
    pressure=None,
    mood=None,
    resonance=1.0,
    link_to=None
):
    data_point = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "label": label,
        "position": position,  # e.g. [lat, lon] or [x, y]
        "code": code,
        "visible_text": visible_text,
        "hidden_fields": {
            "temperature": temperature,
            "emotion_color": emotion_color,
            "pressure": pressure,
            "mood": mood,
            "resonance": resonance,
            "linked_nodes": link_to or []
        }
    }

    point_file = Path("storage/points/{}.flpoint.json".format(label))
    point_file.parent.mkdir(parents=True, exist_ok=True)

    # 若已存在則追加成 list
    if point_file.exists():
        with open(point_file, "r", encoding="utf-8") as f:
            all_data = json.load(f)
    else:
        all_data = []

    all_data.append(data_point)

    with open(point_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)

    print(f"[✔] 已記錄點位 {label} @ {position}，共 {len(all_data)} 筆")
    return point_file

if __name__ == "__main__":
    # 測試用
    write_flpoint(
        label="echo.memory.seed",
        position=[32.5, 118.0],
        code="⋄fx.adj.112",
        visible_text="內省的記憶",
        temperature=0.72,
        emotion_color="#6688aa",
        pressure=0.45,
        mood="reflective",
        resonance=0.91,
        link_to=["⋄fx.flow.007", "⋄fx.per.001"]
    )
