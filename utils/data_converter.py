"""
数据转换工具
提供通用的数据转换函数，减少重复代码
"""
from typing import List
from model import Todo, MeetingRoom, MeetingBooking
from schemas.todo_schemas import TodoItem
from schemas.meeting_schemas import MeetingRoom as MeetingRoomSchema, BookingItem


def convert_to_todo_item(todo: Todo) -> TodoItem:
    """
    将Todo模型转换为TodoItem响应模型
    
    Args:
        todo: Todo数据库模型对象
        
    Returns:
        TodoItem Pydantic模型
    """
    return TodoItem(
        id=todo.id,
        title=todo.title,
        description=todo.description,
        status=todo.status,
        priority=todo.priority,
        category=todo.category,
        due_date=todo.due_date,
        completed_at=todo.completed_at,
        reminder_enabled=todo.reminder_enabled,
        is_reminded=todo.is_reminded,
        created_at=todo.created_at,
        updated_at=todo.updated_at
    )


def convert_to_todo_items(todos: List[Todo]) -> List[TodoItem]:
    """
    批量转换Todo模型为TodoItem响应模型
    
    Args:
        todos: Todo数据库模型对象列表
        
    Returns:
        TodoItem Pydantic模型列表
    """
    return [convert_to_todo_item(todo) for todo in todos]


def convert_to_meeting_room(room: MeetingRoom) -> MeetingRoomSchema:
    """
    将MeetingRoom模型转换为MeetingRoomSchema响应模型
    
    Args:
        room: MeetingRoom数据库模型对象
        
    Returns:
        MeetingRoomSchema Pydantic模型
    """
    return MeetingRoomSchema(
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


def convert_to_booking_item(booking: MeetingBooking, room_name: str = "未知会议室") -> BookingItem:
    """
    将MeetingBooking模型转换为BookingItem响应模型
    
    Args:
        booking: MeetingBooking数据库模型对象
        room_name: 会议室名称
        
    Returns:
        BookingItem Pydantic模型
    """
    return BookingItem(
        id=booking.id,
        room_id=booking.room_id,
        room_name=room_name,
        start_time=booking.start_time,
        end_time=booking.end_time,
        purpose=booking.purpose,
        attendees=booking.attendees or [],
        status=booking.status,
        created_at=booking.created_at
    )
