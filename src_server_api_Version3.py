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
"""FlowAgent REST API Server v3.

This module provides a Flask-based REST API server for the FlowAgent system.
It exposes endpoints for text translation and trace restoration.

API Endpoints:
    - POST /translate: Translate text using the advanced parser
    - POST /restore: Restore trace from file using Fluin interpreter
    - GET /health: Health check endpoint

Usage:
    python src_server_api_Version3.py
    # Server starts on http://0.0.0.0:8080

Example requests:
    # Translate text
    curl -X POST http://localhost:8080/translate \\
        -H "Content-Type: application/json" \\
        -d '{"text": "Hello World"}'
    
    # Restore trace
    curl -X POST http://localhost:8080/restore \\
        -H "Content-Type: application/json" \\
        -d '{"file": "./traces/example.trace"}'
    
    # Health check
    curl http://localhost:8080/health

Version: 3.0
"""

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
    
    Endpoint: POST /translate
    
    Request Body:
        text (str): The input text to translate/parse
    
    Response:
        200: {"result": "Translated/parsed output"}
        400: {"error": "Missing text parameter"}
    
    Example:
        curl -X POST http://localhost:8080/translate \\
            -H "Content-Type: application/json" \\
            -d '{"text": "Hello World"}'
    
    Returns:
        JSON response with parsed result or error message
    """
    input_text = request.json.get('text', '')
    if not input_text:
        return jsonify({'error': 'Missing text parameter'}), 400
    
    parser_output = run_safe_command('advanced_parser.py', input_text)
    return jsonify({'result': parser_output})


@app.route('/restore', methods=['POST'])
def restore() -> Any:
    """Restore trace from file using Fluin interpreter.
    
    Endpoint: POST /restore
    
    Request Body:
        file (str): Path to the trace file to restore
    
    Response:
        200: {"result": "Restored trace data"}
        400: {"error": "Missing file parameter"}
    
    Example:
        curl -X POST http://localhost:8080/restore \\
            -H "Content-Type: application/json" \\
            -d '{"file": "./traces/example.trace"}'
    
    Returns:
        JSON response with restored trace data or error message
    """
    file_path = request.json.get('file', '')
    if not file_path:
        return jsonify({'error': 'Missing file parameter'}), 400
    
    interpreter_output = run_safe_command('FluinTraceInterpreter.py', file_path)
    return jsonify({'result': interpreter_output})


@app.route('/health', methods=['GET'])
def health() -> Any:
    """Health check endpoint.
    
    Endpoint: GET /health
    
    Response:
        200: {"status": "healthy", "version": "3.0"}
    
    Example:
        curl http://localhost:8080/health
    
    Returns:
        JSON response with server health status
    """
    return jsonify({'status': 'healthy', 'version': '3.0'})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)