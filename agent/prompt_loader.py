"""
Prompt管理工具
负责从文件加载prompt模板
"""
import os
from pathlib import Path


class PromptManager:
    """Prompt管理器 - 从文件加载prompt"""
    
    def __init__(self):
        # prompt文件夹路径
        self.prompt_dir = Path(__file__).parent.parent / "prompt"
    
    def load_prompt(self, filename: str) -> str:
        """
        加载prompt文件
        
        Args:
            filename: prompt文件名(不含.txt后缀)
            
        Returns:
            prompt文本内容
        """
        prompt_path = self.prompt_dir / f"{filename}.txt"
        
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt文件不存在: {prompt_path}")
        
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    
    def get_task_classifier_prompt(self) -> str:
        """获取任务分类prompt"""
        return self.load_prompt("task_classifier")
    
    def get_todo_agent_prompt(self) -> str:
        """获取待办事项智能体prompt"""
        return self.load_prompt("todo_agent")
    
    def get_meeting_agent_prompt(self) -> str:
        """获取会议室预定智能体prompt"""
        return self.load_prompt("meeting_agent")
    
    def get_weather_agent_prompt(self) -> str:
        """获取天气查询智能体prompt"""
        return self.load_prompt("weather_agent")


# 单例模式
_prompt_manager = None

def get_prompt_manager() -> PromptManager:
    """获取Prompt管理器实例"""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager
