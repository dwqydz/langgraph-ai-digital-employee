"""
知识库文档模型
对应数据库中的knowledge_documents表
"""
from sqlalchemy import Column, Integer, String, Text, BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.db_config import Base


class KnowledgeDocument(Base):
    """知识库文档模型 - 存储知识库中的文档信息"""
    
    __tablename__ = "knowledge_documents"
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment="文档ID")
    
    # 外键关联
    kb_id = Column(Integer, ForeignKey("knowledge_base.id", ondelete="CASCADE"), nullable=False, index=True, comment="所属知识库ID")
    
    # 文档信息
    title = Column(String(500), nullable=False, comment="文档标题")
    file_name = Column(String(255), comment="原始文件名")
    file_path = Column(String(500), comment="文件存储路径")
    file_type = Column(String(20), comment="文件类型: pdf, docx, txt, md等")
    file_size = Column(BigInteger, comment="文件大小(字节)")
    chunk_count = Column(Integer, default=0, comment="切片数量")
    status = Column(String(20), default="processing", index=True, comment="状态: processing-处理中, indexed-已索引, failed-失败")
    error_message = Column(Text, comment="错误信息")
    indexed_at = Column(DateTime, comment="索引完成时间")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), index=True, comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系映射
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    
    def __repr__(self):
        return f"<KnowledgeDocument(id={self.id}, title='{self.title}', status='{self.status}')>"
