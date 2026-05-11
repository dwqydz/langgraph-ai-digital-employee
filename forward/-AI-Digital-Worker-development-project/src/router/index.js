import { createRouter, createWebHistory } from 'vue-router'

// 导入页面组件
import Layout from '@/views/Layout.vue'
import Login from '@/views/Login.vue'
import Todo from '@/views/Todo.vue'
import Meeting from '@/views/Meeting.vue'
import Weather from '@/views/Weather.vue'
import Chat from '@/views/Chat.vue'

// 路由配置
const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { title: '登录', requiresAuth: false }
  },
  {
    path: '/',
    component: Layout,
    redirect: '/todo',
    children: [
      {
        path: 'todo',
        name: 'Todo',
        component: Todo,
        meta: { title: '代办事项', icon: '📋' }
      },
      {
        path: 'meeting',
        name: 'Meeting',
        component: Meeting,
        meta: { title: '会议室预约', icon: '📅' }
      },
      {
        path: 'weather',
        name: 'Weather',
        component: Weather,
        meta: { title: '天气助手', icon: '🌤️' }
      },
      {
        path: 'chat',
        name: 'Chat',
        component: Chat,
        meta: { title: '智能对话', icon: '💬' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - AI数字员工系统`
  }
  
  // 如果访问登录页，直接允许访问
  if (to.path === '/login') {
    next()
    return
  }
  
  // 检查是否有token
  const token = localStorage.getItem('token')
  if (!token) {
    // 没有token，跳转到登录页
    next('/login')
  } else {
    // 有token，允许访问
    next()
  }
})

export default router