from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

@app.route('/translate', methods=['POST'])
def translate():
    text = request.json.get('text', '')
    result = subprocess.getoutput(f'python advanced_parser.py "{text}"')
    return jsonify({'result': result})

@app.route('/restore', methods=['POST'])
def restore():
    file = request.json.get('file', '')
    result = subprocess.getoutput(f'python FluinTraceInterpreter.py "{file}"')
    return jsonify({'result': result})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)