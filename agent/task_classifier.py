"""
任务分类智能体 - 使用LangChain封装
LLM驱动的意图识别
"""
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from agent.llm import get_qwen_llm
from agent.prompt_loader import get_prompt_manager


class TaskClassification(BaseModel):
    """任务分类输出Schema"""
    task_type: str = Field(description="任务类型: todo/meeting/weather/chat")
    confidence: float = Field(description="置信度,范围0.0-1.0")
    reason: str = Field(description="分类原因的简要说明")


class TaskClassifierAgent:
    """
    任务分类智能体
    
    使用LangChain的ChatPromptTemplate + LLM + JsonOutputParser
    实现基于LLM的智能分类
    """
    
    def __init__(self):
        self.llm = get_qwen_llm(temperature=0.3)
        
        # 从文件加载prompt
        prompt_manager = get_prompt_manager()
        system_prompt = prompt_manager.get_task_classifier_prompt()
        
        # 创建LangChain prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}")
        ])
        
        # JSON输出解析器
        self.parser = JsonOutputParser(pydantic_object=TaskClassification)
        
        # 构建完整链
        self.chain = self.prompt | self.llm | self.parser
    
    def classify(self, message: str, history: str = None) -> Dict[str, Any]:
        """
        使用LLM对用户输入进行分类
        
        Args:
            message: 用户的自然语言输入
            history: 可选的历史对话上下文 (由 Memory Manager 提供)
            
        Returns:
            dict: 包含task_type, confidence, reason的分类结果
        """
        try:
            # 构建输入文本
            input_text = message
            if history:
                input_text = f"{history}\n\n当前用户输入: {message}"
            
            # 调用LangChain链
            result = self.chain.invoke({"input": input_text})
            
            return {
                "task_type": result.get("task_type", "chat"),
                "confidence": result.get("confidence", 0.5),
                "reason": result.get("reason", "")
            }
            
        except Exception as e:
            print(f"[TaskClassifier] LLM分类失败: {e}")
            # 🔥 增强型降级方案：不再直接返回 chat，而是根据关键词简单判断
            todo_keywords = ["待办", "提醒", "记得", "计划", "要", "需要", "帮我记", "创建"]
            if any(kw in message for kw in todo_keywords):
                return {
                    "task_type": "todo",
                    "confidence": 0.6,
                    "reason": "关键词匹配降级"
                }
            return {
                "task_type": "chat",
                "confidence": 0.0,
                "reason": f"LLM调用失败: {str(e)}"
            }


# 单例模式
_classifier_agent = None

def get_task_classifier() -> TaskClassifierAgent:
    """获取任务分类智能体实例"""
    global _classifier_agent
    if _classifier_agent is None:
        _classifier_agent = TaskClassifierAgent()
    return _classifier_agent
