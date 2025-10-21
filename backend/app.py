"""Flask主应用程序"""
from flask import Flask, jsonify
from flask_cors import CORS
import logging
import os
import subprocess
from pathlib import Path
from datetime import datetime
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

# 导入配置
from config import MONGO_URI, MONGO_DB_NAME, DEBUG, CORS_ORIGINS, JSON_CACHE_FILE, CRAWLER_SCRIPT_PATH

# 导入服务
from services.db import DatabaseService
from services.importer import DataImporter

# 导入路由
from routes.items import init_routes as init_items_routes
from routes.stats import init_routes as init_stats_routes
from routes.sync import init_routes as init_sync_routes

# 北京时区
BEIJING_TZ = pytz.timezone('Asia/Shanghai')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局调度器实例
scheduler = None


def scheduled_crawl_task(db_service, importer):
    """定时爬取任务"""
    try:
        start_time = datetime.now(BEIJING_TZ)
        logger.info(f"[定时任务] 开始执行爬取任务 - {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 运行爬虫脚本
        result = subprocess.run(
            ['python3', str(CRAWLER_SCRIPT_PATH), '--auto'],
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        if result.returncode != 0:
            raise Exception(f"爬虫脚本执行失败: {result.stderr}")
        
        logger.info("[定时任务] 爬虫脚本执行成功，开始导入数据...")
        
        # 导入数据到MongoDB
        import_result = importer.import_from_json(clear_existing=False)
        
        if not import_result['success']:
            raise Exception(import_result['message'])
        
        # 记录同步日志
        duration = (datetime.now(BEIJING_TZ) - start_time).total_seconds()
        db_service.add_sync_log({
            'type': 'scheduled',
            'status': 'success',
            'new_count': import_result.get('imported', 0),
            'total_count': db_service.items.count_documents({}),
            'duration': duration,
            'error_message': None
        })
        
        end_time = datetime.now(BEIJING_TZ)
        logger.info(f"[定时任务] 任务完成 - {end_time.strftime('%Y-%m-%d %H:%M:%S')} (耗时: {duration:.2f}秒)")
        logger.info(f"[定时任务] {import_result['message']}")
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"[定时任务] 执行失败: {error_msg}", exc_info=True)
        
        # 记录失败日志
        duration = (datetime.now(BEIJING_TZ) - start_time).total_seconds()
        db_service.add_sync_log({
            'type': 'scheduled',
            'status': 'failed',
            'new_count': 0,
            'total_count': db_service.items.count_documents({}),
            'duration': duration,
            'error_message': error_msg
        })


def create_app():
    """创建Flask应用"""
    global scheduler
    
    # 支持静态文件服务（生产环境）
    static_folder = 'static' if Path('static').exists() else None
    app = Flask(__name__, static_folder=static_folder, static_url_path='')
    app.config['DEBUG'] = DEBUG
    
    # 配置CORS
    CORS(app, resources={r"/api/*": {"origins": CORS_ORIGINS}})
    
    # 初始化数据库服务
    # 验证MongoDB URI
    if not MONGO_URI or not MONGO_URI.startswith(('mongodb://', 'mongodb+srv://')):
        logger.error(f"❌ 无效的MongoDB URI: '{MONGO_URI}'")
        logger.error("请检查环境变量 MONGO_URI 是否正确设置")
        raise ValueError(f"Invalid MongoDB URI: '{MONGO_URI}'")
    
    logger.info(f"连接MongoDB: {MONGO_URI[:50]}...")  # 只显示前50个字符，避免泄露完整URI
    db_service = DatabaseService(MONGO_URI, MONGO_DB_NAME)
    
    # 初始化导入服务
    importer = DataImporter(db_service, JSON_CACHE_FILE)
    
    # 初始化定时调度器（30分钟执行一次）
    if scheduler is None:
        scheduler = BackgroundScheduler(timezone=BEIJING_TZ)
        scheduler.add_job(
            func=lambda: scheduled_crawl_task(db_service, importer),
            trigger=IntervalTrigger(minutes=30),
            id='crawl_job',
            name='定时爬取任务',
            replace_existing=True
        )
        scheduler.start()
        logger.info("✅ 定时调度器已启动，每30分钟执行一次爬取任务")
    else:
        logger.info("⚠️ 定时调度器已存在，跳过初始化")
    
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
    import atexit
    
    app = create_app()
    logger.info("启动Flask服务器...")
    
    # 确保程序退出时关闭调度器
    def shutdown_scheduler():
        if scheduler:
            scheduler.shutdown()
            logger.info("定时调度器已关闭")
    
    atexit.register(shutdown_scheduler)
    
    # 使用5001端口避免macOS AirPlay冲突
    port = int(os.getenv('PORT', 5001))
    try:
        app.run(host='0.0.0.0', port=port, debug=DEBUG)
    except (KeyboardInterrupt, SystemExit):
        shutdown_scheduler()

