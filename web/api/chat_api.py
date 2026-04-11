"""
聊天和RAG相关API模块
"""
import json
from typing import Dict, Any
from datetime import datetime
from utils.logger import logger
from database import db
from rag.engine import rag_engine


class ChatAPI:
    """聊天API处理器"""
    
    def chat(self, handler):
        """处理聊天请求"""
        try:
            content_length = int(handler.headers['Content-Length'])
            post_data = handler.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            message = data.get('message', '')
            category = data.get('category', None)
            session_id = data.get('session_id', None)
            
            if not message:
                handler._send_error_response("缺少message参数")
                return
            
            if not session_id:
                session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                db.create_chat_session(session_id)
            
            context = rag_engine.build_context(message, category)
            
            response = {
                'success': True,
                'message': message,
                'context': context,
                'session_id': session_id,
                'response': f"基于以下新闻回答：\n{context}"
            }
            
            db.add_chat_message(
                session_id,
                'user',
                message
            )
            
            db.add_chat_message(
                session_id,
                'assistant',
                response['response']
            )
            
            handler._send_json_response(response)
            
        except Exception as e:
            logger.error(f"对话失败: {e}")
            handler._send_error_response(str(e))


chat_api = ChatAPI()