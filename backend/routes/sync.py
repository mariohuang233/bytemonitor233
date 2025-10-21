"""同步相关API路由"""
from flask import Blueprint, jsonify
import subprocess
import threading
from datetime import datetime
import logging
import pytz

logger = logging.getLogger(__name__)

# 北京时区
BEIJING_TZ = pytz.timezone('Asia/Shanghai')

sync_bp = Blueprint('sync', __name__)

# 全局状态管理
sync_status = {
    'running': False,
    'message': '',
    'progress': 0
}


def init_routes(db_service, importer, crawler_script_path):
    """初始化路由"""
    
    def run_crawler_and_import():
        """运行爬虫并导入数据"""
        global sync_status
        start_time = datetime.now(BEIJING_TZ)
        
        try:
            sync_status['running'] = True
            sync_status['message'] = '正在运行爬虫脚本...'
            sync_status['progress'] = 30
            
            # 运行Python爬虫脚本
            result = subprocess.run(
                ['python3', str(crawler_script_path)],
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode != 0:
                raise Exception(f"爬虫脚本执行失败: {result.stderr}")
            
            logger.info("爬虫脚本执行成功")
            sync_status['message'] = '爬虫完成，开始导入数据...'
            sync_status['progress'] = 60
            
            # 导入数据到MongoDB
            import_result = importer.import_from_json(clear_existing=False)
            
            if not import_result['success']:
                raise Exception(import_result['message'])
            
            sync_status['message'] = '同步完成！'
            sync_status['progress'] = 100
            
            # 记录同步日志
            duration = (datetime.now(BEIJING_TZ) - start_time).total_seconds()
            db_service.add_sync_log({
                'type': 'manual',
                'status': 'success',
                'new_count': import_result.get('imported', 0),
                'total_count': db_service.items.count_documents({}),
                'duration': duration,
                'error_message': None
            })
            
            logger.info(f"同步成功：{import_result['message']}")
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"同步失败: {error_msg}", exc_info=True)
            sync_status['message'] = f'同步失败: {error_msg}'
            sync_status['progress'] = 0
            
            # 记录失败日志
            duration = (datetime.now(BEIJING_TZ) - start_time).total_seconds()
            db_service.add_sync_log({
                'type': 'manual',
                'status': 'failed',
                'new_count': 0,
                'total_count': db_service.items.count_documents({}),
                'duration': duration,
                'error_message': error_msg
            })
        
        finally:
            # 重置状态（5秒后）
            def reset_status():
                import time
                time.sleep(5)
                sync_status['running'] = False
                sync_status['progress'] = 0
            
            threading.Thread(target=reset_status).start()
    
    @sync_bp.route('/sync', methods=['POST'])
    def trigger_sync():
        """触发同步"""
        global sync_status
        
        if sync_status['running']:
            return jsonify({
                'success': False,
                'message': '同步正在进行中，请稍候'
            }), 400
        
        # 在后台线程中运行同步任务
        thread = threading.Thread(target=run_crawler_and_import)
        thread.start()
        
        return jsonify({
            'success': True,
            'message': '同步已启动'
        })
    
    @sync_bp.route('/sync/status', methods=['GET'])
    def get_sync_status():
        """获取同步状态"""
        return jsonify({
            'success': True,
            'data': sync_status
        })
    
    return sync_bp

