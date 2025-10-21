"""数据导入服务"""
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import logging
import pytz

logger = logging.getLogger(__name__)

# 北京时区
BEIJING_TZ = pytz.timezone('Asia/Shanghai')


class DataImporter:
    """从JSON缓存文件导入数据到MongoDB"""
    
    def __init__(self, db_service, json_file_path: Path):
        self.db = db_service
        self.json_file = json_file_path
    
    @staticmethod
    def _generate_job_hash(job_data: Dict) -> str:
        """生成job_hash（与爬虫脚本保持一致）"""
        key_fields = ['code', 'title', 'description', 'requirement']
        hash_string = ''.join(str(job_data.get(field, '')) for field in key_fields)
        return hashlib.md5(hash_string.encode('utf-8')).hexdigest()
    
    @staticmethod
    def _parse_time(time_str) -> datetime:
        """解析时间字符串为北京时间"""
        if isinstance(time_str, datetime):
            # 如果已经是datetime对象，确保有时区信息
            if time_str.tzinfo is None:
                # 假设无时区的datetime是北京时间
                return BEIJING_TZ.localize(time_str)
            return time_str.astimezone(BEIJING_TZ)
        if isinstance(time_str, str):
            try:
                # 解析字符串为datetime，假设是北京时间
                dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                return BEIJING_TZ.localize(dt)
            except:
                return datetime.now(BEIJING_TZ)
        return datetime.now(BEIJING_TZ)
    
    def import_from_json(self, clear_existing: bool = False) -> Dict:
        """从JSON文件导入数据"""
        if not self.json_file.exists():
            logger.error(f"JSON文件不存在: {self.json_file}")
            return {'success': False, 'message': 'JSON文件不存在'}
        
        try:
            # 读取JSON数据
            with open(self.json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 可选：清空现有数据
            if clear_existing:
                self.db.clear_all_items()
                logger.info("已清空现有数据")
            
            # 导入数据
            total_imported = 0
            total_updated = 0
            
            for sheet_name, records in data.items():
                if not records:
                    continue
                
                logger.info(f"正在导入 {sheet_name}，共 {len(records)} 条")
                
                for record in records:
                    # 生成job_hash
                    job_hash = self._generate_job_hash(record)
                    record['job_hash'] = job_hash
                    record['sheet_name'] = sheet_name
                    
                    # 解析时间字段
                    if '采摘时间' in record and record['采摘时间']:
                        record['采摘时间'] = self._parse_time(record['采摘时间'])
                    
                    if 'publish_time' in record:
                        record['publish_time'] = self._parse_time(record['publish_time'])
                    
                    # 设置类型名称
                    type_mapping = {
                        'intern': '新丝瓜',
                        'campus': '生丝瓜',
                        'experienced': '熟丝瓜'
                    }
                    record['type_name'] = type_mapping.get(sheet_name, sheet_name)
                    
                    # 设置状态
                    if 'is_viewed' not in record:
                        record['is_viewed'] = False
                    
                    # 插入或更新
                    if self.db.upsert_item(job_hash, record):
                        total_updated += 1
                    else:
                        total_imported += 1
            
            message = f"导入完成：新增 {total_imported} 条，更新 {total_updated} 条"
            logger.info(message)
            
            return {
                'success': True,
                'message': message,
                'imported': total_imported,
                'updated': total_updated
            }
            
        except Exception as e:
            error_msg = f"导入失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'message': error_msg
            }

