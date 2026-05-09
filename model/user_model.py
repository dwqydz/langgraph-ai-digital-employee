"""
用户模型
对应数据库中的users表
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from config.db_config import Base


class User(Base):
    """用户模型 - 存储系统用户基本信息和认证信息"""
    
    __tablename__ = "users"
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment="用户ID")
    
    # 基本信息
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名(唯一)")
    password_hash = Column(String(255), nullable=False, comment="密码哈希值(SHA256)")
    email = Column(String(100), unique=True, index=True, comment="邮箱地址")
    phone = Column(String(20), comment="手机号")
    avatar_url = Column(String(255), comment="头像URL")
    
    # 权限和状态
    role = Column(String(20), default="user", index=True, comment="角色: user-普通用户, admin-管理员")
    is_active = Column(Boolean, default=True, comment="是否激活")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    last_login_at = Column(DateTime, comment="最后登录时间")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
