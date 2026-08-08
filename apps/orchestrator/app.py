from flask import Flask, jsonify, request
import os
import sys
import requests

# Add parent directory to path for importing common utilities
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from common.flask_utils import setup_logging, add_health_endpoints, get_port

app = Flask(__name__)
logger = setup_logging(__name__)

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

# Add standard health check endpoints with module-a endpoint info
add_health_endpoints(
    app, 
    service_name='orchestrator',
    version='1.0.0',
    extra_info={'module_a_endpoint': MODULE_A_ENDPOINT}
)

if __name__ == '__main__':
    port = get_port(8081)
    logger.info(f"Starting orchestrator on port {port}")
    app.run(host='0.0.0.0', port=port)
