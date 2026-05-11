"""
基于LangGraph的多智能体工作流
使用状态图编排LLM驱动的智能体
"""
from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

# 导入LLM驱动的智能体
from agent.task_classifier import get_task_classifier
from agent.todo_agent import get_todo_agent
from agent.meeting_agent import get_meeting_agent
from agent.weather_agent import get_weather_agent
from agent.chat_agent import get_chat_agent
from agent.memory_manager import get_memory, update_memory_state, format_context_for_llm
from crud.chat_history_crud import save_chat_message


class AgentState(TypedDict):
    """
    LangGraph工作流状态 - 集成记忆组件
    
    所有节点共享的状态字典
    """
    message: str              # 用户原始输入
    task_type: str            # 任务类型(todo/meeting/weather/chat)
    db: AsyncSession          # 数据库会话
    user_id: int              # 用户ID
    session_id: str           # 会话ID (用于记忆追踪)
    execution_result: dict    # 执行结果
    response: str             # 最终回复文本
    memory_context: str       # 格式化后的记忆上下文


async def classify_node(state: AgentState) -> AgentState:
    """
    分类节点 - LLM驱动的意图识别 (集成记忆上下文)
    """
    print("[LangGraph] >>> 进入分类节点")
    
    # 1. 获取并格式化记忆上下文
    memory = get_memory(state["session_id"])
    context = format_context_for_llm(memory)
    
    classifier = get_task_classifier()
    # 将记忆上下文传递给分类器，提高识别准确率
    classification = classifier.classify(state["message"], history=context if context else None)
    
    print(f"[LangGraph] 分类结果: {classification}")
    
    return {
        **state,
        "task_type": classification["task_type"],
        "memory_context": context,
        "execution_result": {"classification": classification}
    }


async def todo_agent_node(state: AgentState) -> AgentState:
    """
    待办事项节点 - LLM驱动的智能体 (集成记忆更新)
    """
    print("[LangGraph] >>> 进入Todo节点")
    
    todo_agent = get_todo_agent()
    result = await todo_agent.process(state["message"], state["db"], state["user_id"])
    
    response_msg = result.get("message", "")
    
    # 🔥 异步更新记忆和持久化存储
    asyncio.create_task(_update_session_memory(
        state["session_id"], state["message"], response_msg, "todo"
    ))
    
    return {
        **state,
        "execution_result": result,
        "response": response_msg
    }


async def meeting_agent_node(state: AgentState) -> AgentState:
    """
    会议室预定节点 - LLM驱动的智能体 (集成记忆更新)
    """
    print("[LangGraph] >>> 进入Meeting节点")
    
    meeting_agent = get_meeting_agent()
    result = await meeting_agent.process(state["message"], state["db"], state["user_id"])
    
    response_msg = result.get("message", "")
    
    # 🔥 异步更新记忆
    asyncio.create_task(_update_session_memory(
        state["session_id"], state["message"], response_msg, "meeting"
    ))
    
    return {
        **state,
        "execution_result": result,
        "response": response_msg
    }


async def weather_agent_node(state: AgentState) -> AgentState:
    """
    天气查询节点 - LLM驱动的智能体 (集成记忆更新)
    """
    print("[LangGraph] >>> 进入Weather节点")
    
    weather_agent = get_weather_agent()
    result = await weather_agent.process(state["message"])
    
    response_msg = result.get("message", "")
    
    # 🔥 异步更新记忆
    asyncio.create_task(_update_session_memory(
        state["session_id"], state["message"], response_msg, "weather"
    ))
    
    return {
        **state,
        "execution_result": result,
        "response": response_msg
    }


async def chat_node(state: AgentState) -> AgentState:
    """
    聊天节点 - ChatAgent处理普通对话 (集成记忆上下文)
    """
    print("[LangGraph] >>> 进入Chat节点")
    
    chat_agent = get_chat_agent()
    result = await chat_agent.process(state["message"], state.get('memory_context'))
    
    response_msg = result.get("message", "")
    
    # 🔥 异步更新记忆
    asyncio.create_task(_update_session_memory(
        state["session_id"], state["message"], response_msg, "chat"
    ))
    
    return {
        **state,
        "execution_result": result,
        "response": response_msg
    }


async def _update_session_memory(session_id: str, user_msg: str, ai_msg: str, task_type: str):
    """
    后台任务：更新 Redis 记忆状态
    注意：MySQL 持久化已在 Router 层统一处理，此处仅负责 Redis 缓存更新
    """
    try:
        # 更新 Redis 结构化记忆
        update_memory_state(session_id, user_msg, ai_msg, task_type)
    except Exception as e:
        print(f"[Memory] Redis Update failed: {e}")


def route_by_task(state: AgentState) -> Literal["todo", "meeting", "weather", "chat"]:
    """
    路由函数 - 根据task_type分发到对应节点
    """
    task_type = state.get("task_type", "chat")
    print(f"[LangGraph] 路由到: {task_type}")
    return task_type


def create_multi_agent_workflow():
    """
    创建基于LangGraph的多智能体工作流
    
    架构:
    [Entry] -> [classify_node] -> [路由] -> [todo/meeting/weather/chat] -> [END]
    
    Returns:
        编译后的LangGraph应用
    """
    print("[LangGraph] 创建工作流...")
    
    # 1. 创建状态图
    workflow = StateGraph(AgentState)
    
    # 2. 添加节点(Node)
    workflow.add_node("classify", classify_node)
    workflow.add_node("todo", todo_agent_node)
    workflow.add_node("meeting", meeting_agent_node)
    workflow.add_node("weather", weather_agent_node)
    workflow.add_node("chat", chat_node)
    
    # 3. 设置入口点
    workflow.set_entry_point("classify")
    
    # 4. 添加条件边(Conditional Edge) - 路由逻辑
    workflow.add_conditional_edges(
        "classify",           # 从classify节点出发
        route_by_task,        # 路由函数
        {
            "todo": "todo",
            "meeting": "meeting", 
            "weather": "weather",
            "chat": "chat"
        }
    )
    
    # 5. 所有执行节点都指向END
    workflow.add_edge("todo", END)
    workflow.add_edge("meeting", END)
    workflow.add_edge("weather", END)
    workflow.add_edge("chat", END)
    
    # 6. 编译工作流
    app = workflow.compile()
    
    print("[LangGraph] ✓ 工作流创建完成")
    print("[LangGraph] 节点: classify -> [todo|meeting|weather|chat] -> END")
    
    return app


# 单例模式
_workflow_app = None

def get_langgraph_workflow():
    """获取LangGraph工作流实例(单例)"""
    global _workflow_app
    if _workflow_app is None:
        _workflow_app = create_multi_agent_workflow()
    return _workflow_app
