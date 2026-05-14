<template>
  <div class="skeleton-container" :style="{ height: height }">
    <!-- 标题骨架 -->
    <div v-if="title" class="skeleton-title">
      <div class="skeleton-line" :style="{ width: titleWidth }"></div>
    </div>
    
    <!-- 内容骨架 -->
    <div class="skeleton-content">
      <div 
        v-for="i in rows" 
        :key="i" 
        class="skeleton-row"
      >
        <div 
          class="skeleton-line" 
          :style="{ 
            width: getLineWidth(i),
            height: lineHeight 
          }"
        ></div>
      </div>
    </div>
    
    <!-- 卡片骨架（可选） -->
    <div v-if="cardCount > 0" class="skeleton-cards">
      <div 
        v-for="i in cardCount" 
        :key="'card-' + i" 
        class="skeleton-card"
      >
        <div class="skeleton-card-header">
          <div class="skeleton-circle"></div>
          <div class="skeleton-line" style="width: 60%"></div>
        </div>
        <div class="skeleton-card-body">
          <div class="skeleton-line" style="width: 100%; margin-bottom: 8px"></div>
          <div class="skeleton-line" style="width: 80%"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  // 容器高度
  height: {
    type: String,
    default: 'auto'
  },
  // 是否显示标题
  title: {
    type: Boolean,
    default: false
  },
  // 标题宽度
  titleWidth: {
    type: String,
    default: '40%'
  },
  // 行数
  rows: {
    type: Number,
    default: 3
  },
  // 行高
  lineHeight: {
    type: String,
    default: '16px'
  },
  // 卡片数量
  cardCount: {
    type: Number,
    default: 0
  }
})

// 生成不同宽度的线条，模拟真实内容
const getLineWidth = (index) => {
  const widths = ['100%', '90%', '85%', '95%', '80%', '75%']
  return widths[index % widths.length]
}
</script>

<style scoped>
.skeleton-container {
  padding: 16px;
  animation: skeleton-fade-in 0.3s ease-out;
}

@keyframes skeleton-fade-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.skeleton-title {
  margin-bottom: 16px;
}

.skeleton-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.skeleton-row {
  width: 100%;
}

.skeleton-line {
  background: linear-gradient(
    90deg,
    #f0f0f0 25%,
    #e0e0e0 50%,
    #f0f0f0 75%
  );
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s ease-in-out infinite;
  border-radius: 4px;
  height: 16px;
}

@keyframes skeleton-loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

.skeleton-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.skeleton-card {
  background: #ffffff;
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #e5e7eb;
}

.skeleton-card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.skeleton-circle {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(
    90deg,
    #f0f0f0 25%,
    #e0e0e0 50%,
    #f0f0f0 75%
  );
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s ease-in-out infinite;
}

.skeleton-card-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
</style>
