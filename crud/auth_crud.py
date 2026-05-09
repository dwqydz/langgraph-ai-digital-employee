"""
认证模块CRUD操作
包含用户查询、创建等数据库操作
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import datetime
from model import User


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    """
    根据用户名查询用户
    
    Args:
        db: 数据库会话
        username: 用户名
        
    Returns:
        User对象或None
    """
    result = await db.execute(
        select(User).where(User.username == username)
    )
    return result.scalar_one_or_none()


async def update_user_last_login(db: AsyncSession, user: User) -> None:
    """
    更新用户最后登录时间
    
    Args:
        db: 数据库会话
        user: 用户对象
    """
    user.last_login_at = datetime.datetime.now()
    await db.commit()


async def create_user(
    db: AsyncSession,
    username: str,
    password_hash: str,
    role: str = "user",
    is_active: bool = True
) -> User:
    """
    创建新用户
    
    Args:
        db: 数据库会话
        username: 用户名
        password_hash: 哈希后的密码
        role: 用户角色
        is_active: 是否激活
        
    Returns:
        新创建的用户对象
    """
    new_user = User(
        username=username,
        password_hash=password_hash,
        role=role,
        is_active=is_active
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user
