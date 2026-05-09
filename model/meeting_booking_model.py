"""
会议室预订模型
对应数据库中的meeting_bookings表
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.db_config import Base


class MeetingBooking(Base):
    """会议室预订模型 - 存储会议室预订记录"""
    
    __tablename__ = "meeting_bookings"
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment="预订ID")
    
    # 外键关联
    room_id = Column(Integer, ForeignKey("meeting_rooms.id", ondelete="CASCADE"), nullable=False, index=True, comment="会议室ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="预订人ID")
    cancelled_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), comment="取消人ID")
    
    # 预订信息
    start_time = Column(DateTime, nullable=False, index=True, comment="开始时间")
    end_time = Column(DateTime, nullable=False, index=True, comment="结束时间")
    purpose = Column(String(500), comment="会议主题/用途")
    attendees = Column(JSON, comment="参会人列表: ['张三','李四']")
    status = Column(String(20), default="confirmed", index=True, comment="状态: confirmed-已确认, cancelled-已取消, completed-已完成")
    
    # 取消信息
    cancel_reason = Column(String(500), comment="取消原因")
    cancelled_at = Column(DateTime, comment="取消时间")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系映射
    room = relationship("MeetingRoom", backref="bookings")
    user = relationship("User", backref="bookings", foreign_keys=[user_id])
    canceller = relationship("User", foreign_keys=[cancelled_by])
    
    # 唯一约束: 确保同一会议室在同一时间段内只能有一个confirmed状态的预订
    __table_args__ = (
        UniqueConstraint('room_id', 'start_time', 'end_time', name='uk_room_time'),
    )
    
    def __repr__(self):
        return f"<MeetingBooking(id={self.id}, room_id={self.room_id}, status='{self.status}')>"
