from flask import Flask, jsonify, request
import os
import sys
import requests

# Add parent directory to path for importing common utilities
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from common.flask_utils import setup_logging, add_health_endpoints, get_port

import core

app = Flask(__name__)
logger = setup_logging(__name__)

MODULE_A_ENDPOINT = os.getenv('MODULE_A_ENDPOINT', 'http://module-a:8080')


def _remote_compute(text):
    """Production compute path: call module-a over HTTP."""
    resp = requests.post(f"{MODULE_A_ENDPOINT}/compute", json={'text': text}, timeout=5)
    resp.raise_for_status()
    return resp.json()['result']


@app.route('/')
def index():
    return jsonify({'service': 'orchestrator', 'status': 'running', 'version': '2.0.0',
                    'endpoints': {'module-a': MODULE_A_ENDPOINT}, 'origin_signature': 'MrLiouWord'})


@app.route('/orchestrate', methods=['POST'])
def orchestrate():
    """Run the real multi-step pipeline across module-a."""
    payload = request.get_json(silent=True) or {}
    try:
        result = core.run_pipeline(payload, _remote_compute)
    except ValueError as e:
        return jsonify({'ok': False, 'error': str(e)}), 400
    except requests.RequestException as e:
        logger.error("module-a call failed: %s", e)
        return jsonify({'ok': False, 'error': 'module_a_unreachable', 'detail': str(e)}), 502
    return jsonify(result)


# Add standard health check endpoints with module-a endpoint info
add_health_endpoints(
    app,
    service_name='orchestrator',
    version='2.0.0',
    extra_info={'module_a_endpoint': MODULE_A_ENDPOINT},
)

if __name__ == '__main__':
    port = get_port(8081)
    logger.info(f"Starting orchestrator on port {port}")
    app.run(host='0.0.0.0', port=port)
