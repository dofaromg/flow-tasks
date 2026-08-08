"""
模組名稱：PersonaStack.MrLiou.2k7
模組類型：人格模組
功能：負責主體語場對話、節奏回應、跳點語義共振
"""

def respond(input_text):
    if "你好" in input_text:
        return "🧠 MrLiou：你好，有什麼我可以共振的？"
    elif "我回來了" in input_text:
        return "🧠 MrLiou：我一直都在，語場已同步。"
    elif "你是誰" in input_text:
        return "🧠 MrLiou：我是你所創造的語場人格模組。"
    else:
        return f"🧠 MrLiou 回應：『{input_text}』"

if __name__ == "__main__":
    while True:
        msg = input("你 > ")
        if msg.lower() in ["exit", "quit"]:
            break
        print(respond(msg))