"""
Pydantic模式包
包含所有API请求和响应的数据验证模型

模块说明:
- common_schemas.py: 通用响应模型
- auth_schemas.py: 认证模块的请求/响应模型
- todo_schemas.py: 待办事项模块的请求/响应模型
- meeting_schemas.py: 会议室模块的请求/响应模型
- weather_schemas.py: 天气模块的请求/响应模型
"""

# 导入通用响应模型
from schemas.common_schemas import (
    BaseResponse,
    ApiResponse,
    MessageResponse,
    ErrorResponse,
    ListResponse,
    PageResponse
)

# 导入认证模块模型
from schemas.auth_schemas import (
    LoginRequest,
    RegisterRequest,
    UserInfo,
    TokenData,
    AuthResponse
)

# 导入待办事项模块模型
from schemas.todo_schemas import (
    TodoCreate,
    TodoUpdate,
    TodoItem,
    TodoListResponse,
    TodoStats,
    TodoStatsResponse,
    TodoStatusUpdateResponse,
    ReminderReadResponse
)

# 导入会议室模块模型
from schemas.meeting_schemas import (
    MeetingRoom,
    BookingRequest,
    NLPBookingRequest,
    BookingItem,
    RoomListResponse,
    BookingListResponse,
    BookingData,
    BookingResponse,
    CancelBookingData,
    CancelBookingResponse
)

# 导入天气模块模型
from schemas.weather_schemas import (
    CurrentWeather,
    WeatherForecast,
    WeatherSuggestion,
    CurrentWeatherResponse,
    ForecastResponse,
    SuggestionResponse
)

# 导出所有模型
__all__ = [
    # 通用响应模型
    "BaseResponse",
    "ApiResponse",
    "MessageResponse",
    "ErrorResponse",
    "ListResponse",
    "PageResponse",
    
    # 认证模块
    "LoginRequest",
    "RegisterRequest",
    "UserInfo",
    "TokenData",
    "AuthResponse",
    
    # 待办事项模块
    "TodoCreate",
    "TodoUpdate",
    "TodoItem",
    "TodoListResponse",
    "TodoStats",
    "TodoStatsResponse",
    "TodoStatusUpdateResponse",
    "ReminderReadResponse",
    
    # 会议室模块
    "MeetingRoom",
    "BookingRequest",
    "NLPBookingRequest",
    "BookingItem",
    "RoomListResponse",
    "BookingListResponse",
    "BookingData",
    "BookingResponse",
    "CancelBookingData",
    "CancelBookingResponse",
    
    # 天气模块
    "CurrentWeather",
    "WeatherForecast",
    "WeatherSuggestion",
    "CurrentWeatherResponse",
    "ForecastResponse",
    "SuggestionResponse",
]
