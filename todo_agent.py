"""
待办事项智能体 - 基于LangChain
使用LLM理解用户意图并执行待办操作
"""
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from agent.llm import get_qwen_llm
from agent.prompt_loader import get_prompt_manager
from crud import todo_crud
import datetime


class TodoAction(BaseModel):
    """待办事项操作Schema"""
    action: str = Field(description="操作类型: create/query/update")
    title: str = Field(description="待办标题(创建时需要)")
    description: str = Field(default="", description="待办描述(可选)")
    due_date: str = Field(default="", description="截止时间字符串,如'明天 14:00:00'")
    priority: str = Field(default="medium", description="优先级: low/medium/high/urgent")
    category: str = Field(default="other", description="分类: work/study/admin/other")
    todo_id: int = Field(default=0, description="待办ID(更新/查询时需要)")


class TodoAgent:
    """
    待办事项智能体
    
    使用LangChain的LLM理解用户意图,提取参数,调用CRUD执行操作
    """
    
    def __init__(self):
        self.llm = get_qwen_llm(temperature=0.3)
        
        # 从文件加载prompt
        prompt_manager = get_prompt_manager()
        system_prompt = prompt_manager.get_todo_agent_prompt()
        
        # Prompt模板 - 用于理解用户意图并提取参数
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}")
        ])
        
        self.parser = JsonOutputParser(pydantic_object=TodoAction)
        self.chain = self.prompt | self.llm | self.parser
    
    def _parse_due_date(self, due_date_str: str) -> datetime.datetime | None:
        """
        解析自然语言时间为datetime对象
        
        Args:
            due_date_str: 时间字符串,如"明天 14:00:00"或"下周四"
            
        Returns:
            datetime对象或None
        """
        if not due_date_str or due_date_str.strip() == "":
            return None
        
        try:
            now = datetime.datetime.now()
            date_str = due_date_str.strip()
            target_date = now
            
            # 1. 处理相对日期关键词
            if "明天" in date_str:
                target_date = now + datetime.timedelta(days=1)
                date_str = date_str.replace("明天", "")
            elif "后天" in date_str:
                target_date = now + datetime.timedelta(days=2)
                date_str = date_str.replace("后天", "")
            elif "今天" in date_str:
                target_date = now
                date_str = date_str.replace("今天", "")
            
            # 2. 处理“周几”逻辑 (如: 本周四, 下周四)
            weekdays = {"一": 0, "二": 1, "三": 2, "四": 3, "五": 4, "六": 5, "日": 6, "天": 6}
            for cn_day, num in weekdays.items():
                if f"本周{cn_day}" in date_str:
                    days_ahead = num - now.weekday()
                    if days_ahead <= 0: # 如果今天已经是周X或过了周X,则指向下周
                        days_ahead += 7
                    target_date = now + datetime.timedelta(days=days_ahead)
                    date_str = date_str.replace(f"本周{cn_day}", "")
                    break
                elif f"下周{cn_day}" in date_str:
                    days_ahead = num - now.weekday() + 7
                    target_date = now + datetime.timedelta(days=days_ahead)
                    date_str = date_str.replace(f"下周{cn_day}", "")
                    break
            
            # 3. 提取具体时间部分 (如 "14:00:00")
            time_part = date_str.strip()
            if time_part and ":" in time_part:
                try:
                    hour, minute = map(int, time_part.split(":")[:2])
                    target_date = target_date.replace(hour=hour, minute=minute, second=0)
                except:
                    pass
            
            return target_date
            
        except Exception as e:
            print(f"[TodoAgent] 时间解析失败: {e}")
            return None
    
    def _convert_status_to_chinese(self, status: str, due_date: datetime.datetime | None = None) -> str:
        """
        将英文状态转换为中文,并根据截止时间判断是否逾期
        
        Args:
            status: 英文状态 pending/completed/cancelled
            due_date: 截止时间(可选)
            
        Returns:
            中文状态: 进行中/已完成/已取消/已逾期
        """
        # 如果已完成,直接返回
        if status == "completed":
            return "已完成"
        
        # 如果已取消,直接返回
        if status == "cancelled":
            return "已取消"
        
        # 对于pending状态,检查是否逾期
        if status == "pending":
            if due_date and datetime.datetime.now() > due_date:
                return "已逾期"
            else:
                return "进行中"
        
        return status
    
    async def process(self, message: str, db: AsyncSession, user_id: int) -> Dict[str, Any]:
        """
        处理待办事项请求
        
        Args:
            message: 用户输入
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            dict: 执行结果
        """
        try:
            print("[TodoAgent] >>> LLM理解用户意图...")
            
            # 1. 使用LLM理解意图并提取参数
            action_data = self.chain.invoke({"input": message})
            action = action_data.get("action", "query")
            
            print(f"[TodoAgent] 识别操作: {action}")
            print(f"[TodoAgent] 提取参数: {action_data}")
            
            # 2. 根据操作类型执行
            if action == "create":
                return await self._create_todo(db, user_id, action_data)
            elif action == "query":
                return await self._query_todos(db, user_id, action_data)
            elif action == "update":
                return await self._update_todo(db, user_id, action_data)
            else:
                return {"success": False, "message": "未知操作"}
                
        except Exception as e:
            print(f"[TodoAgent] 处理失败: {e}")
            return {"success": False, "message": f"❌ 处理失败: {str(e)}"}
    
    async def _create_todo(self, db: AsyncSession, user_id: int, action_data: dict) -> Dict[str, Any]:
        """创建待办"""
        try:
            title = action_data.get("title", "新待办")
            description = action_data.get("description", "")
            due_date_str = action_data.get("due_date", "")
            priority = action_data.get("priority", "medium")
            category = action_data.get("category", "other")
            
            # 解析截止时间
            due_date = self._parse_due_date(due_date_str)
            
            todo = await todo_crud.create_todo(
                db=db,
                user_id=user_id,
                title=title,
                description=description or f"通过自然语言创建: {title}",
                due_date=due_date,
                priority=priority,
                category=category
            )
            
            # 返回符合TodoItem格式的数据
            return {
                "success": True,
                "message": f"✅ 已创建待办: {title}",
                "data": {
                    "id": todo.id,
                    "title": todo.title,
                    "description": todo.description,
                    "status": self._convert_status_to_chinese(todo.status, todo.due_date),
                    "priority": todo.priority,
                    "category": todo.category,
                    "due_date": todo.due_date.isoformat() if todo.due_date else None,
                    "completed_at": todo.completed_at.isoformat() if todo.completed_at else None,
                    "reminder_enabled": todo.reminder_enabled,
                    "is_reminded": todo.is_reminded,
                    "created_at": todo.created_at.isoformat() if todo.created_at else None,
                    "updated_at": todo.updated_at.isoformat() if todo.updated_at else None
                }
            }
        except Exception as e:
            return {"success": False, "message": f"❌ 创建失败: {str(e)}"}
    
    async def _query_todos(self, db: AsyncSession, user_id: int, action_data: dict = None) -> Dict[str, Any]:
        """
        查询待办列表 - 支持智能筛选
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            action_data: LLM提取的参数(可选),包含category等筛选条件
        """
        try:
            # 从action_data中提取筛选条件
            category = action_data.get("category", "") if action_data else None
            title_keyword = action_data.get("title", "") if action_data else None
            
            # 调用CRUD查询(目前简单实现,后续可增强筛选逻辑)
            todos, total = await todo_crud.get_todos_by_user_id(db, user_id, page=1, page_size=10)
            
            # 如果有分类筛选,过滤结果
            if category and category != "other":
                todos = [t for t in todos if t.category == category]
            
            # 如果有关键词,模糊匹配标题
            if title_keyword:
                todos = [t for t in todos if title_keyword.lower() in t.title.lower()]
            
            if not todos:
                return {
                    "success": True, 
                    "message": "暂无符合条件的待办事项", 
                    "data": []
                }
            
            # 返回符合TodoItem格式的列表
            todo_list = [
                {
                    "id": t.id,
                    "title": t.title,
                    "description": t.description,
                    "status": self._convert_status_to_chinese(t.status, t.due_date),
                    "priority": t.priority,
                    "category": t.category,
                    "due_date": t.due_date.isoformat() if t.due_date else None,
                    "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                    "reminder_enabled": t.reminder_enabled,
                    "is_reminded": t.is_reminded,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "updated_at": t.updated_at.isoformat() if t.updated_at else None
                }
                for t in todos
            ]
            
            return {
                "success": True,
                "message": f"查询到 {len(todo_list)} 条待办",
                "data": todo_list
            }
        except Exception as e:
            return {"success": False, "message": f"❌ 查询失败: {str(e)}"}
    
    async def _update_todo(self, db: AsyncSession, user_id: int, action_data: dict) -> Dict[str, Any]:
        """更新待办状态"""
        try:
            todo_id = action_data.get("todo_id", 0)
            
            if todo_id == 0:
                # 如果没有指定ID,标记第一个待办为完成
                todos, _ = await todo_crud.get_todos_by_user_id(db, user_id, page=1, page_size=1)
                if not todos:
                    return {"success": False, "message": "没有可更新的待办"}
                todo_id = todos[0].id
            
            todo = await todo_crud.get_todo_by_id_and_user(db, todo_id, user_id)
            if not todo:
                return {"success": False, "message": "待办不存在"}
            
            await todo_crud.update_todo_status(db, todo, "completed")
            
            return {
                "success": True,
                "message": f"✅ 已将 \"{todo.title}\" 标记为已完成"
            }
        except Exception as e:
            return {"success": False, "message": f"❌ 更新失败: {str(e)}"}


# 单例
_todo_agent = None

def get_todo_agent() -> TodoAgent:
    global _todo_agent
    if _todo_agent is None:
        _todo_agent = TodoAgent()
    return _todo_agent
