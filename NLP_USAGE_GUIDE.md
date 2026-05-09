# 统一NLP接口使用说明

## 架构概述

所有自然语言指令通过统一的 `/api/agent/chat` 接口接收,后端自动识别意图并路由到相应的Agent处理。

```
用户输入 → /api/agent/chat → TaskClassifier(分类) → 对应Agent处理 → 返回结果
                                      ↓
                            todo/meeting/weather/chat
```

---

## 会议室NLP功能

### 支持的指令类型

#### 1. 预订会议室 (book)

**示例指令:**
- "明天下午3点预定一个能容纳10人的会议室,需要投影仪"
- "后天上午9点订个小型会议室"
- "下周一A栋3楼找个能坐20人的房间"

**处理流程:**
1. TaskClassifier识别为 `meeting` 类型
2. MeetingAgent解析用户需求(时间、人数、设备、楼层等)
3. 筛选匹配的会议室,计算匹配度
4. 返回推荐列表给前端

**前端展示:**
- 自动跳转到 `/meeting` 页面
- 左侧"可预约会议室"区域显示推荐的会议室(按匹配度排序)
- 每个会议室显示匹配说明和匹配分数
- 用户点击"一键预定"完成预订

---

#### 2. 取消预约 (cancel)

**示例指令:**
- "取消明天D101会议室的预定"
- "退订周五下午的会议"
- "取消我明天的所有预约"

**处理流程:**
1. TaskClassifier识别为 `meeting` 类型
2. MeetingAgent解析取消信息(会议室名称、日期等)
3. 查询用户的预约记录,匹配符合条件的预约
4. 返回待确认的预约列表

**前端展示:**
- 自动跳转到 `/meeting` 页面
- 弹出确认对话框,显示待取消的预约详情
- 用户确认后执行取消操作
- 取消成功后,会议室状态变为"可申请",重新出现在左侧列表

---

#### 3. 完成预约 (complete)

**示例指令:**
- "完成今天的会议室预约"
- "结束D101的会议"
- "标记明天的预约为已完成"

**处理流程:**
1. TaskClassifier识别为 `meeting` 类型
2. MeetingAgent解析完成信息
3. 查询用户的预约记录,匹配符合条件的预约
4. 返回待确认的预约列表

**前端展示:**
- 自动跳转到 `/meeting` 页面
- 弹出确认对话框,显示待完成的预约详情
- 用户确认后执行完成操作
- 完成后,预约状态变为"预约完成",移动到历史记录

---

## 数据传递机制

### Layout.vue → Meeting.vue

使用 **sessionStorage** 传递复杂数据:

```javascript
// Layout.vue - 存储数据
const meetingData = {
  recommended_rooms: result.execution_result.recommended_rooms || [],
  matched_bookings: result.execution_result.matched_bookings || []
}
sessionStorage.setItem('nlp_meeting_data', JSON.stringify(meetingData))
router.push({ path: '/meeting', query: { refresh: true } })

// Meeting.vue - 读取数据
const nlpDataStr = sessionStorage.getItem('nlp_meeting_data')
if (nlpDataStr) {
  const nlpData = JSON.parse(nlpDataStr)
  sessionStorage.removeItem('nlp_meeting_data')  // 清除数据
  
  // 处理推荐的会议室或匹配的预约
  if (nlpData.recommended_rooms.length > 0) {
    // 显示推荐会议室
  }
  if (nlpData.matched_bookings.length > 0) {
    // 显示确认弹窗
  }
}
```

---

## 后端实现细节

### 1. MultiAgentWorkflow (`agent/multi_agent_workflow.py`)

提供统一的 `process()` 接口:

```python
class MultiAgentWorkflow:
    async def process(self, message: str, db: AsyncSession, user_id: int) -> Dict[str, Any]:
        # 初始化LangGraph状态
        initial_state = {
            "message": message,
            "task_type": "",
            "db": db,
            "user_id": user_id,
            "execution_result": {},
            "response": ""
        }
        
        # 执行LangGraph工作流
        result = await self.workflow.ainvoke(initial_state)
        
        return {
            "task_type": result["task_type"],
            "execution_result": result["execution_result"],
            "response": result["response"]
        }
```

### 2. LangGraph工作流 (`agent/langgraph_workflow.py`)

编排智能体节点:

```
[classify_node] → [路由] → [todo|meeting|weather|chat] → [END]
```

**Meeting节点:**
```python
async def meeting_agent_node(state: AgentState) -> AgentState:
    meeting_agent = get_meeting_agent()
    result = await meeting_agent.process(state["message"], state["db"], state["user_id"])
    
    return {
        **state,
        "execution_result": result,
        "response": result.get("message", "")
    }
```

### 3. MeetingAgent (`agent/meeting_agent.py`)

核心处理方法:

```python
async def process(self, message: str, db: AsyncSession, user_id: int) -> Dict:
    # 1. 解析用户指令
    parse_result = await self.parse_command(message)
    
    # 2. 根据意图执行不同操作
    if intent == "book":
        result = await self._handle_booking_intent(db, parse_result, user_id)
    elif intent in ["cancel", "complete"]:
        result = await self._handle_cancel_complete_intent(db, parse_result, user_id, intent)
    
    return result
```

**返回格式:**
```json
{
  "success": true,
  "message": "为您找到3个匹配的会议室",
  "intent": "book",
  "action_type": "book",
  "recommended_rooms": [
    {
      "id": 45,
      "name": "D101",
      "capacity": 10,
      "match_score": 95.5,
      "match_explanation": "✓ 容量10人,满足10人需求; ✓ 设备匹配: 投影仪",
      "suggested_time": {
        "start_time": "2026-04-16T15:00:00",
        "end_time": "2026-04-16T16:00:00",
        "display": "2026-04-16 15:00-16:00"
      }
    }
  ],
  "matched_bookings": []
}
```

---

## API路由

### `/api/agent/chat` (POST)

**请求体:**
```json
{
  "message": "明天下午3点预定一个能容纳10人的会议室,需要投影仪"
}
```

**响应:**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "task_type": "meeting",
    "execution_result": {
      "success": true,
      "message": "为您找到3个匹配的会议室",
      "recommended_rooms": [...],
      "matched_bookings": []
    },
    "response": "为您找到3个匹配的会议室"
  }
}
```

---

## 测试步骤

### 1. 启动后端服务
```bash
cd C:\Users\35264\Desktop\project
python ai-project-main.py
```

### 2. 启动前端服务
```bash
cd C:\Users\35264\Desktop\project\forward\-AI-Digital-Worker-development-project
npm run dev
```

### 3. 访问应用
打开浏览器访问: `http://localhost:5174`

### 4. 测试预订指令
在Layout顶部的全局NLP输入框中输入:
```
明天下午3点预定一个能容纳10人的会议室,需要投影仪
```

**预期结果:**
- 显示加载动画"正在处理您的请求..."
- 提示"✅ 为您找到X个匹配的会议室"
- 自动跳转到 `/meeting` 页面
- 左侧"可预约会议室"区域显示推荐的会议室列表
- 每个会议室显示匹配分数和匹配说明

### 5. 测试取消指令
在Layout顶部的全局NLP输入框中输入:
```
取消明天D101会议室的预定
```

**预期结果:**
- 显示加载动画
- 提示"✅ 找到X个待取消的预约"
- 自动跳转到 `/meeting` 页面
- 弹出确认对话框,显示待取消的预约详情
- 点击"确认取消"后执行取消操作
- 取消成功后,会议室重新出现在左侧列表

---

## 常见问题

### Q1: 为什么使用sessionStorage而不是query参数?

**A:** query参数有长度限制(通常2KB),无法传递复杂的JSON数据。sessionStorage可以存储更大的数据,且只在当前会话有效,不会污染URL。

### Q2: TaskClassifier如何区分todo和meeting?

**A:** 分类规则:
- 明确提到"会议室"、"房间"、"预定会议室" → `meeting`
- 只说"开会"但没有提"会议室" → `todo`(准备会议)
- 表达"需要做某事"的意图 → `todo`

详见: `prompt/task_classifier.txt`

### Q3: 置信度过低会怎样?

**A:** 如果MeetingAgent解析的置信度 < 0.6,会返回错误消息:
```json
{
  "success": false,
  "message": "无法理解您的指令: XXX",
  "recommended_rooms": [],
  "matched_bookings": []
}
```

前端会显示错误提示,但仍然跳转到meeting页面。

### Q4: 如何调整会议室筛选算法?

**A:** 修改 `MeetingAgent.filter_rooms_by_requirements()` 方法中的权重配置:

```python
# 当前权重:
# 1. 容量匹配: 30%
# 2. 设备匹配: 25%
# 3. 楼层匹配: 15%
# 4. 楼栋匹配: 15%
# 5. 会议室类型匹配: 15%
```

可以根据实际需求调整权重比例。

---

## 技术栈

- **后端:** FastAPI + LangGraph + LangChain + SQLAlchemy(异步)
- **前端:** Vue 3 + Element Plus + Axios
- **LLM:** Qwen (通义千问)
- **数据库:** MySQL

---

## 相关文件

- `agent/multi_agent_workflow.py` - 多智能体工作流主入口
- `agent/langgraph_workflow.py` - LangGraph工作流编排
- `agent/meeting_agent.py` - 会议室智能Agent
- `agent/task_classifier.py` - 任务分类器
- `routers/agent.py` - Agent API路由
- `forward/.../src/views/Layout.vue` - 全局NLP输入框
- `forward/.../src/views/Meeting.vue` - 会议室页面
