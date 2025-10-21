"""配置文件"""
import os
from pathlib import Path

# MongoDB 配置（使用MongoDB Atlas，独立数据库避免冲突）
MONGO_URI = os.getenv('MONGO_URI', 'mongodb+srv://byte123:fXb39P2JDuJA6U8S@yierbubu.aha67vc.mongodb.net/?retryWrites=true&w=majority&appName=yierbubu')
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'paquzijie_sponge')  # 独立数据库名，不与其他项目冲突

# 文件路径配置
DOCUMENTS_PATH = Path.home() / "Documents"
JSON_CACHE_FILE = DOCUMENTS_PATH / "bytedance_jobs_cache.json"
EXCEL_FILE = DOCUMENTS_PATH / "bytedance_jobs_tracker.xlsx"

# 爬虫脚本路径
CRAWLER_SCRIPT_PATH = Path(__file__).parent.parent / "1.py"

# Flask 配置
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
DEBUG = os.getenv('DEBUG', 'True') == 'True'

# CORS 配置
CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',')

# 类型映射
TYPE_MAPPING = {
    'intern': '新丝瓜',
    'campus': '生丝瓜',
    'experienced': '熟丝瓜'
}

TYPE_REVERSE_MAPPING = {v: k for k, v in TYPE_MAPPING.items()}

