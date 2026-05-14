<template>
  <div class="weather-page">
    <!-- ✨ 使用统一PageHeader -->
    <PageHeader
      icon="🌤️"
      title="智能天气助手"
      subtitle="实时查询 · 生活建议"
      :icon-bg="'linear-gradient(135deg, #fa709a 0%, #fee140 100%)'"
    >
      <template #actions>
        <el-input 
          v-model="weatherCity" 
          placeholder="输入城市名称" 
          style="width:200px" 
          size="small"
        ></el-input>
        <el-button type="primary" size="small" @click="fetchWeather">查询天气</el-button>
      </template>
    </PageHeader>
    
    <div class="card">
      <div class="grid-2col">
        <div>
          <div v-if="currentWeather" class="weather-card" style="background:linear-gradient(135deg,#e6f4ff,#fff);">
            <h2>{{ currentWeather.city }} <span style="font-size:1.8rem;">{{ currentWeather.temp }}°C</span></h2>
            <p>{{ currentWeather.condition }} | 湿度 {{ currentWeather.humidity }}% | 风速 {{ currentWeather.wind }}km/h</p>
            
            <!-- 智能建议区域 -->
            <div v-if="suggestionData" class="suggestion-box">
              <div class="suggestion-item">
                <strong>🌤️ 生活建议：</strong>
                <span>{{ suggestionData.daily }}</span>
              </div>
              <div class="suggestion-item">
                <strong>🏢 会议建议：</strong>
                <span>{{ suggestionData.meeting }}</span>
              </div>
            </div>
          </div>
        </div>
        <div>
          <h4>📅 未来7天天气预报</h4>
          <div v-if="forecastData.length > 0" class="forecast-list">
            <div v-for="day in forecastData" :key="day.date" class="forecast-item">
              <div class="forecast-date">
                <strong>{{ day.date }}</strong>
                <span class="week-day">{{ day.weekday }}</span>
              </div>
              <div class="forecast-info">
                <span class="weather-condition">{{ day.condition }}</span>
                <span class="temperature-range">{{ day.minTemp }}°C - {{ day.maxTemp }}°C</span>
              </div>
              <div class="weather-icon">
                <span v-if="day.condition.includes('晴')">☀️</span>
                <span v-else-if="day.condition.includes('云')">⛅</span>
                <span v-else-if="day.condition.includes('雨')">🌧️</span>
                <span v-else-if="day.condition.includes('雪')">❄️</span>
                <span v-else>🌤️</span>
              </div>
            </div>
          </div>
          <div v-else class="empty-forecast">
            <p style="text-align: center; color: #909399; padding: 40px 0;">暂无天气预报数据</p>
          </div>
        </div>
      </div>
      
      <!-- 24小时天气预报 -->
      <div class="hourly-section">
        <h4>🕒 24小时内天气</h4>
        <div v-if="hourlyData.length > 0" class="hourly-scroll-container">
          <div v-for="hour in hourlyData" :key="hour.time" class="hourly-item">
            <div class="hourly-time">{{ hour.time }}</div>
            <div class="hourly-icon">
              <span v-if="hour.condition.includes('晴')">☀️</span>
              <span v-else-if="hour.condition.includes('云')">⛅</span>
              <span v-else-if="hour.condition.includes('雨')">🌧️</span>
              <span v-else-if="hour.condition.includes('雪')">❄️</span>
              <span v-else>🌤️</span>
            </div>
            <div class="hourly-temp">{{ hour.temperature }}°C</div>
            <div class="hourly-condition">{{ hour.condition }}</div>
          </div>
        </div>
        <div v-else class="empty-hourly">
          <p style="text-align: center; color: #909399; padding: 20px 0;">暂无24小时预报数据</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { getAllWeather } from '@/api/modules/weather'
import PageHeader from '@/components/PageHeader.vue' // ✨ 新增

// 获取路由对象
const route = useRoute()

// 天气数据
const weatherCity = ref('上海')
const currentWeather = ref(null)
const forecastData = ref([])
const hourlyData = ref([])
const suggestionData = ref({ daily: '', meeting: '' })

// 缓存配置
const CACHE_KEY = 'weather_cache'
const CACHE_EXPIRE_TIME = 30 * 60 * 1000 // 30分钟过期

// 从缓存加载天气数据
const loadFromCache = () => {
  try {
    const cacheStr = sessionStorage.getItem(CACHE_KEY)
    if (!cacheStr) return false
    
    const cache = JSON.parse(cacheStr)
    const now = Date.now()
    
    // 检查是否过期
    if (now - cache.timestamp > CACHE_EXPIRE_TIME) {
      console.log('[Weather] 缓存已过期，清除缓存')
      sessionStorage.removeItem(CACHE_KEY)
      return false
    }
    
    // 恢复数据
    weatherCity.value = cache.city
    currentWeather.value = cache.currentWeather
    forecastData.value = cache.forecastData
    hourlyData.value = cache.hourlyData
    suggestionData.value = cache.suggestionData || { daily: '', meeting: '' }
    
    console.log('[Weather] 从缓存加载数据成功')
    return true
  } catch (error) {
    console.error('[Weather] 缓存加载失败:', error)
    return false
  }
}

// 保存到缓存
const saveToCache = (city, current, forecast, hourly, suggestion) => {
  try {
    const cache = {
      city,
      currentWeather: current,
      forecastData: forecast,
      hourlyData: hourly,
      suggestionData: suggestion,
      timestamp: Date.now()
    }
    sessionStorage.setItem(CACHE_KEY, JSON.stringify(cache))
    console.log('[Weather] 数据已保存到缓存')
  } catch (error) {
    console.error('[Weather] 缓存保存失败:', error)
  }
}

// 获取完整天气信息（一次调用获取所有数据）
const fetchAllWeather = async (date = '今天', forceRefresh = false) => {
  // ✅ 输入验证
  const city = weatherCity.value.trim()
  if (!city) {
    ElMessage.warning('请输入城市名称')
    return
  }
  
  // 如果不是强制刷新，先尝试从缓存加载
  if (!forceRefresh && loadFromCache()) {
    console.log('[Weather] 使用缓存数据，跳过API调用')
    return
  }
  
  try {
    const response = await getAllWeather(city, date)
    
    if (response) {
      // 设置当前天气（增加安全检查）
      if (response.current) {
        currentWeather.value = {
          city: city,
          temp: response.current.temperature || 0,
          condition: response.current.condition || '未知',
          humidity: response.current.humidity || 0,
          wind: response.current.wind_speed || 0,
          suggestion: response.suggestion?.daily || '天气适宜'
        }
      }
      
      // 设置7天预报（增加数组检查）
      if (response.forecast && Array.isArray(response.forecast) && response.forecast.length > 0) {
        forecastData.value = response.forecast.slice(0, 7).map((item, index) => ({
          date: item.date || '',
          weekday: '',
          condition: item.condition || '未知',
          minTemp: item.temperature_low || 0,
          maxTemp: item.temperature_high || 0
        }))
        console.log('[Weather] 7天预报数据:', forecastData.value)
      } else {
        forecastData.value = []
        console.warn('[Weather] 无7天预报数据')
      }
      
      // 设置24小时预报（增加数组检查）
      if (response.hourly && Array.isArray(response.hourly)) {
        hourlyData.value = response.hourly
        console.log('[Weather] 24小时预报数据:', hourlyData.value)
      } else {
        hourlyData.value = []
        console.warn('[Weather] 无24小时预报数据')
      }
      
      // 设置建议（增加fallback）
      if (response.suggestion && typeof response.suggestion === 'object') {
        suggestionData.value = {
          daily: response.suggestion.daily || '暂无生活建议',
          meeting: response.suggestion.meeting || '暂无会议建议'
        }
        console.log('[Weather] 天气建议:', suggestionData.value)
      } else {
        suggestionData.value = {
          daily: '暂无生活建议',
          meeting: '暂无会议建议'
        }
      }
      
      // 保存到缓存
      saveToCache(
        city,
        currentWeather.value,
        forecastData.value,
        hourlyData.value,
        suggestionData.value
      )
    }
  } catch (error) {
    console.error('[Weather] 获取天气失败:', error)
    
    // ✅ 降级策略：尝试使用缓存数据
    if (loadFromCache()) {
      ElMessage.warning('获取最新天气失败，显示缓存数据')
    } else {
      ElMessage.error('天气查询失败，请稍后重试')
      // 清空数据
      currentWeather.value = null
      forecastData.value = []
      hourlyData.value = []
      suggestionData.value = { daily: '', meeting: '' }
    }
  }
}

// 处理从 Agent传来的天气数据
const handleAgentWeatherData = async (agentData) => {
  console.log('[Weather] 接收到Agent天气数据:', agentData)
  
  if (!agentData || !agentData.data) {
    console.warn('[Weather] Agent数据格式不正确')
    return false
  }
  
  const weatherData = agentData.data
  const city = weatherData.city || '上海'
  const date = weatherData.date || '今天'
  
  // 设置城市
  weatherCity.value = city
  
  // 一次性获取完整天气信息（7天预报+24小时预报+建议）
  // 注意：这里强制刷新，因为用户主动查询了新数据
  await fetchAllWeather(date, true)
  
  return true
}

// 生成未来7天的日期和星期
const generateWeekDates = () => {
  const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  const dates = []
  const today = new Date()
  
  for (let i = 0; i < 7; i++) {
    const date = new Date(today)
    date.setDate(today.getDate() + i)
    
    const month = (date.getMonth() + 1).toString().padStart(2, '0')
    const day = date.getDate().toString().padStart(2, '0')
    const weekday = weekdays[date.getDay()]
    
    dates.push({
      date: `${month}-${day}`,
      weekday: weekday
    })
  }
  
  return dates
}

// 获取天气信息
const fetchWeather = async () => {
  // ✅ 输入验证
  const city = weatherCity.value.trim()
  if (!city) {
    ElMessage.warning('请输入城市名称')
    return
  }
  
  try {
    // ✨ 修复：强制刷新，清除旧城市缓存
    sessionStorage.removeItem(CACHE_KEY)
    console.log('[Weather] 清除缓存，查询新城市:', city)
    
    // 使用统一的天气接口，强制刷新
    await fetchAllWeather('今天', true)
    
    ElMessage.success(`✅ 已更新 ${city} 的天气信息`)
  } catch (error) {
    console.error('[Weather] 查询失败:', error)
    
    // ✅ 降级处理：优先使用缓存，其次模拟数据
    if (loadFromCache()) {
      ElMessage.warning('获取最新天气失败，显示缓存数据')
    } else {
      ElMessage.error('获取天气信息失败: ' + (error.message || '未知错误'))
      // 使用模拟数据作为最后的降级方案
      currentWeather.value = {
        city: city,
        temp: Math.floor(Math.random() * 15) + 12,
        condition: '多云转晴',
        humidity: 65,
        wind: 12,
        suggestion: city === '上海' ? '今日有雨带伞，建议室内会议' : '适合户外团建'
      }
      
      // 生成模拟的天气预报数据
      const weekDates = generateWeekDates()
      const conditions = ['晴', '多云', '阴', '小雨', '阵雨', '晴转多云', '多云转晴']
      
      forecastData.value = weekDates.map((dateInfo, index) => ({
        date: dateInfo.date,
        weekday: dateInfo.weekday,
        condition: conditions[index % conditions.length],
        minTemp: Math.floor(Math.random() * 5) + 10,
        maxTemp: Math.floor(Math.random() * 10) + 20
      }))
    }
  }
}

onMounted(async () => {
  // 检查是否有从Agent传来的数据
  const nlpDataStr = sessionStorage.getItem('nlp_weather_data')
  if (nlpDataStr) {
    try {
      const nlpData = JSON.parse(nlpDataStr)
      sessionStorage.removeItem('nlp_weather_data')
      
      const success = await handleAgentWeatherData(nlpData)
      if (success) {
        ElMessage.success('✅ 天气查询成功！')
        return
      }
    } catch (error) {
      console.error('[Weather] 解析Agent数据失败:', error)
    }
  }
  
  // 如果没有Agent数据，正常加载
  await fetchWeather()
})
</script>

<style scoped>
/* ✨ 新增：页面布局 */
.weather-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.card {
  background: var(--bg-card);
  border-radius: 24px;
  padding: 20px 24px;
  margin-bottom: 24px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-light);
  transition: 0.1s;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
  border-left: 4px solid var(--primary);
  padding-left: 14px;
}

.card-header h3 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
}

.grid-2col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.weather-card {
  background: linear-gradient(135deg, #e0f2fe, #ffffff);
  border-radius: var(--radius-lg);
  padding: 28px;
  margin-bottom: 12px;
  box-shadow: var(--shadow-md);
  border: 1px solid rgba(255, 255, 255, 0.6);
  transition: all 0.3s ease;
}

.weather-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-lg);
}

.tag-weather {
  background: #cfe7ff;
  color: #0056b3;
  border-radius: 40px;
  padding: 8px 16px;
  font-size: 0.8rem;
  margin-top: 12px;
  display: inline-block;
}

/* 智能建议区域样式 */
.suggestion-box {
  margin-top: 16px;
  padding: 16px;
  background: linear-gradient(135deg, #fff9e6, #ffffff);
  border-radius: 12px;
  border-left: 4px solid #f59e0b;
}

.suggestion-item {
  margin-bottom: 10px;
  font-size: 0.9rem;
  line-height: 1.6;
  color: #374151;
}

.suggestion-item:last-child {
  margin-bottom: 0;
}

.suggestion-item strong {
  color: #f59e0b;
  font-weight: 600;
}

/* 天气预报列表样式 */
.forecast-list {
  max-height: 350px;
  overflow-y: auto;
  padding-right: 8px;
}

.forecast-list::-webkit-scrollbar {
  width: 6px;
}

.forecast-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.forecast-list::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.forecast-list::-webkit-scrollbar-thumb:hover {
  background: #a1a1a1;
}

.forecast-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  margin-bottom: 10px;
  background: var(--bg-card);
  border-radius: var(--radius-md);
  border-left: 4px solid var(--primary);
  transition: all 0.25s ease;
  box-shadow: var(--shadow-sm);
}

.forecast-item:hover {
  background: #f8fafc;
  transform: translateX(4px);
  box-shadow: var(--shadow-md);
}

.forecast-date {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 80px;
}

.forecast-date strong {
  font-size: 0.9rem;
  color: #374151;
}

.week-day {
  font-size: 0.75rem;
  color: #6b7280;
}

.forecast-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin: 0 16px;
}

.weather-condition {
  font-size: 0.85rem;
  color: #374151;
  font-weight: 500;
}

.temperature-range {
  font-size: 0.8rem;
  color: #6b7280;
}

.weather-icon {
  font-size: 1.2rem;
  min-width: 40px;
  text-align: center;
}

.empty-forecast {
  text-align: center;
  padding: 40px 0;
  color: #909399;
}

/* 24小时预报区域 */
.hourly-section {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #e5e7eb;
}

.hourly-section h4 {
  margin-bottom: 16px;
  font-size: 1.1rem;
  color: #374151;
  font-weight: 600;
}

.hourly-scroll-container {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  padding: 12px 4px;
  scroll-behavior: smooth;
}

.hourly-scroll-container::-webkit-scrollbar {
  height: 6px;
}

.hourly-scroll-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.hourly-scroll-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.hourly-scroll-container::-webkit-scrollbar-thumb:hover {
  background: #a1a1a1;
}

.hourly-item {
  flex-shrink: 0;
  min-width: 85px;
  padding: 14px 10px;
  background: linear-gradient(135deg, #f0f9ff, #ffffff);
  border-radius: var(--radius-md);
  border: 1px solid #e0f2fe;
  text-align: center;
  transition: all 0.25s ease;
  box-shadow: var(--shadow-sm);
}

.hourly-item:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-md);
  border-color: var(--primary-light);
}

.hourly-time {
  font-size: 0.85rem;
  color: #6b7280;
  font-weight: 500;
  margin-bottom: 8px;
}

.hourly-icon {
  font-size: 1.5rem;
  margin: 8px 0;
}

.hourly-temp {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1f2937;
  margin: 8px 0;
}

.hourly-condition {
  font-size: 0.75rem;
  color: #6b7280;
}

.empty-hourly {
  text-align: center;
  padding: 20px 0;
  color: #909399;
}

@media (max-width: 768px) {
  .grid-2col {
    grid-template-columns: 1fr;
  }
  
  .card-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .forecast-item {
    padding: 10px 12px;
  }
  
  .forecast-info {
    margin: 0 12px;
  }
}
</style>