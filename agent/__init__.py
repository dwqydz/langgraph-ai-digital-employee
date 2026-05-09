"""
Agent模块 - 基于LangChain + LangGraph的多智能体系统

架构:
- LLM层: 通义千问(ChatTongyi)
- Prompt层: 独立的prompt文件管理
- 智能体层: 各个专用Agent(使用LangChain封装)
  - TaskClassifier: 任务分类智能体
  - TodoAgent: 待办事项智能体
  - MeetingAgent: 会议室预定智能体
  - WeatherAgent: 天气查询智能体
- 工作流层: LangGraph编排多智能体协同
"""
from agent.langgraph_workflow import get_langgraph_workflow
from agent.task_classifier import get_task_classifier
from agent.todo_agent import get_todo_agent
from agent.meeting_agent import get_meeting_agent
from agent.weather_agent import get_weather_agent
from agent.prompt_loader import get_prompt_manager

__all__ = [
    'get_langgraph_workflow',
    'get_task_classifier',
    'get_todo_agent',
    'get_meeting_agent',
    'get_weather_agent',
    'get_prompt_manager'
]
