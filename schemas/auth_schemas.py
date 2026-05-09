"""
认证模块Pydantic模式
包含登录、注册的请求和响应模式
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    """登录请求模式"""
    username: str
    password: str


class RegisterRequest(BaseModel):
    """注册请求模式"""
    username: str
    password: str
    email: Optional[str] = None  # 邮箱为可选字段


class UserInfo(BaseModel):
    """用户信息模式"""
    username: str
    email: Optional[str] = None
    role: str = "user"
    loginTime: Optional[datetime] = None


class TokenData(BaseModel):
    """Token数据模式"""
    token: str
    userInfo: UserInfo


class AuthResponse(BaseModel):
    """认证响应模式"""
    code: int = 200
    message: str
    data: Optional[TokenData] = None
