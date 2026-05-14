<template>
  <div class="login-container">
    <!-- 全屏背景区域 -->
    <div class="login-background" ref="backgroundRef">
      <canvas ref="particleCanvas" class="particle-canvas"></canvas>
      <div class="background-overlay">
        <div class="background-content">
          <!-- 时间和问候语 -->
          <div class="time-greeting">
            <div class="current-time">{{ currentTime }}</div>
            <div class="greeting-text">{{ greetingText }}</div>
          </div>
          
          <h1 class="typewriter-title">{{ displayTitle }}<span class="cursor">|</span></h1>
          <p class="fade-in-text">智能协同 · 敏捷办公 · 未来已来</p>
          
          <!-- 系统状态卡片 -->
          <div class="status-cards">
            <div class="status-card" @click="handleCardClick('todo')">
              <div class="card-icon">📋</div>
              <div class="card-info">
                <div class="card-label">待办事项</div>
                <div class="card-value">{{ todoCount }}</div>
              </div>
            </div>
            <div class="status-card" @click="handleCardClick('meeting')">
              <div class="card-icon">📅</div>
              <div class="card-info">
                <div class="card-label">今日会议</div>
                <div class="card-value">{{ meetingCount }}</div>
              </div>
            </div>
            <div class="status-card" @click="handleCardClick('weather')">
              <div class="card-icon">🌤️</div>
              <div class="card-info">
                <div class="card-label">天气状况</div>
                <div class="card-value">{{ weatherStatus }}</div>
              </div>
            </div>
          </div>
          
          <!-- 功能特性轮播 -->
          <div class="feature-list">
            <div 
              v-for="(feature, index) in features" 
              :key="index"
              class="feature-item"
              :class="{ 'active': activeFeatureIndex === index }"
              @mouseenter="pauseFeatureRotation"
              @mouseleave="resumeFeatureRotation"
            >
              <span class="feature-icon">{{ feature.icon }}</span>
              <span>{{ feature.text }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 右侧登录区域（透明覆盖层） -->
    <div class="login-sidebar">
      <div 
        class="login-card" 
        ref="loginCardRef"
        :style="cardStyle"
        @mousemove="handleCardMouseMove"
        @mouseleave="handleCardMouseLeave"
      >
        <div class="login-header">
          <h2>🤖 AI数字员工系统</h2>
          <p class="login-subtitle">智能登录 · 安全访问</p>
        </div>
        
        <el-form 
          ref="loginFormRef" 
          :model="loginForm" 
          :rules="loginRules" 
          class="login-form"
          @submit.prevent="handleLogin"
        >
          <el-form-item prop="username" label="用户名">
            <el-input
              v-model="loginForm.username"
              placeholder="请输入用户名"
              size="large"
              class="animated-input"
              :class="{ 'input-error': usernameError }"
              @focus="handleUsernameFocus"
              @blur="handleUsernameBlur"
            />
            <span v-if="usernameError" class="error-hint">{{ usernameError }}</span>
          </el-form-item>
          
          <el-form-item prop="password" label="密码">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              size="large"
              show-password
              class="animated-input"
              :class="{ 'input-error': passwordError }"
              @keyup.enter="handleLogin"
              @focus="handlePasswordFocus"
              @blur="handlePasswordBlur"
              style="margin-left: 4px;"
            />
            <div v-if="showPasswordStrength" class="password-strength">
              <div class="strength-bar" :style="{ width: passwordStrength + '%', background: strengthColor }"></div>
            </div>
            <span v-if="passwordError" class="error-hint">{{ passwordError }}</span>
          </el-form-item>
          
          <el-form-item>
            <el-button 
              type="primary" 
              size="large" 
              class="login-btn"
              :loading="loading"
              :class="{ 'btn-success': loginSuccess, 'btn-error': loginFailed }"
              @click="handleLogin"
            >
              <span v-if="!loading">{{ loading ? '登录中...' : '登录' }}</span>
              <div v-if="loading" class="btn-progress">
                <div class="progress-fill" :style="{ width: progressWidth + '%' }"></div>
              </div>
            </el-button>
          </el-form-item>
        </el-form>
        
        <div class="login-footer">
          <p>还没有账号？<span class="register-link" @click="showRegisterDialog = true">立即注册</span></p>
        </div>
      </div>
    </div>
    
    <!-- 注册对话框 -->
    <el-dialog
      v-model="showRegisterDialog"
      title="用户注册"
      width="400px"
      :close-on-click-modal="false"
    >
      <el-form 
        ref="registerFormRef" 
        :model="registerForm" 
        :rules="registerRules"
        label-width="80px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="registerForm.username" placeholder="请输入用户名" />
        </el-form-item>
        
        <el-form-item label="密码" prop="password">
          <el-input v-model="registerForm.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>
        
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="registerForm.confirmPassword" type="password" placeholder="请再次输入密码" show-password />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showRegisterDialog = false">取消</el-button>
          <el-button type="primary" @click="handleRegister" :loading="registerLoading">
            {{ registerLoading ? '注册中...' : '注册' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { login, register } from '@/api/modules/auth'

const router = useRouter()
const loginFormRef = ref()
const registerFormRef = ref()
const loading = ref(false)
const showRegisterDialog = ref(false)
const registerLoading = ref(false)

// 粒子动画相关
const backgroundRef = ref(null)
const particleCanvas = ref(null)
let animationId = null
let particles = []

// 打字机效果
const fullTitle = '🤖 AI数字员工系统'
const displayTitle = ref('')
let typewriterIndex = 0
let typewriterTimer = null

// 功能特性轮播
const features = [
  { icon: '📋', text: '智能待办管理' },
  { icon: '📅', text: '会议室预约' },
  { icon: '🌤️', text: '天气助手' }
]
const activeFeatureIndex = ref(0)
let featureInterval = null

// 3D卡片效果
const loginCardRef = ref(null)
const cardRotateX = ref(0)
const cardRotateY = ref(0)

// 表单交互状态
const usernameError = ref('')
const passwordError = ref('')
const showPasswordStrength = ref(false)
const passwordStrength = ref(0)
const loginSuccess = ref(false)
const loginFailed = ref(false)
const progressWidth = ref(0)
let progressInterval = null

// 时间和问候语
const currentTime = ref('')
const greetingText = ref('')
let timeInterval = null

// 系统状态数据
const todoCount = ref(12)
const meetingCount = ref(3)
const weatherStatus = ref('晴朗 24°C')

// 登录表单数据
const loginForm = reactive({
  username: '',
  password: ''
})

// 表单验证规则
const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
  ]
}

// 注册表单数据
const registerForm = reactive({
  username: '',
  password: '',
  confirmPassword: ''
})

// 注册表单验证规则
const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== registerForm.password) {
          callback(new Error('两次输入密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 处理登录
const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  try {
    const valid = await loginFormRef.value.validate()
    if (!valid) return
    
    loading.value = true
    loginSuccess.value = false
    loginFailed.value = false
    startProgressAnimation()
    
    // 调用真实登录API
    const response = await login(loginForm)
    
    // 停止进度条，显示成功
    clearInterval(progressInterval)
    progressWidth.value = 100
    
    // 存储token到localStorage和cookie
    if (response.token) {
      document.cookie = `token=${response.token}; path=/; max-age=604800` // 7天
      localStorage.setItem('token', response.token)
      
      // 存储用户信息到localStorage
      localStorage.setItem('userInfo', JSON.stringify({
        username: loginForm.username,
        loginTime: new Date().toISOString()
      }))
      
      loginSuccess.value = true
      ElMessage.success('登录成功！')
      
      // 延迟跳转，让用户看到成功动画
      setTimeout(() => {
        router.push('/')
      }, 800)
    }
  } catch (error) {
    clearInterval(progressInterval)
    loginFailed.value = true
    ElMessage.error('登录失败：' + (error.response?.data?.detail || error.message || '用户名或密码错误'))
    
    // 抖动效果
    if (loginCardRef.value) {
      loginCardRef.value.style.animation = 'shake 0.5s'
      setTimeout(() => {
        loginCardRef.value.style.animation = ''
      }, 500)
    }
  } finally {
    setTimeout(() => {
      loading.value = false
      loginSuccess.value = false
      loginFailed.value = false
      progressWidth.value = 0
    }, 1000)
  }
}

// 处理注册
const handleRegister = async () => {
  if (!registerFormRef.value) return
  
  try {
    const valid = await registerFormRef.value.validate()
    if (!valid) return
    
    registerLoading.value = true
    
    // 调用注册API
    await register({
      username: registerForm.username,
      password: registerForm.password
    })
    
    ElMessage.success('注册成功！请登录')
    showRegisterDialog.value = false
    
    // 清空表单
    registerForm.username = ''
    registerForm.password = ''
    registerForm.confirmPassword = ''
    
  } catch (error) {
    ElMessage.error('注册失败：' + (error.message || '未知错误'))
  } finally {
    registerLoading.value = false
  }
}

// 计算属性 - 卡片样式
const cardStyle = computed(() => ({
  transform: `perspective(1000px) rotateX(${cardRotateX.value}deg) rotateY(${cardRotateY.value}deg)`,
  transition: 'transform 0.1s ease-out'
}))

// 计算属性 - 密码强度颜色
const strengthColor = computed(() => {
  if (passwordStrength.value < 30) return '#ff4d4f'
  if (passwordStrength.value < 60) return '#faad14'
  if (passwordStrength.value < 80) return '#52c41a'
  return '#1890ff'
})

// 粒子动画初始化
const initParticles = () => {
  const canvas = particleCanvas.value
  if (!canvas) return
  
  const ctx = canvas.getContext('2d')
  canvas.width = window.innerWidth * 0.6
  canvas.height = window.innerHeight
  
  // 创建粒子
  particles = []
  const particleCount = 100
  
  for (let i = 0; i < particleCount; i++) {
    particles.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      size: Math.random() * 2 + 0.5,
      speedX: (Math.random() - 0.5) * 0.8,
      speedY: (Math.random() - 0.5) * 0.8,
      opacity: Math.random() * 0.6 + 0.2,
      color: Math.random() > 0.5 ? '255, 255, 255' : '99, 102, 241'
    })
  }
  
  // 动画循环
  const animate = () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    
    particles.forEach(particle => {
      // 更新位置
      particle.x += particle.speedX
      particle.y += particle.speedY
      
      // 边界检测
      if (particle.x < 0 || particle.x > canvas.width) particle.speedX *= -1
      if (particle.y < 0 || particle.y > canvas.height) particle.speedY *= -1
      
      // 绘制粒子
      ctx.beginPath()
      ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(${particle.color}, ${particle.opacity})`
      ctx.fill()
      
      // 绘制连线
      particles.forEach(otherParticle => {
        const dx = particle.x - otherParticle.x
        const dy = particle.y - otherParticle.y
        const distance = Math.sqrt(dx * dx + dy * dy)
        
        if (distance < 120) {
          ctx.beginPath()
          ctx.moveTo(particle.x, particle.y)
          ctx.lineTo(otherParticle.x, otherParticle.y)
          ctx.strokeStyle = `rgba(${particle.color}, ${0.15 * (1 - distance / 120)})`
          ctx.stroke()
        }
      })
    })
    
    animationId = requestAnimationFrame(animate)
  }
  
  animate()
}

// 打字机效果
const startTypewriter = () => {
  typewriterIndex = 0
  displayTitle.value = ''
  
  const type = () => {
    if (typewriterIndex < fullTitle.length) {
      displayTitle.value += fullTitle.charAt(typewriterIndex)
      typewriterIndex++
      typewriterTimer = setTimeout(type, 100)
    }
  }
  
  type()
}

// 功能特性轮播
const startFeatureRotation = () => {
  featureInterval = setInterval(() => {
    activeFeatureIndex.value = (activeFeatureIndex.value + 1) % features.length
  }, 3000)
}

// 暂停轮播
const pauseFeatureRotation = () => {
  if (featureInterval) {
    clearInterval(featureInterval)
  }
}

// 恢复轮播
const resumeFeatureRotation = () => {
  startFeatureRotation()
}

// 更新时间 and 问候语
const updateTimeAndGreeting = () => {
  const now = new Date()
  const hours = now.getHours()
  const minutes = now.getMinutes()
  const seconds = now.getSeconds()
  
  // 格式化时间
  currentTime.value = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
  
  // 根据时间设置问候语
  if (hours < 6) {
    greetingText.value = '🌙 夜深了，注意休息'
  } else if (hours < 9) {
    greetingText.value = '🌅 早上好，开启美好一天'
  } else if (hours < 12) {
    greetingText.value = '☀️ 上午好，工作效率满满'
  } else if (hours < 14) {
    greetingText.value = '🍜 中午好，记得休息'
  } else if (hours < 18) {
    greetingText.value = '🌤️ 下午好，继续加油'
  } else if (hours < 22) {
    greetingText.value = '🌆 晚上好，辛苦了'
  } else {
    greetingText.value = '🌙 晚安，早点休息'
  }
}

// 卡片点击处理
const handleCardClick = (type) => {
  console.log(`Clicked on ${type} card`)
  // 这里可以添加跳转到对应页面的逻辑
  // 例如：router.push(`/${type}`)
}

// 3D卡片鼠标移动处理
const handleCardMouseMove = (e) => {
  if (!loginCardRef.value) return
  
  const rect = loginCardRef.value.getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top
  
  const centerX = rect.width / 2
  const centerY = rect.height / 2
  
  const rotateX = (y - centerY) / 20
  const rotateY = (centerX - x) / 20
  
  cardRotateX.value = rotateX
  cardRotateY.value = rotateY
}

const handleCardMouseLeave = () => {
  cardRotateX.value = 0
  cardRotateY.value = 0
}

// 表单交互处理
const handleUsernameFocus = () => {
  usernameError.value = ''
}

const handleUsernameBlur = () => {
  if (loginForm.username && loginForm.username.length < 3) {
    usernameError.value = '用户名至少3个字符'
  }
}

const handlePasswordFocus = () => {
  passwordError.value = ''
  showPasswordStrength.value = true
}

const handlePasswordBlur = () => {
  showPasswordStrength.value = false
  if (loginForm.password && loginForm.password.length < 6) {
    passwordError.value = '密码至少6个字符'
  }
}

// 监听密码输入，计算强度
const calculatePasswordStrength = () => {
  const password = loginForm.password
  if (!password) {
    passwordStrength.value = 0
    return
  }
  
  let strength = 0
  if (password.length >= 6) strength += 20
  if (password.length >= 10) strength += 20
  if (/[a-z]/.test(password)) strength += 15
  if (/[A-Z]/.test(password)) strength += 15
  if (/[0-9]/.test(password)) strength += 15
  if (/[^a-zA-Z0-9]/.test(password)) strength += 15
  
  passwordStrength.value = Math.min(strength, 100)
}

// 登录进度条动画
const startProgressAnimation = () => {
  progressWidth.value = 0
  progressInterval = setInterval(() => {
    if (progressWidth.value < 90) {
      progressWidth.value += Math.random() * 10
    }
  }, 200)
}

// 生命周期钩子
onMounted(() => {
  initParticles()
  startTypewriter()
  startFeatureRotation()
  updateTimeAndGreeting()
  
  // 每秒更新时间
  timeInterval = setInterval(updateTimeAndGreeting, 1000)
  
  // 监听密码输入
  const passwordInput = document.querySelector('input[type="password"]')
  if (passwordInput) {
    passwordInput.addEventListener('input', calculatePasswordStrength)
  }
})

onUnmounted(() => {
  if (animationId) {
    cancelAnimationFrame(animationId)
  }
  if (typewriterTimer) {
    clearTimeout(typewriterTimer)
  }
  if (featureInterval) {
    clearInterval(featureInterval)
  }
  if (progressInterval) {
    clearInterval(progressInterval)
  }
  if (timeInterval) {
    clearInterval(timeInterval)
  }
})
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  position: relative;
  overflow: hidden;
}

/* 粒子画布 */
.particle-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
}

/* 全屏背景区域 */
.login-background {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1920&q=80');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  background-attachment: fixed;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding-left: 5%;
  z-index: 1;
}

.background-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  /* 移除所有渐变滤镜，保持背景原色 */
}

.background-content {
  position: relative;
  z-index: 10;
  color: white;
  text-align: left;
  max-width: 450px;
  width: 100%;
  max-height: 90vh;
  padding: 20px;
  overflow-y: auto;
  overflow-x: hidden;
}

/* 时间和问候语 */
.time-greeting {
  margin-bottom: 15px;
  animation: fadeIn 1s ease-out 0.5s both;
}

.current-time {
  font-size: 2.8rem;
  font-weight: 700;
  font-family: 'Courier New', monospace;
  background: linear-gradient(135deg, #ffffff, #60a5fa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-shadow: 0 0 20px rgba(96, 165, 250, 0.5);
  letter-spacing: 2px;
  line-height: 1.2;
}

.greeting-text {
  font-size: 1.1rem;
  margin-top: 8px;
  opacity: 0.9;
  color: rgba(255, 255, 255, 0.85);
}

.background-content h1 {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 12px;
  text-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  background: linear-gradient(135deg, #ffffff, #e0f7fa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  min-height: 4.5rem;
  line-height: 1.3;
}

/* 打字机效果 */
.typewriter-title {
  display: inline-block;
}

.cursor {
  display: inline-block;
  width: 3px;
  height: 1em;
  background: white;
  margin-left: 2px;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* 淡入文本 */
.fade-in-text {
  animation: fadeIn 1s ease-out 1.5s both;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 0.9;
    transform: translateY(0);
  }
}

.background-content p {
  font-size: 1.1rem;
  margin-bottom: 25px;
  opacity: 0.9;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.feature-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
  align-items: flex-start;
  margin-top: 20px;
}

/* 系统状态卡片 */
.status-cards {
  display: flex;
  gap: 12px;
  margin-top: 20px;
  animation: fadeIn 1s ease-out 1s both;
  flex-wrap: wrap;
}

.status-card {
  flex: 1;
  min-width: 120px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 14px 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-card:hover {
  background: rgba(255, 255, 255, 0.15);
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  border-color: rgba(255, 255, 255, 0.4);
}

.status-card:active {
  transform: translateY(-2px);
}

.card-icon {
  font-size: 2rem;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 10px;
}

.card-info {
  flex: 1;
}

.card-label {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 4px;
}

.card-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: white;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 1.1rem;
  opacity: 0.6;
  transition: all 0.5s ease;
  padding: 8px 12px;
  border-radius: 8px;
}

.feature-item.active {
  opacity: 1;
  transform: translateX(10px);
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
}

.feature-item:hover {
  opacity: 1;
  transform: translateX(5px);
}

.feature-icon {
  font-size: 1.4rem;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  padding: 8px;
  backdrop-filter: blur(10px);
}

/* 右侧登录区域（透明覆盖层） */
.login-sidebar {
  position: fixed;
  top: 0;
  right: 0;
  width: 480px;
  height: 100vh;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  z-index: 10;
  border-left: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: -10px 0 40px rgba(0, 0, 0, 0.1);
}

.login-sidebar::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 1px;
  background: linear-gradient(to bottom, transparent, rgba(255, 255, 255, 0.3), transparent);
}

@keyframes float {
  0%, 100% { 
    transform: translateY(10px) rotate(0deg) scale(1); 
    opacity: 0.8;
  }
  33% { 
    transform: translateY(-10px) rotate(1deg) scale(1.02); 
    opacity: 1;
  }
  66% { 
    transform: translateY(5px) rotate(-0.5deg) scale(0.98); 
    opacity: 0.9;
  }
}

.login-card {
  width: 100%;
  max-width: 380px;
  padding: 40px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(30px);
  -webkit-backdrop-filter: blur(30px);
  border-radius: var(--radius-lg);
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.3);
  animation: cardAppear 0.6s ease-out;
  transition: all 0.3s ease;
}

@keyframes cardAppear {
  0% {
    opacity: 0;
    transform: translateX(20px) scale(0.95);
  }
  100% {
    opacity: 1;
    transform: translateX(0) scale(1);
  }
}

/* 卡片抖动效果 */
@keyframes shake {
  0%, 100% { transform: perspective(1000px) rotateX(0deg) rotateY(0deg) translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: perspective(1000px) rotateX(0deg) rotateY(0deg) translateX(-5px); }
  20%, 40%, 60%, 80% { transform: perspective(1000px) rotateX(0deg) rotateY(0deg) translateX(5px); }
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-header h2 {
  margin: 0 0 10px 0;
  font-size: 2rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  background: linear-gradient(135deg, #ffffff, #e0f7fa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.5px;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.login-header p {
  margin: 0;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.9rem;
}

.login-form {
  margin-bottom: 24px;
}

/* 调整表单项样式 */
.login-form .el-form-item {
  margin-bottom: 24px;
  display: flex;
  align-items: center;
}

.login-form .el-form-item__label {
  font-weight: 700;
  color: #00f0ff;
  width: 80px;
  text-align: right;
  margin-right: 12px;
  margin-bottom: 0;
  text-shadow: 
    0 0 10px rgba(0, 240, 255, 0.8),
    0 0 20px rgba(0, 240, 255, 0.6),
    0 2px 4px rgba(0, 0, 0, 0.8);
  letter-spacing: 1px;
}

.login-form .el-form-item__content {
  flex: 1;
  display: flex;
}

.login-form .el-input {
  width: 100%;
}

.login-form .el-input__wrapper {
  border-radius: 8px;
  padding: 0 12px;
  width: 100%;
}

.login-form .el-input__inner {
  padding: 8px 0;
  width: 100%;
}

/* 动画输入框 */
.animated-input {
  transition: all 0.3s ease;
}

.animated-input :deep(.el-input__wrapper) {
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.1);
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.3) inset;
  backdrop-filter: blur(10px);
}

.animated-input :deep(.el-input__inner) {
  color: rgba(255, 255, 255, 0.95);
}

.animated-input :deep(.el-input__inner::placeholder) {
  color: rgba(255, 255, 255, 0.5);
}

.animated-input:focus-within :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.15);
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.6) inset, 0 0 12px rgba(255, 255, 255, 0.3);
  transform: scale(1.02);
}

.animated-input.input-error :deep(.el-input__wrapper) {
  background: rgba(255, 77, 79, 0.1);
  box-shadow: 0 0 0 2px rgba(255, 77, 79, 0.6) inset, 0 0 12px rgba(255, 77, 79, 0.3);
  animation: shake 0.4s;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-5px); }
  75% { transform: translateX(5px); }
}

/* 错误提示 */
.error-hint {
  display: block;
  color: rgba(255, 100, 100, 0.95);
  font-size: 0.75rem;
  margin-top: 4px;
  margin-left: 92px;
  animation: slideDown 0.3s ease;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 密码强度指示器 */
.password-strength {
  height: 3px;
  background: #f0f0f0;
  border-radius: 2px;
  margin-top: 6px;
  margin-left: 92px;
  overflow: hidden;
  animation: slideDown 0.3s ease;
}

.strength-bar {
  height: 100%;
  border-radius: 2px;
  transition: all 0.3s ease;
}

.login-btn {
  width: 100%;
  background: linear-gradient(135deg, #2b6ef0, #1a4bd6);
  border: none;
  border-radius: var(--radius-md);
  font-weight: 600;
  font-size: 1rem;
  letter-spacing: 1px;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  padding: 14px 24px;
  box-shadow: 
    0 4px 15px rgba(43, 110, 240, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.login-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.6s;
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 
    0 8px 25px rgba(43, 110, 240, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
}

.login-btn:hover::before {
  left: 100%;
}

.login-btn:active {
  transform: translateY(0);
  box-shadow: 
    0 2px 8px rgba(43, 110, 240, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

/* 成功状态 */
.login-btn.btn-success {
  background: linear-gradient(135deg, #52c41a, #389e0d);
  animation: successPulse 0.6s ease;
}

@keyframes successPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

/* 失败状态 */
.login-btn.btn-error {
  background: linear-gradient(135deg, #ff4d4f, #cf1322);
  animation: errorShake 0.5s ease;
}

@keyframes errorShake {
  0%, 100% { transform: translateX(0); }
  20% { transform: translateX(-8px); }
  40% { transform: translateX(8px); }
  60% { transform: translateX(-4px); }
  80% { transform: translateX(4px); }
}

/* 进度条 */
.btn-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background: rgba(255, 255, 255, 0.2);
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #fff, #e0f7fa);
  transition: width 0.2s ease;
  box-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
}

.login-footer {
  text-align: center;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
  padding-top: 16px;
}

.login-footer p {
  margin: 0;
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.8rem;
}

.register-link {
  color: rgba(255, 255, 255, 0.9);
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s;
}

.register-link:hover {
  color: #ffffff;
  text-decoration: underline;
  text-shadow: 0 0 8px rgba(255, 255, 255, 0.5);
}

/* 响应式设计 */
@media (max-width: 480px) {
  .login-card {
    padding: 24px;
    margin: 0 16px;
  }
  
  .login-header h2 {
    font-size: 1.5rem;
  }
}

/* 左侧内容响应式 */
@media (max-width: 1200px) {
  .background-content {
    max-width: 380px;
  }
  
  .current-time {
    font-size: 2.2rem;
  }
  
  .background-content h1 {
    font-size: 2rem;
  }
}

@media (max-width: 992px) {
  .login-background {
    padding-left: 3%;
  }
  
  .background-content {
    max-width: 320px;
  }
  
  .status-cards {
    flex-direction: column;
  }
  
  .status-card {
    min-width: auto;
  }
}

/* 自定义滚动条样式 */
.background-content::-webkit-scrollbar {
  width: 6px;
}

.background-content::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}

.background-content::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 3px;
}

.background-content::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.5);
}
</style>