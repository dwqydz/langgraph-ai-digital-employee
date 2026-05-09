"""
对话历史模型
对应数据库中的chat_history表
"""
from sqlalchemy import Column, BigInteger, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.db_config import Base


class ChatHistory(Base):
    """对话历史模型 - 存储用户与AI助手的对话历史"""
    
    __tablename__ = "chat_history"
    
    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="消息ID")
    
    # 外键关联
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")
    
    # 对话信息
    session_id = Column(String(100), nullable=False, index=True, comment="会话ID(UUID)")
    role = Column(String(20), nullable=False, comment="角色: user-用户, assistant-助手, system-系统")
    content = Column(Text, nullable=False, comment="消息内容")
    message_metadata = Column("metadata", JSON, comment="元数据: 意图、调用的工具等")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), index=True, comment="创建时间")
    
    # 关系映射
    user = relationship("User", backref="chat_histories")
    
    def __repr__(self):
        return f"<ChatHistory(id={self.id}, session_id='{self.session_id}', role='{self.role}')>"
