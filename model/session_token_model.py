"""
会话Token模型
用于存储用户的登录会话信息,支持主动失效和会话管理
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.db_config import Base


class SessionToken(Base):
    """会话Token模型 - 存储用户的活跃会话"""
    
    __tablename__ = "session_tokens"
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment="记录ID")
    
    # 外键关联用户
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="所属用户ID")
    
    # Token值(随机生成的长字符串)
    token = Column(String(256), unique=True, nullable=False, index=True, comment="会话Token")
    
    # Token元数据
    ip_address = Column(String(45), comment="登录IP地址")
    user_agent = Column(String(500), comment="用户代理(浏览器信息)")
    device_info = Column(String(200), comment="设备信息")
    
    # 状态控制
    is_active = Column(Boolean, default=True, index=True, comment="是否有效")
    expires_at = Column(DateTime, nullable=False, index=True, comment="过期时间")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    last_used_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="最后使用时间")
    
    # 关系映射
    user = relationship("User", backref="sessions")
    
    # 索引优化查询
    __table_args__ = (
        Index('idx_user_active', 'user_id', 'is_active'),
        Index('idx_token_expires', 'token', 'expires_at'),
    )
    
    def __repr__(self):
        return f"<SessionToken(id={self.id}, user_id={self.user_id}, active={self.is_active})>"
