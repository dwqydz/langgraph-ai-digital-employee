"""
基于数据库的Session Token认证工具
替代JWT,使用数据库存储和验证Token
"""
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# 导入配置和模型
from config.db_config import get_database
from model import User, SessionToken
from crud import session_crud


async def get_current_user_from_session(
    request: Request,
    db: AsyncSession = Depends(get_database)
) -> User:
    """
    从数据库会话中获取当前用户
    
    流程:
    1. 从请求头或Cookie获取Token
    2. 查询数据库验证Token有效性
    3. 检查是否过期、是否被禁用
    4. 更新最后使用时间
    5. 返回用户对象
    
    Args:
        request: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        User: 当前用户对象
        
    Raises:
        HTTPException: Token无效、过期或用户不存在时抛出401
    """
    # 1. 从请求头获取Token
    authorization = request.headers.get("Authorization")
    
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 提取Token(支持"Bearer xxx"格式)
    if authorization.startswith("Bearer "):
        token = authorization[7:]  # 去掉"Bearer "前缀
    else:
        token = authorization
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证格式",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 2. 查询数据库验证Token
    session = await session_crud.get_session_by_token(db, token)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token无效或已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. 查询用户信息
    result = await db.execute(select(User).where(User.id == session.user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 4. 检查用户是否激活
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被禁用",
        )
    
    # 5. 更新最后使用时间(异步,不阻塞响应)
    session.last_used_at = None  # SQLAlchemy会自动更新为当前时间
    
    return user


async def get_current_user_id_from_session(
    request: Request,
    db: AsyncSession = Depends(get_database)
) -> int:
    """
    从数据库会话中获取当前用户ID(简化版)
    
    Args:
        request: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        int: 当前用户ID
    """
    user = await get_current_user_from_session(request, db)
    return user.id
