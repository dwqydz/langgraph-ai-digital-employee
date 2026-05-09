"""
认证模块工具函数
包含密码加密、验证、JWT Token生成等功能
"""
import hashlib
import jwt
import datetime
import os
from typing import Optional


# JWT配置 - 从环境变量读取,如果未设置则使用默认值(仅用于开发)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 1


def hash_password(password: str) -> str:
    """
    哈希密码
    
    Args:
        password: 明文密码
        
    Returns:
        str: SHA256哈希后的密码
    """
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    
    Args:
        plain_password: 明文密码
        hashed_password: 哈希后的密码
        
    Returns:
        bool: 密码是否匹配
    """
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password


def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    """
    创建JWT Token
    
    Args:
        data: 要编码的数据字典
        expires_delta: Token过期时间增量,默认为1天
        
    Returns:
        str: JWT Token字符串
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    解码JWT Token
    
    Args:
        token: JWT Token字符串
        
    Returns:
        dict: 解码后的数据
        
    Raises:
        jwt.ExpiredSignatureError: Token已过期
        jwt.InvalidTokenError: Token无效
    """
    try:
        decoded_data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return decoded_data
    except jwt.ExpiredSignatureError:
        raise jwt.ExpiredSignatureError("Token已过期")
    except jwt.InvalidTokenError:
        raise jwt.InvalidTokenError("无效的Token")