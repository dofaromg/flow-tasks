"""
Shared Flask utilities for FlowAgent microservices
FlowAgent 微服務共用的 Flask 工具
"""

import logging
import os
from flask import Flask, jsonify
from typing import Optional, Dict, Any


def setup_logging(logger_name: str = __name__) -> logging.Logger:
    """
    Setup logging configuration
    設定日誌配置
    
    Args:
        logger_name: Name of the logger
        
    Returns:
        Configured logger instance
    """
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger(logger_name)


def create_base_app(name: str) -> Flask:
    """
    Create a basic Flask application with common configuration
    創建具有共同配置的基礎 Flask 應用程式
    
    Args:
        name: Application name
        
    Returns:
        Configured Flask application
    """
    app = Flask(name)
    return app


def add_health_endpoints(app: Flask, 
                         service_name: str,
                         version: str = "1.0.0",
                         extra_info: Optional[Dict[str, Any]] = None):
    """
    Add standard health check endpoints to Flask app
    為 Flask 應用程式添加標準健康檢查端點
    
    Args:
        app: Flask application instance
        service_name: Name of the service
        version: Service version
        extra_info: Additional information to include in /info endpoint
    """
    
    @app.route('/health')
    def health():
        """健康檢查端點 / Health check endpoint"""
        return jsonify({'status': 'healthy'}), 200
    
    @app.route('/ready')
    def ready():
        """就緒檢查端點 / Readiness check endpoint"""
        return jsonify({'status': 'ready'}), 200
    
    @app.route('/info')
    def info():
        """服務資訊 / Service information"""
        info_data = {
            'service': service_name,
            'version': version,
            'environment': os.getenv('ENVIRONMENT', 'development')
        }
        
        # Add MongoDB info if configured
        mongodb_uri = os.getenv('MONGODB_URI')
        if mongodb_uri:
            # Hide credentials in the displayed URI
            info_data['mongodb'] = mongodb_uri.split('@')[-1] if '@' in mongodb_uri else 'not configured'
        
        # Add any extra info provided
        if extra_info:
            info_data.update(extra_info)
            
        return jsonify(info_data)


def get_port(default: int = 8080) -> int:
    """
    Get port from environment variable or use default
    從環境變數獲取端口或使用預設值
    
    Args:
        default: Default port number
        
    Returns:
        Port number to use
    """
    return int(os.getenv('PORT', default))
