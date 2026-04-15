<template>
  <div class="app-container">
    <header class="app-header">
      <div class="container">
        <h1>📰 Kwafoo 新闻聚合</h1>
        <p class="subtitle">夸父追日，永不止步</p>
      </div>
    </header>

    <div class="top-nav">
      <div class="container">
        <nav class="main-nav">
          <router-link to="/" class="nav-link" active-class="active">
            📰 新闻
          </router-link>
          <router-link to="/monitor" class="nav-link" active-class="active">
            📊 监控
          </router-link>
          <router-link to="/admin" class="nav-link" active-class="active">
            ⚙️ 管理
          </router-link>
        </nav>
        
        <div class="search-section">
          <input 
            v-model="searchQuery" 
            type="text" 
            placeholder="搜索新闻..." 
            class="search-input"
            @keypress.enter="handleSearch"
          >
          <button @click="handleSearch" class="search-btn">🔍</button>
        </div>
        
        <div class="status-section">
          <div class="server-status" :class="{ online: isServerOnline, offline: !isServerOnline }">
            {{ isServerOnline ? '在线' : '离线' }}
          </div>
          <div class="system-status">
            <span v-if="runningTasks.length > 0" class="status-running">
              ⏳ {{ runningTasks.map(t => t.name).join(', ') }}
            </span>
            <span v-else class="status-idle">✅ 系统运行正常</span>
          </div>
        </div>
      </div>
    </div>

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
  if (configStore.config?.categories) {
    newsStore.setCategories(configStore.config.categories)
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
  padding: 2.5rem 0;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.app-header h1 {
  font-size: 2.25rem;
  margin-bottom: 0.5rem;
  font-weight: 700;
  letter-spacing: -0.025em;
}

.subtitle {
  opacity: 0.95;
  font-size: 1.125rem;
  font-weight: 300;
}

.container {
  width: 100%;
  max-width: 100%;
  padding: 0 1rem;
}

.top-nav {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid #e5e7eb;
  padding: 1rem 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  position: sticky;
  top: 0;
  z-index: 1000;
}

.top-nav .container {
  display: flex;
  align-items: center;
  gap: 2rem;
}

.main-nav {
  display: flex;
  gap: 1rem;
}

.nav-link {
  padding: 0.75rem 1.5rem;
  color: #4b5563;
  text-decoration: none;
  border-radius: 8px;
  transition: all 0.2s ease;
  font-weight: 600;
}

.nav-link:hover {
  background: #f3f4f6;
  color: #667eea;
}

.nav-link.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.search-section {
  flex: 1;
  display: flex;
  gap: 0.5rem;
}

.search-input {
  flex: 1;
  padding: 0.75rem 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.2s ease;
  background: white;
}

.search-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.search-btn {
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 600;
  transition: all 0.2s ease;
}

.search-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.status-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-width: 200px;
}

.server-status {
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-weight: 500;
  text-align: center;
}

.server-status.online {
  background: #d4edda;
  color: #155724;
}

.server-status.offline {
  background: #f8d7da;
  color: #721c24;
}

.system-status {
  font-size: 0.85rem;
  text-align: center;
}

.status-running {
  color: #667eea;
  font-weight: 500;
}

.status-idle {
  color: #10b981;
}

.main-content {
  display: flex;
  gap: 2rem;
  padding: 2rem 1rem;
  flex: 1;
}

.sidebar {
  flex: 0 0 280px;
  position: sticky;
  top: 6rem;
  height: calc(100vh - 8rem);
  overflow-y: auto;
}

.content {
  flex: 1;
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
</style>