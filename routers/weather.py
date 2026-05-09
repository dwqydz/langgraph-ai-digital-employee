from fastapi import APIRouter, HTTPException, Query, Depends
import datetime
import httpx

# 导入Pydantic模式
from schemas.weather_schemas import (
    CurrentWeather, WeatherForecast, WeatherSuggestion,
    CurrentWeatherResponse, ForecastResponse, SuggestionResponse
)

# 导入数据库配置
from config.db_config import get_database

# 导入CRUD操作
from crud import weather_crud

# 导入MCP天气工具
from agent.mcp_weather_tool import get_mcp_weather_tool

router = APIRouter(
    prefix="/weather",
    tags=["天气模块"]
)

# 天气API配置(示例使用OpenWeatherMap,实际可替换为其他API)
WEATHER_API_KEY = "your_api_key_here"  # TODO: 从配置文件读取
WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_API_URL = "https://api.openweathermap.org/data/2.5/forecast"


async def fetch_weather_from_api(city: str):
    """从外部API获取天气数据(模拟实现)"""
    # TODO: 实际使用时需要调用真实的天气API
    # 这里返回模拟数据
    return {
        "city": city,
        "temperature": 25.5,
        "weather": "晴",
        "humidity": 60,
        "wind_speed": 3.2,
        "description": "晴朗舒适",
        "timestamp": datetime.datetime.now().isoformat()
    }


async def fetch_forecast_from_api(city: str, days: int = 3):
    """从外部API获取天气预报数据(模拟实现)"""
    # TODO: 实际使用时需要调用真实的天气API
    forecasts = []
    for i in range(days):
        date = datetime.datetime.now() + datetime.timedelta(days=i)
        forecasts.append({
            "date": date.strftime("%Y-%m-%d"),
            "temperature_high": 28 + i,
            "temperature_low": 18 + i,
            "weather": "晴" if i % 2 == 0 else "多云",
            "wind_speed": 3.0 + i * 0.5
        })
    return forecasts


def generate_weather_suggestion(weather_data: dict) -> WeatherSuggestion:
    """根据天气数据生成建议"""
    temperature = weather_data.get("temperature", 25)
    weather = weather_data.get("weather", "晴")
    
    suggestions = []
    
    # 温度建议
    if temperature < 10:
        suggestions.append("天气较冷,建议穿厚外套")
    elif temperature < 20:
        suggestions.append("温度适中,建议穿长袖")
    elif temperature < 30:
        suggestions.append("温暖舒适,适合户外活动")
    else:
        suggestions.append("天气炎热,注意防暑降温")
    
    # 天气状况建议
    if "雨" in weather:
        suggestions.append("有降雨,记得带伞")
    if "雪" in weather:
        suggestions.append("有降雪,注意防滑")
    if "风" in weather or "大风" in weather:
        suggestions.append("风力较大,注意安全")
    
    # 确定活动建议
    activity = "室内活动" if "雨" in weather or "雪" in weather else "户外活动"
    travel = "出行请注意安全" if "雨" in weather or "雪" in weather else "出行愉快"
    
    return WeatherSuggestion(
        suggestions=suggestions,
        clothing="根据温度选择合适的衣物",
        activity=f"适合{activity}",
        travel=travel
    )


# 注意：以下旧接口已废弃，统一使用 /weather/all 接口
# - /weather/current → 已废弃
# - /weather/forecast → 已废弃
# - /weather/suggestion → 已废弃
# - /weather/hourly → 已废弃
#
# 原因：前端布局固定为三个区域（左侧指定日期、右侧7天预报、下方24小时），
#       只需一个接口返回完整数据即可


@router.get("/all")
async def get_all_weather(
    city: str = Query(..., description="城市名称"),
    date: str = Query(default="今天", description="查询日期（今天/明天/后天/YYYY-MM-DD）")
):
    """
    获取完整天气信息（当前+7天预报+24小时预报）
    
    这是天气查询的唯一入口，固定调用两个MCP工具：
    1. 未来7天天气预报工具 → 返回左侧指定日期天气 + 右侧7天预报
    2. 24小时预报工具 → 返回下方逐时预报
    """
    try:
        mcp_tool = get_mcp_weather_tool()
        
        # 并行调用两个固定的MCP工具
        import asyncio
        
        # 工具1：获取7天预报（包含今天）
        forecast_task = mcp_tool.query_weather(
            city=city,
            need_forecast=True,   # 获取7天预报
            need_hourly=False
        )
        
        # 工具2：获取24小时预报
        hourly_task = mcp_tool.query_weather(
            city=city,
            need_forecast=False,
            need_hourly=True      # 获取24小时预报
        )
        
        # 等待两个任务完成
        forecast_result, hourly_result = await asyncio.gather(
            forecast_task, hourly_task,
            return_exceptions=True
        )
        
        # 检查7天预报是否成功
        if isinstance(forecast_result, Exception) or not forecast_result.get("success"):
            error_msg = str(forecast_result) if isinstance(forecast_result, Exception) else forecast_result.get("message", "获取天气失败")
            raise HTTPException(status_code=500, detail=error_msg)
        
        # 提取数据
        forecast_data = forecast_result.get("forecast", [])
        current_data = forecast_result.get("current", {})
        
        # 24小时预报可选，失败不影响主流程
        hourly_data = []
        if not isinstance(hourly_result, Exception) and hourly_result.get("success"):
            hourly_data = hourly_result.get("hourly", [])
        
        # 生成天气建议
        suggestion = _generate_weather_suggestion(current_data, forecast_data)
        
        return {
            "code": 200,
            "message": "获取成功",
            "data": {
                "city": city,
                "date": date,
                "current": current_data,          # 左侧：指定日期天气
                "forecast": forecast_data[:7],    # 右侧：7天预报
                "hourly": hourly_data,            # 下方：24小时预报
                "suggestion": suggestion          # 智能建议
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取天气失败: {str(e)}")


def _generate_weather_suggestion(current: dict, forecast: list) -> dict:
    """
    根据天气数据生成智能建议
    
    Returns:
        {
            "daily": "日常生活建议",
            "meeting": "会议室预定建议"
        }
    """
    temp = current.get("temperature", 20)
    condition = current.get("condition", "")
    humidity = current.get("humidity", "")
    wind = current.get("wind_speed", "")
    
    daily_suggestions = []
    meeting_suggestions = []
    
    # === 日常生活建议 ===
    
    # 温度建议
    if temp < 10:
        daily_suggestions.append("天气较冷，建议穿厚外套、戴围巾")
    elif temp < 20:
        daily_suggestions.append("温度适中，建议穿长袖或薄外套")
    elif temp < 30:
        daily_suggestions.append("温暖舒适，适合户外活动")
    else:
        daily_suggestions.append("天气炎热，注意防暑降温，多喝水")
    
    # 天气状况建议
    if "雨" in condition:
        daily_suggestions.append("有降雨，记得带伞，注意防滑")
    if "雪" in condition:
        daily_suggestions.append("有降雪，注意保暖和防滑")
    if "风" in condition or "大风" in condition:
        daily_suggestions.append("风力较大，注意安全，避免高空作业")
    
    # 湿度建议
    try:
        humidity_val = int(humidity.replace('%', '')) if isinstance(humidity, str) and '%' in humidity else int(humidity)
        if humidity_val > 80:
            daily_suggestions.append("湿度较大，注意防潮")
        elif humidity_val < 30:
            daily_suggestions.append("空气干燥，注意补水保湿")
    except:
        pass
    
    # === 会议室预定建议 ===
    
    # 根据天气判断是否适合户外活动
    if "雨" in condition or "雪" in condition or "大风" in condition:
        meeting_suggestions.append("天气不佳，建议优先选择室内会议室")
        meeting_suggestions.append("如需团建活动，建议改为室内方案")
    elif temp > 30:
        meeting_suggestions.append("天气炎热，建议选择有空调的会议室")
        meeting_suggestions.append("户外活动时间建议安排在早晚凉爽时段")
    elif 15 <= temp <= 28 and ("晴" in condition or "多云" in condition):
        meeting_suggestions.append("天气良好，适合安排户外团建或露天会议")
        meeting_suggestions.append("可考虑预订有露台的会议室")
    else:
        meeting_suggestions.append("天气适宜，室内外活动均可")
    
    return {
        "daily": "；".join(daily_suggestions) if daily_suggestions else "天气适宜",
        "meeting": "；".join(meeting_suggestions) if meeting_suggestions else "无特殊建议"
    }

