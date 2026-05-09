"""
JWT令牌认证工具
提供JWT Token验证、用户信息提取等功能
"""
import jwt
import os
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# 导入配置和模型
from config.db_config import get_database
from model import User


# JWT配置 - 从环境变量读取,如果未设置则使用默认值(仅用于开发)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"

# HTTP Bearer Token安全方案
security = HTTPBearer()


def decode_access_token(token: str) -> dict:
    """
    解码JWT Token
    
    Args:
        token: JWT Token字符串
        
    Returns:
        dict: 解码后的数据
        
    Raises:
        HTTPException: Token无效或已过期时抛出异常
    """
    try:
        decoded_data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return decoded_data
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token已过期,请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的Token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> int:
    """
    从JWT Token中获取当前用户ID的依赖函数
    
    Args:
        credentials: HTTP Authorization凭证
        
    Returns:
        int: 当前用户ID
        
    Raises:
        HTTPException: Token无效或用户不存在时抛出异常
    """
    # 获取token
    token = credentials.credentials
    
    # 解码token
    payload = decode_access_token(token)
    username: str = payload.get("sub")
    
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证信息",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 查询用户
    db: AsyncSession = await get_database().__anext__()
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user.id


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    从JWT Token中获取当前用户完整信息的依赖函数
    
    Args:
        credentials: HTTP Authorization凭证
        
    Returns:
        User: 当前用户对象
        
    Raises:
        HTTPException: Token无效或用户不存在时抛出异常
    """
    # 获取token
    token = credentials.credentials
    
    # 解码token
    payload = decode_access_token(token)
    username: str = payload.get("sub")
    
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证信息",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 查询用户
    db: AsyncSession = await get_database().__anext__()
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 检查用户是否激活
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被禁用",
        )
    
    return user
