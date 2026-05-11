"""
RAG系统初始化脚本
用于构建和测试RAG向量数据库
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from RAG.vector_db import initialize_rag_database
from RAG.retriever import get_retriever


def main():
    print("="*80)
    print("🚀 RAG系统初始化工具")
    print("="*80)
    
    # 获取项目根目录（RAG目录的父目录）
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_directory = os.path.join(project_root, "DATA")
    
    print(f"\n📂 数据目录: {data_directory}")
    
    # 检查数据目录是否存在
    if not os.path.exists(data_directory):
        print(f"❌ 错误: 数据目录不存在: {data_directory}")
        return 1
    
    # 询问是否重建
    force_rebuild = input("\n是否强制重建向量数据库？(y/n，默认n): ").strip().lower() == 'y'
    
    if force_rebuild:
        print("\n⚠️  警告：这将清空现有数据库并重新索引所有文档！")
        confirm = input("确认继续？(yes/no): ").strip().lower()
        if confirm != 'yes':
            print("操作已取消")
            return
    
    try:
        # 初始化数据库
        print("\n" + "="*80)
        db = initialize_rag_database(data_directory=data_directory, force_rebuild=force_rebuild)
        
        # 显示统计信息
        stats = db.get_stats()
        print(f"\n✅ 数据库状态:")
        print(f"   - 总文档数: {stats['total_documents']}")
        print(f"   - 集合名称: {stats['collection_name']}")
        print(f"   - 存储位置: {stats['persist_directory']}")
        
        # 交互式测试
        print("\n" + "="*80)
        print("🔍 进入测试模式（输入q退出）")
        print("="*80)
        
        retriever = get_retriever()
        
        while True:
            query = input("\n请输入查询: ").strip()
            
            if query.lower() in ['q', 'quit', 'exit']:
                print("\n再见！👋")
                break
            
            if not query:
                continue
            
            # 检查相关性
            is_relevant = retriever.is_relevant(query, threshold=0.4)
            print(f"\n相关性判断: {'✅ 相关' if is_relevant else '❌ 不相关'}")
            
            if is_relevant:
                # 检索文档
                results = retriever.retrieve(query, top_k=3)
                print(f"\n找到 {len(results)} 个相关文档:\n")
                
                for i, result in enumerate(results, 1):
                    metadata = result.get('metadata', {})
                    print(f"{i}. [{metadata.get('category', 'N/A')}] {metadata.get('filename', 'N/A')}")
                    print(f"   相关性分数: {result.get('relevance_score', 0):.2f}")
                    print(f"   内容预览: {result.get('content', '')[:200]}...")
                    print()
                
                # 显示格式化上下文
                context = retriever.retrieve_with_context(query, top_k=2)
                print(f"格式化上下文（前300字符）:\n{context[:300]}...\n")
            else:
                print("\n💡 建议：尝试询问关于公司政策、流程、福利等方面的问题")
                print("   例如：")
                print("   - 公司的请假政策是什么？")
                print("   - 新员工入职需要准备什么？")
                print("   - 如何申请年假？")
        
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
