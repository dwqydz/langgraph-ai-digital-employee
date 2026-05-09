"""
MCP天气工具集成
使用阿里云MCP天气服务（tianqitongmcp）
通过直接HTTP JSON-RPC调用
"""
from typing import Dict, Any, Optional
import httpx
import json
import os


class MCPWeatherTool:
    """
    MCP天气工具
    
    使用阿里云MCP天气服务查询天气
    通过HTTP JSON-RPC协议直接调用
    """
    
    def __init__(self):
        self.mcp_url = "https://dashscope.aliyuncs.com/api/v1/mcps/tianqitongmcp/mcp"
        # 从环境变量获取API密钥
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError(
                "未找到 DASHSCOPE_API_KEY 环境变量。"
                "请设置环境变量以使用MCP天气服务。"
            )
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def _call_mcp_method(self, method: str, params: dict) -> Any:
        """
        调用MCP方法
        
        Args:
            method: 方法名
            params: 参数
            
        Returns:
            响应结果
        """
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(self.mcp_url, headers=self.headers, json=payload)
            
            if response.status_code != 200:
                raise Exception(f"MCP请求失败: {response.status_code}")
            
            result = response.json()
            
            if "error" in result:
                raise Exception(f"MCP错误: {result['error']}")
            
            return result.get("result")
    
    async def query_weather(
        self, 
        city: str, 
        date: Optional[str] = None,
        need_forecast: bool = False,
        need_hourly: bool = False
    ) -> Dict[str, Any]:
        """
        查询天气 - 使用阿里云MCP天气服务
        
        Args:
            city: 城市名称（支持中文，如"上海"）
            date: 查询日期
            need_forecast: 是否需要7天预报
            need_hourly: 是否需要24小时逐时预报
            
        Returns:
            天气数据字典
        """
        try:
            print(f"[MCPWeatherTool] 查询天气 - 城市: {city}, 预报: {need_forecast}, 24小时: {need_hourly}")
            
            result = {
                "success": True,
                "city": city,
                "current": {},
                "forecast": [],
                "hourly": []
            }
            
            # 根据需求调用不同的MCP工具
            if need_forecast:
                # 调用15天预报
                forecast_data = await self._get_15day_forecast(city)
                if forecast_data:
                    result['forecast'] = forecast_data[:7]
            
            if need_hourly:
                # 调用24小时预报
                hourly_data = await self._get_24hour_forecast(city)
                if hourly_data:
                    result['hourly'] = hourly_data
            
            # 获取当前天气（总是需要）
            current_data = await self._get_current_weather(city)
            if current_data:
                result['current'] = current_data
            
            print(f"[MCPWeatherTool] 查询成功 - 当前天气: {result.get('current')}, 预报: {len(result.get('forecast', []))}条, 逐时: {len(result.get('hourly', []))}条")
            return result
                    
        except Exception as e:
            print(f"[MCPWeatherTool] 查询异常: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"天气查询异常: {str(e)}"
            }
    
    async def _get_current_weather(self, city: str) -> Optional[Dict[str, Any]]:
        """获取当前天气"""
        try:
            # 调用tqt-current-weather工具
            call_result = await self._call_mcp_method("tools/call", {
                "name": "tqt-current-weather",
                "arguments": {"cityname": city}
            })
            
            # 解析响应
            if call_result and "content" in call_result:
                content = call_result["content"]
                if isinstance(content, list) and len(content) > 0:
                    text_content = content[0].get("text", "")
                    data = json.loads(text_content)
                    
                    if isinstance(data, list) and len(data) > 0:
                        weather_data = data[0]
                        condition = weather_data.get("condition", {})
                        
                        return {
                            "temperature": int(condition.get("temperature", 0)),
                            "condition": condition.get("weather_desc", ""),
                            "humidity": condition.get("humidity", ""),
                            "wind_speed": condition.get("wind_desc", ""),
                            "wind_direction": condition.get("wind_desc", "").split()[0] if condition.get("wind_desc") else "",
                            "description": f"今天{condition.get('weather_desc', '')}，温度{condition.get('temperature', 0)}°C"
                        }
            
            return None
        except Exception as e:
            print(f"[MCPWeatherTool] 获取当前天气失败: {e}")
            return None
    
    async def _get_15day_forecast(self, city: str) -> Optional[list]:
        """获取15天预报"""
        try:
            # 调用tqt-15day-forecast工具
            call_result = await self._call_mcp_method("tools/call", {
                "name": "tqt-15day-forecast",
                "arguments": {"cityname": city}
            })
            
            # 解析响应
            if call_result and "content" in call_result:
                content = call_result["content"]
                if isinstance(content, list) and len(content) > 0:
                    text_content = content[0].get("text", "")
                    data = json.loads(text_content)
                    
                    if isinstance(data, list) and len(data) > 0:
                        forecast_data = data[0].get("forecast", [])
                        
                        forecasts = []
                        for day in forecast_data[:7]:
                            forecasts.append({
                                "date": day.get("forecast_day", ""),
                                "temperature_high": int(day.get("max_temperature", 0)),
                                "temperature_low": int(day.get("min_temperature", 0)),
                                "condition": day.get("day_weather_desc", ""),
                                "wind_speed": day.get("day_wind_desc", "")
                            })
                        
                        return forecasts
            
            return None
        except Exception as e:
            print(f"[MCPWeatherTool] 获取15天预报失败: {e}")
            return None
    
    async def _get_24hour_forecast(self, city: str) -> Optional[list]:
        """获取24小时预报"""
        try:
            # 调用tqt-24hour-forecast工具
            call_result = await self._call_mcp_method("tools/call", {
                "name": "tqt-24hour-forecast",
                "arguments": {"cityname": city}
            })
            
            # 解析响应
            if call_result and "content" in call_result:
                content = call_result["content"]
                if isinstance(content, list) and len(content) > 0:
                    text_content = content[0].get("text", "")
                    data = json.loads(text_content)
                    
                    if isinstance(data, list) and len(data) > 0:
                        hourly_data = data[0].get("hourly", [])
                        
                        hourly = []
                        for hour in hourly_data[:24]:
                            # 提取时间部分（HH:MM）
                            forecast_time = hour.get("forecast_time", "")
                            time_part = forecast_time.split(" ")[1][:5] if " " in forecast_time else ""
                            
                            hourly.append({
                                "time": time_part,
                                "temperature": int(hour.get("temperature", 0)),
                                "condition": hour.get("weather_desc", ""),
                                "wind_speed": hour.get("wind_desc", ""),
                                "humidity": hour.get("humidity", "")
                            })
                        
                        return hourly
            
            return None
        except Exception as e:
            print(f"[MCPWeatherTool] 获取24小时预报失败: {e}")
            return None


# 单例
_mcp_weather_tool = None

def get_mcp_weather_tool() -> MCPWeatherTool:
    """获取MCP天气工具单例"""
    global _mcp_weather_tool
    if _mcp_weather_tool is None:
        _mcp_weather_tool = MCPWeatherTool()
    return _mcp_weather_tool
