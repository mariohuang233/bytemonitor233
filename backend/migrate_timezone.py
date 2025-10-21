#!/usr/bin/env python3
"""
数据库时区迁移脚本
将MongoDB中所有时间字段转换为北京时间（Asia/Shanghai UTC+8）
"""
import sys
from datetime import datetime
import pytz
from pathlib import Path

# 添加父目录到Python路径以便导入配置
sys.path.insert(0, str(Path(__file__).parent))

from config import MONGO_URI, MONGO_DB_NAME
from services.db import DatabaseService
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 时区定义
UTC_TZ = pytz.UTC
BEIJING_TZ = pytz.timezone('Asia/Shanghai')


def convert_to_beijing_time(dt_value):
    """将datetime转换为北京时间"""
    if dt_value is None:
        return None
    
    if isinstance(dt_value, str):
        # 字符串格式的时间，尝试解析
        try:
            dt = datetime.strptime(dt_value, '%Y-%m-%d %H:%M:%S')
            # 假设字符串时间已经是北京时间，添加时区信息
            return BEIJING_TZ.localize(dt)
        except:
            logger.warning(f"无法解析时间字符串: {dt_value}")
            return None
    
    if isinstance(dt_value, datetime):
        if dt_value.tzinfo is None:
            # 无时区信息，假设是北京时间
            logger.debug(f"假设无时区datetime为北京时间: {dt_value}")
            return BEIJING_TZ.localize(dt_value)
        elif dt_value.tzinfo == UTC_TZ or dt_value.tzinfo.utcoffset(dt_value).total_seconds() == 0:
            # UTC时间，转换为北京时间
            logger.debug(f"UTC时间转换为北京时间: {dt_value}")
            return dt_value.astimezone(BEIJING_TZ)
        else:
            # 其他时区，转换为北京时间
            logger.debug(f"其他时区转换为北京时间: {dt_value}")
            return dt_value.astimezone(BEIJING_TZ)
    
    return dt_value


def migrate_items_collection(db_service):
    """迁移items集合的时间字段"""
    logger.info("开始迁移items集合...")
    
    # 需要转换的时间字段
    time_fields = ['采摘时间', 'publish_time', 'created_at', 'updated_at']
    
    items = db_service.items.find({})
    total_count = db_service.items.count_documents({})
    updated_count = 0
    
    logger.info(f"找到 {total_count} 条记录")
    
    for item in items:
        needs_update = False
        update_data = {}
        
        for field in time_fields:
            if field in item and item[field] is not None:
                original_value = item[field]
                converted_value = convert_to_beijing_time(original_value)
                
                if converted_value and converted_value != original_value:
                    update_data[field] = converted_value
                    needs_update = True
                    logger.debug(f"字段 {field}: {original_value} -> {converted_value}")
        
        if needs_update:
            db_service.items.update_one(
                {'_id': item['_id']},
                {'$set': update_data}
            )
            updated_count += 1
            if updated_count % 100 == 0:
                logger.info(f"已更新 {updated_count}/{total_count} 条记录...")
    
    logger.info(f"✅ items集合迁移完成，共更新 {updated_count} 条记录")
    return updated_count


def migrate_sync_logs_collection(db_service):
    """迁移sync_logs集合的时间字段"""
    logger.info("开始迁移sync_logs集合...")
    
    time_fields = ['created_at']
    
    logs = db_service.sync_logs.find({})
    total_count = db_service.sync_logs.count_documents({})
    updated_count = 0
    
    logger.info(f"找到 {total_count} 条同步日志")
    
    for log in logs:
        needs_update = False
        update_data = {}
        
        for field in time_fields:
            if field in log and log[field] is not None:
                original_value = log[field]
                converted_value = convert_to_beijing_time(original_value)
                
                if converted_value and converted_value != original_value:
                    update_data[field] = converted_value
                    needs_update = True
        
        if needs_update:
            db_service.sync_logs.update_one(
                {'_id': log['_id']},
                {'$set': update_data}
            )
            updated_count += 1
    
    logger.info(f"✅ sync_logs集合迁移完成，共更新 {updated_count} 条记录")
    return updated_count


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("数据库时区迁移工具")
    logger.info("将所有时间字段转换为北京时间（Asia/Shanghai UTC+8）")
    logger.info("=" * 60)
    
    try:
        # 连接数据库
        logger.info(f"连接到MongoDB: {MONGO_URI}")
        logger.info(f"数据库: {MONGO_DB_NAME}")
        db_service = DatabaseService(MONGO_URI, MONGO_DB_NAME)
        
        # 执行迁移
        items_updated = migrate_items_collection(db_service)
        logs_updated = migrate_sync_logs_collection(db_service)
        
        # 汇总报告
        logger.info("=" * 60)
        logger.info("迁移完成汇总:")
        logger.info(f"  - items集合: 更新 {items_updated} 条记录")
        logger.info(f"  - sync_logs集合: 更新 {logs_updated} 条记录")
        logger.info(f"  - 总计: 更新 {items_updated + logs_updated} 条记录")
        logger.info("=" * 60)
        logger.info("✅ 所有时间字段已转换为北京时间")
        
    except Exception as e:
        logger.error(f"❌ 迁移失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    # 确认执行
    print("\n⚠️  警告：此脚本将修改数据库中的所有时间字段")
    print(f"数据库: {MONGO_DB_NAME}")
    print(f"连接: {MONGO_URI[:50]}...")
    response = input("\n确定要继续吗？(yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        main()
    else:
        print("已取消迁移")
        sys.exit(0)

