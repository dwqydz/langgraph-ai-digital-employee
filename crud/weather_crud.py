"""
天气模块CRUD操作
包含天气缓存的查询、创建等数据库操作
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import datetime
from model import WeatherCache


async def get_valid_weather_cache(
    db: AsyncSession,
    city: str,
    weather_type: str
) -> WeatherCache | None:
    """
    查询有效的天气缓存
    
    Args:
        db: 数据库会话
        city: 城市名称
        weather_type: 天气类型(current/forecast)
        
    Returns:
        缓存对象或None
    """
    result = await db.execute(
        select(WeatherCache).where(
            WeatherCache.city == city,
            WeatherCache.weather_type == weather_type,
            WeatherCache.is_valid == True,
            WeatherCache.expires_at > datetime.datetime.now()
        )
    )
    return result.scalar_one_or_none()


async def create_weather_cache(
    db: AsyncSession,
    city: str,
    weather_type: str,
    weather_data: dict,
    expires_minutes: int = 30
) -> WeatherCache:
    """
    创建天气缓存
    
    Args:
        db: 数据库会话
        city: 城市名称
        weather_type: 天气类型(current/forecast)
        weather_data: 天气数据
        expires_minutes: 有效期(分钟)
        
    Returns:
        新创建的缓存对象
    """
    new_cache = WeatherCache(
        city=city,
        weather_type=weather_type,
        weather_data=weather_data,
        expires_at=datetime.datetime.now() + datetime.timedelta(minutes=expires_minutes),
        is_valid=True
    )
    
    db.add(new_cache)
    await db.commit()
    
    return new_cache
