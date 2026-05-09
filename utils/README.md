# 工具函数模块说明

## 📁 目录结构

```
utils/
├── __init__.py              # Python包初始化文件
└── auth_utils.py            # 认证模块工具函数
```

## 📋 工具函数清单

### 🔐 认证工具 (`auth_utils.py`)

#### 密码处理函数

##### `hash_password(password: str) -> str`
**功能**: 使用SHA256算法哈希密码

**参数**:
- `password`: 明文密码 (str)

**返回**: 
- SHA256哈希后的密码字符串 (str)

**示例**:
```python
from utils.auth_utils import hash_password

hashed = hash_password("123456")
# 返回: "8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92"
```

---

##### `verify_password(plain_password: str, hashed_password: str) -> bool`
**功能**: 验证明文密码是否与哈希密码匹配

**参数**:
- `plain_password`: 明文密码 (str)
- `hashed_password`: SHA256哈希后的密码 (str)

**返回**: 
- 密码是否匹配 (bool)

**示例**:
```python
from utils.auth_utils import verify_password

is_valid = verify_password("123456", hashed_password)
# 返回: True 或 False
```

---

#### JWT Token函数

##### `create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str`
**功能**: 创建JWT访问令牌

**参数**:
- `data`: 要编码的数据字典,通常包含用户标识 (dict)
- `expires_delta`: Token过期时间增量,默认为1天 (Optional[timedelta])

**返回**: 
- JWT Token字符串 (str)

**示例**:
```python
from utils.auth_utils import create_access_token
import datetime

token = create_access_token(
    data={"sub": "username"},
    expires_delta=datetime.timedelta(days=1)
)
# 返回: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

##### `decode_access_token(token: str) -> dict`
**功能**: 解码并验证JWT Token

**参数**:
- `token`: JWT Token字符串 (str)

**返回**: 
- 解码后的数据字典 (dict)

**异常**:
- `jwt.ExpiredSignatureError`: Token已过期
- `jwt.InvalidTokenError`: Token无效

**示例**:
```python
from utils.auth_utils import decode_access_token
import jwt

try:
    payload = decode_access_token(token)
    username = payload["sub"]
except jwt.ExpiredSignatureError:
    print("Token已过期")
except jwt.InvalidTokenError:
    print("无效的Token")
```

---

## 🎯 使用方式

### 在路由中导入工具函数

```python
# 认证模块
from utils.auth_utils import hash_password, verify_password, create_access_token

# 在其他需要认证的路由中使用
@router.post("/some-protected-endpoint")
async def protected_endpoint(token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_access_token(token)
        current_user = payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的Token")
    
    # 业务逻辑...
```

---

## 📝 开发规范

### 1. 工具函数设计原则

- **单一职责**: 每个工具函数只负责一个明确的功能
- **无状态**: 工具函数不应依赖外部状态,保持纯函数特性
- **可复用**: 设计通用的工具函数,避免业务逻辑耦合
- **文档完善**: 每个函数都应包含详细的docstring说明

### 2. 命名规范

- 使用小写字母和下划线命名 (snake_case)
- 函数名应清晰表达功能 (如 `hash_password`, `verify_password`)
- 布尔返回值函数以 `is_` 或 `has_` 开头 (如 `is_valid_token`)

### 3. 错误处理

- 使用明确的异常类型
- 提供清晰的错误消息
- 在docstring中说明可能抛出的异常

### 4. 添加新工具函数

1. 根据功能模块在 `utils/` 目录下创建对应的 `.py` 文件
2. 定义工具函数并添加完整的docstring
3. 在 `__init__.py` 中导出常用函数(可选)
4. 在路由文件中通过 `from utils.xxx_utils import ...` 导入使用

示例:
```python
# utils/date_utils.py
import datetime

def format_datetime(dt: datetime.datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """格式化日期时间"""
    return dt.strftime(fmt)

def parse_datetime(date_str: str, fmt: str = "%Y-%m-%d %H:%M:%S") -> datetime.datetime:
    """解析日期时间字符串"""
    return datetime.datetime.strptime(date_str, fmt)
```

---

## ✅ 优势

1. **代码复用**: 避免在多个路由文件中重复实现相同功能
2. **易于维护**: 工具函数集中管理,修改一处全局生效
3. **单元测试**: 工具函数易于单独测试
4. **职责清晰**: 业务逻辑与工具函数分离,代码结构更清晰
5. **可扩展性**: 新增工具函数不影响现有代码

---

## 🔧 配置说明

### JWT配置 (`auth_utils.py`)

```python
SECRET_KEY = "your-secret-key-change-this-in-production"  # ⚠️ 生产环境必须修改
ALGORITHM = "HS256"                                        # JWT签名算法
ACCESS_TOKEN_EXPIRE_DAYS = 1                               # Token有效期(天)
```

**⚠️ 安全提示**:
- 生产环境必须修改 `SECRET_KEY` 为强随机字符串
- 建议使用环境变量管理敏感配置
- 定期轮换密钥

---

## 📊 当前工具函数统计

| 模块 | 文件 | 函数数量 | 功能 |
|------|------|---------|------|
| 认证模块 | auth_utils.py | 4个 | 密码哈希、验证、JWT生成/解码 |

---

## 🚀 下一步建议

可以扩展的工具函数模块:

1. **验证工具** (`validation_utils.py`):
   - 邮箱格式验证
   - 手机号格式验证
   - 用户名规则验证

2. **日期工具** (`date_utils.py`):
   - 日期格式化
   - 时区转换
   - 相对时间计算

3. **文件工具** (`file_utils.py`):
   - 文件上传处理
   - 图片压缩
   - 文件格式验证

4. **加密工具** (`crypto_utils.py`):
   - AES加密/解密
   - RSA密钥管理
   - 数据签名
