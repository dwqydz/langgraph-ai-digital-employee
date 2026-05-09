"""
待办事项模型
对应数据库中的todos表
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.db_config import Base


class Todo(Base):
    """待办事项模型 - 存储用户的待办任务信息"""
    
    __tablename__ = "todos"
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment="任务ID")
    
    # 外键关联
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="所属用户ID")
    
    # 任务信息
    title = Column(String(200), nullable=False, comment="任务标题")
    description = Column(Text, comment="任务描述")
    status = Column(String(20), default="pending", index=True, comment="状态: pending-待处理, completed-已完成, cancelled-已取消")
    priority = Column(String(20), default="medium", index=True, comment="优先级: low-低, medium-中, high-高, urgent-紧急")
    category = Column(String(50), comment="业务分类: work-工作, study-学习, admin-行政, other-其它")
    
    # 智能分类标签（由AI自动生成）
    tags = Column(String(200), comment="智能标签，逗号分隔，如：会议,报告,紧急")
    
    # 时间相关
    due_date = Column(DateTime, index=True, comment="截止时间")
    completed_at = Column(DateTime, comment="完成时间")
    
    # 时间状态分类（由系统根据due_date自动计算）
    time_status = Column(String(20), default="ongoing", index=True, comment="时间状态: ongoing-进行中, overdue-逾期, completed-已完成, upcoming-即将到期")
    
    # 提醒设置
    reminder_enabled = Column(Boolean, default=False, comment="是否启用提醒")
    reminder_time = Column(DateTime, index=True, comment="提醒时间")
    is_reminded = Column(Boolean, default=False, comment="是否已提醒")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系映射
    user = relationship("User", backref="todos")
    
    def __repr__(self):
        return f"<Todo(id={self.id}, title='{self.title}', status='{self.status}')>"
