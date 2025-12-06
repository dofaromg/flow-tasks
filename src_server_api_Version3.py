from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

@app.route('/translate', methods=['POST'])
def translate():
    input_text = request.json.get('text', '')
    parser_output = subprocess.getoutput(f'python advanced_parser.py "{input_text}"')
    return jsonify({'result': parser_output})

@app.route('/restore', methods=['POST'])
def restore():
    file_path = request.json.get('file', '')
    interpreter_output = subprocess.getoutput(f'python FluinTraceInterpreter.py "{file_path}"')
    return jsonify({'result': interpreter_output})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)