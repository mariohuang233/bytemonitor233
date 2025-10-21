"""清单相关API路由"""
from flask import Blueprint, request, jsonify

items_bp = Blueprint('items', __name__)


def init_routes(db_service):
    """初始化路由"""
    
    @items_bp.route('/items', methods=['GET'])
    def get_items():
        """获取清单列表"""
        try:
            # 获取查询参数
            sheet_name = request.args.get('type')  # intern/campus/experienced
            page = int(request.args.get('page', 1))
            limit = int(request.args.get('limit', 20))
            search = request.args.get('search')
            is_new = request.args.get('is_new')
            
            # 转换is_new为布尔值
            if is_new is not None:
                is_new = is_new.lower() == 'true'
            
            # 查询数据
            result = db_service.get_items(
                sheet_name=sheet_name,
                page=page,
                limit=limit,
                search=search,
                is_new=is_new
            )
            
            return jsonify({
                'success': True,
                'data': result
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    @items_bp.route('/items/<item_id>', methods=['GET'])
    def get_item(item_id):
        """获取单个条目详情"""
        try:
            item = db_service.get_item_by_id(item_id)
            
            if not item:
                return jsonify({
                    'success': False,
                    'message': '条目不存在'
                }), 404
            
            return jsonify({
                'success': True,
                'data': item
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
    
    return items_bp

