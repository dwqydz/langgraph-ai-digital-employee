"""
会话Token模块CRUD操作
提供基于数据库的Token管理功能
"""
import secrets
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from model import SessionToken


async def create_session_token(
    db: AsyncSession,
    user_id: int,
    ip_address: str = None,
    user_agent: str = None,
    device_info: str = None,
    expires_days: int = 7
) -> SessionToken:
    """
    创建或更新会话Token (单点登录模式)
    
    策略:
    1. 查询该用户是否已有Token记录
    2. 有：更新Token值和过期时间
    3. 没有：创建新记录
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        ip_address: 登录IP
        user_agent: 浏览器信息
        device_info: 设备信息
        expires_days: 有效期(天)
        
    Returns:
        SessionToken: 会话对象
    """
    # 1. 生成新的Token值和过期时间
    token_value = secrets.token_hex(32)
    expires_at = datetime.now() + timedelta(days=expires_days)
    
    # 2. 查询该用户是否已有Token记录
    query = select(SessionToken).where(SessionToken.user_id == user_id)
    result = await db.execute(query)
    existing_session = result.scalar_one_or_none()
    
    if existing_session:
        # 3a. 存在则更新
        existing_session.token = token_value
        existing_session.expires_at = expires_at
        existing_session.ip_address = ip_address
        existing_session.user_agent = user_agent
        existing_session.device_info = device_info
        existing_session.is_active = True
        if hasattr(existing_session, 'last_used_at'):
            existing_session.last_used_at = datetime.now()
        
        await db.commit()
        await db.refresh(existing_session)
        
        return existing_session
    else:
        # 3b. 不存在则创建
        new_session = SessionToken(
            user_id=user_id,
            token=token_value,
            ip_address=ip_address,
            user_agent=user_agent,
            device_info=device_info,
            is_active=True,
            expires_at=expires_at
        )
        
        db.add(new_session)
        await db.commit()
        await db.refresh(new_session)
        
        return new_session


async def get_session_by_token(
    db: AsyncSession,
    token: str
) -> SessionToken | None:
    """
    根据Token查询会话
    
    Args:
        db: 数据库会话
        token: Token值
        
    Returns:
        SessionToken或None
    """
    result = await db.execute(
        select(SessionToken).where(
            SessionToken.token == token,
            SessionToken.is_active == True,
            SessionToken.expires_at > datetime.now()
        )
    )
    return result.scalar_one_or_none()


async def invalidate_session_token(
    db: AsyncSession,
    token: str
) -> bool:
    """
    使Token失效(登出)
    
    Args:
        db: 数据库会话
        token: Token值
        
    Returns:
        bool: 是否成功
    """
    result = await db.execute(
        update(SessionToken)
        .where(SessionToken.token == token)
        .values(is_active=False)
    )
    
    await db.commit()
    return result.rowcount > 0


async def invalidate_all_user_sessions(
    db: AsyncSession,
    user_id: int
) -> int:
    """
    使指定用户的所有会话失效(强制下线)
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        
    Returns:
        int: 影响的行数
    """
    result = await db.execute(
        update(SessionToken)
        .where(SessionToken.user_id == user_id)
        .values(is_active=False)
    )
    
    await db.commit()
    return result.rowcount


async def cleanup_expired_tokens(db: AsyncSession) -> int:
    """
    清理过期的Token(定时任务调用)
    
    Args:
        db: 数据库会话
        
    Returns:
        int: 删除的记录数
    """
    result = await db.execute(
        delete(SessionToken).where(
            SessionToken.expires_at < datetime.now()
        )
    )
    
    await db.commit()
    return result.rowcount


async def get_user_active_sessions(
    db: AsyncSession,
    user_id: int
) -> list[SessionToken]:
    """
    获取用户的活跃会话列表
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        
    Returns:
        活跃会话列表
    """
    result = await db.execute(
        select(SessionToken)
        .where(
            SessionToken.user_id == user_id,
            SessionToken.is_active == True,
            SessionToken.expires_at > datetime.now()
        )
        .order_by(SessionToken.created_at.desc())
    )
    return result.scalars().all()
