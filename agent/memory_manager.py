"""
记忆管理器 - 负责短期记忆的存储与更新
使用 Redis 存储结构化会话状态，实现多端互通与高效上下文管理
"""
import json
import redis
from typing import Dict, List, Optional
from pydantic import BaseModel

# Redis 连接配置 (根据实际环境调整)
try:
    # 尝试连接本地 Redis
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    print("[Memory] Redis 连接成功")
except Exception as e:
    print(f"[Memory] Redis 连接失败，将使用内存字典降级模式: {e}")
    redis_client = None

# 降级方案：内存字典（仅用于开发测试，重启丢失）
_memory_store = {}

class MemoryState(BaseModel):
    """会话记忆状态模型"""
    session_id: str
    current_intent: str = ""          # 当前意图
    collected_slots: Dict[str, str] = {}  # 已收集的关键信息（槽位）
    recent_messages: List[Dict[str, str]] = []  # 最近 N 轮原始对话
    summary: str = ""                 # 对话摘要

def get_memory(session_id: str) -> MemoryState:
    """获取会话记忆"""
    if redis_client:
        data = redis_client.get(f"mem:{session_id}")
        if data:
            return MemoryState(**json.loads(data))
    else:
        data = _memory_store.get(session_id)
        if data:
            return MemoryState(**data)
    
    return MemoryState(session_id=session_id)

def save_memory(state: MemoryState, ttl: int = 3600):
    """保存会话记忆"""
    # 兼容 Pydantic V1 和 V2
    try:
        data = state.model_dump()
    except AttributeError:
        data = state.dict()
        
    if redis_client:
        redis_client.setex(f"mem:{state.session_id}", ttl, json.dumps(data, ensure_ascii=False))
    else:
        _memory_store[state.session_id] = data

def update_memory_state(
    session_id: str, 
    user_msg: str, 
    ai_msg: str, 
    task_type: str,
    extracted_info: Dict[str, str] = None
) -> MemoryState:
    """
    更新记忆状态
    1. 追加最近消息
    2. 更新关键槽位
    3. 检查长度并触发全量压缩
    """
    state = get_memory(session_id)
    
    # 1. 更新意图与槽位
    if task_type:
        state.current_intent = task_type
    if extracted_info:
        state.collected_slots.update(extracted_info)
    
    # 2. 追加新消息
    state.recent_messages.append({"role": "user", "content": user_msg})
    state.recent_messages.append({"role": "assistant", "content": ai_msg})
    
    # 3. 检查是否需要压缩 (阈值设为 10 条)
    if len(state.recent_messages) > 50:
        # 保留最近的 4 条 (2轮)
        keep_recent = state.recent_messages[-4:]
        # 提取需要压缩的部分 (旧摘要 + 旧原文)
        to_compress_content = state.summary + "\n" + "\n".join(
            [f"{m['role']}: {m['content']}" for m in state.recent_messages[:-4]]
        )
        
        # 调用 LLM 进行全量压缩
        new_summary = _compress_with_llm(to_compress_content)
        
        # 更新状态
        state.summary = new_summary
        state.recent_messages = keep_recent

    # 4. 保存
    save_memory(state)
    return state

def _compress_with_llm(content: str) -> str:
    """调用 LLM 对历史内容进行语义压缩"""
    try:
        from agent.llm import get_qwen_llm
        llm = get_qwen_llm(temperature=0.3)
        prompt = f"""请作为记忆助手，将以下对话历史压缩为一段精炼的背景摘要。
要求：
1. 保留所有关键事实（时间、地点、人物、用户偏好、已完成的动作）。
2. 去除寒暄和无关细节。
3. 如果已有旧摘要，请将其与新内容融合。

待压缩内容：
{content}

精炼摘要："""
        response = llm.invoke(prompt)
        return response.content if hasattr(response, 'content') else str(response)
    except Exception as e:
        print(f"[Memory] LLM 压缩失败: {e}")
        return content[:200]  # 降级方案：截取前200字

def format_context_for_llm(state: MemoryState) -> str:
    """将记忆状态格式化为 LLM 可读的上下文 Prompt"""
    parts = []
    
    if state.summary:
        parts.append(f"【历史背景】{state.summary}")
    
    if state.collected_slots:
        slots_str = ", ".join([f"{k}: {v}" for k, v in state.collected_slots.items()])
        parts.append(f"【已知信息】{slots_str}")
    
    if state.recent_messages:
        parts.append("【最近对话】")
        for msg in state.recent_messages[-6:]: # 只取最近 3 轮原文
            role_cn = "用户" if msg['role'] == 'user' else "助手"
            parts.append(f"{role_cn}: {msg['content']}")
    
    return "\n".join(parts)
