from flask import Flask, request, jsonify
import subprocess
import sys
from typing import Any

app = Flask(__name__)


def run_safe_command(script: str, argument: str) -> str:
    """Run a Python script safely with a single argument.
    
    This function prevents command injection by using subprocess.run with a list
    of arguments instead of shell string interpolation.
    
    Args:
        script: The Python script filename to execute
        argument: The argument to pass to the script
        
    Returns:
        The stdout output if successful, stderr if failed, or error message
    """
    try:
        # Use sys.executable for security - ensures we use the same Python interpreter
        result = subprocess.run(
            [sys.executable, script, argument],
            capture_output=True,
            text=True,
            timeout=30,
            check=False
        )
        return result.stdout if result.returncode == 0 else result.stderr
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds"
    except Exception as e:
        return f"Error: {str(e)}"


@app.route('/translate', methods=['POST'])
def translate() -> Any:
    """Translate input text using advanced parser.
    
    Returns:
        JSON response with result or error
    """
    input_text = request.json.get('text', '')
    if not input_text:
        return jsonify({'error': 'Missing text parameter'}), 400
    
    parser_output = run_safe_command('advanced_parser.py', input_text)
    return jsonify({'result': parser_output})


@app.route('/restore', methods=['POST'])
def restore() -> Any:
    """Restore trace from file using Fluin interpreter.
    
    Returns:
        JSON response with result or error
    """
    file_path = request.json.get('file', '')
    if not file_path:
        return jsonify({'error': 'Missing file parameter'}), 400
    
    interpreter_output = run_safe_command('FluinTraceInterpreter.py', file_path)
    return jsonify({'result': interpreter_output})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)