from fastapi import APIRouter, HTTPException, Depends
import datetime
import json

# 导入Pydantic模式
from schemas.meeting_schemas import (
    BookingRequest, NLPBookingRequest, 
    MeetingRoom as MeetingRoomSchema,
    BookingItem, RoomListResponse, BookingListResponse, 
    BookingData, BookingResponse, CancelBookingData, CancelBookingResponse
)

# 导入数据库配置
from config.db_config import get_database

# 导入CRUD操作
from crud import meeting_crud

# 导入Session Token认证
from utils.session_auth import get_current_user_id_from_session

# 导入MeetingAgent
from agent.meeting_agent import meeting_agent

router = APIRouter(
    prefix="/meeting",
    tags=["会议室模块"]
)


@router.get("/rooms", response_model=RoomListResponse)
async def get_meeting_rooms(
    db = Depends(get_database),
    floor: int = None,
    lighting: str = None,
    min_capacity: int = None,
    page: int = 1,
    page_size: int = 10
):
    """获取会议室列表 - 支持分页和条件筛选"""
    # 查询所有可用的会议室
    rooms, total = await meeting_crud.get_available_rooms(
        db, floor, lighting, min_capacity, page, page_size
    )
    
    # 转换为响应格式
    room_items = [
        MeetingRoomSchema(
            id=room.id,
            name=room.name,
            location=room.location,
            capacity=room.capacity,
            floor=room.floor,
            building=room.building,
            equipment=room.equipment or [],
            status=room.status,
            description=room.description,
            image_url=room.image_url
        )
        for room in rooms
    ]
    
    return RoomListResponse(
        code=200,
        message=f"获取成功，共{total}个会议室",
        data=room_items
    )


@router.get("/bookings/my", response_model=BookingListResponse)
async def get_my_bookings(
    db = Depends(get_database),
    current_user_id: int = Depends(get_current_user_id_from_session),
    page: int = 1,
    page_size: int = 10
):
    """获取我的预订 - 分页查询"""
    # 查询用户的预订记录
    bookings_with_rooms, total = await meeting_crud.get_rooms_with_bookings(
        db, current_user_id, page, page_size
    )
    
    # 转换为响应格式
    booking_items = []
    for item in bookings_with_rooms:
        booking = item["booking"]
        room = item["room"]
        
        booking_items.append(BookingItem(
            id=booking.id,
            room_id=booking.room_id,
            room_name=room.name if room else "未知会议室",
            start_time=booking.start_time,
            end_time=booking.end_time,
            purpose=booking.purpose,
            attendees=booking.attendees or [],
            status=booking.status,
            created_at=booking.created_at
        ))
    
    return BookingListResponse(
        code=200,
        message=f"获取成功，共{total}条预订",
        data=booking_items
    )


@router.post("/rooms/{room_id}/book", response_model=BookingResponse)
async def book_room(
    room_id: int,
    booking: BookingRequest,
    db = Depends(get_database),
    current_user_id: int = Depends(get_current_user_id_from_session)
):
    """预订会议室"""
    # 检查会议室是否存在且可用
    room = await meeting_crud.get_room_by_id(db, room_id)
    
    if not room:
        raise HTTPException(status_code=404, detail="会议室不存在")
    
    if room.status != "可申请":
        raise HTTPException(status_code=400, detail="会议室当前不可用")
    
    # 检查时间冲突
    conflict = await meeting_crud.check_time_conflict(
        db, room_id, booking.start_time, booking.end_time
    )
    
    if conflict:
        raise HTTPException(
            status_code=409,
            detail=f"时间段冲突,该会议室在 {conflict.start_time} 到 {conflict.end_time} 已被预订"
        )
    
    # 创建预订
    new_booking = await meeting_crud.create_booking(
        db=db,
        room_id=room_id,
        user_id=current_user_id,
        start_time=booking.start_time,
        end_time=booking.end_time,
        purpose=booking.purpose,
        attendees=booking.attendees,
        status="confirmed"
    )
    
    booking_data = BookingData(
        id=new_booking.id,
        room_id=new_booking.room_id,
        start_time=new_booking.start_time,
        end_time=new_booking.end_time,
        status=new_booking.status
    )
    
    return BookingResponse(
        code=201,
        message="预订成功",
        data=booking_data
    )


@router.delete("/bookings/{booking_id}", response_model=CancelBookingResponse)
async def cancel_booking(
    booking_id: int,
    db = Depends(get_database),
    current_user_id: int = Depends(get_current_user_id_from_session)
):
    """取消预订"""
    # 查询预订记录
    booking = await meeting_crud.get_booking_by_id_and_user(db, booking_id, current_user_id)
    
    if not booking:
        raise HTTPException(status_code=404, detail="预订记录不存在")
    
    if booking.status != "confirmed":
        raise HTTPException(status_code=400, detail="只能取消已确认的预订")
    
    # 取消预订
    updated_booking = await meeting_crud.cancel_booking(db, booking, current_user_id)
    
    cancel_data = CancelBookingData(
        id=updated_booking.id,
        status=updated_booking.status,
        cancelled_at=updated_booking.cancelled_at
    )
    
    return CancelBookingResponse(
        code=200,
        message="取消成功",
        data=cancel_data
    )


@router.put("/bookings/{booking_id}/complete", response_model=CancelBookingResponse)
async def complete_booking(
    booking_id: int,
    db = Depends(get_database),
    current_user_id: int = Depends(get_current_user_id_from_session)
):
    """完成预订"""
    # 查询预订记录
    booking = await meeting_crud.get_booking_by_id_and_user(db, booking_id, current_user_id)
    
    if not booking:
        raise HTTPException(status_code=404, detail="预订记录不存在")
    
    if booking.status != "confirmed":
        raise HTTPException(status_code=400, detail="只能完成已确认的预订")
    
    # 完成预订
    updated_booking = await meeting_crud.complete_booking(db, booking)
    
    cancel_data = CancelBookingData(
        id=updated_booking.id,
        status=updated_booking.status,
        cancelled_at=updated_booking.cancelled_at
    )
    
    return CancelBookingResponse(
        code=200,
        message="标记为已完成",
        data=cancel_data
    )


@router.post("/nlp-book", response_model=BookingResponse)
async def nlp_book(
    request: NLPBookingRequest,
    db = Depends(get_database),
    current_user_id: int = Depends(get_current_user_id_from_session)
):
    """NLP智能预订 - 简化版,实际需要集成NLP模型"""
    # TODO: 这里应该调用NLP模型解析自然语言
    # 目前仅作为示例,实际使用时需要集成Langchain或其他NLP框架
    
    # 模拟解析结果
    # 实际应该从NLP模型中提取: 时间、人数、设备需求等
    parsed_info = {
        "date": "明天",
        "time": "上午9点",
        "duration": 1,  # 小时
        "capacity": 10,
        "equipment": ["投影仪"]
    }
    
    # 根据解析结果查找合适的会议室
    # 这里简化处理,实际需要更复杂的逻辑
    rooms = await meeting_crud.get_available_rooms(db)
    room = None
    for r in rooms:
        if r.capacity >= parsed_info["capacity"]:
            room = r
            break
    
    if not room:
        raise HTTPException(status_code=404, detail="未找到合适的会议室")
    
    # 计算具体时间(简化处理)
    now = datetime.datetime.now()
    start_time = now + datetime.timedelta(days=1, hours=9)  # 明天9点
    end_time = start_time + datetime.timedelta(hours=parsed_info["duration"])
    
    # 检查时间冲突
    conflict = await meeting_crud.check_time_conflict(db, room.id, start_time, end_time)
    
    if conflict:
        raise HTTPException(status_code=409, detail="该时间段已被预订,请选择其他时间")
    
    # 创建预订
    new_booking = await meeting_crud.create_booking(
        db=db,
        room_id=room.id,
        user_id=current_user_id,
        start_time=start_time,
        end_time=end_time,
        purpose=f"NLP智能预订 - {request.text}",
        attendees=[],
        status="confirmed"
    )
    
    booking_data = BookingData(
        id=new_booking.id,
        room_id=new_booking.room_id,
        room_name=room.name,
        start_time=new_booking.start_time,
        end_time=new_booking.end_time,
        status=new_booking.status
    )
    
    return BookingResponse(
        code=201,
        message=f"智能预订成功!已为您预订 {room.name}",
        data=booking_data
    )
