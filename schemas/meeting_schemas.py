"""
会议室模块Pydantic模式
包含会议室预订的请求和响应模式
"""
from pydantic import BaseModel
from typing import Optional, List
import datetime


class MeetingRoom(BaseModel):
    """会议室响应模式"""
    id: int
    name: str
    location: str
    capacity: int
    floor: Optional[int] = None
    building: Optional[str] = None
    equipment: Optional[List[str]] = []
    status: str = "available"  # available, maintenance, closed
    description: Optional[str] = None
    image_url: Optional[str] = None

    class Config:
        from_attributes = True


class BookingRequest(BaseModel):
    """预订请求模式"""
    start_time: datetime.datetime
    end_time: datetime.datetime
    purpose: Optional[str] = None
    attendees: Optional[List[str]] = []


class NLPBookingRequest(BaseModel):
    """NLP智能预订请求模式"""
    text: str


class BookingItem(BaseModel):
    """预订记录响应模式"""
    id: int
    room_id: int
    room_name: str
    start_time: datetime.datetime
    end_time: datetime.datetime
    purpose: Optional[str] = None
    attendees: Optional[List[str]] = []
    status: str = "confirmed"  # confirmed, cancelled, completed
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class RoomListResponse(BaseModel):
    """会议室列表响应模式"""
    code: int = 200
    message: str = "获取成功"
    data: List[MeetingRoom] = []


class BookingListResponse(BaseModel):
    """预订列表响应模式"""
    code: int = 200
    message: str = "获取成功"
    data: List[BookingItem] = []


class BookingData(BaseModel):
    """预订数据模式"""
    id: int
    room_id: Optional[int] = None
    room_name: Optional[str] = None
    start_time: Optional[datetime.datetime] = None
    end_time: Optional[datetime.datetime] = None
    status: Optional[str] = None


class BookingResponse(BaseModel):
    """预订操作响应模式"""
    code: int = 201
    message: str = "预订成功"
    data: Optional[BookingData] = None


class CancelBookingData(BaseModel):
    """取消预订数据模式"""
    id: int
    status: str
    cancelled_at: Optional[datetime.datetime] = None  # 完成预约时为None


class CancelBookingResponse(BaseModel):
    """取消预订响应模式"""
    code: int = 200
    message: str = "取消成功"
    data: Optional[CancelBookingData] = None


class NLPBookingInfo(BaseModel):
    """NLP解析的预订信息"""
    date: Optional[str] = None
    time: Optional[str] = None
    duration: int = 1
    capacity: int = 5
    equipment: List[str] = []
    floor: Optional[int] = None
    building: Optional[str] = None
    room_type: Optional[str] = None


class NLPCancelInfo(BaseModel):
    """NLP解析的取消信息"""
    room_name: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None


class NLPCommandResponse(BaseModel):
    """NLP命令解析响应"""
    code: int = 200
    message: str = "解析成功"
    data: dict = {
        "intent": "book",  # book, cancel, complete
        "action_type": "book",
        "booking_info": None,
        "cancel_info": None,
        "confidence": 0.9,
        "explanation": "",
        "recommended_rooms": []  # 推荐的会议室列表
    }
