"""
待办事项模块CRUD操作
包含待办事项的查询、更新等数据库操作
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, and_, or_
import datetime
import logging
from model import Todo

# 配置日志
logger = logging.getLogger(__name__)


def _calculate_time_status(due_date, status):
    """
    根据截止时间和状态计算时间状态
    
    Args:
        due_date: 截止时间
        status: 当前状态
        
    Returns:
        时间状态字符串
    """
    if status == "completed":
        return "completed"
    
    if not due_date:
        return "ongoing"
    
    now = datetime.datetime.now()
    hours_diff = (due_date - now).total_seconds() / 3600
    
    if hours_diff < 0:
        return "overdue"
    elif hours_diff <= 1:
        return "upcoming"
    else:
        return "ongoing"


async def create_todo(
    db: AsyncSession,
    user_id: int,
    title: str,
    description: str = None,
    due_date: datetime.datetime = None,
    priority: str = "medium",
    category: str = None,
    tags: str = None,
    reminder_enabled: bool = False
) -> Todo:
    """
    创建新的待办事项
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        title: 待办标题
        description: 待办描述
        due_date: 截止时间
        priority: 优先级(low/medium/high/urgent)
        category: 业务分类(work/study/admin/other)
        tags: 智能标签，逗号分隔
        reminder_enabled: 是否启用提醒
        
    Returns:
        新创建的待办事项对象
    """
    try:
        # 自动计算时间状态
        time_status = _calculate_time_status(due_date, "pending")
        
        new_todo = Todo(
            user_id=user_id,
            title=title,
            description=description,
            status="pending",
            priority=priority,
            category=category,
            tags=tags,
            due_date=due_date,
            time_status=time_status,
            reminder_enabled=reminder_enabled,
            is_reminded=False
        )
        
        db.add(new_todo)
        await db.commit()
        await db.refresh(new_todo)
        
        logger.info(f"[TODO_CREATE] user_id={user_id}, todo_id={new_todo.id}, title={title}")
        return new_todo
        
    except Exception as e:
        await db.rollback()
        logger.error(f"[TODO_CREATE_ERROR] user_id={user_id}, title={title}, error={str(e)}", exc_info=True)
        raise


async def get_todos_by_user_id(
    db: AsyncSession,
    user_id: int,
    status: str = None,
    category: str = None,
    time_status: str = None,
    tag: str = None,
    page: int = 1,
    page_size: int = 10
) -> tuple[list[Todo], int]:
    """
    分页查询用户的待办事项，支持多条件筛选
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        status: 状态筛选(pending/completed/cancelled)
        category: 业务分类筛选(work/study/admin/other)
        time_status: 时间状态筛选(ongoing/overdue/completed/upcoming)
        tag: 标签筛选
        page: 页码（从1开始）
        page_size: 每页数量
        
    Returns:
        (待办事项列表, 总数)
    """
    # 构建查询条件
    conditions = [Todo.user_id == user_id]
    
    if status:
        conditions.append(Todo.status == status)
    
    if category:
        conditions.append(Todo.category == category)
    
    if time_status:
        conditions.append(Todo.time_status == time_status)
    
    if tag:
        conditions.append(Todo.tags.like(f"%{tag}%"))
    
    # 查询总数
    count_result = await db.execute(
        select(func.count(Todo.id)).where(and_(*conditions))
    )
    total = count_result.scalar()
    
    # 分页查询 - 优先显示未完成的任务，再按截止时间升序排列
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Todo)
        .where(and_(*conditions))
        .order_by(
            case(
                (Todo.status == "pending", 0),
                (Todo.status == "cancelled", 1),
                else_=2
            ),  # pending(0) > cancelled(1) > completed(2)
            Todo.due_date.asc(),  # 有截止时间的排前面（NULL会排在最后）
            Todo.created_at.desc()  # 没有截止时间的，按创建时间倒序
        )
        .offset(offset)
        .limit(page_size)
    )
    todos = result.scalars().all()
    
    return todos, total


async def get_overdue_todos_soon(
    db: AsyncSession,
    user_id: int,
    hours_threshold: float = 1.0,
    page: int = 1,
    page_size: int = 10
) -> tuple[list[Todo], int]:
    """
    查询即将逾期（距离截止时间少于指定小时数）的待办事项
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        hours_threshold: 小时阈值，默认1小时
        page: 页码
        page_size: 每页数量
        
    Returns:
        (待办事项列表, 总数)
    """
    now = datetime.datetime.now()
    threshold_time = now + datetime.timedelta(hours=hours_threshold)
    
    conditions = [
        Todo.user_id == user_id,
        Todo.status == "pending",
        Todo.due_date != None,
        Todo.due_date > now,
        Todo.due_date <= threshold_time
    ]
    
    # 查询总数
    count_result = await db.execute(
        select(func.count(Todo.id)).where(and_(*conditions))
    )
    total = count_result.scalar()
    
    # 分页查询
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Todo)
        .where(and_(*conditions))
        .order_by(Todo.due_date.asc())
        .offset(offset)
        .limit(page_size)
    )
    todos = result.scalars().all()
    
    return todos, total


async def get_todo_by_id_and_user(
    db: AsyncSession,
    todo_id: int,
    user_id: int
) -> Todo | None:
    """
    根据ID和用户ID查询待办事项
    
    Args:
        db: 数据库会话
        todo_id: 待办事项ID
        user_id: 用户ID
        
    Returns:
        待办事项对象或None
    """
    result = await db.execute(
        select(Todo).where(
            Todo.id == todo_id,
            Todo.user_id == user_id
        )
    )
    return result.scalar_one_or_none()


async def update_todo_status(
    db: AsyncSession,
    todo: Todo,
    status: str
) -> Todo:
    """
    更新待办事项状态
    
    Args:
        db: 数据库会话
        todo: 待办事项对象
        status: 新状态
        
    Returns:
        更新后的待办事项对象
    """
    todo.status = status
    
    # 如果状态变为completed,记录完成时间
    if status == "completed" and not todo.completed_at:
        todo.completed_at = datetime.datetime.now()
    
    # 如果状态从 completed变为其他,清除完成时间
    elif status != "completed" and todo.completed_at:
        todo.completed_at = None
    
    # 更新时间状态
    todo.time_status = _calculate_time_status(todo.due_date, status)
    
    await db.commit()
    await db.refresh(todo)
    
    return todo


async def update_todo_info(
    db: AsyncSession,
    todo: Todo,
    title: str = None,
    description: str = None,
    priority: str = None,
    category: str = None,
    tags: str = None,
    due_date: datetime.datetime = None
) -> Todo:
    """
    更新待办事项信息
    
    Args:
        db: 数据库会话
        todo: 待办事项对象
        title: 新标题
        description: 新描述
        priority: 新优先级
        category: 新分类
        tags: 新标签
        due_date: 新截止时间
        
    Returns:
        更新后的待办事项对象
    """
    if title is not None:
        todo.title = title
    if description is not None:
        todo.description = description
    if priority is not None:
        todo.priority = priority
    if category is not None:
        todo.category = category
    if tags is not None:
        todo.tags = tags
    if due_date is not None:
        todo.due_date = due_date
        todo.time_status = _calculate_time_status(due_date, todo.status)
    
    await db.commit()
    await db.refresh(todo)
    
    return todo


async def get_todo_stats(
    db: AsyncSession,
    user_id: int
) -> dict:
    """
    获取用户待办事项统计数据
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        
    Returns:
        包含各状态数量的字典
    """
    result = await db.execute(
        select(
            func.count(case((Todo.status == "pending", 1))).label("pending_count"),
            func.count(case((Todo.status == "completed", 1))).label("completed_count"),
            func.count(case((Todo.status == "cancelled", 1))).label("cancelled_count"),
            func.count(case((Todo.time_status == "overdue", 1))).label("overdue_count"),
            func.count(case((Todo.time_status == "upcoming", 1))).label("upcoming_count"),
            func.count(Todo.id).label("total_count")
        ).where(Todo.user_id == user_id)
    )
    
    row = result.first()
    
    return {
        "pending_count": row.pending_count or 0,
        "completed_count": row.completed_count or 0,
        "cancelled_count": row.cancelled_count or 0,
        "overdue_count": row.overdue_count or 0,
        "upcoming_count": row.upcoming_count or 0,
        "total_count": row.total_count or 0
    }


async def mark_reminder_read(
    db: AsyncSession,
    todo: Todo
) -> Todo:
    """
    标记提醒已读
    
    Args:
        db: 数据库会话
        todo: 待办事项对象
        
    Returns:
        更新后的待办事项对象
    """
    todo.is_reminded = True
    await db.commit()
    
    return todo
