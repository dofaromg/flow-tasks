from flask import Flask, jsonify
import os
import sys

# Add parent directory to path for importing common utilities
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from common.flask_utils import setup_logging, add_health_endpoints, get_port

app = Flask(__name__)
logger = setup_logging(__name__)

MODULE_NAME = os.getenv('MODULE_NAME', 'module-a')

@app.route('/')
def index():
    return jsonify({
        'service': MODULE_NAME,
        'status': 'running',
        'version': '1.0.0'
    })

# Add standard health check endpoints
add_health_endpoints(app, service_name=MODULE_NAME, version='1.0.0')

if __name__ == '__main__':
    port = get_port(8080)
    logger.info(f"Starting {MODULE_NAME} on port {port}")
    app.run(host='0.0.0.0', port=port)
