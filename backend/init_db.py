"""数据库初始化脚本 - 从JSON导入现有数据"""
import sys
from pathlib import Path

# 添加backend目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from config import MONGO_URI, MONGO_DB_NAME, JSON_CACHE_FILE
from services.db import DatabaseService
from services.importer import DataImporter
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """主函数"""
    logger.info("=== 开始初始化数据库 ===")
    
    # 初始化服务
    db_service = DatabaseService(MONGO_URI, MONGO_DB_NAME)
    importer = DataImporter(db_service, JSON_CACHE_FILE)
    
    # 询问是否清空现有数据
    print(f"\n当前数据库: {MONGO_DB_NAME}")
    print(f"JSON文件: {JSON_CACHE_FILE}")
    print(f"现有条目数: {db_service.items.count_documents({})}")
    
    clear = input("\n是否清空现有数据后导入？(y/N): ").strip().lower()
    clear_existing = clear == 'y'
    
    if clear_existing:
        logger.warning("将清空现有数据！")
    
    # 执行导入
    result = importer.import_from_json(clear_existing=clear_existing)
    
    if result['success']:
        logger.info(f"✅ {result['message']}")
        
        # 显示统计
        stats = db_service.get_stats()
        logger.info(f"\n数据库统计:")
        logger.info(f"  总条目数: {stats['total']}")
        logger.info(f"  新丝瓜: {stats['type_distribution'].get('新丝瓜', 0)}")
        logger.info(f"  生丝瓜: {stats['type_distribution'].get('生丝瓜', 0)}")
        logger.info(f"  熟丝瓜: {stats['type_distribution'].get('熟丝瓜', 0)}")
    else:
        logger.error(f"❌ {result['message']}")
        sys.exit(1)
    
    logger.info("\n=== 初始化完成 ===")


if __name__ == '__main__':
    main()

