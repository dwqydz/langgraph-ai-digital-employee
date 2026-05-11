"""
RAG 向量数据库模块
负责文档加载、分块、嵌入和存储到向量数据库
"""
import os
import hashlib
from typing import List, Dict, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import DashScopeEmbeddings
from dotenv import load_dotenv

load_dotenv()


class VectorDatabase:
    """向量数据库管理类"""
    
    def __init__(self, persist_directory: str = "./RAG/chroma_db"):
        """
        初始化向量数据库
        
        Args:
            persist_directory: ChromaDB持久化目录
        """
        self.persist_directory = persist_directory
        self.collection_name = "company_documents"
        
        # 初始化ChromaDB客户端
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Company documents for RAG"}
        )
        
        # 初始化嵌入模型（使用阿里云DashScope）
        self.embeddings = DashScopeEmbeddings(
            model="text-embedding-v2",
            dashscope_api_key=os.getenv("DASHSCOPE_API_KEY")
        )
        
        # 文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,      # 每个chunk的字符数
            chunk_overlap=50,    # chunk之间的重叠字符数
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        print(f"[VectorDB] 向量数据库初始化完成，当前文档数: {self.collection.count()}")
    
    def _generate_document_id(self, file_path: str, chunk_index: int) -> str:
        """
        生成唯一的文档ID
        
        Args:
            file_path: 文件路径
            chunk_index: chunk索引
            
        Returns:
            唯一ID
        """
        content = f"{file_path}_{chunk_index}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def load_documents_from_directory(self, data_directory: str) -> List:
        """
        从目录加载所有Markdown文档
        
        Args:
            data_directory: 数据目录路径
            
        Returns:
            文档列表
        """
        print(f"[VectorDB] 开始从 {data_directory} 加载文档...")
        
        # 使用DirectoryLoader加载所有.md文件
        loader = DirectoryLoader(
            path=data_directory,
            glob="**/*.md",
            loader_cls=TextLoader,
            loader_kwargs={'encoding': 'utf-8'}
        )
        
        documents = loader.load()
        print(f"[VectorDB] 成功加载 {len(documents)} 个文档")
        
        return documents
    
    def split_documents(self, documents: List) -> List:
        """
        将文档分割成chunks
        
        Args:
            documents: 原始文档列表
            
        Returns:
            分割后的chunks列表
        """
        print(f"[VectorDB] 开始分割文档...")
        
        chunks = self.text_splitter.split_documents(documents)
        print(f"[VectorDB] 文档分割完成，共 {len(chunks)} 个chunks")
        
        return chunks
    
    def add_documents(self, chunks: List, batch_size: int = 100):
        """
        将chunks添加到向量数据库
        
        Args:
            chunks: 文档chunks列表
            batch_size: 批量处理大小
        """
        print(f"[VectorDB] 开始向量化并存储 {len(chunks)} 个chunks...")
        
        # 准备数据
        ids = []
        texts = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            doc_id = self._generate_document_id(
                chunk.metadata.get('source', 'unknown'), 
                i
            )
            ids.append(doc_id)
            texts.append(chunk.page_content)
            
            # 提取元数据
            source_path = chunk.metadata.get('source', '')
            category = self._extract_category(source_path)
            
            metadatas.append({
                "source": source_path,
                "category": category,
                "filename": os.path.basename(source_path),
                "chunk_index": i
            })
        
        # 批量添加（避免API限制）
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i+batch_size]
            batch_texts = texts[i:i+batch_size]
            batch_metadatas = metadatas[i:i+batch_size]
            
            # 生成嵌入
            embeddings = self.embeddings.embed_documents(batch_texts)
            
            # 添加到集合
            self.collection.add(
                ids=batch_ids,
                documents=batch_texts,
                embeddings=embeddings,
                metadatas=batch_metadatas
            )
            
            print(f"[VectorDB] 已处理 {min(i+batch_size, len(ids))}/{len(ids)} 个chunks")
        
        print(f"[VectorDB] ✅ 所有chunks已成功存储到向量数据库")
    
    def _extract_category(self, file_path: str) -> str:
        """
        从文件路径提取分类
        
        Args:
            file_path: 文件路径
            
        Returns:
            分类名称
        """
        # 例如: DATA/入职文件/Welcome.md -> 入职文件
        parts = Path(file_path).parts
        for i, part in enumerate(parts):
            if part == "DATA" and i + 1 < len(parts):
                return parts[i + 1]
        return "其他"
    
    def search(self, query: str, n_results: int = 5, filter_category: str = None) -> List[Dict]:
        """
        搜索相关文档
        
        Args:
            query: 查询文本
            n_results: 返回结果数量
            filter_category: 可选的分类过滤
            
        Returns:
            搜索结果列表
        """
        # 生成查询嵌入
        query_embedding = self.embeddings.embed_query(query)
        
        # 构建过滤条件
        where_filter = None
        if filter_category:
            where_filter = {"category": filter_category}
        
        # 执行相似度搜索
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )
        
        # 格式化结果
        formatted_results = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                formatted_results.append({
                    "content": doc,
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "distance": results['distances'][0][i] if results['distances'] else 0,
                    "relevance_score": 1 - (results['distances'][0][i] / 2) if results['distances'] else 0
                })
        
        return formatted_results
    
    def clear_collection(self):
        """清空集合"""
        print("[VectorDB] 清空向量数据库...")
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "Company documents for RAG"}
        )
        print("[VectorDB] ✅ 向量数据库已清空")
    
    def get_stats(self) -> Dict:
        """获取数据库统计信息"""
        return {
            "total_documents": self.collection.count(),
            "collection_name": self.collection_name,
            "persist_directory": self.persist_directory
        }


def initialize_rag_database(data_directory: str = None, force_rebuild: bool = False):
    """
    初始化RAG数据库
    
    Args:
        data_directory: 数据目录路径（默认为项目根目录下的DATA文件夹）
        force_rebuild: 是否强制重建（清空现有数据）
        
    Returns:
        VectorDatabase实例
    """
    print("="*60)
    print("🚀 开始初始化RAG向量数据库")
    print("="*60)
    
    # 如果未指定数据目录，使用默认路径
    if data_directory is None:
        import os
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_directory = os.path.join(project_root, "DATA")
        print(f"[VectorDB] 使用默认数据目录: {data_directory}")
    
    # 创建向量数据库实例（使用绝对路径）
    import os
    persist_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
    vector_db = VectorDatabase(persist_directory=persist_directory)
    
    # 如果需要重建，先清空
    if force_rebuild:
        vector_db.clear_collection()
    
    # 检查是否已有数据
    stats = vector_db.get_stats()
    if stats["total_documents"] > 0 and not force_rebuild:
        print(f"[VectorDB] 数据库中已有 {stats['total_documents']} 个文档，跳过加载")
        return vector_db
    
    # 加载文档
    documents = vector_db.load_documents_from_directory(data_directory)
    
    if not documents:
        print("[VectorDB] ⚠️ 未找到任何文档，请检查数据目录")
        return vector_db
    
    # 分割文档
    chunks = vector_db.split_documents(documents)
    
    # 添加到数据库
    vector_db.add_documents(chunks)
    
    # 打印统计信息
    final_stats = vector_db.get_stats()
    print("="*60)
    print(f"✅ RAG数据库初始化完成！")
    print(f"   - 总文档数: {final_stats['total_documents']}")
    print(f"   - 数据存储位置: {final_stats['persist_directory']}")
    print("="*60)
    
    return vector_db


if __name__ == "__main__":
    # 测试代码
    db = initialize_rag_database(data_directory="./DATA", force_rebuild=True)
    
    # 测试搜索
    print("\n" + "="*60)
    print("🔍 测试搜索功能")
    print("="*60)
    
    test_queries = [
        "如何申请休假？",
        "公司的薪酬政策是什么？",
        "新员工入职流程"
    ]
    
    for query in test_queries:
        print(f"\n查询: {query}")
        results = db.search(query, n_results=3)
        print(f"找到 {len(results)} 个相关文档:")
        for i, result in enumerate(results, 1):
            print(f"  {i}. [{result['metadata'].get('category', 'N/A')}] {result['metadata'].get('filename', 'N/A')}")
            print(f"     相关性: {result['relevance_score']:.2f}")
            print(f"     内容预览: {result['content'][:100]}...")
