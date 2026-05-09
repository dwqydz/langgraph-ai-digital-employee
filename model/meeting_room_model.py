"""
会议室模型
对应数据库中的meeting_rooms表
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean
from sqlalchemy.sql import func
from config.db_config import Base


class MeetingRoom(Base):
    """会议室模型 - 存储会议室基本信息"""
    
    __tablename__ = "meeting_rooms"
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment="会议室ID")
    
    # 基本信息
    name = Column(String(100), nullable=False, comment="会议室名称")
    location = Column(String(200), nullable=False, index=True, comment="位置(如:A栋3楼)")
    capacity = Column(Integer, nullable=False, index=True, comment="容纳人数")
    floor = Column(Integer, comment="楼层")
    building = Column(String(50), comment="楼栋")
    
    # 环境属性
    lighting = Column(String(20), default="normal", comment="采光: good-良好, normal-一般, poor-较差")
    has_window = Column(Boolean, default=True, comment="是否有窗户")
    environment = Column(String(200), comment="环境描述，如：安静、通风良好")
    
    # 设备和状态
    equipment = Column(JSON, comment="设备列表: ['投影仪','白板','音响']")
    status = Column(String(20), default="available", index=True, comment="状态: available-可用, maintenance-维护中, closed-关闭")
    description = Column(Text, comment="详细描述")
    image_url = Column(String(255), comment="图片URL")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def __repr__(self):
        return f"<MeetingRoom(id={self.id}, name='{self.name}', capacity={self.capacity})>"
