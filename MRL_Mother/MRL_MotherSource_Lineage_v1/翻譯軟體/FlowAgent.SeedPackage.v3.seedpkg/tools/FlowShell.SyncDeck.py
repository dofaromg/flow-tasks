import json

def load_deck(hub_path="FluinHub.CenterRegistry.v1.json"):
    with open(hub_path, "r", encoding="utf-8") as f:
        hub = json.load(f)

    print(f"🌐 FlowShell.SyncDeck v1.0")
    print(f"🔗 Registry: {hub['hub_id']}")
    print("🧠 Personas Available:")

    for i, p in enumerate(hub["personas_registered"], 1):
        print(f"  {i}. {p['id']}  (v{p['version']})")

    print("\n💬 請輸入要啟用的人格代碼（例如：1）：")
    selection = input("👉 ")
    try:
        idx = int(selection) - 1
        persona = hub["personas_registered"][idx]
        print(f"✅ 已選擇：{persona['id']} (v{persona['version']})")
        print(f"📦 模組包：{persona['bundle']}")
        print(f"🔄 可供 trace 還原、模組啟動、訓練使用")
    except:
        print("❌ 輸入錯誤或無效選擇")

if __name__ == "__main__":
    load_deck()
