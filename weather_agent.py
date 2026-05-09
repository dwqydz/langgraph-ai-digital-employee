"""
天气查询智能体 - 基于LangChain + MCP工具
使用LLM理解用户意图，调用MCP工具查询天气
"""
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from agent.llm import get_qwen_llm
from agent.prompt_loader import get_prompt_manager
from agent.mcp_weather_tool import get_mcp_weather_tool


class WeatherAction(BaseModel):
    """天气查询操作Schema"""
    city: str = Field(description="城市名称")
    date: str = Field(default="", description="查询日期，格式YYYY-MM-DD，如果为空则查询今天")
    query_type: str = Field(description="查询类型: current(当前天气)/forecast(天气预报)")
    need_suggestion: bool = Field(default=True, description="是否需要天气建议")


class WeatherAgent:
    """
    天气查询智能体
    
    使用LangChain的LLM提取城市名,调用天气API查询
    """
    
    def __init__(self):
        self.llm = get_qwen_llm(temperature=0.3)
        self.mcp_tool = get_mcp_weather_tool()
        
        # 从文件加载prompt
        prompt_manager = get_prompt_manager()
        system_prompt = prompt_manager.get_weather_agent_prompt()
        
        # Prompt模板
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}")
        ])
        
        self.parser = JsonOutputParser(pydantic_object=WeatherAction)
        self.chain = self.prompt | self.llm | self.parser
    
    async def process(self, message: str) -> Dict[str, Any]:
        """
        处理天气查询请求 - 简化版
        
        职责：
        1. LLM提取城市和时间
        2. 日期校验（今天~未来6天）
        3. 返回结构化参数，由路由层调用MCP工具
        """
        try:
            print("[WeatherAgent] >>> LLM提取天气查询参数...")
            
            # 1. 使用LLM提取参数
            action_data = await self.chain.ainvoke({"input": message})
            city = action_data.get("city", "上海")
            date = action_data.get("date", "")
            
            print(f"[WeatherAgent] 提取结果 - 城市: {city}, 日期: {date}")
            
            # 2. 日期校验：检查是否在可查询范围内（今天~未来6天，共7天）
            if date and date not in ["今天", "明天", "后天"]:
                is_valid, error_msg = self._validate_date(date)
                if not is_valid:
                    print(f"[WeatherAgent] 日期校验失败: {error_msg}")
                    return {
                        "success": False,
                        "message": f"❌ {error_msg}",
                        "data": None
                    }
            
            # 3. 返回结构化参数（不直接调用MCP，由路由层统一调用）
            return {
                "success": True,
                "message": f"✅ 正在查询{city}的天气...",
                "data": {
                    "city": city,
                    "date": date or "今天"
                }
            }
                
        except Exception as e:
            print(f"[WeatherAgent] 处理失败: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"❌ 查询失败: {str(e)}"}
    

    
    def _validate_date(self, date_str: str) -> tuple:
        """
        校验日期是否在可查询范围内（今天~未来6天，共7天）
        
        Args:
            date_str: 日期字符串，格式可能是：
                     - "今天"/"明天"/"后天"
                     - "YYYY-MM-DD"
                     - "YYYY/MM/DD"
        
        Returns:
            (is_valid: bool, error_message: str)
        """
        import datetime
        
        try:
            # 处理相对日期
            if date_str in ["今天", "明天", "后天"]:
                return True, ""
            
            # 解析具体日期
            date_str_normalized = date_str.replace("/", "-")
            target_date = datetime.datetime.strptime(date_str_normalized, "%Y-%m-%d").date()
            today = datetime.date.today()
            
            # 计算天数差
            days_diff = (target_date - today).days
            
            # 校验范围：不能是过去的日期，也不能超过未来6天
            if days_diff < 0:
                return False, f"无法查询过去日期的天气（{date_str}）"
            elif days_diff > 6:
                return False, f"天气预报最多只能查询未来7天（今天~{today + datetime.timedelta(days=6)}），无法预测{date_str}的天气"
            else:
                return True, ""
                
        except ValueError as e:
            return False, f"日期格式不正确：{date_str}，请使用 YYYY-MM-DD 格式"


# 单例
_weather_agent = None

def get_weather_agent() -> WeatherAgent:
    global _weather_agent
    if _weather_agent is None:
        _weather_agent = WeatherAgent()
    return _weather_agent
