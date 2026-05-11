# 📚 RAG 企业知识库检索系统使用指南

## 概述

本系统基于 RAG (Retrieval-Augmented Generation) 技术，实现了企业内部文档的智能检索和问答功能。通过向量数据库存储企业文档，结合大语言模型实现精准的知识检索。

## 架构说明

```
用户提问 → ChatAgent → 关键词检测 → 向量检索 → LLM生成回答
                              ↓
                        ChromaDB向量数据库
                              ↓
                        DATA目录文档库
```

## 快速开始

### 1. 准备知识库文档

将企业文档（Markdown格式）放入 `DATA/` 目录：

```
DATA/
├── 员工手册.md
├── 请假政策.md
├── 会议室管理规定.md
└── ...
```

**支持的格式**：
- ✅ Markdown (.md)
- ✅ PDF (.pdf) - 需要安装 pypdf

### 2. 初始化向量数据库

```bash
cd RAG
python init_rag.py
```

这将：
1. 扫描 `DATA/` 目录下的所有文档
2. 使用 DashScope 文本嵌入模型生成向量
3. 存储到 `RAG/chroma_db/` 目录

**预期输出**：
```
📂 数据目录: C:\Users\...\project\DATA
📄 找到 35 个文档文件
🔄 正在加载文档...
✅ 成功加载 35 个文档
🔪 正在分割文档...
✅ 分割为 355 个文本块
🧠 正在生成向量嵌入...
✅ 向量数据库初始化完成！
📊 统计信息:
   - 文档数量: 35
   - 文本块数量: 355
   - 向量维度: 1536
```

### 3. 启动服务

```bash
# 后端
python ai-project-main.py

# 前端
cd forward\-AI-Digital-Worker-development-project
npm run dev
```

### 4. 测试RAG功能

在Chat页面输入问题，例如：
- "休假政策是什么？"
- "如何申请年假？"
- "会议室预订流程是怎样的？"

系统会自动：
1. 检测到RAG相关关键词
2. 从向量数据库检索相关文档
3. 基于检索结果生成回答

## 技术细节

### 向量数据库

- **引擎**: ChromaDB
- **存储位置**: `RAG/chroma_db/`
- **持久化**: 自动保存，重启后无需重新初始化

### 文本嵌入

- **模型**: DashScope text-embedding-v2
- **维度**: 1536维
- **API**: 阿里云通义千问

### 检索策略

- **相似度算法**: Cosine Similarity
- **返回数量**: Top 3 最相关文档
- **相关性阈值**: 0.4

### RAG触发机制

ChatAgent 内置关键词检测，以下关键词会触发RAG检索：

```python
rag_keywords = [
    "政策", "规定", "流程", "制度", "如何", "怎么", 
    "入职", "离职", "请假", "休假", "薪酬", "福利",
    "招聘", "面试", "培训", "考核", "会议", "报销",
    "远程", "办公", "设备", "系统", "账号"
]
```

## 更新知识库

### 添加新文档

1. 将新文档放入 `DATA/` 目录
2. 重新运行初始化脚本：
   ```bash
   cd RAG
   python init_rag.py
   ```

### 强制重建数据库

如果需要完全重建向量数据库：

```bash
cd RAG
python init_rag.py --force-rebuild
```

这会删除旧的向量数据库并重新构建。

## 故障排查

### 问题1: Directory not found: './DATA'

**原因**: 脚本运行时的工作目录不正确

**解决**: 确保从项目根目录运行：
```bash
cd C:\Users\35264\Desktop\project
python RAG/init_rag.py
```

### 问题2: 未找到相关文档

**可能原因**:
1. 向量数据库未初始化
2. 问题与文档内容不相关
3. 相关性阈值设置过高

**解决**:
1. 检查 `RAG/chroma_db/` 目录是否存在
2. 尝试用不同的方式提问
3. 调整 `retriever.py` 中的 threshold 参数

### 问题3: API Key 错误

**错误信息**: DashScope API key is required

**解决**: 确保 `.env` 文件中配置了正确的 API Key：
```
DASHSCOPE_API_KEY=your-api-key-here
```

## 性能优化建议

1. **文档分块大小**: 当前设置为 1000 字符，可根据文档类型调整
2. **重叠长度**: 当前设置为 200 字符，保持上下文连贯性
3. **Top-K**: 当前返回 3 个文档，可根据需要调整
4. **阈值**: 当前为 0.4，降低可提高召回率但可能降低精度

## 安全注意事项

⚠️ **重要**: 

1. **DATA/ 目录**: 包含企业内部文档，请根据实际情况决定是否上传到公开仓库
2. **RAG/chroma_db/**: 向量数据库文件较大，建议添加到 `.gitignore`
3. **API Key**: 确保 `.env` 文件不被提交到版本控制系统

## 扩展开发

### 自定义关键词

编辑 `agent/chat_agent.py` 中的 `_should_use_rag()` 方法：

```python
def _should_use_rag(self, message: str) -> bool:
    rag_keywords = [
        "政策", "规定", "流程",  # 添加你的关键词
        "你的关键词1", "你的关键词2"
    ]
    # ...
```

### 调整检索参数

编辑 `RAG/retriever.py`：

```python
def retrieve_with_context(self, query: str, top_k: int = 3):
    # 修改 top_k 参数
    docs = self.vector_db.similarity_search(query, k=top_k)
```

### 支持更多文档格式

编辑 `RAG/vector_db.py` 的 `load_documents()` 方法，添加新的文档加载器。

## 相关文件

- `RAG/vector_db.py` - 向量数据库核心逻辑
- `RAG/retriever.py` - 检索器实现
- `RAG/init_rag.py` - 初始化脚本
- `agent/chat_agent.py` - ChatAgent集成RAG
- `DATA/` - 知识库文档目录
- `RAG/chroma_db/` - 向量数据存储

## 参考资料

- [ChromaDB 官方文档](https://docs.trychroma.com/)
- [LangChain RAG 教程](https://python.langchain.com/docs/use_cases/question_answering/)
- [DashScope API 文档](https://help.aliyun.com/zh/dashscope/)

---

如有问题，请提 Issue 或联系开发者。
