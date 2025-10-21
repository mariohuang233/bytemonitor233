"""统计相关API路由"""
from flask import Blueprint, jsonify

stats_bp = Blueprint('stats', __name__)


def init_routes(db_service):
    """初始化路由"""
    
    @stats_bp.route('/stats', methods=['GET'])
    def get_stats():
        """获取统计数据"""
        try:
            stats = db_service.get_stats()
            
            return jsonify({
                'success': True,
                'data': stats
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    @stats_bp.route('/sync-logs', methods=['GET'])
    def get_sync_logs():
        """获取同步日志"""
        try:
            logs = db_service.get_latest_sync_logs(limit=20)
            
            return jsonify({
                'success': True,
                'data': logs
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    return stats_bp

