
# mrliouai_persona_emulator.py - Fluin Persona Emulator (Web 對話模擬器)

from flask import Flask, render_template_string, request
import json

app = Flask(__name__)

DICT_PATH = "dictionary/Fluin.Dict.Base.json"
with open(DICT_PATH, "r", encoding="utf-8") as f:
    DICT = json.load(f)
REVERSE_DICT = {v: k for k, v in DICT.items()}

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Fluin Persona Emulator</title>
  <style>
    body { font-family: monospace; background: #f4f4f4; padding: 20px; }
    input[type=text] { width: 400px; padding: 6px; font-size: 16px; }
    .log { background: #fff; padding: 10px; border: 1px solid #ccc; margin-top: 20px; white-space: pre-wrap; }
  </style>
</head>
<body>
  <h2>🧠 Fluin Persona Emulator</h2>
  <form method="POST">
    <input name="message" placeholder="輸入語句..." />
    <button type="submit">傳送</button>
  </form>
  <div class="log">{{log}}</div>
</body>
</html>
'''

@app.route("/", methods=["GET", "POST"])
def emulate():
    log = ""
    if request.method == "POST":
        msg = request.form.get("message", "")
        tokens = msg.strip().split()
        encoded = [REVERSE_DICT.get(t, "[???]") for t in tokens]
        decoded = [DICT.get(t, t) for t in encoded if t != "[???]"]
        log = f"> 使用者輸入：{msg}\n> 粒子語法：{' '.join(encoded)}\n> 語場還原：{' '.join(decoded)}"
    return render_template_string(HTML_TEMPLATE, log=log)

if __name__ == "__main__":
    app.run(port=8788)
