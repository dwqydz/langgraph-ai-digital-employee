# 🤖 AI数字员工系统

一个基于 LangChain + Vue3 的智能助手系统，支持待办管理、会议室预定、天气查询等功能，通过自然语言与用户交互。

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

### 💬 对话历史
- 完整的对话记录
- 会话管理
- 上下文记忆

## 🛠️ 技术栈

### 后端
- **框架**: FastAPI + Uvicorn
- **AI**: LangChain + ChatTongyi (通义千问 qwen-plus)
- **数据库**: SQLite + SQLAlchemy (异步)
- **认证**: JWT Token
- **MCP**: 阿里云通义千问 MCP 服务

### 前端
- **框架**: Vue 3 + Vite
- **UI**: Element Plus
- **HTTP**: Axios
- **路由**: Vue Router

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

# 编辑 .env 文件，填入你的 API Key
# DASHSCOPE_API_KEY=your-api-key-here
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
│   ├── todo_agent.py      # 待办 Agent
│   ├── meeting_agent.py   # 会议 Agent
│   ├── weather_agent.py   # 天气 Agent
│   └── langgraph_workflow.py # LangGraph 工作流
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
├── prompt/                # Prompt 模板
├── forward/               # 前端项目
│   └── -AI-Digital-Worker-development-project/
├── parttest/              # 测试文件
└── config/                # 配置文件
```

## 🔑 API 文档

启动后端后访问：
- Swagger UI: `http://localhost:8080/docs`
- ReDoc: `http://localhost:8080/redoc`

详细 API 文档请查看 [API接口文档.md](./API接口文档.md)

## 🧪 测试

```bash
# 运行所有测试
cd parttest
python run_tests.py

# 运行单元测试
python -m pytest unit/

# 运行集成测试
python -m pytest integration/
```

## 📊 系统架构

```
用户 → Vue3 前端 → FastAPI 后端 → LangChain Agent
                                    ↓
                            任务分类器 (LLM)
                            ↓         ↓         ↓
                        待办Agent  会议Agent  天气Agent
                            ↓         ↓         ↓
                        CRUD操作  MCP服务   数据库
```

## 🔐 安全说明

- ✅ API 密钥通过环境变量管理
- ✅ `.env` 文件已加入 `.gitignore`
- ✅ 使用 JWT 进行身份认证
- ✅ 密码使用 SHA256 哈希存储

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
