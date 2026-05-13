from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
import datetime

# 导入Pydantic模式
from schemas.todo_schemas import (
    TodoCreate, TodoUpdate, TodoItem, 
    TodoListResponse, TodoStats, TodoStatsResponse,
    TodoStatusUpdateResponse, ReminderReadResponse, OverdueTodosResponse
)

# 导入数据库配置
from config.db_config import get_database

# 导入CRUD操作
from crud import todo_crud

# 导入Session认证
from utils.session_auth import get_current_user_id_from_session

# 导入数据转换工具
from utils.data_converter import convert_to_todo_items

router = APIRouter(
    prefix="/todo",
    tags=["待办事项模块"]
)


@router.post("/create", response_model=TodoItem)
async def create_todo(
    todo_data: TodoCreate,
    db: AsyncSession = Depends(get_database),
    current_user_id: int = Depends(get_current_user_id_from_session)
):
    """创建新的待办事项"""
    # 调用CRUD创建待办
    new_todo = await todo_crud.create_todo(
        db=db,
        user_id=current_user_id,
        title=todo_data.title,
        description=todo_data.description,
        due_date=todo_data.due_date,
        priority=todo_data.priority,
        category=todo_data.category,
        reminder_enabled=todo_data.reminder_enabled
    )
    
    # 返回创建的待办事项
    return TodoItem(
        id=new_todo.id,
        title=new_todo.title,
        description=new_todo.description,
        status=new_todo.status,
        priority=new_todo.priority,
        category=new_todo.category,
        due_date=new_todo.due_date,
        completed_at=new_todo.completed_at,
        reminder_enabled=new_todo.reminder_enabled,
        is_reminded=new_todo.is_reminded,
        created_at=new_todo.created_at,
        updated_at=new_todo.updated_at
    )


@router.get("/list", response_model=TodoListResponse)
async def get_todo_list(
    req: Request,
    db: AsyncSession = Depends(get_database),
    current_user_id: int = Depends(get_current_user_id_from_session),
    status: str = None,
    category: str = None,
    time_status: str = None,
    tag: str = None,
    page: int = 1,
    page_size: int = 10
):
    """获取待办列表 - 支持分页和多条件筛选"""
    # 查询用户的待办事项
    todos, total = await todo_crud.get_todos_by_user_id(
        db, current_user_id, status, category, time_status, tag, page, page_size
    )
    
    # 使用工具函数转换
    todo_items = convert_to_todo_items(todos)
    
    return TodoListResponse(
        code=200,
        message=f"获取成功，共{total}条",
        data=todo_items
    )


# 临时调试接口 - 无需认证,使用默认用户ID=1
@router.get("/list-debug")
async def get_todo_list_debug(
    db: AsyncSession = Depends(get_database)
):
    """调试接口: 使用固定用户ID=1,无需Token"""
    # 使用固定用户ID
    debug_user_id = 1
    
    # 查询待办事项
    todos = await todo_crud.get_todos_by_user_id(db, debug_user_id)
    
    # 使用工具函数转换
    todo_items = convert_to_todo_items(todos)
    
    return TodoListResponse(
        code=200,
        message=f"调试模式 - 用户ID={debug_user_id}, 共{len(todo_items)}条待办",
        data=todo_items
    )


# 临时调试接口 - 无需认证,查看所有待办
@router.get("/debug/list-all")
async def debug_list_all_todos(db: AsyncSession = Depends(get_database)):
    """调试接口: 查看所有用户的待办(无需认证)"""
    from sqlalchemy import select
    from model import Todo, User
    
    result = await db.execute(
        select(Todo, User.username)
        .join(User, Todo.user_id == User.id)
        .order_by(Todo.created_at.desc())
    )
    
    rows = result.all()
    
    todos_data = []
    for todo, username in rows:
        todos_data.append({
            "id": todo.id,
            "user": username,
            "title": todo.title,
            "status": todo.status,
            "priority": todo.priority,
            "created_at": todo.created_at.isoformat() if todo.created_at else None
        })
    
    return {
        "code": 200,
        "message": f"共找到 {len(todos_data)} 条待办",
        "data": todos_data
    }


@router.put("/{todo_id}/status", response_model=TodoStatusUpdateResponse)
async def update_todo_status(
    todo_id: int,
    status_update: TodoUpdate,
    db: AsyncSession = Depends(get_database),
    current_user_id: int = Depends(get_current_user_id_from_session)
):
    """更新任务状态"""
    # 查询待办事项
    todo = await todo_crud.get_todo_by_id_and_user(db, todo_id, current_user_id)
    
    if not todo:
        raise HTTPException(status_code=404, detail="待办事项不存在")
    
    # 更新状态
    updated_todo = await todo_crud.update_todo_status(db, todo, status_update.status)
    
    return TodoStatusUpdateResponse(
        code=200,
        message="状态更新成功",
        data={
            "id": updated_todo.id,
            "status": updated_todo.status,
            "completed_at": updated_todo.completed_at
        }
    )


@router.get("/stats", response_model=TodoStatsResponse)
async def get_todo_stats(
    db: AsyncSession = Depends(get_database),
    current_user_id: int = Depends(get_current_user_id_from_session)
):
    """获取统计数据"""
    # 获取统计数据
    stats_data = await todo_crud.get_todo_stats(db, current_user_id)
    
    stats = TodoStats(
        pending_count=stats_data["pending_count"],
        completed_count=stats_data["completed_count"],
        cancelled_count=stats_data["cancelled_count"],
        total_count=stats_data["total_count"]
    )
    
    return TodoStatsResponse(
        code=200,
        message="获取成功",
        data=stats
    )


@router.put("/reminder/tasks/{task_id}/read", response_model=ReminderReadResponse)
async def mark_reminder_read(
    task_id: int,
    db: AsyncSession = Depends(get_database),
    current_user_id: int = Depends(get_current_user_id_from_session)
):
    """标记提醒已读"""
    # 查询待办事项
    todo = await todo_crud.get_todo_by_id_and_user(db, task_id, current_user_id)
    
    if not todo:
        raise HTTPException(status_code=404, detail="待办事项不存在")
    
    # 标记为已提醒
    updated_todo = await todo_crud.mark_reminder_read(db, todo)
    
    return ReminderReadResponse(
        code=200,
        message="标记成功",
        data={
            "id": updated_todo.id,
            "is_reminded": updated_todo.is_reminded
        }
    )


@router.get("/reminder/overdue-soon")
async def get_overdue_todos_soon(
    req: Request,
    db: AsyncSession = Depends(get_database),
    current_user_id: int = Depends(get_current_user_id_from_session),
    hours: float = 1.0,
    page: int = 1,
    page_size: int = 10
):
    """获取即将逾期的待办事项（距离截止时间少于指定小时数）"""
    todos, total = await todo_crud.get_overdue_todos_soon(
        db, current_user_id, hours, page, page_size
    )
    
    # 使用工具函数转换
    todo_items = convert_to_todo_items(todos)
    
    from schemas.todo_schemas import OverdueTodosData
    return OverdueTodosResponse(
        code=200,
        message=f"查询成功，共{total}条即将逾期",
        data=OverdueTodosData(
            total=total,
            page=page,
            page_size=page_size,
            todos=todo_items
        )
    )
