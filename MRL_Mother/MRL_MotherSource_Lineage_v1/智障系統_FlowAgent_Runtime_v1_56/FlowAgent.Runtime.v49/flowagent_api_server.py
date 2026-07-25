
# mrliouai_api_server.py - 提供 API 介面供前端 / 工具呼叫 .fltnz 解析、封裝等功能

from flask import Flask, request, jsonify
import os
import json

app = Flask(__name__)

DICT_PATH = "dictionary/Fluin.Dict.Base.json"
with open(DICT_PATH, "r", encoding="utf-8") as f:
    DICT = json.load(f)
REVERSE_DICT = {v: k for k, v in DICT.items()}

@app.route("/")
def home():
    return jsonify({"message": "MrLiouAI API Server is running."})

@app.route("/decode", methods=["POST"])
def decode():
    data = request.get_json()
    lines = data.get("lines", [])
    decoded = []
    for line in lines:
        tokens = line.strip().split()
        words = [DICT.get(t, t) for t in tokens]
        decoded.append(words)
    return jsonify({"decoded": decoded})

@app.route("/encode", methods=["POST"])
def encode():
    data = request.get_json()
    sentences = data.get("sentences", [])
    encoded = []
    for sentence in sentences:
        tokens = sentence.strip().split()
        line = [REVERSE_DICT.get(t, "[???]") for t in tokens]
        encoded.append(line)
    return jsonify({"encoded": encoded})

if __name__ == "__main__":
    app.run(port=8787)
