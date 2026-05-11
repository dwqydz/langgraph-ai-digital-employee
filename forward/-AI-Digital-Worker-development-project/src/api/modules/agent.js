// 智能Agent API模块
import api from '../index.js'

/**
 * 与智能Agent对话
 * @param {string} message - 用户输入消息
 * @param {string|null} sessionId - 会话ID (用于多端互通)
 * @returns {Promise}
 */
export const chatWithAgent = (message, sessionId = null) => {
  return api.post('/agent/chat', { 
    message,
    session_id: sessionId
  })
}

/**
 * 语音对话
 * @param {FormData} formData - 包含音频文件的表单数据
 * @returns {Promise}
 */
export const voiceChatWithAgent = (formData) => {
  return api.post('/agent/voice-chat', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 获取聊天历史
 * @param {string} sessionId - 会话ID
 * @returns {Promise}
 */
export const getChatHistory = (sessionId) => {
  return api.get(`/agent/chat/history/${sessionId}`)
}