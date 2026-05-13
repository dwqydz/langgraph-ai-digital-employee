import ssl
import urllib3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import datetime
import logging
from dotenv import load_dotenv

# 禁用SSL验证（开发环境，解决阿里云API证书问题）
# 必须在导入其他模块之前设置
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 加载环境变量(从.env文件读取)
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # 控制台输出
        logging.FileHandler('app.log', encoding='utf-8')  # 文件输出
    ]
)
logger = logging.getLogger(__name__)

# 导入子路由模块
from routers import auth, todo, meeting, weather, agent, meeting_nlp

# 导入中间件
from middleware import RequestLoggingMiddleware, ExceptionHandlingMiddleware, AuditLoggingMiddleware

app = FastAPI(
    title="AI数字员工系统",
    description="智能办公助手API服务 - 支持通义千问LLM驱动",
    version="2.0.0"
)

# 注册中间件（注意：中间件的执行顺序与添加顺序相反）
# 1. 审计日志中间件 - 记录关键操作
app.add_middleware(AuditLoggingMiddleware)

# 2. 请求日志中间件 - 记录所有请求
app.add_middleware(RequestLoggingMiddleware)

# 3. 异常处理中间件 - 全局异常捕获
app.add_middleware(ExceptionHandlingMiddleware)

# 4. CORS中间件 - 跨域支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],  # 明确允许前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]  # 暴露所有响应头
)

# 挂载子路由
app.include_router(auth.router, prefix="/api")
app.include_router(todo.router, prefix="/api")
app.include_router(meeting.router, prefix="/api")
app.include_router(meeting_nlp.router, prefix="/api")  # NLP智能预订/取消
app.include_router(weather.router, prefix="/api")
app.include_router(agent.router, prefix="/api")  # Agent路由

# 健康检查接口
@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok", "timestamp": datetime.datetime.now().isoformat()}

# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "欢迎使用AI数字员工系统API",
        "version": "2.0.0",
        "features": [
            "待办事项管理",
            "会议室预订",
            "天气查询",
            "通义千问LLM驱动",
            "语音输入支持",
            "智能意图识别"
        ],
        "docs": "/docs",
        "redoc": "/redoc"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
