from flask import Flask, jsonify, request
import os
import logging
import requests

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
MODULE_A_ENDPOINT = os.getenv('MODULE_A_ENDPOINT', 'http://module-a:8080')

@app.route('/')
def index():
    return jsonify({
        'service': 'orchestrator',
        'status': 'running',
        'version': '1.0.0',
        'endpoints': {
            'module-a': MODULE_A_ENDPOINT
        }
    })

@app.route('/health')
def health():
    """健康檢查端點"""
    return jsonify({'status': 'healthy'}), 200

@app.route('/ready')
def ready():
    """就緒檢查端點"""
    return jsonify({'status': 'ready'}), 200

@app.route('/orchestrate', methods=['POST'])
def orchestrate():
    """編排端點 - 協調多個服務"""
    try:
        data = request.get_json()
        logger.info(f"Orchestrating request: {data}")
        
        # 呼叫 Module-A
        try:
            response = requests.get(f"{MODULE_A_ENDPOINT}/info", timeout=5)
            module_a_info = response.json()
        except Exception as e:
            logger.error(f"Failed to call Module-A: {e}")
            module_a_info = {'error': str(e)}
        
        return jsonify({
            'orchestrator': 'success',
            'input': data,
            'module_a': module_a_info
        })
    except Exception as e:
        logger.error(f"Orchestration failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/info')
def info():
    """服務資訊"""
    return jsonify({
        'service': 'orchestrator',
        'mongodb': MONGODB_URI.split('@')[-1] if '@' in MONGODB_URI else 'not configured',
        'module_a_endpoint': MODULE_A_ENDPOINT,
        'environment': os.getenv('ENVIRONMENT', 'development')
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8081))
    logger.info(f"Starting orchestrator on port {port}")
    app.run(host='0.0.0.0', port=port)
