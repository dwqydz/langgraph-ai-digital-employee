"""
数据库模型包
包含所有SQLAlchemy ORM模型定义

模块说明:
- user_model.py: 用户模型
- todo_model.py: 待办事项模型
- meeting_room_model.py: 会议室模型
- meeting_booking_model.py: 会议室预订模型
- weather_cache_model.py: 天气缓存模型
- chat_history_model.py: 对话历史模型
- knowledge_base_model.py: 知识库模型
- knowledge_document_model.py: 知识库文档模型
- notification_model.py: 通知提醒模型
- operation_log_model.py: 操作日志模型

注意: 数据库配置(引擎、会话工厂、Base类)统一在 config/db_config.py 中定义
"""

# 从config导入数据库配置
from config.db_config import Base, async_engine, AsyncSessionLocal, get_database

# 导入所有模型
from model.user_model import User
from model.todo_model import Todo
from model.meeting_room_model import MeetingRoom
from model.meeting_booking_model import MeetingBooking
from model.weather_cache_model import WeatherCache
from model.chat_history_model import ChatHistory
from model.knowledge_base_model import KnowledgeBase
from model.knowledge_document_model import KnowledgeDocument
from model.notification_model import Notification
from model.operation_log_model import OperationLog
from model.session_token_model import SessionToken

# 导出所有模型和配置
__all__ = [
    # 数据库配置(从config导入)
    "Base",
    "async_engine",
    "AsyncSessionLocal",
    "get_database",
    
    # 模型类
    "User",
    "Todo",
    "MeetingRoom",
    "MeetingBooking",
    "WeatherCache",
    "ChatHistory",
    "KnowledgeBase",
    "KnowledgeDocument",
    "Notification",
    "OperationLog",
    "SessionToken",
]
