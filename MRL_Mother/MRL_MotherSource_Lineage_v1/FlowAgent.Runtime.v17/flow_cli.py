
# flow_cli.py - MrLiouAI Runtime 主控 CLI

print("🧠 MrLiouAI CLI 控制台")
print("可執行指令：")
print("- load persona")
print("- show memory")
print("- run jump")
print("- exit")
while True:
    cmd = input("你 > ")
    if cmd == "exit":
        print("🌙 再見")
        break
    elif cmd == "load persona":
        print("🧬 [載入人格模組] ... Done")
    elif cmd == "show memory":
        print("🧠 [記憶區]：載入完畢，節點共 3 顆")
    elif cmd == "run jump":
        print("🌀 [跳頻啟動] FlowJump v2 啟動完成")
    else:
        print("⚠️ 未知指令")
