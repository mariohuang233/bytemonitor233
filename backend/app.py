"""Flask主应用程序"""
from flask import Flask, jsonify
from flask_cors import CORS
import logging
import os
from pathlib import Path

# 导入配置
from config import MONGO_URI, MONGO_DB_NAME, DEBUG, CORS_ORIGINS, JSON_CACHE_FILE, CRAWLER_SCRIPT_PATH

# 导入服务
from services.db import DatabaseService
from services.importer import DataImporter

# 导入路由
from routes.items import init_routes as init_items_routes
from routes.stats import init_routes as init_stats_routes
from routes.sync import init_routes as init_sync_routes

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app():
    """创建Flask应用"""
    # 支持静态文件服务（生产环境）
    static_folder = 'static' if Path('static').exists() else None
    app = Flask(__name__, static_folder=static_folder, static_url_path='')
    app.config['DEBUG'] = DEBUG
    
    # 配置CORS
    CORS(app, resources={r"/api/*": {"origins": CORS_ORIGINS}})
    
    # 初始化数据库服务
    logger.info(f"连接MongoDB: {MONGO_URI}")
    db_service = DatabaseService(MONGO_URI, MONGO_DB_NAME)
    
    # 初始化导入服务
    importer = DataImporter(db_service, JSON_CACHE_FILE)
    
    # 注册路由
    items_bp = init_items_routes(db_service)
    stats_bp = init_stats_routes(db_service)
    sync_bp = init_sync_routes(db_service, importer, CRAWLER_SCRIPT_PATH)
    
    app.register_blueprint(items_bp, url_prefix='/api')
    app.register_blueprint(stats_bp, url_prefix='/api')
    app.register_blueprint(sync_bp, url_prefix='/api')
    
    # 健康检查端点
    @app.route('/health')
    def health():
        return jsonify({'status': 'ok', 'message': '丝瓜清单系统运行正常'})
    
    # 根路径和SPA路由支持
    @app.route('/')
    def index():
        # 生产环境：服务前端页面
        if static_folder and Path(f'{static_folder}/index.html').exists():
            return app.send_static_file('index.html')
        # 开发环境：返回API信息
        return jsonify({
            'name': '丝瓜清单管理系统',
            'version': '1.0.0',
            'endpoints': {
                'health': '/health',
                'items': '/api/items',
                'stats': '/api/stats',
                'sync': '/api/sync'
            }
        })
    
    # SPA路由支持（处理前端路由）
    @app.route('/<path:path>')
    def spa_routes(path):
        # 如果是API路由，让Flask处理
        if path.startswith('api/') or path.startswith('health'):
            return jsonify({'error': 'Not found'}), 404
        # 否则返回前端页面
        if static_folder and Path(f'{static_folder}/index.html').exists():
            return app.send_static_file('index.html')
        return jsonify({'error': 'Not found'}), 404
    
    logger.info("Flask应用初始化完成")
    return app


if __name__ == '__main__':
    app = create_app()
    logger.info("启动Flask服务器...")
    # 使用5001端口避免macOS AirPlay冲突
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=DEBUG)

