#!/usr/bin/env python3
"""
Flask Hello World API
Created according to task specification in 2025-06-29_hello-world-api.yaml
"""

from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def hello_world():
    """Return hello world message in Chinese"""
    return jsonify({"message": "你好，世界"})

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)