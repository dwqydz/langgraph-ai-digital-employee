<template>
  <div class="agent-chat">
    <div class="chat-container">
      <div class="chat-header">
        <h3>🤖 AI 智能助手</h3>
        <p class="chat-subtitle">自然语言交互，智能任务处理</p>
      </div>

      <!-- 聊天消息区域 -->
      <div class="chat-messages" ref="messagesContainer">
        <div
          v-for="(message, index) in messages"
          :key="index"
          class="message-item"
          :class="{ 'user-message': message.type === 'user', 'agent-message': message.type === 'agent' }"
        >
          <div class="message-avatar">
            <span v-if="message.type === 'user'">👤</span>
            <span v-else>🤖</span>
          </div>
          <div class="message-content">
            <div class="message-text" v-html="formatMessage(message.text)"></div>
            <div class="message-time">{{ formatTime(message.timestamp) }}</div>
            <!-- 显示任务类型和执行结果 -->
            <div v-if="message.taskType && message.taskType !== 'chat'" class="message-meta">
              <el-tag size="small" :type="getTaskTypeColor(message.taskType)">
                {{ getTaskTypeName(message.taskType) }}
              </el-tag>
              <span v-if="message.executionResult" class="execution-status">
                {{ message.executionResult.success ? '✅ 执行成功' : '❌ 执行失败' }}
              </span>
            </div>
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
            placeholder="输入您的问题或指令，例如：'帮我创建一个任务：明天开会讨论项目进展'..."
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

    <!-- 任务选择对话框 -->
    <el-dialog
      v-model="showTodoSelectDialog"
      title="📋 请选择要完成的任务"
      width="600px"
      :close-on-click-modal="false"
    >
      <div class="todo-select-list">
        <el-table
          :data="todoCandidates"
          style="width: 100%"
          highlight-current-row
          @current-change="handleTodoSelect"
        >
          <el-table-column label="选择" width="80">
            <template #default="scope">
              <el-radio
                v-model="selectedTodoId"
                :label="scope.row.id"
              >
                &nbsp;
              </el-radio>
            </template>
          </el-table-column>
          <el-table-column prop="title" label="任务标题" min-width="150" />
          <el-table-column prop="due_date" label="截止时间" width="160">
            <template #default="scope">
              {{ formatDueDate(scope.row.due_date) }}
            </template>
          </el-table-column>
          <el-table-column prop="priority" label="优先级" width="100">
            <template #default="scope">
              <el-tag :type="getPriorityType(scope.row.priority)" size="small">
                {{ getPriorityText(scope.row.priority) }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="cancelTodoSelect">取消</el-button>
          <el-button type="primary" @click="confirmTodoComplete" :disabled="!selectedTodoId">
            确认完成
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 功能说明 -->
    <div class="feature-info">
      <el-card class="info-card">
        <template #header>
          <div class="card-header">
            <span>💡 智能功能说明</span>
          </div>
        </template>
        <div class="feature-list">
          <div class="feature-item">
            <strong>📋 待办事项：</strong>
            <span>"帮我创建一个任务：明天开会讨论项目"</span>
          </div>
          <div class="feature-item">
            <strong>📅 会议预订：</strong>
            <span>"预订会议室，明天上午9点到11点"</span>
          </div>
          <div class="feature-item">
            <strong>🌤️ 天气查询：</strong>
            <span>"今天天气怎么样，有什么建议"</span>
          </div>
          <div class="feature-item">
            <strong>💬 智能对话：</strong>
            <span>"你好啊，今天过得怎么样"</span>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script>
import { ElMessage } from 'element-plus'
import { chatWithAgent } from '@/api/modules/agent.js'

export default {
  name: 'Agent',
  components: {
  },
  data() {
    return {
      messages: [
        {
          type: 'agent',
          text: '您好！我是您的AI智能助手。我可以帮您管理待办事项、预订会议室、查询天气信息。请告诉我您需要什么帮助？',
          timestamp: new Date(),
          taskType: null
        }
      ],
      userInput: '',
      isLoading: false,
      sessionId: localStorage.getItem('agent_session_id') || null, // 🔥 记忆组件：Session ID
      quickActions: [
        { key: 'todo', label: '📋 创建任务', text: '帮我创建一个任务：明天上午开项目会议' },
        { key: 'meeting', label: '📅 预订会议', text: '预订会议室，明天上午10点到12点' },
        { key: 'weather', label: '🌤️ 查天气', text: '今天天气怎么样' },
        { key: 'list', label: '📝 查看任务', text: '帮我查看一下我的待办事项' }
      ],
      // 任务选择对话框相关
      showTodoSelectDialog: false,
      todoCandidates: [],
      selectedTodoId: null,
      pendingAction: null // 保存待执行的操作
    }
  },
  mounted() {
    this.scrollToBottom()
    
    // 检查是否有待办选择任务
    const candidatesStr = sessionStorage.getItem('todo_candidates')
    if (candidatesStr) {
      try {
        const candidates = JSON.parse(candidatesStr)
        if (candidates && candidates.length > 0) {
          console.log('[Agent] 从 sessionStorage 加载候选任务:', candidates)
          this.todoCandidates = candidates
          this.selectedTodoId = null
          this.showTodoSelectDialog = true
          
          // 清除 sessionStorage
          sessionStorage.removeItem('todo_candidates')
          
          // 添加提示消息
          this.messages.push({
            type: 'agent',
            text: `找到 ${candidates.length} 个相似任务，请选择要完成的任务：`,
            timestamp: new Date(),
            taskType: 'todo'
          })
        }
      } catch (error) {
        console.error('[Agent] 解析候选任务失败:', error)
      }
    }
  },
  methods: {
    async sendMessage() {
      if (!this.userInput.trim() || this.isLoading) return
      
      // ✅ 输入长度限制
      const MAX_INPUT_LENGTH = 2000
      if (this.userInput.length > MAX_INPUT_LENGTH) {
        ElMessage.warning(`输入内容不能超过${MAX_INPUT_LENGTH}字符`)
        return
      }

      const userMessage = {
        type: 'user',
        text: this.userInput,
        timestamp: new Date()
      }

      this.messages.push(userMessage)
      const currentInput = this.userInput
      this.userInput = ''
      this.isLoading = true

      try {
        // 🔥 发送请求时携带 session_id
        const response = await chatWithAgent(currentInput, this.sessionId)

        if (response.data.code === 200) {
          const result = response.data.data

          // 🔥 更新 Session ID (如果是新生成的)
          if (result.session_id) {
            this.sessionId = result.session_id
            localStorage.setItem('agent_session_id', result.session_id)
          }

          // 添加agent回复（增加安全检查）
          const agentMessage = {
            type: 'agent',
            text: result.response || '抱歉，我没有理解您的问题。',
            timestamp: new Date(),
            taskType: result.task_type,
            executionResult: result.execution_result
          }

          this.messages.push(agentMessage)

          // 检查是否需要选择任务
          console.log('[Agent] 完整响应:', result)
          console.log('[Agent] task_type:', result.task_type)
          console.log('[Agent] execution_result:', result.execution_result)
          console.log('[Agent] action:', result.execution_result?.action)
          
          if (result.task_type === 'todo' && result.execution_result?.action === 'select_todo') {
            console.log('[Agent] ✅ 匹配成功！显示任务选择对话框')
            console.log('[Agent] 候选任务:', result.execution_result.candidates)
            // 显示任务选择对话框
            this.todoCandidates = result.execution_result.candidates || []
            this.selectedTodoId = null
            this.pendingAction = {
              originalInput: currentInput,
              sessionId: this.sessionId
            }
            this.showTodoSelectDialog = true
            console.log('[Agent] showTodoSelectDialog 设置为:', this.showTodoSelectDialog)
            return // 不继续执行后续逻辑
          } else {
            console.log('[Agent] ❌ 条件不匹配，不显示对话框')
          }

          // 如果是todo相关操作，提示用户刷新待办页面
          if (result.task_type === 'todo' && result.execution_result?.success) {
            setTimeout(() => {
              ElMessage.success('任务已创建！请刷新待办事项页面查看')
            }, 1000)
          }
        } else {
          throw new Error(response.data.message || '请求失败')
        }
      } catch (error) {
        console.error('[Agent] 发送消息失败:', error)
        
        // ✅ Session失效处理
        if (error.response?.status === 401 || error.response?.status === 403) {
          ElMessage.error('登录已过期，请重新登录')
          localStorage.removeItem('agent_session_id')
          setTimeout(() => {
            this.$router.push('/login')
          }, 1500)
          return
        }
        
        // ✅ 超时处理
        if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
          ElMessage.warning('请求超时，请检查网络连接后重试')
        } else {
          ElMessage.error('发送消息失败，请稍后重试')
        }

        // 添加错误消息
        this.messages.push({
          type: 'agent',
          text: '抱歉，处理您的请求时出现了错误，请稍后重试。',
          timestamp: new Date(),
          taskType: null
        })
      } finally {
        this.isLoading = false
        this.$nextTick(() => {
          this.scrollToBottom()
        })
      }
    },

    useQuickAction(action) {
      this.userInput = action.text
      this.sendMessage()
    },

    formatMessage(text) {
      if (!text) return ''

      // 简单的文本格式化，将\n转换为<br>
      return text.replace(/\n/g, '<br>')
    },

    formatTime(timestamp) {
      return timestamp.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit'
      })
    },

    getTaskTypeColor(taskType) {
      const colors = {
        todo: 'success',
        meeting: 'primary',
        weather: 'warning',
        chat: 'info'
      }
      return colors[taskType] || 'info'
    },

    getTaskTypeName(taskType) {
      const names = {
        todo: '待办事项',
        meeting: '会议预订',
        weather: '天气查询',
        chat: '智能对话'
      }
      return names[taskType] || '未知'
    },

    scrollToBottom() {
      this.$nextTick(() => {
        if (this.$refs.messagesContainer) {
          this.$refs.messagesContainer.scrollTop = this.$refs.messagesContainer.scrollHeight
        }
      })
    },

    // 任务选择对话框相关方法
    handleTodoSelect(row) {
      if (row) {
        this.selectedTodoId = row.id
      }
    },

    cancelTodoSelect() {
      this.showTodoSelectDialog = false
      this.todoCandidates = []
      this.selectedTodoId = null
      this.pendingAction = null
    },

    async confirmTodoComplete() {
      if (!this.selectedTodoId) return

      try {
        // 调用API完成任务
        const { updateTodoStatus } = await import('@/api/modules/todo')
        const completionTime = new Date().toISOString()
        
        await updateTodoStatus(this.selectedTodoId, 'completed', completionTime)
        
        ElMessage.success('任务已标记为完成！')
        
        // 关闭对话框
        this.showTodoSelectDialog = false
        this.todoCandidates = []
        this.selectedTodoId = null
        this.pendingAction = null
        
        // 在聊天中添加确认消息
        this.messages.push({
          type: 'agent',
          text: '✅ 任务已完成！请刷新待办事项页面查看最新状态。',
          timestamp: new Date(),
          taskType: 'todo',
          executionResult: { success: true }
        })
        
        this.scrollToBottom()
      } catch (error) {
        console.error('完成任务失败:', error)
        ElMessage.error('完成任务失败，请重试')
      }
    },

    // 格式化截止时间
    formatDueDate(dueDate) {
      if (!dueDate) return '无'
      
      try {
        const date = new Date(dueDate)
        if (isNaN(date.getTime())) return '无'
        
        const month = (date.getMonth() + 1).toString().padStart(2, '0')
        const day = date.getDate().toString().padStart(2, '0')
        const hours = date.getHours().toString().padStart(2, '0')
        const minutes = date.getMinutes().toString().padStart(2, '0')
        
        return `${month}-${day} ${hours}:${minutes}`
      } catch (error) {
        return '无'
      }
    },

    // 获取优先级类型
    getPriorityType(priority) {
      const types = {
        'low': 'info',
        'medium': '',
        'high': 'warning',
        'urgent': 'danger'
      }
      return types[priority] || ''
    },

    // 获取优先级文本
    getPriorityText(priority) {
      const texts = {
        'low': '低',
        'medium': '中',
        'high': '高',
        'urgent': '紧急'
      }
      return texts[priority] || priority
    }
  }
}
</script>

<style scoped>
.agent-chat {
  display: flex;
  gap: 20px;
  height: calc(100vh - 120px);
  padding: 20px;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
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

.message-meta {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-top: 8px;
}

.execution-status {
  font-size: 12px;
  color: #67c23a;
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

.feature-info {
  width: 300px;
}

.info-card {
  height: fit-content;
}

.card-header {
  font-weight: bold;
}

.feature-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.feature-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.feature-item strong {
  color: #409eff;
  font-size: 14px;
}

.feature-item span {
  color: #606266;
  font-size: 13px;
  font-style: italic;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .agent-chat {
    flex-direction: column;
    height: auto;
  }

  .feature-info {
    width: 100%;
  }

  .message-item {
    max-width: 90%;
  }
}
</style>