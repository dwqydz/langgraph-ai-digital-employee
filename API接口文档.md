# AI数字员工系统 - API接口文档

## 文档概述

**项目名称**: AI数字员工系统  
**版本**: v1.0  
**基础URL**: `http://localhost:8080/api`  
**超时时间**: 10秒  
**认证方式**: Bearer Token  

---

## 目录

1. [通用说明](#通用说明)
2. [认证模块](#认证模块)
3. [待办事项模块](#待办事项模块)
4. [会议室预订模块](#会议室预订模块)
5. [天气助手模块](#天气助手模块)
6. [数据字典](#数据字典)
7. [错误码说明](#错误码说明)

---

## 通用说明

### 请求头规范

所有需要认证的接口都需要在请求头中携带Token:

```http
Authorization: Bearer {token}
Content-Type: application/json
```

### 响应格式

所有接口统一返回JSON格式:

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

**字段说明**:
- `code`: 状态码，200表示成功
- `message`: 响应消息
- `data`: 响应数据

### 分页参数

对于列表接口，支持以下分页参数:

| 参数名 | 类型 | 必填 | 说明 | 默认值 |
|--------|------|------|------|--------|
| pageNum | Integer | 否 | 页码，从1开始 | 1 |
| pageSize | Integer | 否 | 每页条数 | 10 |

---

## 认证模块

### 1. 用户登录

**接口地址**: `POST /api/auth/login`

**接口描述**: 用户通过用户名和密码进行登录，获取访问令牌

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| username | String | 是 | 用户名，长度3-20个字符 | admin |
| password | String | 是 | 密码，长度6-20个字符 | 123456 |

**请求示例**:

```json
{
  "username": "admin",
  "password": "123456"
}
```

**响应示例**:

```
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "userInfo": {
      "username": "admin",
      "loginTime": "2025-04-13T10:30:00.000Z"
    }
  }
}
```

**响应字段说明**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| token | String | Session Token，存储在数据库中，默认有效期7天 |
| userInfo | Object | 用户信息对象 |
| userInfo.username | String | 用户名 |
| userInfo.loginTime | String | 登录时间(ISO 8601格式) |

**错误响应**:

```json
{
  "code": 401,
  "message": "用户名或密码错误",
  "data": null
}
```

---

### 2. 用户注册/登录

**接口地址**: `POST /api/auth/register`

**接口描述**: 
- 智能注册接口：如果用户已存在，则直接返回登录信息（自动登录）
- 如果用户不存在，则创建新用户并自动登录
- 简化用户体验，无需区分注册和登录操作

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| username | String | 是 | 用户名，长度3-20个字符 | newuser |
| password | String | 是 | 密码，长度6-20个字符 | 123456 |

**请求示例**:

```json
{
  "username": "newuser",
  "password": "123456"
}
```

**响应示例 - 新用户注册**:

```json
{
  "code": 200,
  "message": "注册成功并已自动登录",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "userInfo": {
      "username": "newuser",
      "loginTime": "2025-04-13T10:30:00.000Z"
    },
    "isNewUser": true
  }
}
```

**响应示例 - 已存在用户自动登录**:

```json
{
  "code": 200,
  "message": "用户已存在,自动登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "userInfo": {
      "username": "admin",
      "loginTime": "2025-04-13T10:30:00.000Z"
    },
    "isNewUser": false
  }
}
```

**响应字段说明**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| token | String | Session Token，存储在数据库中，默认有效期7天 |
| userInfo | Object | 用户信息对象 |
| userInfo.username | String | 用户名 |
| userInfo.loginTime | String | 登录时间(ISO 8601格式) |
| isNewUser | Boolean | 是否为新注册用户（true=新注册，false=已存在用户） |

**错误响应**:

```json
{
  "code": 400,
  "message": "用户名长度必须在3-20个字符之间",
  "data": null
}
```

或

```json
{
  "code": 400,
  "message": "密码长度必须在6-20个字符之间",
  "data": null
}
```

**使用场景**:
1. **首次使用**: 用户输入用户名和密码，系统自动创建账户并登录
2. **再次使用**: 用户输入相同的用户名和密码，系统识别为老用户，直接登录
3. **忘记密码**: 用户只需重新输入用户名和密码，系统会自动登录（如需重置密码可联系管理员）

---

## 待办事项模块

### 3. 获取待办列表

**接口地址**: `GET /api/todo/list`

**接口描述**: 获取当前用户的待办事项列表，支持分页和筛选

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| status | String | 否 | 任务状态筛选：进行中/已完成/已逾期 | 进行中 |
| category | String | 否 | 任务分类筛选：工作/行政/学习/其他 | 工作 |
| pageNum | Integer | 否 | 页码 | 1 |
| pageSize | Integer | 否 | 每页条数 | 10 |

**请求示例**:

```
GET /api/todo/list?status=进行中&category=工作&pageNum=1&pageSize=10
```

**响应示例**:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "id": 1,
        "title": "完成AI数字员工竞标方案",
        "deadline": "2025-04-14",
        "category": "工作",
        "status": "进行中",
        "urgent": true,
        "createTime": "2025-04-10T09:00:00.000Z"
      },
      {
        "id": 2,
        "title": "会议室设备巡检",
        "deadline": "2025-04-15",
        "category": "行政",
        "status": "进行中",
        "urgent": false,
        "createTime": "2025-04-11T10:00:00.000Z"
      }
    ],
    "total": 15,
    "pageNum": 1,
    "pageSize": 10
  }
}
```

**响应字段说明**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| list | Array | 待办事项列表 |
| list[].id | Integer | 任务ID |
| list[].title | String | 任务标题 |
| list[].deadline | String | 截止日期(YYYY-MM-DD格式) |
| list[].category | String | 任务分类：工作/行政/学习/其他 |
| list[].status | String | 任务状态：进行中/已完成/已逾期 |
| list[].urgent | Boolean | 是否紧急 |
| list[].createTime | String | 创建时间(ISO 8601格式) |
| total | Integer | 总记录数 |
| pageNum | Integer | 当前页码 |
| pageSize | Integer | 每页条数 |

---

### 4. 更新任务状态

**接口地址**: `PUT /api/todo/{id}/status`

**接口描述**: 更新指定任务的状态，标记为已完成时需要传入完成时间

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | Integer | 是 | 任务ID |

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| status | String | 是 | 新状态：已完成/已逾期 | 已完成 |
| completionTime | String | 条件 | 完成时间(状态为已完成时必填)，ISO 8601格式 | 2025-04-13T15:30:00.000Z |

**请求示例**:

```json
{
  "status": "已完成",
  "completionTime": "2025-04-13T15:30:00.000Z"
}
```

**响应示例**:

```json
{
  "code": 200,
  "message": "任务状态更新成功",
  "data": {
    "id": 1,
    "title": "完成AI数字员工竞标方案",
    "status": "已完成",
    "completionTime": "2025-04-13T15:30:00.000Z"
  }
}
```

---

### 5. 获取统计数据

**接口地址**: `GET /api/todo/stats`

**接口描述**: 获取待办事项的统计信息，包括完成率和建议

**请求参数**: 无

**响应示例**:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "completionRate": 65,
    "totalCount": 20,
    "completedCount": 13,
    "pendingCount": 5,
    "overdueCount": 2,
    "suggestion": "优先处理逾期任务"
  }
}
```

**响应字段说明**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| completionRate | Integer | 完成率(百分比) |
| totalCount | Integer | 总任务数 |
| completedCount | Integer | 已完成任务数 |
| pendingCount | Integer | 进行中任务数 |
| overdueCount | Integer | 逾期任务数 |
| suggestion | String | 智能建议文本 |

---

### 6. 标记提醒已读

**接口地址**: `PUT /api/reminder/tasks/{id}/read`

**接口描述**: 将即将逾期的提醒任务标记为已读

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | Integer | 是 | 提醒任务ID |

**请求参数**: 无

**响应示例**:

```json
{
  "code": 200,
  "message": "已标记为已读",
  "data": null
}
```

---

## 会议室预订模块

### 7. 获取会议室列表

**接口地址**: `GET /api/meeting/rooms`

**接口描述**: 获取所有可用的会议室列表及其状态

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| available | Boolean | 否 | 是否只查询可用会议室 | true |
| capacity | Integer | 否 | 最小容纳人数 | 10 |

**请求示例**:

```
GET /api/meeting/rooms?available=true&capacity=10
```

**响应示例**:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "rooms": [
      {
        "id": 1,
        "name": "3F 创新厅",
        "capacity": 8,
        "location": "3楼东",
        "available": true,
        "facilities": ["投影仪", "白板", "视频会议系统"]
      },
      {
        "id": 2,
        "name": "5F 董事会",
        "capacity": 20,
        "location": "5楼",
        "available": false,
        "facilities": ["投影仪", "音响系统", "视频会议系统", "录音设备"]
      }
    ]
  }
}
```

**响应字段说明**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| rooms | Array | 会议室列表 |
| rooms[].id | Integer | 会议室ID |
| rooms[].name | String | 会议室名称 |
| rooms[].capacity | Integer | 容纳人数 |
| rooms[].location | String | 位置描述 |
| rooms[].available | Boolean | 是否可预订 |
| rooms[].facilities | Array | 设施列表 |

---

### 8. 获取我的预订记录

**接口地址**: `GET /api/meeting/bookings/my`

**接口描述**: 获取当前用户的会议室预订记录

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| status | String | 否 | 预订状态：预约中/预约完成/预约取消 | 预约中 |
| startDate | String | 否 | 开始日期(YYYY-MM-DD) | 2025-04-01 |
| endDate | String | 否 | 结束日期(YYYY-MM-DD) | 2025-04-30 |
| pageNum | Integer | 否 | 页码 | 1 |
| pageSize | Integer | 否 | 每页条数 | 10 |

**请求示例**:

```
GET /api/meeting/bookings/my?status=预约中&pageNum=1&pageSize=10
```

**响应示例**:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "bookings": [
      {
        "id": 101,
        "roomName": "3F 创新厅",
        "roomId": 1,
        "date": "2025-04-14",
        "timeSlot": "14:00-15:00",
        "status": "预约中",
        "participants": 5,
        "purpose": "项目讨论",
        "createTime": "2025-04-13T10:00:00.000Z"
      }
    ],
    "total": 5,
    "pageNum": 1,
    "pageSize": 10
  }
}
```

**响应字段说明**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| bookings | Array | 预订记录列表 |
| bookings[].id | Integer | 预订ID |
| bookings[].roomName | String | 会议室名称 |
| bookings[].roomId | Integer | 会议室ID |
| bookings[].date | String | 预订日期(YYYY-MM-DD) |
| bookings[].timeSlot | String | 时间段(HH:mm-HH:mm) |
| bookings[].status | String | 状态：预约中/预约完成/预约取消 |
| bookings[].participants | Integer | 参会人数 |
| bookings[].purpose | String | 会议目的 |
| bookings[].createTime | String | 创建时间 |
| total | Integer | 总记录数 |
| pageNum | Integer | 当前页码 |
| pageSize | Integer | 每页条数 |

---

### 9. 预订会议室

**接口地址**: `POST /api/meeting/rooms/{id}/book`

**接口描述**: 预订指定会议室

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | Integer | 是 | 会议室ID |

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| date | String | 是 | 预订日期(YYYY-MM-DD) | 2025-04-15 |
| timeSlot | String | 是 | 时间段(HH:mm-HH:mm) | 14:00-15:00 |
| participants | Integer | 是 | 参会人数 | 5 |
| purpose | String | 否 | 会议目的 | 项目讨论 |

**请求示例**:

```json
{
  "date": "2025-04-15",
  "timeSlot": "14:00-15:00",
  "participants": 5,
  "purpose": "项目讨论"
}
```

**响应示例**:

```json
{
  "code": 200,
  "message": "预订成功",
  "data": {
    "id": 102,
    "roomName": "3F 创新厅",
    "date": "2025-04-15",
    "timeSlot": "14:00-15:00",
    "status": "预约中"
  }
}
```

**错误响应**:

```json
{
  "code": 400,
  "message": "该时间段已被预订",
  "data": null
}
```

---

### 10. 取消预订

**接口地址**: `DELETE /api/meeting/bookings/{id}`

**接口描述**: 取消指定的会议室预订

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | Integer | 是 | 预订ID |

**请求参数**: 无

**响应示例**:

```json
{
  "code": 200,
  "message": "已取消预订，资源已释放",
  "data": null
}
```

---

### 11. NLP智能预订

**接口地址**: `POST /api/meeting/nlp-book`

**接口描述**: 通过自然语言指令智能解析并预订会议室

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| command | String | 是 | 自然语言指令 | 明天下午2点预定3楼小型会议室，时长1小时，参会人数5人 |

**请求示例**:

```json
{
  "command": "明天下午2点预定3楼小型会议室，时长1小时，参会人数5人"
}
```

**响应示例**:

```json
{
  "code": 200,
  "message": "智能解析预订成功",
  "data": {
    "parsedInfo": {
      "date": "2025-04-14",
      "timeSlot": "14:00-15:00",
      "roomName": "3F 创新厅",
      "participants": 5
    },
    "bookingId": 103,
    "status": "预约中"
  }
}
```

**错误响应**:

```json
{
  "code": 400,
  "message": "无法解析预订指令，请提供更详细的信息",
  "data": null
}
```

---

## 天气助手模块

### 12. 获取当前天气

**接口地址**: `GET /api/weather/current`

**接口描述**: 获取指定城市的当前天气信息

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| city | String | 是 | 城市名称 | 上海 |

**请求示例**:

```
GET /api/weather/current?city=上海
```

**响应示例**:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "city": "上海",
    "temp": 22,
    "condition": "多云转晴",
    "humidity": 65,
    "wind": 12,
    "windDirection": "东南风",
    "aqi": 45,
    "updateTime": "2025-04-13T14:00:00.000Z"
  }
}
```

**响应字段说明**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| city | String | 城市名称 |
| temp | Integer | 当前温度(摄氏度) |
| condition | String | 天气状况 |
| humidity | Integer | 湿度(百分比) |
| wind | Integer | 风速(km/h) |
| windDirection | String | 风向 |
| aqi | Integer | 空气质量指数 |
| updateTime | String | 更新时间 |

---

### 13. 获取天气预报

**接口地址**: `GET /api/weather/forecast`

**接口描述**: 获取指定城市的未来天气预报

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| city | String | 是 | 城市名称 | 上海 |
| days | Integer | 否 | 预报天数(1-7) | 7 |

**请求示例**:

```
GET /api/weather/forecast?city=上海&days=7
```

**响应示例**:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "city": "上海",
    "list": [
      {
        "date": "04-13",
        "weekday": "周一",
        "condition": "晴",
        "minTemp": 15,
        "maxTemp": 25,
        "wind": "东南风 3-4级",
        "humidity": 60
      },
      {
        "date": "04-14",
        "weekday": "周二",
        "condition": "多云",
        "minTemp": 16,
        "maxTemp": 24,
        "wind": "东风 2-3级",
        "humidity": 65
      }
    ]
  }
}
```

**响应字段说明**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| city | String | 城市名称 |
| list | Array | 预报列表 |
| list[].date | String | 日期(MM-DD) |
| list[].weekday | String | 星期 |
| list[].condition | String | 天气状况 |
| list[].minTemp | Integer | 最低温度 |
| list[].maxTemp | Integer | 最高温度 |
| list[].wind | String | 风力风向 |
| list[].humidity | Integer | 湿度 |

---

### 14. 获取天气建议

**接口地址**: `GET /api/weather/suggestion`

**接口描述**: 根据天气情况获取个性化建议

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| city | String | 是 | 城市名称 | 上海 |

**请求示例**:

```
GET /api/weather/suggestion?city=上海
```

**响应示例**:

``json
{
  "code": 200,
  "message": "success",
  "data": {
    "city": "上海",
    "advice": "今日有雨带伞，建议室内会议",
    "clothingSuggestion": "建议穿长袖衬衫加薄外套",
    "outdoorActivity": "不适合户外活动",
    "carWash": "不宜洗车",
    "uvIndex": "中等",
    "comfortIndex": "较舒适"
  }
}
```

**响应字段说明**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| city | String | 城市名称 |
| advice | String | 综合建议 |
| clothingSuggestion | String | 穿衣建议 |
| outdoorActivity | String | 户外活动建议 |
| carWash | String | 洗车建议 |
| uvIndex | String | 紫外线指数 |
| comfortIndex | String | 舒适度指数 |

---

## 数据字典

### 任务状态

| 值 | 说明 |
|----|------|
| 进行中 | 任务正在进行中 |
| 已完成 | 任务已完成 |
| 已逾期 | 任务已超过截止日期 |

### 任务分类

| 值 | 说明 |
|----|------|
| 工作 | 工作相关任务 |
| 行政 | 行政事务 |
| 学习 | 学习提升 |
| 其他 | 其他类别 |

### 预订状态

| 值 | 说明 |
|----|------|
| 预约中 | 预订已提交，等待确认 |
| 预约完成 | 预订已确认 |
| 预约取消 | 预订已取消 |

### 天气状况

| 值 | 说明 |
|----|------|
| 晴 | 晴天 |
| 多云 | 多云天气 |
| 阴 | 阴天 |
| 小雨 | 小雨 |
| 阵雨 | 阵雨 |
| 晴转多云 | 晴转多云 |
| 多云转晴 | 多云转晴 |

---

## 错误码说明

### HTTP状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 401 | 未授权，Token无效或过期 |
| 403 | 禁止访问，权限不足 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

### 业务错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| 10001 | 用户名或密码错误 | 检查输入的用户名和密码 |
| 10002 | Token已过期 | 重新登录获取新Token |
| 20001 | 任务不存在 | 检查任务ID是否正确 |
| 20002 | 任务状态不允许此操作 | 确认任务当前状态 |
| 30001 | 会议室不存在 | 检查会议室ID |
| 30002 | 该时间段已被预订 | 选择其他时间段或会议室 |
| 30003 | 无法解析预订指令 | 提供更详细的自然语言指令 |
| 40001 | 城市名称无效 | 检查城市名称是否正确 |
| 40002 | 天气数据获取失败 | 稍后重试或联系管理员 |

---

## 附录

### 注意事项

1. **Token管理**: 
   - Token有效期为24小时
   - Token过期后需重新登录
   - 建议在Token过期前5分钟主动刷新

2. **频率限制**:
   - 同一IP每分钟最多调用100次API
   - 超过限制将返回429状态码

3. **数据缓存**:
   - 天气数据缓存时间为30分钟
   - 会议室状态实时更新

4. **时区说明**:
   - 所有时间字段均使用UTC时间(ISO 8601格式)
   - 前端展示时需转换为本地时区

### 联系方式

如有问题，请联系技术支持团队:
- 邮箱: support@ai-assistant.com
- 电话: 400-xxx-xxxx

---

**文档更新日期**: 2025-04-13  
**文档版本**: v1.0  
**维护团队**: AI数字员工系统开发组
