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
      <aside class="sidebar">
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
import { useRouter } from 'vue-router'
import CategoryList from '@/components/CategoryList.vue'
import ChatModal from '@/components/ChatModal.vue'
import { useNewsStore } from '@/stores/news'
import { useConfigStore } from '@/stores/config'
import { api } from '@/api'

const router = useRouter()
const newsStore = useNewsStore()
const configStore = useConfigStore()

const searchQuery = ref('')
const isServerOnline = ref(true)
const showChatModal = ref(false)
const showOfflineMessage = ref(false)
const userClosedOfflineMessage = ref(false)
const tasks = ref<any[]>([])

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
  background: #f5f5f5;
  color: #333;
}

.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 2rem 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.app-header h1 {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.subtitle {
  opacity: 0.9;
  font-size: 1rem;
}

.container {
  width: 100%;
  max-width: 100%;
  padding: 0 1rem;
}

.top-nav {
  background: white;
  border-bottom: 1px solid #e0e0e0;
  padding: 1rem 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
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
  color: #333;
  text-decoration: none;
  border-radius: 6px;
  transition: all 0.3s ease;
  font-weight: 500;
}

.nav-link:hover {
  background: #f5f5f5;
  color: #007bff;
}

.nav-link.active {
  background: #007bff;
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
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 1rem;
}

.search-btn {
  padding: 0.75rem 1.5rem;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
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
  color: #007bff;
  font-weight: 500;
}

.status-idle {
  color: #28a745;
}

.main-content {
  display: flex;
  gap: 2rem;
  padding: 2rem 1rem;
  flex: 1;
}

.sidebar {
  flex: 0 0 250px;
}

.content {
  flex: 1;
}

.chat-fab {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: #007bff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transition: transform 0.3s ease;
  z-index: 1000;
}

.chat-fab:hover {
  transform: scale(1.1);
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
  color: #333;
}

.offline-text p {
  margin-bottom: 1.5rem;
  color: #666;
}

.retry-button,
.close-button {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
  margin: 0 0.5rem;
}

.retry-button {
  background: #007bff;
  color: white;
}

.close-button {
  background: #6c757d;
  color: white;
}
</style>