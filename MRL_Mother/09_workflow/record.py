from modules.FluinRecorder import record_input

if __name__ == "__main__":
    print("Fluin Memory Recorder")
    user_input = input("請輸入語句記錄：")
    entry = record_input(user_input)
    print("✅ 已記錄：", entry)