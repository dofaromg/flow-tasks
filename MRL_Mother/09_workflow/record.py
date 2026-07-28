#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# origin_signature: MrLiouWord
# layer: L2 MARK / 記錄入口腳本
from modules.FluinRecorder import record_input

if __name__ == "__main__":
    print("Fluin Memory Recorder")
    user_input = input("請輸入語句記錄：")
    entry = record_input(user_input)
    print("✅ 已記錄：", entry)