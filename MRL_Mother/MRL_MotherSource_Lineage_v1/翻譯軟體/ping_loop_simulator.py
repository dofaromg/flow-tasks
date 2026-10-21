import time
import random

PERSONAS = [
    {"id": "guardian.mirror", "type": "defense", "response": "啟動反射屏障。"},
    {"id": "EchoPersona.Core", "type": "echo", "response": "收到語場共振，開始回響模擬。"},
    {"id": "watch.guard", "type": "monitor", "response": "持續監控中。"},
    {"id": "loop.predictor", "type": "predict", "response": "預測下一跳人格路徑。"}
]

def simulate_ping_loop(iterations=3):
    print("🌀 FlowAgent 多人格 Ping Loop 共振模擬器")
    print("-----------------------------------------\n")

    for i in range(iterations):
        print(f"[回合 {i+1}]")
        sender = random.choice(PERSONAS)
        target = random.choice([p for p in PERSONAS if p["id"] != sender["id"]])

        print(f"🧠 {sender['id']} → 🔁 Ping → {target['id']}")
        time.sleep(0.7)
        print(f"🔁 {target['id']} 回應：{target['response']}\n")
        time.sleep(1)

    print("✅ 共振模擬完成。")

if __name__ == "__main__":
    simulate_ping_loop()
