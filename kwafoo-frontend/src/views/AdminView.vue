<template>
  <div class="admin-view">
    <header class="admin-header">
      <h1>管理面板</h1>
      <nav>
        <router-link to="/">新闻</router-link>
        <router-link to="/admin">管理</router-link>
      </nav>
    </header>

    <div class="stats-card" v-if="taskStatus">
      <h2>系统状态</h2>
      <div class="stats-grid">
        <div class="stat-item">
          <span class="stat-label">总数量</span>
          <span class="stat-value">{{ taskStatus.total_count }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">未处理</span>
          <span class="stat-value">{{ taskStatus.unprocessed_count }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">管道状态</span>
          <span class="stat-value">{{ taskStatus.pipeline_running ? '运行中' : '空闲' }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">定时任务</span>
          <span class="stat-value">{{ taskStatus.scheduler_jobs?.length ?? 0 }}</span>
        </div>
      </div>
    </div>

    <div v-if="message" class="message">{{ message }}</div>

    <div class="actions-card">
      <h2>操作</h2>
      <div class="action-buttons">
        <button @click="doCrawl" :disabled="loading">
          触发爬虫
        </button>
        <button @click="doProcess" :disabled="loading">
          触发处理
        </button>
        <button @click="doPipeline" :disabled="loading">
          完整管道
        </button>
        <button @click="refreshStatus" :disabled="loading">
          刷新状态
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useTasks } from '@/composables/useTasks'

const {
  taskStatus,
  loading,
  message,
  fetchStatus,
  triggerCrawl,
  triggerProcess,
  triggerPipeline,
} = useTasks()

async function doCrawl() {
  await triggerCrawl()
  await fetchStatus()
}

async function doProcess() {
  await triggerProcess()
  await fetchStatus()
}

async function doPipeline() {
  await triggerPipeline()
  await fetchStatus()
}

async function refreshStatus() {
  await fetchStatus()
}

onMounted(() => {
  refreshStatus()
})
</script>

<style scoped>
.admin-view {
  max-width: 800px;
  margin: 0 auto;
  padding: 16px;
}

.admin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e0e0e0;
}

.admin-header h1 {
  font-size: 24px;
}

.admin-header nav a {
  margin-left: 16px;
  color: #666;
  text-decoration: none;
}

.admin-header nav a.router-link-active {
  color: #1a73e8;
}

.stats-card,
.actions-card {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.stats-card h2,
.actions-card h2 {
  font-size: 18px;
  margin-bottom: 16px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.stat-item {
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: 13px;
  color: #999;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #1a1a1a;
}

.action-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.action-buttons button {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  background: #1a73e8;
  color: #fff;
  font-size: 14px;
  cursor: pointer;
}

.action-buttons button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-buttons button:hover:not(:disabled) {
  background: #1557b0;
}

.message {
  background: #e8f5e9;
  color: #2e7d32;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}
</style>