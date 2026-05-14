import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import '@/assets/theme.css' // ✨ 新增：全局主题样式

// 创建Vue应用
const app = createApp(App)

// 使用路由和Element Plus
app.use(router)
app.use(ElementPlus)

// 挂载应用
app.mount('#app')