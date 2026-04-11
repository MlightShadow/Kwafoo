<template>
  <div class="monitor-view">
    <div class="page-header">
      <h2>📊 系统监控</h2>
    </div>

    <div class="monitor-content">
      <div class="monitor-section">
        <h3>任务进度</h3>
        <div class="progress-container">
          <div v-if="tasks.length === 0" class="no-tasks">
            暂无运行中的任务
          </div>
          <div v-else class="task-list">
            <div 
              v-for="task in tasks" 
              :key="task.id" 
              class="task-item"
            >
              <div class="task-header">
                <span class="task-name">{{ task.name }}</span>
                <span class="task-status" :class="task.status">
                  {{ task.status }}
                </span>
              </div>
              <div class="task-progress">
                <div class="progress-bar">
                  <div 
                    class="progress-fill" 
                    :style="{ width: `${task.progress || 0}%` }"
                  ></div>
                </div>
                <span class="progress-text">{{ task.progress || 0 }}%</span>
              </div>
              <div v-if="task.message" class="task-message">
                {{ task.message }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="monitor-section">
        <h3>系统信息</h3>
        <div class="system-info">
          <div class="info-item">
            <span class="info-label">服务器状态：</span>
            <span class="info-value" :class="{ online: isServerOnline, offline: !isServerOnline }">
              {{ isServerOnline ? '在线' : '离线' }}
            </span>
          </div>
          <div class="info-item">
            <span class="info-label">AI状态：</span>
            <span class="info-value ai-status" :class="aiStatusClass">
              {{ aiStatusText }}
            </span>
          </div>
          <div v-if="stats" class="info-item">
            <span class="info-label">总新闻数：</span>
            <span class="info-value">{{ stats.total }}</span>
          </div>
          <div v-if="stats" class="info-item">
            <span class="info-label">活跃新闻：</span>
            <span class="info-value">{{ stats.active }}</span>
          </div>
          <div v-if="stats" class="info-item">
            <span class="info-label">已处理：</span>
            <span class="info-value">{{ stats.processed }}</span>
          </div>
        </div>
      </div>

      <div class="monitor-section">
        <h3>快捷操作</h3>
        <div class="quick-actions">
          <button @click="handleFetch" class="action-button">
            🔄 手动抓取新闻
          </button>
          <button @click="handleAIProcess" class="action-button">
            🤖 AI分析新闻
          </button>
          <button @click="refreshData" class="action-button">
            🔄 刷新数据
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useNewsStore } from '@/stores/news'
import { api } from '@/api'

const newsStore = useNewsStore()

const tasks = ref<any[]>([])
const isServerOnline = ref(true)
const aiStatus = ref<string>('idle')
const loading = ref(false)

const stats = computed(() => newsStore.stats)

const aiStatusClass = computed(() => {
  const statusMap: Record<string, string> = {
    idle: 'status-idle',
    processing: 'status-processing',
    error: 'status-error'
  }
  return statusMap[aiStatus.value] || 'status-idle'
})

const aiStatusText = computed(() => {
  const statusMap: Record<string, string> = {
    idle: '空闲',
    processing: '处理中',
    error: '错误'
  }
  return statusMap[aiStatus.value] || '未知'
})

let monitorInterval: number | null = null

async function loadProgress() {
  try {
    const response = await api.getProgress()
    if (response.data.success) {
      tasks.value = response.data.data
    }
  } catch (error: any) {
    console.error('加载进度失败:', error)
  }
}

async function loadAIStatus() {
  try {
    const response = await api.getAIStatus()
    if (response.data.success) {
      aiStatus.value = response.data.data.status
    }
  } catch (error: any) {
    console.error('加载AI状态失败:', error)
  }
}

async function checkServerStatus() {
  try {
    const response = await api.healthCheck()
    isServerOnline.value = response.data.success
  } catch (error: any) {
    isServerOnline.value = false
  }
}

async function handleFetch() {
  try {
    const response = await api.manualFetch()
    if (response.data.success) {
      alert(response.data.message)
    } else {
      alert(response.data.message)
    }
  } catch (error: any) {
    alert('抓取失败: ' + error.message)
  }
}

async function handleAIProcess() {
  try {
    const response = await api.processAINews()
    if (response.data.success) {
      alert(response.data.message)
    } else {
      alert(response.data.message)
    }
  } catch (error: any) {
    alert('AI处理失败: ' + error.message)
  }
}

async function refreshData() {
  loading.value = true
  try {
    await Promise.all([
      loadProgress(),
      loadAIStatus(),
      checkServerStatus(),
      newsStore.loadStats()
    ])
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await refreshData()
  
  monitorInterval = window.setInterval(() => {
    loadProgress()
    loadAIStatus()
    checkServerStatus()
  }, 5000)
})

onUnmounted(() => {
  if (monitorInterval) {
    clearInterval(monitorInterval)
  }
})
</script>

<style scoped>
.monitor-view {
  width: 100%;
}

.page-header {
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e0e0e0;
}

.page-header h2 {
  font-size: 1.8rem;
  color: #333;
}

.monitor-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 1.5rem;
}

.monitor-section {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.monitor-section h3 {
  margin: 0 0 1rem 0;
  color: #333;
  font-size: 1.2rem;
}

.progress-container {
  min-height: 200px;
}

.no-tasks {
  text-align: center;
  padding: 2rem;
  color: #666;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.task-item {
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 1rem;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.task-name {
  font-weight: 500;
  color: #333;
}

.task-status {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 500;
}

.task-status.pending {
  background: #fff3cd;
  color: #856404;
}

.task-status.running {
  background: #d1ecf1;
  color: #0c5460;
}

.task-status.completed {
  background: #d4edda;
  color: #155724;
}

.task-status.error {
  background: #f8d7da;
  color: #721c24;
}

.task-progress {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.5rem;
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  transition: width 0.3s ease;
}

.progress-text {
  min-width: 40px;
  text-align: right;
  font-size: 0.9rem;
  color: #666;
}

.task-message {
  font-size: 0.85rem;
  color: #666;
  margin-top: 0.5rem;
}

.system-info {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 6px;
}

.info-label {
  font-weight: 500;
  color: #666;
}

.info-value {
  font-weight: 600;
  color: #333;
}

.info-value.online {
  color: #28a745;
}

.info-value.offline {
  color: #dc3545;
}

.ai-status.status-idle {
  color: #6c757d;
}

.ai-status.status-processing {
  color: #007bff;
}

.ai-status.status-error {
  color: #dc3545;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.action-button {
  padding: 0.75rem 1rem;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
  transition: background 0.3s ease;
  text-align: left;
}

.action-button:hover {
  background: #0056b3;
}

@media (max-width: 768px) {
  .monitor-content {
    grid-template-columns: 1fr;
  }
}
</style>