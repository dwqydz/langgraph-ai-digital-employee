"""
通知提醒模型
对应数据库中的notifications表
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.db_config import Base


class Notification(Base):
    """通知提醒模型 - 存储系统通知和提醒记录"""
    
    __tablename__ = "notifications"
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment="通知ID")
    
    # 外键关联
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="接收用户ID")
    
    # 通知信息
    type = Column(String(50), nullable=False, index=True, comment="类型: todo_reminder-待办提醒, meeting_reminder-会议提醒, system-系统通知")
    title = Column(String(200), nullable=False, comment="通知标题")
    content = Column(Text, nullable=False, comment="通知内容")
    related_id = Column(Integer, index=True, comment="关联ID(任务ID或预订ID)")
    related_type = Column(String(50), index=True, comment="关联类型: todo-待办, booking-预订")
    
    # 阅读状态
    is_read = Column(Boolean, default=False, index=True, comment="是否已读")
    read_at = Column(DateTime, comment="阅读时间")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), index=True, comment="创建时间")
    
    # 关系映射
    user = relationship("User", backref="notifications")
    
    def __repr__(self):
        return f"<Notification(id={self.id}, type='{self.type}', is_read={self.is_read})>"
