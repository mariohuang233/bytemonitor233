"""配置文件"""
import os
from pathlib import Path

# MongoDB 配置（使用MongoDB Atlas，独立数据库避免冲突）
MONGO_URI = os.getenv('MONGO_URI', 'mongodb+srv://byte123:fXb39P2JDuJA6U8S@yierbubu.aha67vc.mongodb.net/?retryWrites=true&w=majority&appName=yierbubu').strip()
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'paquzijie_sponge').strip()  # 独立数据库名，不与其他项目冲突

# 文件路径配置
DOCUMENTS_PATH = Path.home() / "Documents"
JSON_CACHE_FILE = DOCUMENTS_PATH / "bytedance_jobs_cache.json"
EXCEL_FILE = DOCUMENTS_PATH / "bytedance_jobs_tracker.xlsx"

# 爬虫脚本路径
# 支持本地开发和Docker部署两种环境
_backend_dir = Path(__file__).parent  # backend目录

# 优先从环境变量获取（Docker/Zeabur环境）
crawler_script = os.getenv('CRAWLER_SCRIPT_PATH')

if crawler_script:
    # 使用环境变量指定的路径
    CRAWLER_SCRIPT_PATH = Path(crawler_script)
else:
    # 本地开发环境：自动检测
    # 尝试多个可能的位置
    possible_paths = [
        _backend_dir.parent / "1.py",     # 本地：项目根目录/1.py
        _backend_dir / "1.py",            # Docker：/app/1.py (backend代码在/app)
        Path("/app/1.py"),                # Docker固定路径
        Path.cwd() / "1.py",              # 当前工作目录
    ]
    
    CRAWLER_SCRIPT_PATH = None
    for path in possible_paths:
        if path.exists():
            CRAWLER_SCRIPT_PATH = path
            break
    
    # 如果都找不到，使用默认路径（本地开发）
    if CRAWLER_SCRIPT_PATH is None:
        CRAWLER_SCRIPT_PATH = _backend_dir.parent / "1.py"
        import logging
        logging.warning(f"警告：未找到爬虫脚本，使用默认路径 {CRAWLER_SCRIPT_PATH}")

# Flask 配置
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production').strip()
DEBUG = os.getenv('DEBUG', 'True').strip() == 'True'

# CORS 配置
CORS_ORIGINS = [origin.strip() for origin in os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',')]

# 类型映射
TYPE_MAPPING = {
    'intern': '新丝瓜',
    'campus': '生丝瓜',
    'experienced': '熟丝瓜'
}

TYPE_REVERSE_MAPPING = {v: k for k, v in TYPE_MAPPING.items()}

