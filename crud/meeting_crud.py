"""
会议室模块CRUD操作
包含会议室和预订记录的查询、创建等数据库操作
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
import datetime
from model import MeetingRoom, MeetingBooking


async def get_available_rooms(
    db: AsyncSession,
    floor: int = None,
    lighting: str = None,
    min_capacity: int = None,
    page: int = 1,
    page_size: int = 10
) -> tuple[list[MeetingRoom], int]:
    """
    分页查询可用会议室，支持条件筛选
    
    Args:
        db: 数据库会话
        floor: 楼层筛选
        lighting: 采光筛选(good/normal/poor)
        min_capacity: 最小容纳人数
        page: 页码
        page_size: 每页数量
        
    Returns:
        (会议室列表, 总数)
    """
    conditions = [MeetingRoom.status == "可申请"]
    
    if floor is not None:
        conditions.append(MeetingRoom.floor == floor)
    
    if lighting:
        conditions.append(MeetingRoom.lighting == lighting)
    
    if min_capacity is not None:
        conditions.append(MeetingRoom.capacity >= min_capacity)
    
    # 查询总数
    count_result = await db.execute(
        select(func.count(MeetingRoom.id)).where(and_(*conditions))
    )
    total = count_result.scalar()
    
    # 分页查询
    offset = (page - 1) * page_size
    result = await db.execute(
        select(MeetingRoom)
        .where(and_(*conditions))
        .order_by(MeetingRoom.capacity.asc())
        .offset(offset)
        .limit(page_size)
    )
    rooms = result.scalars().all()
    
    return rooms, total


async def get_filtered_rooms(db: AsyncSession, filter_params: dict) -> list[MeetingRoom]:
    """
    根据动态参数进行SQL粗筛选（用于Agent智能匹配）
    
    Args:
        db: 数据库会话
        filter_params: 过滤参数字典 {min_capacity, target_floor, target_building}
        
    Returns:
        符合条件的会议室列表
    """
    conditions = [MeetingRoom.status == "可申请"]
    
    if filter_params.get("min_capacity"):
        conditions.append(MeetingRoom.capacity >= filter_params["min_capacity"])
    
    if filter_params.get("target_floor"):
        conditions.append(MeetingRoom.floor == filter_params["target_floor"])
    
    if filter_params.get("target_building"):
        conditions.append(MeetingRoom.building.like(f"%{filter_params['target_building']}%"))
    
    result = await db.execute(
        select(MeetingRoom).where(and_(*conditions))
    )
    return result.scalars().all()


async def get_room_by_id(db: AsyncSession, room_id: int) -> MeetingRoom | None:
    """
    根据ID查询会议室
    
    Args:
        db: 数据库会话
        room_id: 会议室ID
        
    Returns:
        会议室对象或None
    """
    result = await db.execute(
        select(MeetingRoom).where(MeetingRoom.id == room_id)
    )
    return result.scalar_one_or_none()


async def get_rooms_with_bookings(
    db: AsyncSession,
    user_id: int,
    page: int = 1,
    page_size: int = 10
) -> tuple[list[dict], int]:
    """
    分页查询用户已预订的会议室列表（包含会议室信息和预订信息）
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        page: 页码
        page_size: 每页数量
        
    Returns:
        (预订记录列表, 总数)
    """
    # 查询总数 - 查询所有状态的预约
    count_result = await db.execute(
        select(func.count(MeetingBooking.id)).where(
            MeetingBooking.user_id == user_id
        )
    )
    total = count_result.scalar()
    
    # 分页查询 - 查询所有状态的预约
    offset = (page - 1) * page_size
    result = await db.execute(
        select(MeetingBooking, MeetingRoom)
        .join(MeetingRoom, MeetingBooking.room_id == MeetingRoom.id)
        .where(MeetingBooking.user_id == user_id)
        .order_by(MeetingBooking.start_time.desc())
        .offset(offset)
        .limit(page_size)
    )
    
    bookings_with_rooms = []
    for booking, room in result.all():
        bookings_with_rooms.append({
            "booking": booking,
            "room": room
        })
    
    return bookings_with_rooms, total


async def get_bookings_by_user_id(
    db: AsyncSession,
    user_id: int,
    status: str = None,
    page: int = 1,
    page_size: int = 10
) -> tuple[list[MeetingBooking], int]:
    """
    分页查询用户的预订记录
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        status: 状态筛选(confirmed/cancelled/completed)
        page: 页码
        page_size: 每页数量
        
    Returns:
        (预订记录列表, 总数)
    """
    conditions = [MeetingBooking.user_id == user_id]
    
    if status:
        conditions.append(MeetingBooking.status == status)
    
    # 查询总数
    count_result = await db.execute(
        select(func.count(MeetingBooking.id)).where(and_(*conditions))
    )
    total = count_result.scalar()
    
    # 分页查询
    offset = (page - 1) * page_size
    result = await db.execute(
        select(MeetingBooking)
        .where(and_(*conditions))
        .order_by(MeetingBooking.start_time.desc())
        .offset(offset)
        .limit(page_size)
    )
    bookings = result.scalars().all()
    
    return bookings, total


async def check_time_conflict(
    db: AsyncSession,
    room_id: int,
    start_time: datetime.datetime,
    end_time: datetime.datetime
) -> MeetingBooking | None:
    """
    检查时间段是否冲突
    
    Args:
        db: 数据库会话
        room_id: 会议室ID
        start_time: 开始时间
        end_time: 结束时间
        
    Returns:
        冲突的预订记录或None
    """
    result = await db.execute(
        select(MeetingBooking).where(
            and_(
                MeetingBooking.room_id == room_id,
                MeetingBooking.status == "confirmed",
                MeetingBooking.start_time < end_time,
                MeetingBooking.end_time > start_time
            )
        )
    )
    return result.scalar_one_or_none()


async def update_room_status(
    db: AsyncSession,
    room_id: int,
    status: str
) -> MeetingRoom | None:
    """
    更新会议室状态
    
    Args:
        db: 数据库会话
        room_id: 会议室ID
        status: 新状态(可申请/已申请/被占用)
        
    Returns:
        更新后的会议室对象或None
    """
    room = await get_room_by_id(db, room_id)
    if room:
        room.status = status
        await db.commit()
        await db.refresh(room)
    return room


async def create_booking(
    db: AsyncSession,
    room_id: int,
    user_id: int,
    start_time: datetime.datetime,
    end_time: datetime.datetime,
    purpose: str,
    attendees: list = None,
    status: str = "confirmed"
) -> MeetingBooking:
    """
    创建预订记录
    
    Args:
        db: 数据库会话
        room_id: 会议室ID
        user_id: 用户ID
        start_time: 开始时间
        end_time: 结束时间
        purpose: 预订目的
        attendees: 参会人员列表
        status: 预订状态
        
    Returns:
        新创建的预订记录
    """
    # 检查是否存在相同时间段的非confirmed状态记录（cancelled或completed），如果有则删除
    # 这样可以避免唯一约束冲突
    old_bookings = await db.execute(
        select(MeetingBooking).where(
            and_(
                MeetingBooking.room_id == room_id,
                MeetingBooking.start_time == start_time,
                MeetingBooking.end_time == end_time,
                MeetingBooking.status != "confirmed"  # 排除confirmed状态的预订
            )
        )
    )
    old_list = old_bookings.scalars().all()
    for old_booking in old_list:
        await db.delete(old_booking)
    await db.commit()
    
    new_booking = MeetingBooking(
        room_id=room_id,
        user_id=user_id,
        start_time=start_time,
        end_time=end_time,
        purpose=purpose,
        attendees=attendees or [],
        status=status
    )
    
    db.add(new_booking)
    await db.commit()
    await db.refresh(new_booking)
    
    # 创建预订成功后，将会议室状态改为"已申请"
    await update_room_status(db, room_id, "已申请")
    
    return new_booking


async def get_booking_by_id_and_user(
    db: AsyncSession,
    booking_id: int,
    user_id: int
) -> MeetingBooking | None:
    """
    根据ID和用户ID查询预订记录
    
    Args:
        db: 数据库会话
        booking_id: 预订ID
        user_id: 用户ID
        
    Returns:
        预订记录对象或None
    """
    result = await db.execute(
        select(MeetingBooking).where(
            and_(
                MeetingBooking.id == booking_id,
                MeetingBooking.user_id == user_id
            )
        )
    )
    return result.scalar_one_or_none()


async def cancel_booking(
    db: AsyncSession,
    booking: MeetingBooking,
    cancelled_by: int
) -> MeetingBooking:
    """
    取消预订
    
    Args:
        db: 数据库会话
        booking: 预订记录对象
        cancelled_by: 取消人ID
        
    Returns:
        更新后的预订记录
    """
    room_id = booking.room_id  # 保存会议室ID
    
    booking.status = "cancelled"
    booking.cancelled_by = cancelled_by
    booking.cancelled_at = datetime.datetime.now()
    
    await db.commit()
    
    # 取消预订成功后，将会议室状态改回“可申请”
    await update_room_status(db, room_id, "可申请")
    
    return booking


async def complete_booking(
    db: AsyncSession,
    booking: MeetingBooking
) -> MeetingBooking:
    """
    完成预订
    
    Args:
        db: 数据库会话
        booking: 预订记录对象
        
    Returns:
        更新后的预订记录
    """
    room_id = booking.room_id  # 保存会议室ID
    
    booking.status = "completed"
    
    await db.commit()
    
    # 完成预订后，将会议室状态改回“可申请”
    await update_room_status(db, room_id, "可申请")
    
    return booking
