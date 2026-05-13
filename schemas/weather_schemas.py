"""
天气模块Pydantic模式
包含天气查询的请求和响应模式
"""
from pydantic import BaseModel
from typing import Optional, List


class CurrentWeather(BaseModel):
    """当前天气数据模式"""
    city: str
    temperature: float
    weather: str
    humidity: int
    wind_speed: float
    description: str
    timestamp: str

    class Config:
        from_attributes = True


class WeatherForecast(BaseModel):
    """天气预报数据模式"""
    date: str
    temperature_high: float
    temperature_low: float
    weather: str
    humidity: Optional[int] = None
    wind_speed: Optional[float] = None

    class Config:
        from_attributes = True


class WeatherSuggestion(BaseModel):
    """天气建议数据模式"""
    suggestions: List[str] = []
    clothing: str = "根据温度选择合适的衣物"
    activity: str = "适合户外活动"
    travel: str = "出行愉快"

    class Config:
        from_attributes = True


class CurrentWeatherResponse(BaseModel):
    """当前天气响应模式"""
    code: int = 200
    message: str = "获取成功"
    data: Optional[CurrentWeather] = None


class ForecastResponse(BaseModel):
    """天气预报响应模式"""
    code: int = 200
    message: str = "获取成功"
    data: List[WeatherForecast] = []


class SuggestionResponse(BaseModel):
    """天气建议响应模式"""
    code: int = 200
    message: str = "获取成功"
    data: Optional[WeatherSuggestion] = None


class WeatherSuggestionDetail(BaseModel):
    """天气建议详情"""
    daily: str = "天气适宜"
    meeting: str = "无特殊建议"


class AllWeatherData(BaseModel):
    """完整天气数据"""
    city: str
    date: str
    current: dict = {}
    forecast: list = []
    hourly: list = []
    suggestion: Optional[WeatherSuggestionDetail] = None


class AllWeatherResponse(BaseModel):
    """完整天气响应"""
    code: int = 200
    message: str = "获取成功"
    data: Optional[AllWeatherData] = None
