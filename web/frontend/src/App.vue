<template>
  <div class="app-container">
    <header class="app-header">
      <div class="container header-content">
        <div class="header-left">
          <h1>📰 Kwafoo</h1>
        </div>
        
        <nav class="main-nav">
          <router-link to="/" class="nav-link" active-class="active">
            📰 新闻
          </router-link>
          <router-link to="/monitor" class="nav-link" active-class="active">
            📊 监控
          </router-link>
          <router-link to="/reports" class="nav-link" active-class="active">
            📊 报告
          </router-link>
          <router-link to="/admin" class="nav-link" active-class="active">
            ⚙️ 管理
          </router-link>
        </nav>
        
        <div class="header-right">
          <div class="search-section">
            <input 
              v-model="searchQuery" 
              type="text" 
              placeholder="搜索..." 
              class="search-input"
              @keypress.enter="handleSearch"
            >
            <button @click="handleSearch" class="search-btn">🔍</button>
          </div>
          
          <div class="status-section">
            <div class="server-status" :class="{ online: isServerOnline, offline: !isServerOnline }">
              {{ isServerOnline ? '在线' : '离线' }}
            </div>
          </div>
        </div>
      </div>
    </header>

    <main class="container main-content">
      <aside v-if="showSidebar" class="sidebar">
        <CategoryList />
      </aside>

      <div class="content">
        <router-view />
      </div>
    </main>

    <div class="chat-fab" @click="openChat">
      💬
    </div>

    <ChatModal :is-open="showChatModal" @close="closeChat" />

    <div v-if="showOfflineMessage" class="server-offline-message">
      <div class="offline-content">
        <div class="offline-icon">⚠️</div>
        <div class="offline-text">
          <h3>服务器连接失败</h3>
          <p>无法连接到服务器，请检查网络连接</p>
          <button @click="reconnect" class="retry-button">🔄 重新连接</button>
          <button @click="hideOfflineMessage" class="close-button">✕ 关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import CategoryList from '@/components/CategoryList.vue'
import ChatModal from '@/components/ChatModal.vue'
import { useNewsStore } from '@/stores/news'
import { useConfigStore } from '@/stores/config'
import { api } from '@/api'
import { useWebSocket } from '@/composables/useWebSocket'

const router = useRouter()
const route = useRoute()
const newsStore = useNewsStore()
const configStore = useConfigStore()

const searchQuery = ref('')
const isServerOnline = ref(true)
const showChatModal = ref(false)
const showOfflineMessage = ref(false)
const userClosedOfflineMessage = ref(false)
const tasks = ref<any[]>([])

const showSidebar = computed(() => {
  return route.name === 'news'
})

const runningTasks = computed(() => {
  return tasks.value.filter(task => task.status === 'running')
})

let serverMonitorInterval: number | null = null
let progressMonitorInterval: number | null = null

async function checkServerStatus() {
  try {
    const response = await api.healthCheck()
    if (response.data.success) {
      isServerOnline.value = true
      hideOfflineMessage()
    } else {
      throw new Error('Server returned error')
    }
  } catch (error) {
    isServerOnline.value = false
    if (!userClosedOfflineMessage.value) {
      showOfflineMessage.value = true
    }
    console.error('服务器连接失败:', error)
  }
}

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

async function handleSearch() {
  if (!searchQuery.value.trim()) return
  await newsStore.searchNews(searchQuery.value.trim())
}

function openChat() {
  showChatModal.value = true
}

function closeChat() {
  showChatModal.value = false
}

function reconnect() {
  checkServerStatus()
}

function hideOfflineMessage() {
  showOfflineMessage.value = false
  userClosedOfflineMessage.value = true
}

onMounted(async () => {
  // 初始化WebSocket连接
  const { onMessage, connect } = useWebSocket()
  
  // 手动连接WebSocket
  connect()
  
  // 设置WebSocket消息监听
  onMessage((message) => {
    console.log('App.vue收到WebSocket消息:', message)
    if (message.type === 'news_updated') {
      console.log('处理news_updated消息:', message.news_id, message.updates)
      newsStore.updateSingleNews(message.news_id, message.updates)
    } else if (message.type === 'task_started') {
      console.log('处理task_started消息:', message.task_id, message.task_name)
      // 可以在这里添加任务开始的逻辑
    } else if (message.type === 'progress_update') {
      console.log('处理progress_update消息:', message.task_id, message.progress, message.message)
      // 可以在这里添加进度更新的逻辑
    } else if (message.type === 'task_completed') {
      console.log('处理task_completed消息:', message.task_id, message.task_name, message.success)
      // 可以在这里添加任务完成的逻辑
    } else {
      console.log('忽略其他类型的消息:', message.type)
    }
  })
  
  await checkServerStatus()
  await configStore.loadConfig()
  
  // 将分类配置设置到 newsStore
  console.log('配置加载完成，检查分类数据:', configStore.config)
  if (configStore.config?.categories) {
    console.log('设置分类数据:', configStore.config.categories)
    newsStore.setCategories(configStore.config.categories)
  } else {
    console.warn('配置中没有分类数据')
  }
  
  await newsStore.loadNews()
  
  serverMonitorInterval = window.setInterval(() => {
    checkServerStatus()
  }, 30000)
  
  progressMonitorInterval = window.setInterval(() => {
    loadProgress()
  }, 2000)
})

onUnmounted(() => {
  if (serverMonitorInterval) {
    clearInterval(serverMonitorInterval)
  }
  if (progressMonitorInterval) {
    clearInterval(progressMonitorInterval)
  }
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  color: #1f2937;
  line-height: 1.6;
}

.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0.75rem 0;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 1000;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
}

.header-left h1 {
  font-size: 1.5rem;
  margin: 0;
  font-weight: 700;
  letter-spacing: -0.025em;
}

.main-nav {
  display: flex;
  gap: 0.5rem;
}

.nav-link {
  color: white;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  transition: all 0.2s;
  font-weight: 500;
  font-size: 0.875rem;
}

.nav-link:hover {
  background: rgba(255, 255, 255, 0.15);
}

.nav-link.active {
  background: rgba(255, 255, 255, 0.2);
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.search-section {
  display: flex;
  gap: 0.5rem;
}

.search-input {
  padding: 0.5rem 0.75rem;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  width: 180px;
  background: rgba(255, 255, 255, 0.9);
}

.search-input:focus {
  outline: none;
  background: white;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.3);
}

.search-btn {
  padding: 0.5rem 0.75rem;
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.2s;
}

.search-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.status-section {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.server-status {
  padding: 0.375rem 0.75rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.15);
}

.server-status.online {
  background: rgba(34, 197, 94, 0.3);
  color: #86efac;
}

.server-status.offline {
  background: rgba(239, 68, 68, 0.3);
  color: #fca5a5;
}

.container {
  width: 100%;
  max-width: 100%;
  padding: 0 1rem;
}

.main-content {
  display: flex;
  padding: 2rem 1rem 2rem 220px;
  flex: 1;
}

.sidebar {
  flex: 0 0 280px;
  position: fixed;
  top: 4rem;
  left: 0;
  height: calc(100vh - 4rem);
  overflow-y: auto;
  padding: 1rem;
  background: white;
  border-right: 1px solid #e5e7eb;
}

.content {
  flex: 1;
  width: 100%;
}

.chat-fab {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.75rem;
  cursor: pointer;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
  transition: all 0.3s ease;
  z-index: 1000;
}

.chat-fab:hover {
  transform: scale(1.1) translateY(-4px);
  box-shadow: 0 12px 32px rgba(102, 126, 234, 0.5);
}

.server-offline-message {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.offline-content {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  max-width: 500px;
  text-align: center;
}

.offline-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.offline-text h3 {
  margin-bottom: 1rem;
  color: #1f2937;
}

.offline-text p {
  margin-bottom: 1.5rem;
  color: #6b7280;
}

.retry-button,
.close-button {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  margin: 0 0.5rem;
}

.retry-button {
  background: #667eea;
  color: white;
}

.close-button {
  background: #6b7280;
  color: white;
}

@media (max-width: 768px) {
  .sidebar {
    position: relative;
    top: 0;
    left: 0;
    height: auto;
    padding: 1rem;
    border-right: none;
    border-bottom: 1px solid #e5e7eb;
  }
  
  .content {
    margin-left: 0;
  }
  
  .main-content {
    padding: 2rem 1rem;
  }
}
</style>