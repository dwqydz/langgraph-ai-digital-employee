"""
认证模块Pydantic模式
包含登录、注册的请求和响应模式
"""
from pydantic import BaseModel
from typing import Optional, List
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


class LogoutResponse(BaseModel):
    """登出响应模式"""
    code: int = 200
    message: str = "登出成功"


class SessionInfo(BaseModel):
    """会话信息"""
    id: int
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_info: Optional[str] = None
    created_at: str
    last_used_at: str
    expires_at: str


class SessionListResponse(BaseModel):
    """会话列表响应"""
    code: int = 200
    message: str
    data: List[SessionInfo] = []


class UserInfoDetail(BaseModel):
    """用户详细信息"""
    id: int
    username: str
    email: str = ""
    description: str = ""
    avatar_url: str = ""
    role: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_login_at: Optional[str] = None


class UserInfoResponse(BaseModel):
    """用户信息响应"""
    code: int = 200
    message: str = "获取成功"
    data: UserInfoDetail


class UpdateUserInfoRequest(BaseModel):
    """更新用户信息请求"""
    email: Optional[str] = None
    description: Optional[str] = None


class UpdateUserInfoResponse(BaseModel):
    """更新用户信息响应"""
    code: int = 200
    message: str = "更新成功"
    data: dict


class LogoutAllResponse(BaseModel):
    """登出所有设备响应"""
    code: int = 200
    message: str
