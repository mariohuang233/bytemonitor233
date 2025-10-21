"""数据库服务"""
from pymongo import MongoClient, DESCENDING, ASCENDING
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class DatabaseService:
    """MongoDB数据库服务"""
    
    def __init__(self, mongo_uri: str, db_name: str):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.items = self.db['sponge_items']
        self.sync_logs = self.db['sync_logs']
        
        # 创建索引
        self._create_indexes()
    
    def _create_indexes(self):
        """创建数据库索引"""
        # 为常用查询字段创建索引
        self.items.create_index([('sheet_name', ASCENDING)])
        self.items.create_index([('job_hash', ASCENDING)], unique=True)
        self.items.create_index([('采摘时间', DESCENDING)])
        self.items.create_index([('publish_time', DESCENDING)])
        self.items.create_index([('title', 'text'), ('description', 'text'), ('requirement', 'text')])
        
        self.sync_logs.create_index([('sync_time', DESCENDING)])
    
    # ===== 数据查询 =====
    
    def get_items(self, sheet_name: Optional[str] = None, 
                  page: int = 1, limit: int = 20,
                  search: Optional[str] = None,
                  is_new: Optional[bool] = None,
                  sort_by: str = '采摘时间',
                  sort_order: int = DESCENDING) -> Dict:
        """获取清单列表"""
        query = {}
        
        # 筛选条件
        if sheet_name:
            query['sheet_name'] = sheet_name
        if is_new is not None:
            query['is_new'] = is_new
        if search:
            query['$text'] = {'$search': search}
        
        # 计算分页
        skip = (page - 1) * limit
        
        # 查询
        cursor = self.items.find(query).sort(sort_by, sort_order).skip(skip).limit(limit)
        items = list(cursor)
        
        # 转换ObjectId为字符串
        for item in items:
            item['_id'] = str(item['_id'])
        
        # 总数
        total = self.items.count_documents(query)
        
        return {
            'items': items,
            'total': total,
            'page': page,
            'limit': limit,
            'pages': (total + limit - 1) // limit
        }
    
    def get_item_by_id(self, item_id: str) -> Optional[Dict]:
        """根据ID获取单个条目"""
        from bson.objectid import ObjectId
        try:
            item = self.items.find_one({'_id': ObjectId(item_id)})
            if item:
                item['_id'] = str(item['_id'])
            return item
        except Exception as e:
            logger.error(f"获取条目失败: {e}")
            return None
    
    # ===== 统计数据 =====
    
    def get_stats(self) -> Dict:
        """获取统计数据"""
        # 总数
        total = self.items.count_documents({})
        
        # 今日新增
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_new = self.items.count_documents({
            '采摘时间': {'$gte': today_start}
        })
        
        # 本周新增
        week_start = today_start - timedelta(days=today_start.weekday())
        week_new = self.items.count_documents({
            '采摘时间': {'$gte': week_start}
        })
        
        # 分类统计
        type_distribution = {}
        for sheet_name in ['intern', 'campus', 'experienced']:
            count = self.items.count_documents({'sheet_name': sheet_name})
            type_name = {'intern': '新丝瓜', 'campus': '生丝瓜', 'experienced': '熟丝瓜'}[sheet_name]
            type_distribution[type_name] = count
        
        # 每日趋势（最近7天）
        daily_trend = []
        for i in range(6, -1, -1):
            day_start = today_start - timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            count = self.items.count_documents({
                '采摘时间': {'$gte': day_start, '$lt': day_end}
            })
            daily_trend.append({
                'date': day_start.strftime('%m-%d'),
                'count': count
            })
        
        return {
            'total': total,
            'today_new': today_new,
            'week_new': week_new,
            'type_distribution': type_distribution,
            'daily_trend': daily_trend
        }
    
    # ===== 数据操作 =====
    
    def insert_item(self, item: Dict) -> str:
        """插入单个条目"""
        item['created_at'] = datetime.now()
        item['updated_at'] = datetime.now()
        result = self.items.insert_one(item)
        return str(result.inserted_id)
    
    def bulk_insert_items(self, items: List[Dict]) -> int:
        """批量插入条目"""
        if not items:
            return 0
        
        now = datetime.now()
        for item in items:
            item['created_at'] = now
            item['updated_at'] = now
        
        try:
            result = self.items.insert_many(items, ordered=False)
            return len(result.inserted_ids)
        except Exception as e:
            # 可能有重复的job_hash
            logger.warning(f"批量插入时有重复: {e}")
            return 0
    
    def upsert_item(self, job_hash: str, item: Dict) -> bool:
        """更新或插入条目"""
        item['updated_at'] = datetime.now()
        if 'created_at' not in item:
            item['created_at'] = datetime.now()
        
        result = self.items.update_one(
            {'job_hash': job_hash},
            {'$set': item},
            upsert=True
        )
        return result.modified_count > 0 or result.upserted_id is not None
    
    def clear_all_items(self):
        """清空所有条目（慎用）"""
        self.items.delete_many({})
    
    # ===== 同步日志 =====
    
    def add_sync_log(self, log_data: Dict) -> str:
        """添加同步日志"""
        log_data['sync_time'] = datetime.now()
        result = self.sync_logs.insert_one(log_data)
        return str(result.inserted_id)
    
    def get_latest_sync_logs(self, limit: int = 10) -> List[Dict]:
        """获取最近的同步日志"""
        cursor = self.sync_logs.find().sort('sync_time', DESCENDING).limit(limit)
        logs = list(cursor)
        for log in logs:
            log['_id'] = str(log['_id'])
        return logs

