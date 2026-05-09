from fastapi import APIRouter, HTTPException, Depends, Request
import datetime

# 导入Pydantic模式
from schemas.auth_schemas import LoginRequest, RegisterRequest, UserInfo, TokenData, AuthResponse

# 导入工具函数
from utils.auth_utils import hash_password, verify_password

# 导入数据库配置
from config.db_config import get_database

# 导入CRUD操作
from crud import auth_crud, session_crud

router = APIRouter(
    prefix="/auth",
    tags=["认证模块"]
)

# ACCESS_TOKEN_EXPIRE_DAYS常量(用于文档说明)
ACCESS_TOKEN_EXPIRE_DAYS = 7  # Session Token默认7天有效期


@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    req: Request,
    db = Depends(get_database)
):
    """用户登录 - 使用基于数据库的Session Token"""
    # 查询用户
    user = await auth_crud.get_user_by_username(db, request.username)
    
    # 检查用户是否存在
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # 验证密码
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # 检查用户是否激活
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账户已被禁用")
    
    # 更新最后登录时间
    await auth_crud.update_user_last_login(db, user)
    
    # 获取请求信息
    ip_address = req.client.host if req.client else None
    user_agent = req.headers.get("User-Agent", "")
    
    # 创建Session Token(存储到数据库)
    session = await session_crud.create_session_token(
        db=db,
        user_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent,
        expires_days=ACCESS_TOKEN_EXPIRE_DAYS
    )
    
    # 构建响应数据
    user_info = UserInfo(
        username=user.username,
        email=user.email,
        role=user.role,
        loginTime=datetime.datetime.now()
    )
    
    token_data = TokenData(
        token=session.token,  # 返回数据库生成的Token
        userInfo=user_info
    )
    
    return AuthResponse(
        code=200,
        message="登录成功",
        data=token_data
    )


@router.post("/logout")
async def logout(
    request: Request,
    db = Depends(get_database)
):
    """用户登出 - 使Session Token失效"""
    authorization = request.headers.get("Authorization")
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=400, detail="无效的Token")
    
    token = authorization[7:]
    
    # 使Token失效
    success = await session_crud.invalidate_session_token(db, token)
    
    if not success:
        raise HTTPException(status_code=400, detail="Token不存在")
    
    return {
        "code": 200,
        "message": "登出成功"
    }


@router.post("/register", response_model=AuthResponse)
async def register(
    request: RegisterRequest,
    req: Request,
    db = Depends(get_database)
):
    """用户注册 - 如果用户已存在则直接登录,否则创建新用户并自动登录"""
    # 验证用户名格式
    if len(request.username) < 3 or len(request.username) > 20:
        raise HTTPException(status_code=400, detail="用户名长度必须在3-20个字符之间")
    
    # 验证密码格式
    if len(request.password) < 6 or len(request.password) > 20:
        raise HTTPException(status_code=400, detail="密码长度必须在6-20个字符之间")
    
    # 检查用户是否已存在
    existing_user = await auth_crud.get_user_by_username(db, request.username)
    
    if existing_user:
        # 用户已存在,直接返回登录信息
        ip_address = req.client.host if req.client else None
        user_agent = req.headers.get("User-Agent", "")
        
        session = await session_crud.create_session_token(
            db=db,
            user_id=existing_user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_days=ACCESS_TOKEN_EXPIRE_DAYS
        )
        
        user_info = UserInfo(
            username=existing_user.username,
            email=existing_user.email,
            role=existing_user.role,
            loginTime=datetime.datetime.now()
        )
        
        token_data = TokenData(
            token=session.token,
            userInfo=user_info
        )
        
        return AuthResponse(
            code=200,
            message="用户已存在,自动登录",
            data=token_data
        )
    
    # 创建新用户
    hashed_password = hash_password(request.password)
    
    new_user = await auth_crud.create_user(
        db=db,
        username=request.username,
        password_hash=hashed_password
        # email字段暂时不传，因为create_user不支持
    )
    
    # 自动登录
    ip_address = req.client.host if req.client else None
    user_agent = req.headers.get("User-Agent", "")
    
    session = await session_crud.create_session_token(
        db=db,
        user_id=new_user.id,
        ip_address=ip_address,
        user_agent=user_agent,
        expires_days=ACCESS_TOKEN_EXPIRE_DAYS
    )
    
    user_info = UserInfo(
        username=new_user.username,
        email=new_user.email,
        role=new_user.role,
        loginTime=datetime.datetime.now()
    )
    
    token_data = TokenData(
        token=session.token,
        userInfo=user_info
    )
    
    return AuthResponse(
        code=200,
        message="注册成功,已自动登录",
        data=token_data
    )


@router.get("/sessions/my")
async def get_my_sessions(
    db = Depends(get_database),
    current_user_id: int = Depends(lambda req, db: __import__('utils.session_auth', fromlist=['get_current_user_id_from_session']).get_current_user_id_from_session(req, db))
):
    """获取当前用户的所有活跃会话"""
    sessions = await session_crud.get_user_active_sessions(db, current_user_id)
    
    return {
        "code": 200,
        "message": f"共{len(sessions)}个活跃会话",
        "data": [
            {
                "id": s.id,
                "ip_address": s.ip_address,
                "user_agent": s.user_agent[:50] + "..." if s.user_agent and len(s.user_agent) > 50 else s.user_agent,
                "device_info": s.device_info,
                "created_at": s.created_at.isoformat(),
                "last_used_at": s.last_used_at.isoformat(),
                "expires_at": s.expires_at.isoformat()
            }
            for s in sessions
        ]
    }


@router.post("/sessions/logout-all")
async def logout_all_sessions(
    db = Depends(get_database),
    current_user_id: int = Depends(lambda req, db: __import__('utils.session_auth', fromlist=['get_current_user_id_from_session']).get_current_user_id_from_session(req, db))
):
    """登出所有设备(强制下线)"""
    count = await session_crud.invalidate_all_user_sessions(db, current_user_id)
    
    return {
        "code": 200,
        "message": f"已登出{count}个设备"
    }
