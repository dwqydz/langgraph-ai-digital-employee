<template>
  <div class="chat-page">
    <div class="chat-container">
      <div class="chat-header">
        <h3>💬 AI 智能对话</h3>
        <p class="chat-subtitle">随时随地，畅聊无限</p>
      </div>

      <!-- 聊天消息区域 -->
      <div class="chat-messages" ref="messagesContainer">
        <div v-if="messages.length === 0" class="empty-state">
          <div class="empty-icon">🤖</div>
          <p>开始与AI助手对话吧！</p>
          <p class="empty-hint">您可以问我任何问题，或者随便聊聊</p>
        </div>

        <div
          v-for="(message, index) in messages"
          :key="index"
          class="message-item"
          :class="{ 'user-message': message.role === 'user', 'agent-message': message.role === 'assistant' }"
        >
          <div class="message-avatar">
            <span v-if="message.role === 'user'">👤</span>
            <span v-else>🤖</span>
          </div>
          <div class="message-content">
            <div class="message-text" v-html="formatMessage(message.content)"></div>
            
            <!-- 会议室推荐卡片容器（分页展示） -->
            <div v-if="message.recommendedRooms && message.recommendedRooms.length > 0" class="meeting-carousel">
              <div class="carousel-header">
                <span class="carousel-title">🏢 找到 {{ message.recommendedRooms.length }} 个可用会议室</span>
                <span class="carousel-hint">第 {{ getMeetingPage(message) + 1 }}/{{ getTotalPages(message) }} 页</span>
              </div>
              
              <div class="carousel-container">
                <div 
                  v-for="(room, index) in getCurrentPageRooms(message)" 
                  :key="room.id" 
                  class="carousel-card"
                  :class="{ 'selected': message.selectedRoomIndex === (getMeetingPage(message) * 3 + index) }"
                  @click="selectRoom(message, getMeetingPage(message) * 3 + index)"
                >
                  <div class="card-badge" v-if="message.selectedRoomIndex === (getMeetingPage(message) * 3 + index)">✓</div>
                  <div class="card-content">
                    <h4 class="room-name">{{ room.room_name }}</h4>
                    <div class="room-info">
                      <p>📍 {{ room.location || '未指定' }}</p>
                      <p>👥 {{ room.capacity }}人</p>
                      <p v-if="room.equipment">🔧 {{ room.equipment }}</p>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- 分页控制 -->
              <div class="carousel-pagination" v-if="getTotalPages(message) > 1">
                <el-button 
                  size="small" 
                  @click="prevMeetingPage(message)"
                  :disabled="getMeetingPage(message) === 0"
                >
                  ← 上一页
                </el-button>
                <span class="page-indicator">{{ getMeetingPage(message) + 1 }} / {{ getTotalPages(message) }}</span>
                <el-button 
                  size="small" 
                  @click="nextMeetingPage(message)"
                  :disabled="getMeetingPage(message) >= getTotalPages(message) - 1"
                >
                  下一页 →
                </el-button>
              </div>
              
              <!-- 操作按钮 -->
              <div class="carousel-actions">
                <el-button 
                  size="small"
                  @click="cancelRoomSelection(message)"
                >
                  取消
                </el-button>
                <el-button 
                  type="primary" 
                  size="small"
                  @click="confirmRoomBooking(message)"
                  :disabled="message.selectedRoomIndex === undefined || message.selectedRoomIndex === null"
                >
                  确定预约
                </el-button>
              </div>
            </div>
            
            <!-- 待办事项卡片 -->
            <div v-if="message.todoInfo" class="todo-card">
              <div class="card-header">
                <span class="todo-title">✅ {{ message.todoInfo.title }}</span>
              </div>
              <div class="card-body">
                <p v-if="message.todoInfo.due_date">⏰ 截止时间: {{ formatTodoDate(message.todoInfo.due_date) }}</p>
                <p v-if="message.todoInfo.priority">🎯 优先级: {{ getPriorityText(message.todoInfo.priority) }}</p>
                <p v-if="message.todoInfo.description">📝 {{ message.todoInfo.description }}</p>
              </div>
            </div>
            
            <div class="message-time">{{ formatTime(message.created_at || message.timestamp) }}</div>
          </div>
        </div>

        <!-- 加载中指示器 -->
        <div v-if="isLoading" class="message-item agent-message">
          <div class="message-avatar">🤖</div>
          <div class="message-content">
            <div class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="chat-input">
        <div class="input-container">
          <el-input
            v-model="userInput"
            placeholder="输入您的问题或想法..."
            @keyup.enter="sendMessage"
            :disabled="isLoading"
            clearable
          >
            <template #suffix>
              <el-button
                type="primary"
                @click="sendMessage"
                :loading="isLoading"
                :disabled="!userInput.trim()"
              >
                发送
              </el-button>
            </template>
          </el-input>
        </div>

        <!-- 快捷指令 -->
        <div class="quick-actions">
          <el-button
            v-for="action in quickActions"
            :key="action.key"
            size="small"
            @click="useQuickAction(action)"
            :disabled="isLoading"
          >
            {{ action.label }}
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { chatWithAgent } from '@/api/modules/agent'

const messages = ref([])
const userInput = ref('')
const isLoading = ref(false)
const messagesContainer = ref(null)
const sessionId = ref(localStorage.getItem('agent_session_id') || null)

const quickActions = [
  { key: 'greet', label: '👋 打个招呼', text: '你好' },
  { key: 'help', label: '❓ 你能做什么', text: '你能帮我什么' },
  { key: 'joke', label: '😄 讲个笑话', text: '给我讲个笑话' },
  { key: 'weather', label: '🌤️ 查天气', text: '今天天气怎么样' }
]

// 加载历史消息
const loadHistory = async () => {
  if (!sessionId.value) return
  
  try {
    const { getChatHistory } = await import('@/api/modules/agent')
    const result = await getChatHistory(sessionId.value)
    
    messages.value = result.messages.map(msg => ({
      role: msg.role,
      content: msg.content,
      created_at: msg.created_at
    }))
    
    scrollToBottom()
  } catch (error) {
    console.error('加载历史失败:', error)
  }
}

// 发送消息
const sendMessage = async () => {
  if (!userInput.value.trim() || isLoading.value) return

  const userMessage = {
    role: 'user',
    content: userInput.value,
    timestamp: new Date()
  }

  messages.value.push(userMessage)
  const currentInput = userInput.value
  userInput.value = ''
  isLoading.value = true

  try {
    const result = await chatWithAgent(currentInput, sessionId.value)

    // 更新 Session ID
    if (result.session_id) {
      sessionId.value = result.session_id
      localStorage.setItem('agent_session_id', result.session_id)
    }

    // 构建消息对象
    const agentMessage = {
      role: 'assistant',
      content: result.response,
      timestamp: new Date()
    }

    // 解析会议室推荐数据
    if (result.task_type === 'meeting' && result.execution_result) {
      const execResult = result.execution_result
      
      // 如果有推荐的会议室
      if (execResult.recommended_rooms && execResult.recommended_rooms.length > 0) {
        agentMessage.recommendedRooms = execResult.recommended_rooms
        agentMessage.selectedRoomIndex = null // 初始未选择
        agentMessage.currentMeetingPage = 0 // 初始页码
        agentMessage.bookingInfo = {
          date: execResult.booking_date,
          start_time: execResult.start_time,
          end_time: execResult.end_time,
          purpose: execResult.purpose
        }
      }
      
      // 如果有匹配的预订
      if (execResult.matched_bookings && execResult.matched_bookings.length > 0) {
        agentMessage.matchedBookings = execResult.matched_bookings
      }
    }
    
    // 解析待办事项数据
    if (result.task_type === 'todo' && result.execution_result) {
      const execResult = result.execution_result
      
      // 如果创建了待办
      if (execResult.todo_created) {
        agentMessage.todoInfo = {
          title: execResult.title,
          due_date: execResult.due_date,
          priority: execResult.priority,
          description: execResult.description
        }
      }
    }

    messages.value.push(agentMessage)
    scrollToBottom()
  } catch (error) {
    console.error('发送消息失败:', error)
    ElMessage.error('发送消息失败，请重试')

    // 添加错误消息
    messages.value.push({
      role: 'assistant',
      content: '抱歉，处理您的请求时出现了错误，请稍后重试。',
      timestamp: new Date()
    })
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

const useQuickAction = (action) => {
  userInput.value = action.text
  sendMessage()
}

const formatMessage = (text) => {
  if (!text) return ''
  return text.replace(/\n/g, '<br>')
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// 预约会议室
const bookRoom = async (room, bookingInfo) => {
  try {
    // ✅ 添加空值检查
    if (!bookingInfo || !bookingInfo.date || !bookingInfo.start_time || !bookingInfo.end_time) {
      console.error('[Chat] bookingInfo数据不完整:', bookingInfo)
      ElMessage.error('预约信息不完整，请重新选择会议室')
      return
    }
    
    console.log('[Chat] 开始预约:', { room, bookingInfo })
    
    const { quickBookRoom } = await import('@/api/modules/meeting')
    
    // ✅ 复用 Meeting 页面的时间处理逻辑，避免时区问题
    // 将日期和时间字符串解析为 Date 对象
    const [year, month, day] = bookingInfo.date.split('-').map(Number)
    const [startHour, startMinute] = bookingInfo.start_time.split(':').map(Number)
    const [endHour, endMinute] = bookingInfo.end_time.split(':').map(Number)
    
    // 验证解析结果
    if (isNaN(year) || isNaN(month) || isNaN(day) || isNaN(startHour) || isNaN(startMinute)) {
      console.error('[Chat] 时间格式解析失败:', bookingInfo)
      ElMessage.error('时间格式错误，请重新选择会议室')
      return
    }
    
    // 创建本地时间的 Date 对象
    const startDateTime = new Date(year, month - 1, day, startHour, startMinute, 0)
    const endDateTime = new Date(year, month - 1, day, endHour, endMinute, 0)
    
    console.log('[Chat] 转换后的时间:', {
      date: bookingInfo.date,
      start_time: bookingInfo.start_time,
      end_time: bookingInfo.end_time,
      startDateTime: startDateTime.toLocaleString(),
      endDateTime: endDateTime.toLocaleString()
    })
    
    // ✅ 关键修复：不使用 toISOString()，而是手动构造不含时区的 ISO 格式字符串
    // 这样后端接收到的是本地时间，不会再次转换
    const formatDateTime = (date) => {
      const y = date.getFullYear()
      const m = String(date.getMonth() + 1).padStart(2, '0')
      const d = String(date.getDate()).padStart(2, '0')
      const h = String(date.getHours()).padStart(2, '0')
      const min = String(date.getMinutes()).padStart(2, '0')
      const s = String(date.getSeconds()).padStart(2, '0')
      return `${y}-${m}-${d}T${h}:${min}:${s}`
    }
    
    const bookingData = {
      start_time: formatDateTime(startDateTime),
      end_time: formatDateTime(endDateTime),
      purpose: bookingInfo.purpose || '会议'
    }
    
    console.log('[Chat] 发送预约请求:', { roomId: room.id, bookingData })
    
    await quickBookRoom(room.id, bookingData)
    
    ElMessage.success(`✅ 成功预约 ${room.room_name}！`)
    
    // 添加确认消息
    messages.value.push({
      role: 'assistant',
      content: `已成功为您预约 ${room.room_name}！\n时间: ${bookingInfo.date} ${bookingInfo.start_time}-${bookingInfo.end_time}\n用途: ${bookingInfo.purpose || '会议'}`,
      timestamp: new Date()
    })
    
    // 🔥 触发自定义事件，通知其他页面刷新
    window.dispatchEvent(new CustomEvent('meetingBookingUpdated'))
    
    scrollToBottom()
  } catch (error) {
    console.error('预约失败:', error)
    ElMessage.error('预约失败，请重试')
  }
}

// 选择会议室（点击卡片）
const selectRoom = (message, index) => {
  message.selectedRoomIndex = index
}

// 取消选择
const cancelRoomSelection = (message) => {
  message.selectedRoomIndex = null
  ElMessage.info('已取消选择')
}

// 确认预约
const confirmRoomBooking = async (message) => {
  if (message.selectedRoomIndex === null || message.selectedRoomIndex === undefined) {
    ElMessage.warning('请先选择一个会议室')
    return
  }
  
  const selectedRoom = message.recommendedRooms[message.selectedRoomIndex]
  await bookRoom(selectedRoom, message.bookingInfo)
}

// 获取当前页的会议室列表（每页3个）
const getCurrentPageRooms = (message) => {
  const pageSize = 3
  const start = message.currentMeetingPage * pageSize
  const end = start + pageSize
  return message.recommendedRooms.slice(start, end)
}

// 获取总页数
const getTotalPages = (message) => {
  const pageSize = 3
  return Math.ceil(message.recommendedRooms.length / pageSize)
}

// 获取当前页码
const getMeetingPage = (message) => {
  return message.currentMeetingPage || 0
}

// 上一页
const prevMeetingPage = (message) => {
  if (message.currentMeetingPage > 0) {
    message.currentMeetingPage--
  }
}

// 下一页
const nextMeetingPage = (message) => {
  const totalPages = getTotalPages(message)
  if (message.currentMeetingPage < totalPages - 1) {
    message.currentMeetingPage++
  }
}

// 格式化待办日期
const formatTodoDate = (dateStr) => {
  if (!dateStr) return '无'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 获取优先级文本
const getPriorityText = (priority) => {
  const texts = {
    high: '高',
    medium: '中',
    low: '低'
  }
  return texts[priority] || priority
}

onMounted(() => {
  loadHistory()
  
  // 检查是否有来自 NLP 指令的消息
  const nlpChatStr = sessionStorage.getItem('nlp_chat_message')
  if (nlpChatStr) {
    try {
      const chatData = JSON.parse(nlpChatStr)
      
      // 添加用户消息
      messages.value.push({
        role: 'user',
        content: chatData.userMessage,
        timestamp: new Date(chatData.timestamp)
      })
      
      // 添加 AI 回复（包含结构化数据）
      const aiMessage = {
        role: 'assistant',
        content: chatData.aiResponse,
        timestamp: new Date(chatData.timestamp)
      }
      
      // 如果有执行结果，解析结构化数据
      if (chatData.execution_result) {
        const execResult = chatData.execution_result
        
        // 会议室数据
        if (chatData.task_type === 'meeting' && execResult.recommended_rooms) {
          aiMessage.recommendedRooms = execResult.recommended_rooms
          aiMessage.selectedRoomIndex = null // 初始未选择
          aiMessage.currentMeetingPage = 0 // 初始页码
          aiMessage.bookingInfo = {
            date: execResult.booking_date,
            start_time: execResult.start_time,
            end_time: execResult.end_time,
            purpose: execResult.purpose
          }
        }
        
        // 待办数据
        if (chatData.task_type === 'todo' && execResult.todo_created) {
          aiMessage.todoInfo = {
            title: execResult.title,
            due_date: execResult.due_date,
            priority: execResult.priority,
            description: execResult.description
          }
        }
      }
      
      messages.value.push(aiMessage)
      
      // 更新 session_id
      if (chatData.session_id) {
        sessionId.value = chatData.session_id
        localStorage.setItem('agent_session_id', chatData.session_id)
      }
      
      // 清除 sessionStorage
      sessionStorage.removeItem('nlp_chat_message')
      
      scrollToBottom()
    } catch (error) {
      console.error('[Chat] 解析 NLP 消息失败:', error)
    }
  }
})
</script>

<style scoped>
.chat-page {
  height: calc(100vh - 140px);
  padding: 0;
}

.chat-container {
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  height: 100%;
}

.chat-header {
  padding: 20px;
  border-bottom: 1px solid #e4e7ed;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.chat-header h3 {
  margin: 0 0 5px 0;
  font-size: 18px;
}

.chat-subtitle {
  margin: 0;
  font-size: 14px;
  opacity: 0.9;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.empty-state p {
  margin: 8px 0;
  font-size: 16px;
}

.empty-hint {
  font-size: 14px;
  color: #c0c4cc;
}

.message-item {
  display: flex;
  gap: 12px;
  max-width: 80%;
}

.user-message {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.agent-message {
  align-self: flex-start;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}

.user-message .message-avatar {
  background: #409eff;
  color: white;
}

.agent-message .message-avatar {
  background: #f5f5f5;
  border: 2px solid #e4e7ed;
}

.message-content {
  flex: 1;
}

.message-text {
  background: #f5f5f5;
  padding: 12px 16px;
  border-radius: 18px;
  margin-bottom: 4px;
  line-height: 1.5;
}

.user-message .message-text {
  background: #409eff;
  color: white;
}

/* 会议室卡片容器（横向滚动） */
.meeting-carousel {
  margin-top: 12px;
  background: #f8f9fa;
  border-radius: 12px;
  padding: 12px;
  border: 1px solid #e4e7ed;
}

.carousel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding: 0 4px;
}

.carousel-title {
  font-weight: 600;
  color: #303133;
  font-size: 14px;
}

.carousel-hint {
  font-size: 12px;
  color: #909399;
}

.carousel-container {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  padding: 4px;
  margin-bottom: 12px;
  scrollbar-width: thin;
  scrollbar-color: #c0c4cc #f0f0f0;
}

.carousel-container::-webkit-scrollbar {
  height: 6px;
}

.carousel-container::-webkit-scrollbar-track {
  background: #f0f0f0;
  border-radius: 3px;
}

.carousel-container::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 3px;
}

.carousel-container::-webkit-scrollbar-thumb:hover {
  background: #909399;
}

.carousel-card {
  flex: 0 0 200px;
  scroll-snap-align: start;
  background: white;
  border: 2px solid #e4e7ed;
  border-radius: 10px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
  overflow: hidden;
}

.carousel-card:hover {
  border-color: #409eff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
}

.carousel-card.selected {
  border-color: #409eff;
  background: #ecf5ff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.2);
}

.card-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 24px;
  height: 24px;
  background: #409eff;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: bold;
}

.card-content {
  height: 100%;
}

.carousel-card .room-name {
  margin: 0 0 10px 0;
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  line-height: 1.4;
}

.room-info p {
  margin: 6px 0;
  font-size: 12px;
  color: #606266;
  line-height: 1.5;
}

.carousel-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding-top: 8px;
  border-top: 1px solid #e4e7ed;
}

/* 待办事项卡片样式 */
.todo-card {
  background: #f0f9ff;
  border: 1px solid #b3d8ff;
  border-radius: 8px;
  padding: 12px;
  margin-top: 12px;
}

.todo-card .card-header {
  margin-bottom: 8px;
}

.todo-card .todo-title {
  font-weight: 600;
  color: #409eff;
  font-size: 14px;
}

.todo-card .card-body p {
  margin: 4px 0;
  font-size: 13px;
  color: #606266;
}

.message-time {
  font-size: 12px;
  color: #909399;
  margin-left: 16px;
}

.user-message .message-time {
  text-align: right;
  margin-right: 16px;
  margin-left: 0;
}

.chat-input {
  padding: 20px;
  border-top: 1px solid #e4e7ed;
  background: #fafafa;
}

.input-container {
  margin-bottom: 12px;
}

.quick-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background: #f5f5f5;
  border-radius: 18px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #909399;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-10px);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .message-item {
    max-width: 90%;
  }
}
</style>
