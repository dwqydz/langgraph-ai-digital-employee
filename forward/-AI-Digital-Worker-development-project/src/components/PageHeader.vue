<template>
  <div class="page-header">
    <div class="header-content">
      <!-- 图标 -->
      <div v-if="icon" class="header-icon" :style="{ background: iconBg }">
        <span>{{ icon }}</span>
      </div>
      
      <!-- 标题区域 -->
      <div class="header-text">
        <h2 class="header-title">{{ title }}</h2>
        <p v-if="subtitle" class="header-subtitle">{{ subtitle }}</p>
      </div>
    </div>
    
    <!-- 右侧操作区（可选） -->
    <div v-if="$slots.actions" class="header-actions">
      <slot name="actions"></slot>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  // 页面图标（emoji或文字）
  icon: {
    type: String,
    default: ''
  },
  // 页面标题
  title: {
    type: String,
    required: true
  },
  // 副标题（可选）
  subtitle: {
    type: String,
    default: ''
  },
  // 图标背景色
  iconBg: {
    type: String,
    default: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
  }
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 28px;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-light);
  transition: all 0.3s ease;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
  transition: transform 0.3s ease;
}

.header-icon:hover {
  transform: scale(1.05) rotate(5deg);
}

.header-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.header-title {
  margin: 0;
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}

.header-subtitle {
  margin: 0;
  font-size: 0.95rem;
  color: var(--text-secondary);
  font-weight: 400;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-header {
    padding: 16px 20px;
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .header-content {
    width: 100%;
  }
  
  .header-actions {
    width: 100%;
    justify-content: flex-end;
  }
  
  .header-title {
    font-size: 1.5rem;
  }
}
</style>
