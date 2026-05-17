from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
import os

# 从环境变量读取数据库URL，支持本地和云端部署
ASYNC_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+aiomysql://root:Hh261819.@localhost:3306/aiproject?charset=utf8"  # 默认本地MySQL
)

# 根据数据库类型判断是否使用连接池参数
is_sqlite = "sqlite" in ASYNC_DATABASE_URL.lower()

# 创建异步数据库引擎
if is_sqlite:
    # SQLite不支持连接池参数
    async_engine = create_async_engine(
        ASYNC_DATABASE_URL,
        echo=False  # 生产环境关闭SQL日志
    )
else:
    # MySQL/PostgreSQL等支持连接池
    async_engine = create_async_engine(
        ASYNC_DATABASE_URL,
        echo=False,  # 生产环境关闭SQL日志
        pool_size=20,
        max_overflow=10
    )

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 创建异步ORM基类
class Base(DeclarativeBase):
    """异步ORM基类"""
    pass

# 创建依赖项，用于获取数据库会话
async def get_database():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
