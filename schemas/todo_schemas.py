"""
待办事项模块Pydantic模式
包含待办事项的请求和响应模式
"""
from pydantic import BaseModel
from typing import Optional, List
import datetime


class TodoCreate(BaseModel):
    """创建待办请求模式"""
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime.datetime] = None
    priority: str = "medium"  # low, medium, high, urgent
    category: Optional[str] = None
    reminder_enabled: bool = False
    reminder_time: Optional[datetime.datetime] = None


class TodoUpdate(BaseModel):
    """更新待办请求模式"""
    status: Optional[str] = None  # pending, completed, cancelled


class TodoItem(BaseModel):
    """待办事项响应模式"""
    id: int
    title: str
    description: Optional[str] = None
    status: str = "pending"
    priority: str = "medium"
    category: Optional[str] = None
    due_date: Optional[datetime.datetime] = None
    completed_at: Optional[datetime.datetime] = None
    reminder_enabled: bool = False
    is_reminded: bool = False
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


class TodoListResponse(BaseModel):
    """待办列表响应模式"""
    code: int = 200
    message: str = "获取成功"
    data: List[TodoItem] = []


class TodoStats(BaseModel):
    """待办统计数据模式"""
    pending_count: int = 0
    completed_count: int = 0
    cancelled_count: int = 0
    total_count: int = 0


class TodoStatsResponse(BaseModel):
    """待办统计响应模式"""
    code: int = 200
    message: str = "获取成功"
    data: TodoStats


class TodoStatusUpdateResponse(BaseModel):
    """待办状态更新响应模式"""
    code: int = 200
    message: str = "状态更新成功"
    data: dict


class ReminderReadResponse(BaseModel):
    """提醒已读响应模式"""
    code: int = 200
    message: str = "标记成功"
    data: dict


class OverdueTodosData(BaseModel):
    """即将逾期待办数据结构"""
    total: int = 0
    page: int = 1
    page_size: int = 10
    todos: List[TodoItem] = []


class OverdueTodosResponse(BaseModel):
    """即将逾期待办响应模式"""
    code: int = 200
    message: str = "查询成功"
    data: OverdueTodosData
