from flask import Flask, jsonify
import os
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODULE_NAME = os.getenv('MODULE_NAME', 'module-a')
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')

@app.route('/')
def index():
    return jsonify({
        'service': MODULE_NAME,
        'status': 'running',
        'version': '1.0.0'
    })

@app.route('/health')
def health():
    """健康檢查端點"""
    return jsonify({'status': 'healthy'}), 200

@app.route('/ready')
def ready():
    """就緒檢查端點"""
    # 這裡可以加入更複雜的檢查，例如資料庫連線
    return jsonify({'status': 'ready'}), 200

@app.route('/info')
def info():
    """服務資訊"""
    return jsonify({
        'module': MODULE_NAME,
        'mongodb': MONGODB_URI.split('@')[-1] if '@' in MONGODB_URI else 'not configured',
        'environment': os.getenv('ENVIRONMENT', 'development')
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    logger.info(f"Starting {MODULE_NAME} on port {port}")
    app.run(host='0.0.0.0', port=port)
