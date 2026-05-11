<template>
  <div>
    <div class="card">
      <div class="card-header">
        <h3>📅 会议室智能预约</h3>
        <div class="header-actions">
          <!-- 历史记录按钮 -->
          <el-button 
            type="info" 
            plain 
            size="small" 
            @click="showHistoryDialog = true" 
            class="history-btn"
          >
            <el-icon><Clock /></el-icon>
            历史记录
          </el-button>
        </div>
      </div>
      <div class="grid-2col">
        <div>
          <h4>📌 可预约会议室</h4>
          
          <!-- 会议室列表 -->
          <div v-for="room in paginatedRooms" :key="room.id" class="room-item">
            <div class="flex-between">
              <span><b>{{ room.name }}</b> ({{ room.capacity }}人)</span>
              <span :style="{color: room.available ? '#2ecc71' : '#e67e22'}">{{ room.available ? '可预约' : '已占用' }}</span>
            </div>
            <!-- ✅ 新增：展示 AI 匹配说明 -->
            <div v-if="room.nlp_explanation" style="font-size: 12px; color: #2b6ef0; margin: 4px 0;">
              💡 {{ room.nlp_explanation }}
            </div>
            <div class="flex-between mt-1">
              <small>{{ room.location }}</small>
              <button class="btn-sm" v-if="room.available" @click="quickBookRoomHandler(room.id)">一键预定</button>
            </div>
          </div>
          
          <!-- 会议室分页组件 -->
          <div class="pagination-container" v-if="meetingRooms.length > 0">
            <div class="total-count">
              共 {{ meetingRooms.length }} 个会议室
            </div>
            
            <div class="page-size-selector">
              <span class="label">每页显示：</span>
              <el-select 
                v-model="roomPageSize" 
                size="small" 
                @change="handleRoomSizeChange"
                class="page-size-select"
              >
                <el-option label="5个/页" :value="5" />
                <el-option label="10个/页" :value="10" />
                <el-option label="20个/页" :value="20" />
              </el-select>
            </div>
            
            <el-pagination
              v-model:current-page="roomCurrentPage"
              v-model:page-size="roomPageSize"
              :page-sizes="[5, 10, 20]"
              :total="meetingRooms.length"
              layout="prev, pager, next"
              small
              @current-change="handleRoomPageChange"
            />
          </div>
          
          <!-- 无会议室时显示 -->
          <div v-if="meetingRooms.length === 0" class="empty-booking">
            <p style="text-align: center; color: #909399; padding: 20px 0;">暂无可预约的会议室</p>
          </div>
        </div>
        <div>
          <h4>📋 我的预约记录</h4>
          <div v-for="book in paginatedBookings" :key="book.id" class="room-item">
            <div><b>{{ book.roomName }}</b> | {{ book.date }} {{ book.timeSlot }}</div>
            <div class="flex-between mt-1">
              <span>状态: {{ book.status }}</span>
              <button class="btn-sm" @click="cancelBookingHandler(book.id)">取消</button>
            </div>
          </div>
          
          <!-- 分页组件 -->
          <div class="pagination-container" v-if="currentBookings.length > 0">
            <div class="total-count">
              共 {{ currentBookings.length }} 条预约记录
            </div>
            
            <div class="page-size-selector">
              <span class="label">每页显示：</span>
              <el-select 
                v-model="pageSize" 
                size="small" 
                @change="handleSizeChange"
                class="page-size-select"
              >
                <el-option label="5条/页" :value="5" />
                <el-option label="10条/页" :value="10" />
                <el-option label="20条/页" :value="20" />
              </el-select>
            </div>
            
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[5, 10, 20]"
              :total="currentBookings.length"
              layout="prev, pager, next"
              small
              @current-change="handlePageChange"
            />
          </div>
          
          <!-- 无预约记录时显示 -->
          <div v-if="currentBookings.length === 0" class="empty-booking">
            <p style="text-align: center; color: #909399; padding: 20px 0;">暂无预约记录</p>
          </div>
        </div>
      </div>
    </div>



    <!-- NLP智能指令输入框 -->
    <div class="card" style="margin-top: 20px;">
      <div class="card-header">
        <h3>🤖 智能指令</h3>
      </div>
      <div style="padding: 15px;">
        <el-input
          v-model="nlpCommandInput"
          placeholder="例如: 明天下午3点预定一个能容纳10人的会议室，需要投影仪 | 取消明天D101的预约"
          clearable
          @keyup.enter="handleNLPCommand"
        >
          <template #append>
            <el-button type="primary" @click="handleNLPCommand" :loading="nlpLoading">
              <el-icon><Promotion /></el-icon>
              发送
            </el-button>
          </template>
        </el-input>
        <div style="margin-top: 10px; font-size: 12px; color: #909399;">
          💡 提示: 可以说“预定”、“取消”或“完成”会议室预约
        </div>
      </div>
    </div>

    <!-- NLP确认弹窗(取消/完成) -->
    <el-dialog 
      v-model="showNLPConfirmDialog" 
      :title="nlpConfirmTitle" 
      width="600px"
    >
      <div v-if="nlpMatchedBookings.length > 0">
        <p style="margin-bottom: 15px; color: #606266;">{{ nlpConfirmMessage }}</p>
        
        <div 
          v-for="booking in nlpMatchedBookings" 
          :key="booking.booking_id"
          class="room-item"
          style="margin-bottom: 10px;"
        >
          <div class="flex-between">
            <div>
              <strong>{{ booking.room_name }}</strong>
              <span style="margin-left: 10px; color: #909399;">{{ booking.date }} {{ booking.time_slot }}</span>
            </div>
            <el-tag :type="booking.action === 'cancel' ? 'danger' : 'success'" size="small">
              {{ booking.action === 'cancel' ? '取消' : '完成' }}
            </el-tag>
          </div>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="showNLPConfirmDialog = false">我再想想</el-button>
        <el-button 
          type="primary" 
          @click="confirmNLPAction"
          :loading="nlpActionLoading"
        >
          确认{{ nlpConfirmData.action_type === 'cancel' ? '取消' : '完成' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 历史记录弹窗 -->
    <el-dialog 
      v-model="showHistoryDialog" 
      title="📚 预约历史记录" 
      width="800px"
      :close-on-click-modal="true"
    >
      <div class="history-dialog">
        <!-- 筛选工具栏 -->
        <div class="filter-toolbar">
          <div class="filter-left">
            <span class="filter-label">状态筛选：</span>
            <el-radio-group v-model="historyFilter" size="small">
              <el-radio-button label="all">全部</el-radio-button>
              <el-radio-button label="completed">预约完成</el-radio-button>
              <el-radio-button label="cancelled">预约取消</el-radio-button>
            </el-radio-group>
          </div>
          <div class="filter-right">
            <span class="total-count">共 {{ filteredHistoryBookings.length }} 条记录</span>
          </div>
        </div>

        <!-- 历史记录列表 -->
        <div class="history-tasks-list" v-if="filteredHistoryBookings.length > 0">
          <div 
            v-for="book in paginatedHistoryBookings" 
            :key="book.id" 
            class="history-booking-item"
            :class="{ 'completed-booking': book.status === '预约完成', 'cancelled-booking': book.status === '预约取消' }"
          >
            <div class="booking-info">
              <div class="booking-title">
                <strong>{{ book.roomName }}</strong>
              </div>
              <div class="booking-details">
                <span class="booking-time">
                  <el-icon><Clock /></el-icon>
                  时间: {{ book.date }} {{ book.timeSlot }}
                </span>
              </div>
              <div class="booking-category">
                <el-tag size="small" :type="getBookingStatusType(book.status)">
                  {{ book.status }}
                </el-tag>
              </div>
            </div>
            <div class="booking-status">
              <span :class="getBookingStatusClass(book.status)">{{ book.status }}</span>
            </div>
          </div>
        </div>

        <!-- 分页组件 -->
        <div class="pagination-container" v-if="filteredHistoryBookings.length > 0">
          <div class="total-count">
            共 {{ filteredHistoryBookings.length }} 条记录
          </div>
          
          <div class="page-size-selector">
            <span class="label">每页显示：</span>
            <el-select 
              v-model="historyPageSize" 
              size="small" 
              @change="handleHistorySizeChange"
              class="page-size-select"
            >
              <el-option label="5条/页" :value="5" />
              <el-option label="10条/页" :value="10" />
              <el-option label="20条/页" :value="20" />
            </el-select>
          </div>
          
          <el-pagination
            v-model:current-page="historyCurrentPage"
            v-model:page-size="historyPageSize"
            :page-sizes="[5, 10, 20]"
            :total="filteredHistoryBookings.length"
            layout="prev, pager, next"
            small
            @current-change="handleHistoryPageChange"
          />
        </div>

        <!-- 无历史记录 -->
        <div v-else class="empty-state">
          <el-empty description="暂无历史记录">
            <template #image>
              <el-icon size="48" color="#909399"><List /></el-icon>
            </template>
          </el-empty>
        </div>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showHistoryDialog = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick, computed, watch } from 'vue'
import { useRoute, onBeforeRouteUpdate } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Clock, List, Promotion } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { 
  getMeetingRooms, 
  getMyBookings, 
  quickBookRoom, 
  cancelBooking,
  completeBooking,
  getMeetingStats,
  nlpCommand 
} from '@/api/modules/meeting'

// 获取路由对象
const route = useRoute()

// 会议室数据
const meetingRooms = ref([])
const myBookings = ref([])
const meetingStats = ref({ show: false })
const showHistoryDialog = ref(false)

// NLP相关数据
const nlpCommandInput = ref('')
const nlpLoading = ref(false)
const showNLPConfirmDialog = ref(false)
const nlpConfirmTitle = ref('')
const nlpConfirmMessage = ref('')
const nlpMatchedBookings = ref([])
const nlpConfirmData = ref({})
const nlpActionLoading = ref(false)
const nlpRecommendedRooms = ref([])  // NLP推荐的会议室

// 分页相关数据 - 会议室
const roomCurrentPage = ref(1)
const roomPageSize = ref(5) // 每页显示5个会议室

// 分页相关数据 - 当前预约
const currentPage = ref(1)
const pageSize = ref(5) // 每页显示5条预约记录

// 分页相关数据 - 历史记录
const historyCurrentPage = ref(1)
const historyPageSize = ref(5) // 每页显示5条历史记录

// 历史记录筛选状态
const historyFilter = ref('all') // all: 全部, completed: 预约完成, cancelled: 预约取消

// 计算当前页显示的会议室
const paginatedRooms = computed(() => {
  const startIndex = (roomCurrentPage.value - 1) * roomPageSize.value
  const endIndex = startIndex + roomPageSize.value
  return meetingRooms.value.slice(startIndex, endIndex)
})

// 当前预约记录（已申请状态）
const currentBookings = computed(() => {
  return myBookings.value.filter(booking => booking.status === '已申请')
})

// 历史记录（预约完成 + 预约取消）
const historyBookings = computed(() => {
  return myBookings.value.filter(booking => booking.status === '预约完成' || booking.status === '预约取消')
})

// 筛选后的历史记录
const filteredHistoryBookings = computed(() => {
  if (historyFilter.value === 'completed') {
    return historyBookings.value.filter(booking => booking.status === '预约完成')
  } else if (historyFilter.value === 'cancelled') {
    return historyBookings.value.filter(booking => booking.status === '预约取消')
  } else {
    return historyBookings.value
  }
})

// 计算当前页显示的预约记录
const paginatedBookings = computed(() => {
  const startIndex = (currentPage.value - 1) * pageSize.value
  const endIndex = startIndex + pageSize.value
  return currentBookings.value.slice(startIndex, endIndex)
})

// 计算当前页显示的历史记录
const paginatedHistoryBookings = computed(() => {
  const startIndex = (historyCurrentPage.value - 1) * historyPageSize.value
  const endIndex = startIndex + historyPageSize.value
  return filteredHistoryBookings.value.slice(startIndex, endIndex)
})

// 获取会议室列表 - 只查询status='可申请'的会议室
const fetchMeetingRooms = async () => {
  try {
    const response = await getMeetingRooms({ 
      page: 1, 
      page_size: 100  // 获取所有可申请的会议室
    })
    console.log('[Meeting] API响应:', response)
    
    // API拦截器已经提取了response.data.data
    // 后端返回格式: {code: 200, message: '...', data: [rooms...]}
    const rawData = Array.isArray(response) ? response : []
    
    // 字段映射：过滤出status='可申请'的会议室
    meetingRooms.value = rawData
      .filter(room => room.status === '可申请')
      .map(room => ({
        ...room,
        available: room.status === '可申请'  // 添加available字段用于前端显示
      }))
    
    console.log('[Meeting] 可预约会议室:', meetingRooms.value.length, '个')
  } catch (error) {
    console.error('[Meeting] 获取失败:', error)
    ElMessage.error('获取会议室列表失败: ' + error.message)
    meetingRooms.value = []
  }
}

// 获取我的预约记录
const fetchMyBookings = async () => {
  try {
    const response = await getMyBookings({ 
      page: 1, 
      page_size: 100  // 获取所有预约记录
    })
    console.log('[Meeting] 预约记录API响应:', response)
    console.log('[Meeting] 响应类型:', typeof response, '是否数组:', Array.isArray(response))
    
    // API拦截器已经提取了response.data.data
    // 后端返回格式: {code: 200, message: '...', data: [bookings...]}
    // 拦截器返回: [bookings...]
    const rawData = Array.isArray(response) ? response : []
    console.log('[Meeting] 原始数据:', rawData)
    console.log('[Meeting] 数据长度:', rawData.length)
    
    // 字段映射：将后端数据转换为前端期望的格式
    myBookings.value = rawData.map(booking => {
      // 状态映射：confirmed -> 已申请, cancelled -> 预约取消, completed -> 预约完成
      let status = '已申请'
      if (booking.status === 'cancelled') {
        status = '预约取消'
      } else if (booking.status === 'completed') {
        status = '预约完成'
      }
      
      // 格式化时间
      const startTime = new Date(booking.start_time)
      const endTime = new Date(booking.end_time)
      const date = startTime.toLocaleDateString('zh-CN', { 
        year: 'numeric', 
        month: '2-digit', 
        day: '2-digit' 
      }).replace(/\//g, '-')
      const timeSlot = `${startTime.getHours().toString().padStart(2, '0')}:${startTime.getMinutes().toString().padStart(2, '0')}-${endTime.getHours().toString().padStart(2, '0')}:${endTime.getMinutes().toString().padStart(2, '0')}`
      
      return {
        ...booking,
        roomName: booking.room_name || '未知会议室',
        date,
        timeSlot,
        status  // 使用映射后的中文状态
      }
    })
    
    console.log('[Meeting] 我的预约记录:', myBookings.value.length, '条')
  } catch (error) {
    console.error('[Meeting] 获取失败:', error)
    ElMessage.error('获取预约记录失败: ' + error.message)
    myBookings.value = []
  }
}

// 快速预定会议室
const quickBookRoomHandler = async (roomId) => {
  try {
    const room = meetingRooms.value.find(r => r.id === roomId)
    if (!room || !room.available) {
      ElMessage.warning('会议室不可用')
      return
    }
    
    // 计算默认时间：明天下午15:00-16:00
    const tomorrow = new Date()
    tomorrow.setDate(tomorrow.getDate() + 1)
    tomorrow.setHours(15, 0, 0, 0)
    
    const endTime = new Date(tomorrow)
    endTime.setHours(16, 0, 0, 0)
    
    // 构建后端需要的预订数据格式
    const bookingData = {
      start_time: tomorrow.toISOString(),  // ISO格式: "2026-04-16T15:00:00.000Z"
      end_time: endTime.toISOString(),      // ISO格式: "2026-04-16T16:00:00.000Z"
      purpose: '快速预定',
      attendees: []
    }
    
    console.log('[Meeting] 预订数据:', bookingData)
    
    // 调用后端API
    await quickBookRoom(roomId, bookingData)
    
    ElMessage.success(`已成功预定 ${room.name}，时间：明天 15:00-16:00`)
    
    // 刷新数据：重新获取会议室列表和预约记录
    await Promise.all([fetchMeetingRooms(), fetchMyBookings()])
    
  } catch (error) {
    console.error('[Meeting] 预定失败:', error)
    ElMessage.error('预定失败: ' + error.message)
  }
}

// 取消预约
const cancelBookingHandler = async (bookId) => {
  try {
    // 查找对应的预约记录
    const booking = myBookings.value.find(b => b.id === bookId)
    if (!booking) {
      ElMessage.error('未找到预约记录')
      return
    }
    
    // 显示确认弹窗
    await ElMessageBox.confirm(
      `确定要取消以下预约吗？\n\n会议室：${booking.roomName}\n时间：${booking.date} ${booking.timeSlot}`,
      '⚠️ 确认取消',
      {
        confirmButtonText: '确认取消',
        cancelButtonText: '我再想想',
        type: 'warning',
        distinguishCancelAndClose: true
      }
    )
    
    // 用户确认后执行取消
    await cancelBooking(bookId)
    ElMessage.info('已取消预约，会议室已释放')
    
    // 刷新数据：重新获取会议室列表和预约记录
    await Promise.all([fetchMeetingRooms(), fetchMyBookings()])
  } catch (error) {
    // 用户点击取消或关闭弹窗
    if (error === 'cancel' || error === 'close') {
      console.log('[Meeting] 用户取消操作')
      return
    }
    console.error('[Meeting] 取消失败:', error)
    ElMessage.error('取消预约失败: ' + error.message)
  }
}

// 获取使用统计
const fetchUsageStats = async () => {
  try {
    const response = await getMeetingStats({ days: 7 })
    meetingStats.value = { ...response, show: true }
    
    nextTick(() => {
      renderMeetingStatsChart(response.data)
    })
  } catch (error) {
    ElMessage.error('获取统计信息失败: ' + error.message)
  }
}

// 分页大小改变事件 - 会议室
const handleRoomSizeChange = (newSize) => {
  roomPageSize.value = newSize
  roomCurrentPage.value = 1 // 重置到第一页
}

// 页面切换事件 - 会议室
const handleRoomPageChange = (newPage) => {
  roomCurrentPage.value = newPage
}

// 分页大小改变事件 - 当前预约
const handleSizeChange = (newSize) => {
  pageSize.value = newSize
  currentPage.value = 1 // 重置到第一页
}

// 页面切换事件 - 当前预约
const handlePageChange = (newPage) => {
  currentPage.value = newPage
}

// 分页大小改变事件 - 历史记录
const handleHistorySizeChange = (newSize) => {
  historyPageSize.value = newSize
  historyCurrentPage.value = 1 // 重置到第一页
}

// 页面切换事件 - 历史记录
const handleHistoryPageChange = (newPage) => {
  historyCurrentPage.value = newPage
}

// 获取预约状态对应的CSS类名
const getBookingStatusClass = (status) => {
  if (status === '预约完成') return 'status-completed'
  if (status === '预约取消') return 'status-cancelled'
  return 'status-booking'
}

// 获取预约状态对应的Element Plus标签类型
const getBookingStatusType = (status) => {
  const typeMap = {
    '预约中': 'primary',
    '预约完成': 'success',
    '预约取消': 'danger'
  }
  return typeMap[status] || 'info'
}

// NLP智能命令处理
const handleNLPCommand = async () => {
  if (!nlpCommandInput.value.trim()) {
    ElMessage.warning('请输入指令')
    return
  }
  
  try {
    nlpLoading.value = true
    const response = await nlpCommand(nlpCommandInput.value)
    
    console.log('[NLP] 解析结果:', response)
    
    const data = response.data || {}
    const intent = data.intent
    const actionType = data.action_type
    const explanation = data.explanation || ''
    
    if (intent === 'book') {
      // 预订意图 - 显示推荐会议室
      const recommendedRooms = data.recommended_rooms || []
      
      if (recommendedRooms.length === 0) {
        ElMessage.warning('未找到匹配的会议室，请调整您的需求')
        return
      }
      
      // 将推荐的会议室添加到左侧列表
      nlpRecommendedRooms.value = recommendedRooms.map(room => ({
        ...room,
        available: true,
        location: room.location || `${room.building || ''}${room.floor || ''}楼`,
        nlp_match_score: room.match_score,
        nlp_explanation: room.match_explanation
      }))
      
      // 合并到meetingRooms
      meetingRooms.value = [...nlpRecommendedRooms.value]
      
      ElMessage.success(`✅ ${explanation}，已为您展示${recommendedRooms.length}个推荐会议室`)
      
      // 清空输入
      nlpCommandInput.value = ''
      
    } else if (intent === 'cancel' || intent === 'complete') {
      // 取消/完成意图 - 显示确认弹窗
      const matchedBookings = data.matched_bookings || []
      
      if (matchedBookings.length === 0) {
        ElMessage.warning('未找到匹配的预约记录')
        return
      }
      
      // 设置确认弹窗数据
      nlpConfirmTitle.value = intent === 'cancel' ? '⚠️ 确认取消预约' : '✅ 确认完成预约'
      nlpConfirmMessage.value = explanation
      nlpMatchedBookings.value = matchedBookings
      nlpConfirmData.value = {
        action_type: intent,
        bookings: matchedBookings
      }
      
      // 显示确认弹窗
      showNLPConfirmDialog.value = true
      
      // 清空输入
      nlpCommandInput.value = ''
    } else {
      ElMessage.warning(`无法理解您的指令: ${explanation}`)
    }
    
  } catch (error) {
    console.error('[NLP] 处理失败:', error)
    ElMessage.error('NLP处理失败: ' + error.message)
  } finally {
    nlpLoading.value = false
  }
}

// 确认NLP操作(取消/完成)
const confirmNLPAction = async () => {
  try {
    nlpActionLoading.value = true
    
    const bookings = nlpConfirmData.value.bookings || []
    const actionType = nlpConfirmData.value.action_type
    
    // 批量执行操作
    for (const booking of bookings) {
      if (actionType === 'cancel') {
        // 取消预约
        await cancelBooking(booking.booking_id)
      } else if (actionType === 'complete') {
        // 完成预约
        await completeBooking(booking.booking_id)
      }
    }
    
    ElMessage.success(`成功${actionType === 'cancel' ? '取消' : '完成'}${bookings.length}个预约`)
    
    // 关闭弹窗
    showNLPConfirmDialog.value = false
    
    // 刷新数据
    await Promise.all([fetchMeetingRooms(), fetchMyBookings()])
    
  } catch (error) {
    console.error('[NLP] 操作失败:', error)
    ElMessage.error('操作失败: ' + error.message)
  } finally {
    nlpActionLoading.value = false
  }
}

// 渲染统计图表
const renderMeetingStatsChart = (data) => {
  const chartDom = document.getElementById('meetingStatChart')
  if (chartDom) {
    const chart = echarts.init(chartDom)
    chart.setOption({
      xAxis: { 
        data: data.days || ['周一', '周二', '周三', '周四', '周五', '周六'] 
      },
      yAxis: { name: '使用率(%)' },
      series: [{ 
        type: 'line', 
        data: data.rates || [65, 72, 80, 78, 90, 45], 
        smooth: true, 
        lineStyle: { color: '#2b6ef0' } 
      }]
    })
  }
}

// 处理NLP数据的通用函数
const handleNLPData = (nlpData) => {
  console.log('[Meeting] 接收到NLP数据:', nlpData)
  
  // 处理推荐的会议室
  if (nlpData.recommended_rooms && nlpData.recommended_rooms.length > 0) {
    console.log('[Meeting] 显示推荐会议室:', nlpData.recommended_rooms.length, '个')
    
    // 将推荐的会议室转换为前端格式
    nlpRecommendedRooms.value = nlpData.recommended_rooms.map(room => ({
      ...room,
      available: true,
      location: room.location || `${room.building || ''}${room.floor || ''}楼`
    }))
    
    // 替换当前显示的会议室列表为推荐的会议室
    meetingRooms.value = [...nlpRecommendedRooms.value]
    
    ElMessage.success(`✅ 已为您展示${nlpData.recommended_rooms.length}个推荐会议室，请点击"一键预定"完成预订`)
  }
  
  // 处理匹配的预约（取消/完成意图）
  if (nlpData.matched_bookings && nlpData.matched_bookings.length > 0) {
    console.log('[Meeting] 显示待确认的预约:', nlpData.matched_bookings.length, '个')
    
    // 自动打开确认弹窗
    const firstBooking = nlpData.matched_bookings[0]
    const actionText = firstBooking.action === 'cancel' ? '取消' : '完成'
    
    nlpConfirmTitle.value = firstBooking.action === 'cancel' ? '⚠️ 确认取消预约' : '✅ 确认完成预约'
    nlpConfirmMessage.value = `找到${nlpData.matched_bookings.length}个待${actionText}的预约：`
    nlpMatchedBookings.value = nlpData.matched_bookings
    nlpConfirmData.value = {
      action_type: firstBooking.action,
      bookings: nlpData.matched_bookings  // 存储完整的预约列表
    }
    showNLPConfirmDialog.value = true
  }
}

// 检查并处理NLP数据
const checkAndHandleNLPData = () => {
  const nlpDataStr = sessionStorage.getItem('nlp_meeting_data')
  if (nlpDataStr) {
    try {
      const nlpData = JSON.parse(nlpDataStr)
      // 清除sessionStorage中的数据
      sessionStorage.removeItem('nlp_meeting_data')
      // 处理NLP数据
      handleNLPData(nlpData)
      return true
    } catch (error) {
      console.error('[Meeting] 解析NLP数据失败:', error)
      return false
    }
  }
  return false
}

onMounted(async () => {
  await Promise.all([fetchMeetingRooms(), fetchMyBookings()])
  
  // 如果从Layout的NLP指令跳转过来（带有refresh参数），处理NLP数据
  if (route.query.refresh === 'true' || route.query.refresh === true) {
    const hasNLPData = checkAndHandleNLPData()
    if (!hasNLPData) {
      // 没有NLP数据，只是普通的刷新
      ElMessage.success('✅ 会议室预订已添加！')
    }
  }
  
  // 🔥 监听来自Chat页面的预约更新事件
  window.addEventListener('meetingBookingUpdated', handleBookingUpdate)
})

// 处理预约更新事件
const handleBookingUpdate = async () => {
  console.log('[Meeting] 收到预约更新事件，刷新数据...')
  await Promise.all([fetchMeetingRooms(), fetchMyBookings()])
  ElMessage.success('✅ 检测到新的预约，已自动刷新！')
}

// 组件卸载时移除事件监听器
onBeforeUnmount(() => {
  window.removeEventListener('meetingBookingUpdated', handleBookingUpdate)
})

// 监听路由更新（处理在同一页面内路由参数变化的情况）
onBeforeRouteUpdate(async (to, from) => {
  // 如果新的路由有refresh参数，处理NLP数据
  if (to.query.refresh === 'true' || to.query.refresh === true) {
    // 等待一下确保DOM更新
    await nextTick()
    const hasNLPData = checkAndHandleNLPData()
    if (!hasNLPData) {
      ElMessage.success('✅ 会议室预订已添加！')
    }
  }
})
</script>

<style scoped>
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

.room-item {
  background: #f9fcff;
  border-radius: 20px;
  padding: 12px;
  margin-bottom: 12px;
}

.flex-between {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.btn-sm {
  background: #eef3ff;
  border: none;
  border-radius: 30px;
  padding: 4px 12px;
  cursor: pointer;
  color: var(--primary);
}

.mt-1 {
  margin-top: 0.25rem;
}

/* 分页组件样式 */
.pagination-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #eef2ff;
  flex-wrap: wrap;
  gap: 12px;
}

.total-count {
  font-size: 0.9rem;
  color: #6b7280;
  flex-shrink: 0;
}

.page-size-selector {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.page-size-selector .label {
  font-size: 0.9rem;
  color: #6b7280;
  white-space: nowrap;
}

.page-size-select {
  width: 100px;
}

.pagination-container .el-pagination {
  flex-shrink: 0;
}

/* 历史记录弹窗样式 */
.history-dialog {
  max-height: 500px;
  overflow-y: auto;
}

.filter-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 12px 0;
  border-bottom: 1px solid #eef2ff;
}

.filter-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.filter-label {
  font-size: 0.9rem;
  color: #606266;
  font-weight: 500;
}

.filter-right {
  font-size: 0.9rem;
  color: #909399;
}

.history-tasks-list {
  max-height: 400px;
  overflow-y: auto;
}

.history-booking-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  margin-bottom: 12px;
  background: #f8f9fa;
  border-radius: 12px;
  transition: all 0.2s;
}

.completed-booking {
  border-left: 4px solid #10b981;
}

.cancelled-booking {
  border-left: 4px solid #f56565;
}

.history-booking-item:hover {
  background: #f1f5f9;
  transform: translateY(-1px);
}

.booking-info {
  flex: 1;
}

.booking-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.booking-title strong {
  font-size: 1rem;
  color: #374151;
}

.completed-booking .booking-title strong {
  text-decoration: line-through;
  color: #6b7280;
}

.booking-details {
  display: flex;
  gap: 16px;
  font-size: 0.85rem;
  color: #6b7280;
  margin-bottom: 8px;
}

.booking-time {
  display: flex;
  align-items: center;
  gap: 4px;
}

.booking-category {
  margin-top: 4px;
}

.booking-status {
  margin-left: 12px;
}

.status-completed {
  background: #d4edda;
  color: #155724;
  padding: 4px 12px;
  border-radius: 40px;
  font-size: 0.75rem;
  font-weight: 500;
}

.status-cancelled {
  background: #f8d7da;
  color: #721c24;
  padding: 4px 12px;
  border-radius: 40px;
  font-size: 0.75rem;
  font-weight: 500;
}

.status-booking {
  background: #fff3cd;
  color: #856404;
  padding: 4px 12px;
  border-radius: 40px;
  font-size: 0.75rem;
  font-weight: 500;
}

.empty-state {
  text-align: center;
  padding: 40px 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

@media (max-width: 768px) {
  .grid-2col {
    grid-template-columns: 1fr;
  }
}
</style>