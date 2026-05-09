"""
智能Agent路由
提供LLM驱动的对话接口
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from typing import Optional

from pydantic import BaseModel

from agent.llm import get_qwen_llm
# 导入数据库配置
from config.db_config import get_database

# 导入Session Token认证
from utils.session_auth import get_current_user_id_from_session


# 定义请求模型
class ChatRequest(BaseModel):
    """聊天请求模型 - 集成会话ID"""
    message: str
    session_id: Optional[str] = None  # 会话ID，用于多端互通和历史追踪


router = APIRouter(
    prefix="/agent",
    tags=["智能Agent模块"]
)


@router.post("/chat")
async def chat_with_agent(
    request: ChatRequest,
    db = Depends(get_database),
    current_user_id: int = Depends(get_current_user_id_from_session)
):
    """
    与智能Agent对话 (支持记忆组件)
    
    Args:
        request: 聊天请求（包含message和session_id）
        db: 数据库会话
        current_user_id: 当前用户ID(从Session Token获取)
        
    Returns:
        dict: Agent回复和处理结果
    """
    try:
        import uuid
        from agent.langgraph_workflow import get_langgraph_workflow
        from config.db_config import AsyncSessionLocal
        from crud.chat_history_crud import save_chat_message
        
        # 1. 生成或使用现有 Session ID
        session_id = request.session_id or str(uuid.uuid4())
        
        # 2. 异步保存用户输入 (使用独立会话，避免与主请求 db 冲突)
        async def _save_user_msg():
            async with AsyncSessionLocal() as new_db:
                await save_chat_message(new_db, current_user_id, session_id, "user", request.message)
        import asyncio
        asyncio.create_task(_save_user_msg())
        
        # 3. 执行 LangGraph 工作流 (增加 recursion_limit 防止死循环)
        workflow = get_langgraph_workflow()
        result = await workflow.ainvoke({
            "message": request.message,
            "db": db,
            "user_id": current_user_id,
            "session_id": session_id,
            "task_type": "",
            "execution_result": {},
            "response": "",
            "memory_context": ""
        }, config={"recursion_limit": 10})
        
        # 4. 处理闲聊 (Chat) 逻辑
        # 如果工作流因为 chat 意图直接结束，result['response'] 可能为空
        if not result.get("response"):
            from agent.llm import get_qwen_llm
            from langchain_core.messages import SystemMessage, HumanMessage
            llm = get_qwen_llm(temperature=0.7)
            try:
                messages = [
                    SystemMessage(content="你是一个专业的AI数字员工助手。请用**纯中文**、简洁、自然地回应用户的闲聊。不要使用英文单词，不要过度热情。"),
                    HumanMessage(content=request.message)
                ]
                response = await llm.ainvoke(messages)
                result["response"] = response.content if hasattr(response, 'content') else str(response)
            except Exception as e:
                result["response"] = "抱歉，我暂时无法回应。"
        
        # 5. 异步保存 Agent 回复 (使用独立会话)
        async def _save_ai_msg():
            async with AsyncSessionLocal() as new_db:
                await save_chat_message(new_db, current_user_id, session_id, "assistant", result["response"])
        asyncio.create_task(_save_ai_msg())
        
        return {
            "code": 200,
            "message": "处理成功",
            "data": {
                "response": result["response"],
                "session_id": session_id,
                "task_type": result.get("task_type")
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.post("/voice-chat")
async def voice_chat_with_agent(
    audio: UploadFile = File(...),
    db = Depends(get_database),
    current_user_id: int = Depends(get_current_user_id_from_session)
):
    """
    语音对话 - 上传音频文件,返回文本回复
    
    Args:
        audio: 音频文件(mp3/wav等格式)
        db: 数据库会话
        current_user_id: 当前用户ID
        
    Returns:
        dict: 识别文本和Agent回复
    """
    try:
        # 读取音频数据
        audio_bytes = await audio.read()
        
        # 语音识别
        speech_service = get_speech_service()
        text = speech_service.recognize_from_bytes(audio_bytes, language="zh-CN")
        
        # LLM处理
        agent = get_qwen_llm()
        result = await agent.process(text, db, current_user_id)
        
        # 添加识别文本
        result["recognized_text"] = text
        
        return {
            "code": 200,
            "message": "处理成功",
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"语音处理失败: {str(e)}")


@router.post("/intent-recognition")
async def recognize_intent(
    message: str,
    current_user_id: int = Depends(get_current_user_id_from_session)
):
    """
    意图识别 - 仅识别意图,不执行操作
    
    Args:
        message: 用户输入
        current_user_id: 当前用户ID
        
    Returns:
        dict: 识别结果
    """
    try:
        agent = get_qwen_llm()
        # 使用简化智能体的分类功能
        from config.db_config import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            result = await agent.process(message, db, current_user_id)
        
        return {
            "code": 200,
            "message": "识别成功",
            "data": {
                "task_type": result.get("task_type"),
                "intent_data": result.get("execution_result", {})
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"识别失败: {str(e)}")


@router.get("/capabilities")
async def get_capabilities():
    """
    获取Agent能力说明
    
    Returns:
        dict: 支持的功能列表
    """
    return {
        "code": 200,
        "message": "获取成功",
        "data": {
            "modules": [
                {
                    "name": "todo",
                    "description": "待办事项管理",
                    "actions": [
                        "create_todo - 创建待办",
                        "query_todos - 查询待办列表",
                        "update_todo - 更新待办状态"
                    ],
                    "examples": [
                        "帮我创建一个明天下午3点的项目评审会议待办",
                        "查看我的所有待办事项",
                        "把第一个待办标记为已完成"
                    ]
                },
                {
                    "name": "meeting",
                    "description": "会议室预订",
                    "actions": [
                        "query_rooms - 查询可用会议室",
                        "book_meeting - 预订会议室",
                        "cancel_booking - 取消预订",
                        "query_bookings - 查询我的预订"
                    ],
                    "examples": [
                        "有哪些能容纳20人的会议室",
                        "帮我预订明天下午2点到4点的会议室",
                        "取消我的预订",
                        "查看我的预订记录"
                    ]
                },
                {
                    "name": "weather",
                    "description": "天气查询",
                    "actions": [
                        "query_weather - 查询当前天气",
                        "query_forecast - 查询天气预报"
                    ],
                    "examples": [
                        "北京今天天气怎么样",
                        "上海未来3天天气预报"
                    ]
                },
                {
                    "name": "chat",
                    "description": "普通聊天对话",
                    "actions": [
                        "chat - 自由对话"
                    ]
                }
            ],
            "features": [
                "自然语言理解",
                "意图识别",
                "语音输入支持",
                "多轮对话",
                "智能参数提取",
                "真实业务操作执行"
            ]
        }
    }
