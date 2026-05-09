"""
操作日志模型
对应数据库中的operation_logs表
"""
from sqlalchemy import Column, BigInteger, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.db_config import Base


class OperationLog(Base):
    """操作日志模型 - 记录用户操作日志,用于审计和分析"""
    
    __tablename__ = "operation_logs"
    
    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="日志ID")
    
    # 外键关联
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True, comment="操作用户ID")
    
    # 操作信息
    action = Column(String(100), nullable=False, index=True, comment="操作类型: create-创建, update-更新, delete-删除, login-登录等")
    module = Column(String(50), nullable=False, index=True, comment="模块: todo-待办, meeting-会议, weather-天气, auth-认证等")
    resource_id = Column(Integer, comment="资源ID")
    request_method = Column(String(10), comment="HTTP方法: GET, POST, PUT, DELETE")
    request_url = Column(String(500), comment="请求URL")
    ip_address = Column(String(50), comment="IP地址")
    user_agent = Column(String(500), comment="浏览器信息")
    status_code = Column(Integer, index=True, comment="响应状态码")
    error_message = Column(Text, comment="错误信息")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), index=True, comment="操作时间")
    
    # 关系映射
    user = relationship("User", backref="operation_logs")
    
    def __repr__(self):
        return f"<OperationLog(id={self.id}, user_id={self.user_id}, action='{self.action}')>"
