"""
ChatTonyi LLM服务 - LangChain集成
"""
try:
    from langchain_community.chat_models import ChatTongyi
except ImportError:
    raise ImportError("请安装langchain-community: pip install langchain-community")
import os
import urllib3

# 禁用SSL警告（开发环境）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_qwen_llm(temperature=0.7):
    """
    获取ChatTonyi qwen-plus-2025-07-28模型实例
    
    Args:
        temperature: 温度参数,控制随机性
        
    Returns:
        ChatTongyi实例
    """
    # 从环境变量获取API密钥，如果没有则使用默认值
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError(
            "未找到 DASHSCOPE_API_KEY 环境变量。"
            "请设置环境变量或在代码中配置 API 密钥。"
        )
    llm = ChatTongyi(
        model="qwen-plus-2025-07-28",
        api_key=api_key,
        temperature=temperature,
        max_tokens=512,  # 最大生成token数
    )
    
    return llm
