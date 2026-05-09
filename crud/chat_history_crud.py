"""
对话历史 CRUD - 负责将对话记录异步写入 MySQL
用于审计、长期存储和多端同步基础数据
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from model.chat_history_model import ChatHistory
from datetime import datetime
from typing import List, Dict

async def save_chat_message(
    db: AsyncSession,
    user_id: int,
    session_id: str,
    role: str,
    content: str,
    metadata: dict = None
):
    """保存单条对话消息到 MySQL"""
    try:
        message = ChatHistory(
            user_id=user_id,
            session_id=session_id,
            role=role,
            content=content,
            message_metadata=metadata or {}
            # created_at 使用数据库默认值 server_default=func.now()
        )
        db.add(message)
        await db.commit()
    except Exception as e:
        print(f"[ChatHistory] 保存失败: {e}")
        await db.rollback()

async def get_session_messages(
    db: AsyncSession,
    session_id: str,
    limit: int = 50
) -> List[Dict]:
    """获取指定会话的历史消息"""
    query = (
        select(ChatHistory)
        .where(ChatHistory.session_id == session_id)
        .order_by(desc(ChatHistory.created_at))
        .limit(limit)
    )
    result = await db.execute(query)
    messages = result.scalars().all()
    
    return [
        {
            "role": msg.role,
            "content": msg.content,
            "created_at": msg.created_at.isoformat()
        }
        for msg in reversed(messages)
    ]
