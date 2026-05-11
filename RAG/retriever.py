"""
RAG 检索器模块
提供文档检索功能，支持相似度搜索和混合检索
"""
from typing import List, Dict, Optional
from .vector_db import VectorDatabase


class RAGRetriever:
    """RAG检索器"""
    
    def __init__(self, vector_db: VectorDatabase):
        """
        初始化检索器
        
        Args:
            vector_db: 向量数据库实例
        """
        self.vector_db = vector_db
    
    def retrieve(self, 
                 query: str, 
                 top_k: int = 5,
                 filter_category: str = None,
                 min_relevance_score: float = 0.3) -> List[Dict]:
        """
        检索相关文档
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            filter_category: 可选的分类过滤
            min_relevance_score: 最小相关性分数阈值
            
        Returns:
            检索结果列表（按相关性排序）
        """
        # 执行搜索
        results = self.vector_db.search(
            query=query,
            n_results=top_k * 2,  # 多取一些，后续过滤
            filter_category=filter_category
        )
        
        # 过滤低相关性结果
        filtered_results = [
            r for r in results 
            if r.get('relevance_score', 0) >= min_relevance_score
        ]
        
        # 按相关性排序并截取top_k
        sorted_results = sorted(
            filtered_results, 
            key=lambda x: x.get('relevance_score', 0), 
            reverse=True
        )[:top_k]
        
        return sorted_results
    
    def retrieve_with_context(self, 
                              query: str, 
                              top_k: int = 3,
                              include_metadata: bool = True) -> str:
        """
        检索并格式化上下文
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            include_metadata: 是否包含元数据
            
        Returns:
            格式化的上下文字符串
        """
        results = self.retrieve(query, top_k=top_k)
        
        if not results:
            return "未找到相关文档。"
        
        # 构建上下文
        context_parts = []
        for i, result in enumerate(results, 1):
            metadata = result.get('metadata', {})
            category = metadata.get('category', '未知分类')
            filename = metadata.get('filename', '未知文件')
            content = result.get('content', '')
            
            if include_metadata:
                context_parts.append(
                    f"[文档 {i}] ({category}/{filename})\n{content}"
                )
            else:
                context_parts.append(content)
        
        return "\n\n".join(context_parts)
    
    def is_relevant(self, query: str, threshold: float = 0.4) -> bool:
        """
        判断是否有相关文档
        
        Args:
            query: 查询文本
            threshold: 相关性阈值
            
        Returns:
            是否有相关文档
        """
        results = self.retrieve(query, top_k=1, min_relevance_score=threshold)
        return len(results) > 0
    
    def get_categories(self) -> List[str]:
        """获取所有可用的分类"""
        # ChromaDB不直接支持获取唯一值，这里返回预定义的分类
        return [
            "入职文件",
            "就业政策",
            "招聘文件",
            "操作文档",
            "福利和优待"
        ]


# 全局检索器实例（懒加载）
_retriever_instance = None


def get_retriever() -> RAGRetriever:
    """
    获取全局检索器实例（单例模式）
    
    Returns:
        RAGRetriever实例
    """
    global _retriever_instance
    
    if _retriever_instance is None:
        from .vector_db import initialize_rag_database
        # 使用默认参数，自动检测DATA目录
        vector_db = initialize_rag_database()
        _retriever_instance = RAGRetriever(vector_db)
    
    return _retriever_instance


if __name__ == "__main__":
    # 测试代码
    retriever = get_retriever()
    
    print("="*60)
    print("🔍 测试RAG检索器")
    print("="*60)
    
    test_queries = [
        "如何申请年假？",
        "公司的远程工作政策是什么？",
        "新员工需要完成哪些入职手续？",
        "今天的天气怎么样？"  # 这个应该不相关
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"查询: {query}")
        print(f"{'='*60}")
        
        # 检查是否相关
        is_relevant = retriever.is_relevant(query)
        print(f"是否相关: {'✅ 是' if is_relevant else '❌ 否'}")
        
        if is_relevant:
            # 检索文档
            results = retriever.retrieve(query, top_k=3)
            print(f"\n找到 {len(results)} 个相关文档:\n")
            
            for i, result in enumerate(results, 1):
                metadata = result.get('metadata', {})
                print(f"{i}. [{metadata.get('category', 'N/A')}] {metadata.get('filename', 'N/A')}")
                print(f"   相关性: {result.get('relevance_score', 0):.2f}")
                print(f"   内容: {result.get('content', '')[:150]}...")
                print()
            
            # 获取格式化上下文
            context = retriever.retrieve_with_context(query, top_k=2)
            print(f"格式化上下文预览:\n{context[:300]}...")
