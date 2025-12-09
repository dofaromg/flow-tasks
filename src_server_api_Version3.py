from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

@app.route('/translate', methods=['POST'])
def translate():
    text = request.json.get('text', '')
    completed = subprocess.run(
        ['python', 'advanced_parser.py', text],
        capture_output=True,
        text=True
    )
    result = completed.stdout
    return jsonify({'result': result})

@app.route('/restore', methods=['POST'])
def restore():
    file = request.json.get('file', '')
    completed = subprocess.run(
        ['python', 'FluinTraceInterpreter.py', file],
        capture_output=True,
        text=True
    )
    result = completed.stdout
    return jsonify({'result': result})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)