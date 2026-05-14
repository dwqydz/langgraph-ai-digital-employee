# 🤖 AI数字员工系统

一个基于 LangGraph + FastAPI + Vue3 的智能助手系统，支持待办管理、会议室预定、天气查询、企业知识库检索等功能，通过自然语言与用户交互。

**最新更新 (2026-05-14)**: 完成前端全面优化与主题统一 - PageHeader组件、路由过渡动画、骨架屏、批量操作、交互动画

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![Vue](https://img.shields.io/badge/Vue-3.x-brightgreen.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ 核心功能

### 🎯 智能任务分类
- 自动识别用户意图（待办、会议、天气等）
- 基于 LLM 的语义理解
- 支持多轮对话上下文

### 📝 待办事项管理
- 自然语言创建/查询/更新待办
- 优先级管理和逾期提醒
- 状态追踪和历史记录

### 🏢 会议室预定
- 智能推荐合适会议室
- 时间冲突检测
- 一键预定和取消

### 🌤️ 天气查询
- 实时天气信息
- 7天天气预报
- 24小时逐时预报
- 基于阿里云 MCP 服务

### 📚 企业知识库检索 (RAG)
- 基于向量数据库的智能检索
- 支持公司政策、流程、制度查询
- ChromaDB 向量存储
- BGE 中文 Embedding 模型（本地部署）
- 混合检索（语义 + 关键词 BM25）
- Cross-Encoder 重排序
- 查询扩展技术
- 智能判断是否需要检索

### 📊 RAGAS 评估系统
- 自动化 RAG 系统质量评估
- 20 个问题的标准测试集
- 6 大评估指标：
  - Context Precision（上下文精确率）
  - Context Recall（上下文召回率）
  - Faithfulness（忠诚度/无幻觉）
  - Answer Relevancy（答案相关性）
  - Answer Similarity（答案相似度）
  - Answer Correctness（答案准确性）
- 持续优化与迭代

### 💬 对话历史
- 完整的对话记录
- 会话管理
- 上下文记忆

### 🚀 系统优化 (2026-05-14)

#### 🎨 前端UI/UX全面优化
- ✅ **PageHeader组件**: 统一的页面头部设计，支持图标、标题、副标题、操作区
- ✅ **路由过渡动画**: 页面切换淡入淡出效果（0.3s平滑过渡）
- ✅ **骨架屏组件**: SkeletonLoader通用加载占位，提升用户体验
- ✅ **批量操作功能**: Todo页面支持全选、批量完成/删除任务
- ✅ **交互动画增强**:
  - Chat页面：消息滑入动画、快捷回复按钮
  - Meeting页面：预订成功脉冲动画、加载状态提示
  - Todo页面：任务完成淡出动画、悬停效果
- ✅ **主题色系统**: 四个核心页面采用不同渐变配色
  - Chat: 紫色系 `#667eea → #764ba2`
  - Todo: 粉色系 `#f093fb → #f5576c`
  - Meeting: 青色系 `#4facfe → #00f2fe`
  - Weather: 橙黄色系 `#fa709a → #fee140`
- ✅ **全局样式规范**: theme.css统一定义颜色、按钮、标签、空状态等样式

#### 🐛 稳定性修复
- ✅ **完成率计算修复**: 修复Todo页面刷新后完成率变为0的竞态条件问题
- ✅ **天气查询修复**: 修复Weather页面切换城市后仍显示旧数据的缓存问题
- ✅ **Session失效检测**: 所有页面添加401/403错误处理和自动跳转登录
- ✅ **输入验证**: 添加输入长度限制、空值检查、异常降级策略
- ✅ **数据加载优化**: 改为串行执行避免竞态条件，确保数据一致性

#### 📊 代码质量提升
- ✅ **组件化**: 创建PageHeader、SkeletonLoader两个可复用组件
- ✅ **响应式设计**: 所有页面支持移动端自适应布局
- ✅ **错误处理**: 完善的try-catch-finally结构和用户友好提示
- ✅ **性能优化**: 骨架屏替代loading spinner，提升感知性能

### 🚀 系统优化 (2026-05-13)
- ✅ **统一响应格式**: 所有API使用Pydantic模型，提高类型安全
- ✅ **中间件系统**: 请求日志、异常处理、审计追踪三层中间件
- ✅ **异常处理**: CRUD层全面异常捕获和回滚机制
- ✅ **日志审计**: 结构化日志输出（控制台 + 文件），支持链路追踪
- ✅ **代码重构**: 消除75+行重复代码，提高可维护性
- ✅ **数据转换工具**: 统一的模型转换函数，DRY原则

## 🛠️ 技术栈

### 后端
- **框架**: FastAPI + Uvicorn
- **AI**: LangGraph + ChatTongyi (通义千问)
- **数据库**: SQLite + SQLAlchemy (异步)
- **向量数据库**: ChromaDB
- **Embedding 模型**: BAAI/bge-base-zh-v1.5 (本地)
- **重排序模型**: BAAI/bge-reranker-base (本地)
- **认证**: Session Token (数据库存储)
- **MCP**: 阿里云通义千问 MCP 服务
- **评估框架**: RAGAS
- **中间件**: 自定义请求日志、异常处理、审计日志

### 前端
- **框架**: Vue 3 + Vite
- **UI**: Element Plus
- **HTTP**: Axios
- **路由**: Vue Router
- **图表**: ECharts

## 📦 快速开始

### 前置要求
- Python 3.9+
- Node.js 16+
- 阿里云 DashScope API Key ([获取地址](https://dashscope.console.aliyun.com/))

### 后端部署

1. **克隆项目**
```bash
git clone https://github.com/your-username/ai-digital-employee.git
cd ai-digital-employee
```

2. **安装依赖**
```bash
pip install -r requirements_llm.txt
```

3. **配置环境变量**
```bash
# 复制环境配置模板
cp .env.example .env

# 编辑 .env 文件，填入你的 API Key 和 JWT 密钥
# DASHSCOPE_API_KEY=your-api-key-here
# JWT_SECRET_KEY=your-secret-key-change-this-in-production
```

4. **启动服务**
```bash
python ai-project-main.py
```

后端服务将在 `http://localhost:8080` 运行

### 前端部署

1. **进入前端目录**
```bash
cd forward/-AI-Digital-Worker-development-project
```

2. **安装依赖**
```bash
npm install
```

3. **启动开发服务器**
```bash
npm run dev
```

前端应用将在 `http://localhost:5173` 运行

## 📁 项目结构

```
project/
├── agent/                  # AI Agent 模块
│   ├── llm.py             # LLM 配置 (ChatTongyi)
│   ├── task_classifier.py # 任务分类器
│   ├── chat_agent.py      # 聊天 Agent (支持RAG)
│   ├── todo_agent.py      # 待办 Agent
│   ├── meeting_agent.py   # 会议 Agent
│   ├── weather_agent.py   # 天气 Agent
│   ├── langgraph_workflow.py # LangGraph 工作流
│   └── memory_manager.py  # 记忆管理 (Redis)
├── RAG/                    # RAG 检索增强生成模块
│   ├── vector_db.py       # 向量数据库管理
│   ├── retriever.py       # 检索器（混合检索+重排序）
│   ├── reranker.py        # Cross-Encoder 重排序
│   ├── query_expansion.py # 查询扩展
│   ├── init_rag.py        # 初始化脚本
│   └── chroma_db/         # ChromaDB 数据存储
├── RAG_eval/               # RAGAS 评估系统
│   ├── ragas_evaluator.py # 评估器核心
│   ├── evaluation_dataset.py # 测试数据集（69个问题）
│   ├── run_eval.py        # 评估运行脚本
│   ├── fix_nan_results.py # NaN修复工具
│   └── results/           # 评估结果（不上传git）
├── DATA/                   # 企业知识库文档 (Markdown格式)
├── routers/               # API 路由
│   ├── agent.py          # Agent 接口
│   ├── todo.py           # 待办接口
│   ├── meeting.py        # 会议接口
│   ├── weather.py        # 天气接口
│   └── auth.py           # 认证接口
├── crud/                  # 数据库操作
├── model/                 # 数据模型
├── schemas/               # Pydantic 模式
├── utils/                 # 工具函数
│   ├── data_converter.py # 数据转换工具 ⭐新增
│   ├── session_auth.py   # Session认证
│   └── auth_utils.py     # 认证工具
├── uploads/               # 文件存储目录 ⭐新增
│   └── avatars/          # 用户头像存储
├── middleware/            # 中间件 ⭐新增
│   └── __init__.py       # 请求日志、异常处理、审计日志
├── prompt/                # Prompt 模板
├── forward/               # 前端项目
│   └── -AI-Digital-Worker-development-project/
│       ├── src/
│       │   ├── components/    # Vue 组件 ⭐新增
│       │   │   ├── PageHeader.vue      # 统一页面头部
│       │   │   ├── SkeletonLoader.vue  # 骨架屏加载组件
│       │   │   └── ReminderButton.vue  # 提醒按钮组件
│       │   ├── views/         # 页面视图
│       │   │   ├── Chat.vue          # 智能对话页面
│       │   │   ├── Todo.vue          # 待办事项页面
│       │   │   ├── Meeting.vue       # 会议室预约页面
│       │   │   ├── Weather.vue       # 天气查询页面
│       │   │   └── Layout.vue        # 布局组件（含路由过渡）
│       │   ├── assets/        # 静态资源
│       │   │   └── theme.css         # 全局主题样式规范 ⭐新增
│       │   └── router/        # 路由配置
├── parttest/              # 测试文件
└── config/                # 配置文件
```

## 🔑 API 文档

启动后端后访问：
- Swagger UI: `http://localhost:8080/docs`
- ReDoc: `http://localhost:8080/redoc`

详细 API 文档请查看 [API接口文档.md](./API接口文档.md)

## 🧪 测试

### 单元测试和集成测试
```bash
# 运行所有测试
cd parttest
python run_tests.py

# 运行单元测试
python -m pytest unit/

# 运行集成测试
python -m pytest integration/
```

### RAGAS 评估
```bash
# 运行 RAGAS 评估（需要安装评估依赖）
pip install -r RAG_eval/requirements_eval.txt

# 启动评估
cd RAG_eval
python run_eval.py

# 查看评估结果
# 结果保存在 RAG_eval/results/ 目录下
```

详细评估说明请查看 [RAG_eval/README.md](./RAG_eval/README.md)

## 📊 系统架构

```
用户 → Vue3 前端 → FastAPI 后端 → LangGraph 工作流
                                    ↓
                            中间件层 (日志/异常/审计)
                                    ↓
                            任务分类器 (LLM)
                            ↓         ↓         ↓
                        待办Agent  会议Agent  天气Agent
                            ↓         ↓         ↓
                        CRUD操作  MCP服务   数据库
                                    ↓
                            RAG检索 (可选)
```

## 🔐 安全说明

- ✅ API 密钥通过环境变量管理
- ✅ `.env` 文件已加入 `.gitignore`
- ✅ 使用 Session Token 进行身份认证（数据库存储）
- ✅ 密码使用 SHA256 哈希存储
- ✅ RAGAS 评估结果不上传到 Git
- ✅ **新增**: 审计日志中间件记录关键操作
- ✅ **新增**: 全局异常处理防止信息泄露
- ⚠️ **DATA/** 目录包含企业内部文档，请根据实际情况决定是否上传
- ⚠️ **RAG/chroma_db/** 目录为向量数据库，已加入 `.gitignore`
- ⚠️ **RAG_eval/results/** 目录为评估结果，已加入 `.gitignore`

**重要**: 请勿将 `.env` 文件或 API 密钥提交到版本控制系统！

## 📝 开发指南

### 添加新的 Agent

1. 在 `agent/` 目录创建新的 Agent 类
2. 在 `prompt/` 目录添加对应的 Prompt 模板
3. 在 `routers/agent.py` 注册新的意图处理
4. 更新 `task_classifier.py` 的意图识别

### 自定义 Prompt

所有 Prompt 模板位于 `prompt/` 目录，可以根据需求调整：
- `task_classifier.txt` - 任务分类提示词
- `todo_agent.txt` - 待办处理提示词
- `meeting_agent.txt` - 会议处理提示词
- `weather_agent.txt` - 天气查询提示词

### 🚀 代码优化说明 (2026-05-13)

本次优化主要包含三个方面：

#### 1. 响应格式统一化
- **新增Pydantic模型**: 15+个响应模型覆盖所有API
- **类型安全**: 所有接口使用强类型定义
- **IDE友好**: 完整的类型提示和自动补全

**示例：**
```python
# 优化前
return {"code": 200, "message": "成功", "data": {...}}

# 优化后
return TodoListResponse(
    code=200,
    message="获取成功",
    data=todo_items
)
```

#### 2. 中间件系统
创建了三个核心中间件：

- **RequestLoggingMiddleware**: 记录所有HTTP请求（方法、路径、耗时、状态码）
- **ExceptionHandlingMiddleware**: 全局异常捕获，返回统一错误格式
- **AuditLoggingMiddleware**: 审计关键操作（登录、注册、数据修改）

**日志示例：**
```
[REQUEST] POST /api/todo/create | status=200 | time=0.045s | client=127.0.0.1 | user=authenticated
[AUDIT] action=POST /api/auth/login | user=anonymous | ip=192.168.1.100 | status=200
```

#### 3. 架构优化
- **数据转换工具**: `utils/data_converter.py` 消除75+行重复代码
- **异常处理**: CRUD层全面try-except + rollback机制
- **日志审计**: 结构化日志输出到控制台和文件

详细优化内容请查看 [OPTIMIZATION_SUMMARY.md](./OPTIMIZATION_SUMMARY.md)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [LangChain](https://github.com/langchain-ai/langchain) - AI 应用开发框架
- [FastAPI](https://fastapi.tiangolo.com/) - 高性能 Web 框架
- [Vue.js](https://vuejs.org/) - 渐进式 JavaScript 框架
- [阿里云通义千问](https://tongyi.aliyun.com/) - LLM 服务
- [Element Plus](https://element-plus.org/) - Vue 3 组件库

## 📧 联系方式

如有问题或建议，欢迎提 Issue 或联系作者。

---

⭐ 如果这个项目对你有帮助，请给个 Star 支持一下！
