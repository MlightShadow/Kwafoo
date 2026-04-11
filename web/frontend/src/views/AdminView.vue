<template>
  <div class="admin-view">
    <div class="page-header">
      <h2>⚙️ 管理界面</h2>
    </div>

    <div class="admin-content">
      <div class="admin-section">
        <h3>📊 新闻统计</h3>
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-label">总新闻数</div>
            <div class="stat-value">{{ stats?.total || 0 }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">活跃新闻</div>
            <div class="stat-value">{{ stats?.active || 0 }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">已删除</div>
            <div class="stat-value">{{ stats?.deleted || 0 }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">已处理</div>
            <div class="stat-value">{{ stats?.processed || 0 }}</div>
          </div>
        </div>
      </div>

      <div class="admin-section">
        <h3>🔄 快捷操作</h3>
        <div class="quick-actions">
          <button @click="handleFetch" class="action-button primary">
            🔄 手动抓取新闻
          </button>
          <button @click="handleAIProcess" class="action-button success">
            🤖 AI分析新闻
          </button>
          <button @click="handleClearNews" class="action-button danger">
            🗑️ 清空新闻数据
          </button>
        </div>
      </div>

      <div class="admin-section">
        <h3>📰 新闻源管理</h3>
        <div class="config-form">
          <div class="form-group">
            <label>RSS订阅源</label>
            <textarea 
              v-model="rssSources" 
              placeholder="每行一个RSS订阅源URL"
              rows="4"
            ></textarea>
          </div>
          <div class="form-group">
            <label>API接口</label>
            <textarea 
              v-model="apiSources" 
              placeholder="每行一个API接口配置"
              rows="4"
            ></textarea>
          </div>
          <button @click="saveNewsSources" class="save-button">
            💾 保存新闻源配置
          </button>
        </div>
      </div>

      <div class="admin-section">
        <h3>🤖 AI配置</h3>
        <div class="config-form">
          <div class="form-group">
            <label>AI服务地址</label>
            <input 
              v-model="aiConfig.base_url" 
              type="text"
              placeholder="http://localhost:1234"
            >
          </div>
          <div class="form-group">
            <label>模型名称</label>
            <input 
              v-model="aiConfig.model" 
              type="text"
              placeholder="nvidia/nemotron-3-nano-4b"
            >
          </div>
          <div class="form-group">
            <label>最大Token数</label>
            <input 
              v-model.number="aiConfig.max_tokens" 
              type="number"
              min="1"
            >
          </div>
          <div class="form-group">
            <label>温度参数</label>
            <input 
              v-model.number="aiConfig.temperature" 
              type="number"
              min="0"
              max="2"
              step="0.1"
            >
          </div>
          <div class="form-group">
            <label>最大并发数</label>
            <input 
              v-model.number="aiConfig.max_workers" 
              type="number"
              min="1"
            >
          </div>
          <button @click="saveAIConfig" class="save-button">
            💾 保存AI配置
          </button>
        </div>
      </div>

      <div class="admin-section">
        <h3>⏰ 调度配置</h3>
        <div class="config-form">
          <div class="form-group">
            <label>抓取间隔（秒）</label>
            <input 
              v-model.number="schedulerConfig.fetch_interval" 
              type="number"
              min="60"
            >
          </div>
          <div class="form-group">
            <label>AI处理间隔（秒）</label>
            <input 
              v-model.number="schedulerConfig.ai_process_interval" 
              type="number"
              min="60"
            >
          </div>
          <div class="form-group checkbox-group">
            <label>
              <input 
                v-model="schedulerConfig.auto_fetch" 
                type="checkbox"
              >
              自动抓取新闻
            </label>
          </div>
          <div class="form-group checkbox-group">
            <label>
              <input 
                v-model="schedulerConfig.auto_ai_process" 
                type="checkbox"
              >
              自动AI处理
            </label>
          </div>
          <div class="form-group checkbox-group">
            <label>
              <input 
                v-model="schedulerConfig.auto_ai_after_fetch" 
                type="checkbox"
              >
              抓取后自动AI处理
            </label>
          </div>
          <button @click="saveSchedulerConfig" class="save-button">
            💾 保存调度配置
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useNewsStore } from '@/stores/news'
import { useConfigStore } from '@/stores/config'
import { api } from '@/api'

const newsStore = useNewsStore()
const configStore = useConfigStore()

const stats = computed(() => newsStore.stats)
const config = computed(() => configStore.config)

const rssSources = ref('')
const apiSources = ref('')

const aiConfig = ref({
  base_url: 'http://localhost:1234',
  model: 'nvidia/nemotron-3-nano-4b',
  max_tokens: 4096,
  temperature: 0.7,
  max_workers: 1
})

const schedulerConfig = ref({
  fetch_interval: 1800,
  ai_process_interval: 600,
  auto_fetch: false,
  auto_ai_process: false,
  auto_ai_after_fetch: false
})

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

async function handleClearNews() {
  if (!confirm('确定要清空所有新闻吗？此操作不可恢复！')) return
  
  try {
    const response = await api.clearNews()
    if (response.data.success) {
      alert(response.data.message)
      await newsStore.loadNews()
      await newsStore.loadStats()
    }
  } catch (error: any) {
    alert('清空新闻失败: ' + error.message)
  }
}

async function saveNewsSources() {
  try {
    const newsSources = {
      rss: rssSources.value.split('\n').filter(url => url.trim()),
      api: apiSources.value.split('\n').filter(url => url.trim())
    }
    await configStore.updateConfig({ news_sources: newsSources })
    alert('新闻源配置保存成功')
  } catch (error: any) {
    alert('保存失败: ' + error.message)
  }
}

async function saveAIConfig() {
  try {
    await configStore.updateConfig({ ai: aiConfig.value })
    alert('AI配置保存成功')
  } catch (error: any) {
    alert('保存失败: ' + error.message)
  }
}

async function saveSchedulerConfig() {
  try {
    await configStore.updateConfig({ scheduler: schedulerConfig.value })
    alert('调度配置保存成功')
  } catch (error: any) {
    alert('保存失败: ' + error.message)
  }
}

onMounted(async () => {
  await newsStore.loadStats()
  await configStore.loadConfig()
  
  if (config.value) {
    if (config.value.news_sources) {
      rssSources.value = (config.value.news_sources as any).rss?.join('\n') || ''
      apiSources.value = (config.value.news_sources as any).api?.join('\n') || ''
    }
    if (config.value.ai) {
      Object.assign(aiConfig.value, config.value.ai)
    }
    if (config.value.scheduler) {
      Object.assign(schedulerConfig.value, config.value.scheduler)
    }
  }
})
</script>

<style scoped>
.admin-view {
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

.admin-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 1.5rem;
}

.admin-section {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.admin-section h3 {
  margin: 0 0 1.5rem 0;
  color: #333;
  font-size: 1.2rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
}

.stat-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1.5rem;
  border-radius: 8px;
  text-align: center;
}

.stat-label {
  font-size: 0.9rem;
  opacity: 0.9;
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 2rem;
  font-weight: bold;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.action-button {
  padding: 0.75rem 1rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.3s ease;
  color: white;
}

.action-button.primary {
  background: #007bff;
}

.action-button.primary:hover {
  background: #0056b3;
}

.action-button.success {
  background: #28a745;
}

.action-button.success:hover {
  background: #218838;
}

.action-button.danger {
  background: #dc3545;
}

.action-button.danger:hover {
  background: #c82333;
}

.config-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: 500;
  color: #333;
}

.form-group input,
.form-group textarea {
  padding: 0.75rem;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 1rem;
  font-family: inherit;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #007bff;
}

.form-group textarea {
  resize: vertical;
  font-family: monospace;
}

.form-group.checkbox-group {
  flex-direction: row;
  align-items: center;
  gap: 0.5rem;
}

.form-group.checkbox-group input {
  width: auto;
}

.save-button {
  padding: 0.75rem 1.5rem;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
  transition: background 0.3s ease;
  align-self: flex-start;
}

.save-button:hover {
  background: #0056b3;
}

@media (max-width: 768px) {
  .admin-content {
    grid-template-columns: 1fr;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>