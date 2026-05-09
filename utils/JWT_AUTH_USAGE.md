# JWT令牌认证工具使用说明

## 📁 文件位置
`utils/jwt_auth.py`

## 🔧 功能说明

### 1. **配置常量**
```python
SECRET_KEY = "your-secret-key-change-this-in-production"  # JWT密钥
ALGORITHM = "HS256"  # 加密算法
security = HTTPBearer()  # HTTP Bearer Token安全方案
```

### 2. **核心函数**

#### `decode_access_token(token: str) -> dict`
解码JWT Token,返回payload数据

**参数:**
- `token`: JWT Token字符串

**返回:**
- `dict`: 解码后的数据(包含sub、exp等字段)

**异常:**
- `HTTPException 401`: Token已过期或无效

**使用示例:**
```python
from utils.jwt_auth import decode_access_token

try:
    payload = decode_access_token("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    username = payload.get("sub")
except HTTPException as e:
    print(f"Token验证失败: {e.detail}")
```

---

#### `get_current_user_id(credentials) -> int`
从JWT Token中获取当前用户ID的依赖函数

**参数:**
- `credentials`: HTTP Authorization凭证(通过Depends自动注入)

**返回:**
- `int`: 当前用户ID

**异常:**
- `HTTPException 401`: Token无效或用户不存在

**使用示例:**
```python
from fastapi import Depends
from utils.jwt_auth import get_current_user_id

@router.get("/my-data")
async def get_my_data(
    current_user_id: int = Depends(get_current_user_id)
):
    # 直接使用用户ID查询数据
    data = await db.query(Data).filter(Data.user_id == current_user_id).all()
    return data
```

---

#### `get_current_user(credentials) -> User`
从JWT Token中获取当前用户完整信息的依赖函数

**参数:**
- `credentials`: HTTP Authorization凭证(通过Depends自动注入)

**返回:**
- `User`: 当前用户对象(包含username、email、role等所有字段)

**异常:**
- `HTTPException 401`: Token无效或用户不存在
- `HTTPException 403`: 账户已被禁用

**使用示例:**
```python
from fastapi import Depends
from utils.jwt_auth import get_current_user

@router.get("/profile")
async def get_profile(
    current_user: User = Depends(get_current_user)
):
    # 直接使用用户对象
    return {
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role
    }
```

---

## 🚀 在路由中使用

### 方式1: 只需要用户ID(推荐,性能更好)
```python
from fastapi import APIRouter, Depends
from utils.jwt_auth import get_current_user_id

router = APIRouter()

@router.get("/todos")
async def get_todos(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_database)
):
    # 查询当前用户的待办事项
    todos = await todo_crud.get_todos_by_user_id(db, current_user_id)
    return {"data": todos}
```

### 方式2: 需要完整用户信息
```python
from fastapi import APIRouter, Depends
from utils.jwt_auth import get_current_user

router = APIRouter()

@router.get("/profile")
async def get_profile(
    current_user: User = Depends(get_current_user)
):
    # 使用完整的用户对象
    return {
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "created_at": current_user.created_at
    }
```

---

## 🔐 前端调用方式

前端需要在请求头中添加Authorization字段:

```javascript
// 登录成功后保存token
const token = response.data.token;
localStorage.setItem('token', token);

// 后续请求携带token
axios.get('/api/todo/list', {
    headers: {
        'Authorization': `Bearer ${token}`
    }
});
```

---

## ⚠️ 注意事项

1. **SECRET_KEY配置**: 
   - 生产环境必须修改为强随机字符串
   - 建议从环境变量读取: `os.getenv("JWT_SECRET_KEY")`

2. **Token过期时间**:
   - 在`auth_utils.create_access_token()`中设置
   - 默认1天,可根据业务需求调整

3. **依赖注入顺序**:
   ```python
   # ✅ 正确:先注入数据库会话,再注入用户
   async def handler(
       db: AsyncSession = Depends(get_database),
       current_user_id: int = Depends(get_current_user_id)
   ):
       pass
   
   # ❌ 错误:可能导致数据库会话未正确初始化
   async def handler(
       current_user_id: int = Depends(get_current_user_id),
       db: AsyncSession = Depends(get_database)
   ):
       pass
   ```

4. **异常处理**:
   - JWT认证失败会自动返回401状态码
   - 无需在路由中手动捕获异常

---

## 📝 迁移指南

### 之前的写法(硬编码用户ID):
```python
@router.get("/list")
async def get_todo_list(
    db: AsyncSession = Depends(get_database),
    current_user_id: int = 1  # TODO: 从JWT token中获取
):
    todos = await todo_crud.get_todos_by_user_id(db, current_user_id)
    return todos
```

### 现在的写法(使用JWT认证):
```python
from utils.jwt_auth import get_current_user_id

@router.get("/list")
async def get_todo_list(
    db: AsyncSession = Depends(get_database),
    current_user_id: int = Depends(get_current_user_id)
):
    todos = await todo_crud.get_todos_by_user_id(db, current_user_id)
    return todos
```

---

## 🎯 最佳实践

1. **优先使用`get_current_user_id`**: 如果只需要用户ID,不要使用`get_current_user`,减少数据库查询
2. **统一认证方式**: 所有需要登录的接口都应使用JWT认证依赖
3. **公开接口不加认证**: 如登录、注册接口不需要添加认证依赖
4. **测试环境配置**: 开发时可以使用固定的测试token,避免频繁登录
