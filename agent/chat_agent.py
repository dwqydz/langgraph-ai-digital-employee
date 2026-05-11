"""
聊天智能体 - 处理普通对话
使用LLM进行自然语言对话，支持RAG检索增强
"""
from typing import Dict, Any
from agent.llm import get_qwen_llm
from agent.prompt_loader import get_prompt_manager
# 🔥 RAG模块导入
try:
    from RAG.retriever import get_retriever
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    print("[ChatAgent] ⚠️ RAG模块未安装，将禁用RAG功能")


class ChatAgent:
    """
    聊天智能体
    
    处理普通对话、闲聊、问答等非任务型交互
    """
    
    def __init__(self):
        self.llm = get_qwen_llm(temperature=0.7)
        
        # 从文件加载prompt
        prompt_manager = get_prompt_manager()
        system_prompt = prompt_manager.get_chat_agent_prompt()
        
        self.system_prompt = system_prompt
    
    async def process(self, message: str, history_context: str = None) -> Dict[str, Any]:
        """
        处理用户聊天消息（支持RAG）
        
        Args:
            message: 用户的聊天消息
            history_context: 可选的历史对话上下文
            
        Returns:
            dict: 包含回复消息和处理结果
        """
        try:
            # 🔥 判断是否需要使用RAG
            use_rag = self._should_use_rag(message)
            
            if use_rag and RAG_AVAILABLE:
                print(f"[ChatAgent] 🔍 检测到RAG相关查询，启用检索增强")
                return await self._process_with_rag(message, history_context)
            else:
                # 普通对话模式
                return await self._process_normal_chat(message, history_context)
            
        except Exception as e:
            print(f"[ChatAgent] 处理失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"抱歉，我暂时无法回应。({str(e)})",
                "action": "chat_response"
            }
    
    def _should_use_rag(self, message: str) -> bool:
        """
        判断是否应该使用RAG
        
        Args:
            message: 用户消息
            
        Returns:
            bool: 是否使用RAG
        """
        # RAG相关关键词
        rag_keywords = [
            "政策", "规定", "流程", "制度", "如何", "怎么", 
            "入职", "离职", "请假", "休假", "薪酬", "福利",
            "招聘", "面试", "培训", "考核", "会议", "报销",
            "远程", "办公", "设备", "系统", "账号"
        ]
        
        # 检查是否包含RAG关键词
        has_rag_keyword = any(keyword in message for keyword in rag_keywords)
        
        if has_rag_keyword:
            print(f"[ChatAgent] 📌 检测到RAG关键词，将使用向量检索")
            return True
        
        return False
    
    async def _process_with_rag(self, message: str, history_context: str = None) -> Dict[str, Any]:
        """
        使用RAG处理查询
        
        Args:
            message: 用户消息
            history_context: 历史对话上下文
            
        Returns:
            dict: 处理结果
        """
        try:
            # 获取检索器
            retriever = get_retriever()
            
            # 检查是否有相关文档
            is_relevant = retriever.is_relevant(message, threshold=0.4)
            
            if not is_relevant:
                print(f"[ChatAgent] ❌ 未找到相关文档，降级为普通对话")
                return await self._process_normal_chat(message, history_context)
            
            # 检索相关文档
            context = retriever.retrieve_with_context(message, top_k=3)
            print(f"[ChatAgent] ✅ 检索到相关文档，上下文长度: {len(context)}字符")
            
            # 构建RAG Prompt
            rag_prompt = f"""你是一个专业的企业助手，基于公司内部文档回答员工问题。

请严格基于以下提供的文档内容回答问题。如果文档中没有相关信息，请明确说明"根据现有文档，我无法回答这个问题"。

## 相关文档内容：
{context}

## 用户问题：
{message}

## 回答要求：
1. 只基于上述文档内容回答，不要编造信息
2. 如果文档中有明确的步骤或流程，请清晰列出
3. 引用文档来源（文件名）
4. 保持回答简洁、专业、友好
5. 如果问题涉及多个方面，分点回答

请开始回答："""
            
            # 调用LLM生成回答
            response = await self.llm.ainvoke(rag_prompt)
            answer = response.content if hasattr(response, 'content') else str(response)
            
            print(f"[ChatAgent] ✅ RAG回答生成完成，长度: {len(answer)}字符")
            
            return {
                "success": True,
                "message": answer,
                "action": "rag_response",
                "rag_used": True,
                "context_length": len(context)
            }
        
        except Exception as e:
            print(f"[ChatAgent] RAG处理失败，降级为普通对话: {e}")
            # 降级为普通对话
            return await self._process_normal_chat(message, history_context)
    
    async def _process_normal_chat(self, message: str, history_context: str = None) -> Dict[str, Any]:
        """
        普通对话模式（不使用RAG）
        
        Args:
            message: 用户消息
            history_context: 历史对话上下文
            
        Returns:
            dict: 处理结果
        """
        # 构建对话提示
        if history_context:
            prompt = f"{self.system_prompt}\n\n【对话历史】\n{history_context}\n\n【当前消息】\n用户: {message}"
        else:
            prompt = f"{self.system_prompt}\n\n用户: {message}"
        
        # 调用LLM生成回复
        response = await self.llm.ainvoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        return {
            "success": True,
            "message": response_text,
            "action": "chat_response",
            "rag_used": False
        }


# 单例模式
_chat_agent = None

def get_chat_agent() -> ChatAgent:
    """获取聊天智能体实例"""
    global _chat_agent
    if _chat_agent is None:
        _chat_agent = ChatAgent()
    return _chat_agent
