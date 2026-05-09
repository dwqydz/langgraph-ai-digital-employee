# AI数字员工 - 智能Agent业务操作指南

## 📋 概述

本文档介绍如何让智能Agent真正执行业务操作,包括:
- ✅ 创建、查询、更新待办事项
- ✅ 查询、预订、取消会议室
- ✅ 查询天气信息
- ✅ 语音输入支持

---

## 🏗️ 架构说明

### 数据流向

```
用户自然语言输入
    ↓
┌─────────────────────┐
│  Agent路由层         │
│  (routers/agent.py) │
└──────────┬──────────┘
           │ 传入 db + user_id
           ↓
┌─────────────────────┐
│  LLM意图识别         │
│  (qwen_llm.py)      │
│  - 识别意图          │
│  - 提取参数          │
└──────────┬──────────┘
           │ 根据意图调用对应crud
           ↓
┌─────────────────────┐
│  CRUD操作层          │
│  (crud/*.py)        │
│  - todo_crud        │
│  - meeting_crud     │
│  - weather_crud     │
└──────────┬──────────┘
           │ 执行数据库操作
           ↓
      数据库持久化
           ↓
      返回执行结果
```

### 关键改进点

**之前(仅识别不执行):**
```python
# qwen_llm.py - 旧版本
def execute_todo_action(self, action, parameters):
    return {"success": True, "message": "模拟数据"}  # ❌ 假执行
```

**现在(真实执行):**
```python
# qwen_llm.py - 新版本
async def execute_todo_action(self, action, parameters, db, user_id):
    todo = await todo_crud.create_todo(db, user_id, ...)  # ✅ 真执行
    return {"success": True, "data": todo}
```

---

## 🚀 快速开始

### 1. 确保环境配置正确

```bash
# 设置通义千问API Key
$env:DASHSCOPE_API_KEY="your-api-key-here"  # Windows PowerShell
export DASHSCOPE_API_KEY="your-api-key-here"  # Linux/Mac
```

### 2. 启动服务

```bash
python ai-project-main.py
```

### 3. 运行测试

```bash
python test_agent_business.py
```

---

## 💡 使用示例

### 示例1: 创建待办事项

#### **用户输入:**
```
"帮我创建一个明天下午3点的项目评审会议待办"
```

#### **系统处理流程:**

1. **意图识别** (LLM):
```json
{
  "intent": "todo",
  "action": "create_todo",
  "parameters": {
    "title": "项目评审会议",
    "due_date": "2026-04-15 15:00",
    "description": "明天下午3点的项目评审"
  },
  "confidence": 0.95
}
```

2. **执行CRUD**:
```python
# qwen_llm.py 调用
todo = await todo_crud.create_todo(
    db=db,
    user_id=current_user_id,
    title="项目评审会议",
    description="明天下午3点的项目评审",
    due_date=datetime(2026, 4, 15, 15, 0),
    priority="medium"
)
```

3. **返回结果**:
```json
{
  "code": 200,
  "message": "处理成功",
  "data": {
    "intent": "todo",
    "action": "create_todo",
    "reply": "好的,已为您创建待办事项:项目评审会议,时间是明天下午3点",
    "data": {
      "success": true,
      "message": "已创建待办: 项目评审会议",
      "data": {
        "id": 123,
        "title": "项目评审会议",
        "status": "pending"
      }
    }
  }
}
```

---

### 示例2: 查询待办列表

#### **用户输入:**
```
"查看我的所有待办事项"
```

#### **执行流程:**

1. **意图识别**: `intent=todo, action=query_todos`

2. **执行CRUD**:
```python
todos = await todo_crud.get_todos_by_user_id(db, user_id)
```

3. **返回结果**:
```json
{
  "data": {
    "success": true,
    "message": "查询到 5 条待办",
    "data": {
      "count": 5,
      "todos": [
        {
          "id": 123,
          "title": "项目评审会议",
          "status": "pending",
          "priority": "medium",
          "due_date": "2026-04-15T15:00:00"
        }
      ]
    }
  }
}
```

---

### 示例3: 更新待办状态

#### **用户输入:**
```
"把第一个待办标记为已完成"
```

#### **执行流程:**

1. **意图识别**: 
   - LLM需要从上下文中获取todo_id
   - 或者用户明确指定: "把待办123标记为已完成"

2. **执行CRUD**:
```python
todo = await todo_crud.get_todo_by_id_and_user(db, todo_id, user_id)
updated_todo = await todo_crud.update_todo_status(db, todo, "completed")
```

3. **返回结果**:
```json
{
  "data": {
    "success": true,
    "message": "已将待办'项目评审会议'标记为completed",
    "data": {
      "id": 123,
      "status": "completed"
    }
  }
}
```

---

### 示例4: 预订会议室

#### **用户输入:**
```
"帮我预订明天下午2点到4点的会议室,需要投影仪,大概10个人"
```

#### **执行流程:**

1. **意图识别**:
```json
{
  "intent": "meeting",
  "action": "book_meeting",
  "parameters": {
    "capacity": 10,
    "start_time": "2026-04-15 14:00",
    "end_time": "2026-04-15 16:00",
    "purpose": "会议"
  }
}
```

2. **执行CRUD**:
```python
# 先查询合适的会议室
rooms = await meeting_crud.get_available_rooms(db)
suitable_room = next((r for r in rooms if r.capacity >= 10), None)

# 检查时间冲突
conflict = await meeting_crud.check_time_conflict(
    db, suitable_room.id, start_time, end_time
)

if not conflict:
    booking = await meeting_crud.create_booking(
        db=db,
        room_id=suitable_room.id,
        user_id=user_id,
        start_time=start_time,
        end_time=end_time,
        purpose="会议",
        status="confirmed"
    )
```

3. **返回结果**:
```json
{
  "data": {
    "success": true,
    "message": "成功预订 A栋301会议室",
    "data": {
      "booking_id": 456,
      "room_name": "A栋301",
      "start_time": "2026-04-15T14:00:00",
      "end_time": "2026-04-15T16:00:00"
    }
  }
}
```

---

### 示例5: 查询天气

#### **用户输入:**
```
"北京今天天气怎么样"
```

#### **执行流程:**

1. **意图识别**: `intent=weather, action=query_weather, parameters={city: "北京"}`

2. **执行CRUD**:
```python
# 先检查缓存
cached = await weather_crud.get_valid_weather_cache(db, "北京", "current")

if cached:
    weather_data = cached.weather_data  # 从缓存读取
else:
    # TODO: 调用真实天气API
    weather_data = {...}  # 模拟数据
```

3. **返回结果**:
```json
{
  "data": {
    "success": true,
    "message": "北京当前天气",
    "data": {
      "city": "北京",
      "temperature": 25.5,
      "weather": "晴",
      "humidity": 60,
      "from_cache": false
    }
  }
}
```

---

## 🔧 API接口详解

### 1. 文本对话接口

**接口:** `POST /api/agent/chat`

**请求:**
```bash
curl -X POST http://localhost:8080/api/agent/chat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "帮我创建一个明天的待办"}'
```

**响应结构:**
```json
{
  "code": 200,
  "message": "处理成功",
  "data": {
    "intent": "todo|meeting|weather|chat",
    "action": "具体操作",
    "parameters": {...},
    "reply": "AI回复文本",
    "data": {
      "success": true/false,
      "message": "执行结果说明",
      "data": {...}  // 具体业务数据
    }
  }
}
```

---

### 2. 语音对话接口

**接口:** `POST /api/agent/voice-chat`

**请求:**
```bash
curl -X POST http://localhost:8080/api/agent/voice-chat \
  -H "Authorization: Bearer <token>" \
  -F "audio=@recording.mp3"
```

**响应:** 同上,额外包含 `recognized_text` 字段

---

## 📊 支持的意图和操作

### 待办事项 (todo)

| 操作 | 用户表达示例 | 必需参数 | 可选参数 |
|------|------------|---------|---------|
| create_todo | "创建明天开会的待办" | title | description, due_date, priority, category |
| query_todos | "查看我的待办" | - | status |
| update_todo | "把待办123标记为完成" | todo_id, status | - |

### 会议室 (meeting)

| 操作 | 用户表达示例 | 必需参数 | 可选参数 |
|------|------------|---------|---------|
| query_rooms | "有哪些可用会议室" | - | capacity |
| book_meeting | "预订明天下午的会议室" | room_id, start_time, end_time | purpose, attendees |
| cancel_booking | "取消预订456" | booking_id | - |
| query_bookings | "查看我的预订" | - | - |

### 天气 (weather)

| 操作 | 用户表达示例 | 必需参数 | 可选参数 |
|------|------------|---------|---------|
| query_weather | "北京天气如何" | city | - |
| query_forecast | "上海未来3天预报" | city | days |

---

## ⚙️ 技术细节

### 1. 时间解析

LLM会自动推断相对时间:

```python
# 用户说"明天下午3点"
# LLM提取: due_date = "2026-04-15 15:00"

# 在execute_todo_action中解析
try:
    due_date = datetime.fromisoformat(due_date_str)
except:
    due_date = datetime.strptime(due_date_str, "%Y-%m-%d %H:%M")
```

### 2. 参数验证

每个操作都会验证必需参数:

```python
if not room_id or not start_time_str or not end_time_str:
    return {
        "success": False,
        "message": "缺少必要参数: room_id, start_time, end_time"
    }
```

### 3. 错误处理

所有异常都会被捕获并返回友好提示:

```python
try:
    # 执行业务逻辑
    ...
except Exception as e:
    return {
        "success": False,
        "message": f"执行失败: {str(e)}"
    }
```

### 4. 事务管理

CRUD操作使用SQLAlchemy异步会话,自动管理事务:

```python
db.add(new_todo)
await db.commit()  # 提交事务
await db.refresh(new_todo)  # 刷新对象
```

---

## 🎯 最佳实践

### 1. 明确的指令

✅ **好:** "帮我创建一个明天上午10点的产品评审会待办,优先级高"  
❌ **差:** "弄个待办"

### 2. 提供完整信息

✅ **好:** "预订A栋301会议室,明天下午2点到4点,讨论项目进度"  
❌ **差:** "订个会议室"

### 3. 分步操作

对于复杂任务,建议分步进行:

```
第1步: "有哪些能容纳20人的会议室?"
第2步: "预订ID为5的会议室,明天下午2点到4点"
```

### 4. 确认执行结果

每次操作后检查返回的 `data.success` 字段:

```javascript
if (response.data.data.success) {
    console.log("操作成功:", response.data.data.message);
} else {
    console.error("操作失败:", response.data.data.message);
}
```

---

## 🐛 常见问题

### Q1: LLM识别错误怎么办?

**A:** 
1. 优化Prompt模板,添加更多示例
2. 降低temperature参数(提高准确性)
3. 使用更明确的表达方式

### Q2: 数据库操作失败?

**A:**
1. 检查数据库连接
2. 查看后端日志
3. 验证user_id是否正确传递

### Q3: 时间解析错误?

**A:**
1. 使用标准格式: "YYYY-MM-DD HH:mm"
2. 避免模糊表达如"过几天"
3. 在Prompt中明确时间格式要求

### Q4: 如何调试?

**A:**
1. 使用 `/api/agent/intent-recognition` 接口单独测试意图识别
2. 查看控制台输出的详细日志
3. 使用 `test_agent_business.py` 进行端到端测试

---

## 📈 性能优化建议

1. **缓存策略**: 天气数据已实现缓存,减少API调用
2. **批量操作**: 避免频繁的小操作,尽量合并
3. **索引优化**: 确保数据库关键字段有索引
4. **异步处理**: 所有IO操作都是异步的,不会阻塞

---

## 🔐 安全注意事项

1. **JWT认证**: 所有业务操作都需要有效的JWT token
2. **用户隔离**: 每个用户只能访问自己的数据
3. **参数校验**: 所有输入都经过严格验证
4. **SQL注入防护**: 使用ORM,避免原始SQL

---

## 🚀 扩展新功能

要添加新的业务模块:

1. **创建crud文件**: `crud/new_module_crud.py`
2. **在qwen_llm.py中添加**:
   - Prompt中说明新模块
   - 添加 `execute_new_module_action` 方法
   - 在 `process_user_request` 中添加分支
3. **更新capabilities接口**: 添加新模块说明

---

## 📞 技术支持

- 📖 API文档: 访问 http://localhost:8080/docs
- 🐛 问题反馈: 查看后端日志
- 💬 使用咨询: 参考本文档示例

---

**祝您使用愉快!🎉**
