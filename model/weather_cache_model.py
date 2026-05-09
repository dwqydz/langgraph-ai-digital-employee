"""
天气缓存模型
对应数据库中的weather_cache表
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean
from sqlalchemy.sql import func
from config.db_config import Base


class WeatherCache(Base):
    """天气缓存模型 - 缓存天气数据,减少API调用次数"""
    
    __tablename__ = "weather_cache"
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment="缓存ID")
    
    # 缓存信息
    city = Column(String(100), nullable=False, index=True, comment="城市名称")
    weather_type = Column(String(20), nullable=False, index=True, comment="类型: current-当前天气, forecast-预报, suggestion-建议")
    weather_data = Column(JSON, nullable=False, comment="天气数据JSON")
    
    # 有效期
    cached_at = Column(DateTime, server_default=func.now(), comment="缓存时间")
    expires_at = Column(DateTime, nullable=False, index=True, comment="过期时间")
    is_valid = Column(Boolean, default=True, index=True, comment="是否有效")
    
    def __repr__(self):
        return f"<WeatherCache(city='{self.city}', type='{self.weather_type}')>"
