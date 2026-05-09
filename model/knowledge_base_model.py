"""
知识库模型
对应数据库中的knowledge_base表
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.db_config import Base


class KnowledgeBase(Base):
    """知识库模型 - 管理FastGPT知识库元信息"""
    
    __tablename__ = "knowledge_base"
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment="知识库ID")
    
    # 外键关联
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="所有者ID")
    
    # 知识库信息
    name = Column(String(200), nullable=False, comment="知识库名称")
    description = Column(Text, comment="描述")
    kb_id = Column(String(100), unique=True, index=True, comment="FastGPT知识库ID")
    is_public = Column(Boolean, default=False, comment="是否公开")
    document_count = Column(Integer, default=0, comment="文档数量")
    status = Column(String(20), default="active", index=True, comment="状态: active-活跃, inactive-停用")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系映射
    owner = relationship("User", backref="knowledge_bases")
    documents = relationship("KnowledgeDocument", back_populates="knowledge_base", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<KnowledgeBase(id={self.id}, name='{self.name}', documents={self.document_count})>"
