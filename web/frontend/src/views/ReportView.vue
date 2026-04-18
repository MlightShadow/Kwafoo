<template>
  <div class="report-view">
    <div class="page-header">
      <h2>📊 报告中心</h2>
    </div>

    <div class="report-controls">
      <div class="report-type-tabs">
        <button
          v-for="type in reportTypes"
          :key="type.value"
          :class="['tab-button', { active: currentType === type.value }]"
          @click="switchType(type.value)"
        >
          {{ type.label }}
        </button>
      </div>

      <button
        @click="generateReport"
        :disabled="generating"
        class="generate-button"
      >
        {{ generating ? '生成中...' : '🚀 生成报告' }}
      </button>
    </div>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>加载中...</p>
    </div>

    <div v-else-if="reports.length === 0" class="empty-state">
      <div class="empty-icon">📭</div>
      <p>暂无报告</p>
      <button @click="generateReport" class="generate-first-button">
        生成第一份报告
      </button>
    </div>

    <div v-else class="report-list">
      <div
        v-for="report in reports"
        :key="report.id"
        class="report-card"
        @click="viewReport(report)"
      >
        <div class="report-header">
          <h3 class="report-title">{{ report.title }}</h3>
          <span class="report-time">{{ formatTime(report.created_at) }}</span>
        </div>

        <div class="report-meta">
          <div class="meta-item">
            <span class="meta-label">新闻数量</span>
            <span class="meta-value">{{ report.news_count }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">生成耗时</span>
            <span class="meta-value">{{ report.generation_time.toFixed(2) }}s</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">AI模型</span>
            <span class="meta-value">{{ report.ai_model }}</span>
          </div>
        </div>

        <div class="report-footer">
          <button class="view-button" @click.stop="viewReport(report)">
            查看详情
          </button>
          <button class="delete-button" @click.stop="deleteReport(report.id)">
            删除
          </button>
        </div>
      </div>
    </div>

    <div v-if="hasMore" class="load-more">
      <button @click="loadMore" :disabled="loadingMore">
        {{ loadingMore ? '加载中...' : '加载更多' }}
      </button>
    </div>

    <ReportDetailModal
      v-if="selectedReport"
      :report="selectedReport"
      @close="closeModal"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/api'
import type { Report } from '@/types/report'
import ReportDetailModal from '@/components/ReportDetailModal.vue'

const reportTypes = [
  { value: 'daily', label: '日报' },
  { value: 'weekly', label: '周报' },
  { value: 'monthly', label: '月报' }
]

const currentType = ref<'daily' | 'weekly' | 'monthly'>('daily')
const reports = ref<Report[]>([])
const loading = ref(false)
const loadingMore = ref(false)
const generating = ref(false)
const selectedReport = ref<Report | null>(null)
const hasMore = ref(false)
const offset = ref(0)
const limit = 10

async function loadReports() {
  loading.value = true
  try {
    const response = await api.getReports({
      type: currentType.value,
      limit,
      offset: offset.value
    })

    if (response.data.success) {
      if (offset.value === 0) {
        reports.value = response.data.data
      } else {
        reports.value.push(...response.data.data)
      }
      hasMore.value = response.data.data.length === limit
    }
  } catch (error) {
    console.error('加载报告失败:', error)
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  offset.value += limit
  loadingMore.value = true
  await loadReports()
  loadingMore.value = false
}

function switchType(type: 'daily' | 'weekly' | 'monthly') {
  currentType.value = type
  offset.value = 0
  reports.value = []
  loadReports()
}

async function generateReport() {
  generating.value = true
  try {
    const hours = currentType.value === 'daily' ? 24 : currentType.value === 'weekly' ? 168 : 720
    const response = await api.generateReport({
      report_type: currentType.value,
      hours
    })

    if (response.data.success) {
      alert(`报告生成成功！\n标题：${response.data.report_title}\n新闻数量：${response.data.news_count}`)
      offset.value = 0
      loadReports()
    } else {
      alert('报告生成失败：' + (response.data.message || '未知错误'))
    }
  } catch (error: any) {
    console.error('生成报告失败:', error)
    alert('报告生成失败：' + (error.response?.data?.error || error.message || '未知错误'))
  } finally {
    generating.value = false
  }
}

function viewReport(report: Report) {
  selectedReport.value = report
}

function closeModal() {
  selectedReport.value = null
}

async function deleteReport(id: number) {
  if (!confirm('确定要删除这份报告吗？')) {
    return
  }

  try {
    const response = await api.deleteReport(id)
    if (response.data.success) {
      alert('报告删除成功')
      offset.value = 0
      loadReports()
    } else {
      alert('报告删除失败')
    }
  } catch (error) {
    console.error('删除报告失败:', error)
    alert('报告删除失败')
  }
}

function formatTime(time: string): string {
  const date = new Date(time)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString('zh-CN')
}

onMounted(() => {
  loadReports()
})
</script>

<style scoped>
.report-view {
  padding: 2rem;
}

.page-header {
  margin-bottom: 2rem;
}

.page-header h2 {
  font-size: 2rem;
  color: #1f2937;
  margin: 0;
}

.report-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  gap: 1rem;
}

.report-type-tabs {
  display: flex;
  gap: 0.5rem;
  background: #f3f4f6;
  padding: 0.25rem;
  border-radius: 8px;
}

.tab-button {
  padding: 0.5rem 1.5rem;
  border: none;
  background: transparent;
  color: #6b7280;
  cursor: pointer;
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.tab-button:hover {
  color: #4b5563;
}

.tab-button.active {
  background: white;
  color: #667eea;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.generate-button {
  padding: 0.5rem 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s ease;
}

.generate-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.generate-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem;
  color: #6b7280;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e5e7eb;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem;
  color: #6b7280;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.generate-first-button {
  margin-top: 1rem;
  padding: 0.5rem 1.5rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
}

.report-list {
  display: grid;
  gap: 1.5rem;
}

.report-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.2s ease;
}

.report-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.report-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.report-time {
  font-size: 0.875rem;
  color: #6b7280;
}

.report-meta {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e5e7eb;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.meta-label {
  font-size: 0.75rem;
  color: #6b7280;
  font-weight: 500;
}

.meta-value {
  font-size: 0.875rem;
  color: #1f2937;
  font-weight: 600;
}

.report-footer {
  display: flex;
  gap: 0.5rem;
}

.view-button,
.delete-button {
  flex: 1;
  padding: 0.5rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s ease;
}

.view-button {
  background: #667eea;
  color: white;
}

.view-button:hover {
  background: #5568d3;
}

.delete-button {
  background: #f3f4f6;
  color: #6b7280;
}

.delete-button:hover {
  background: #e5e7eb;
  color: #ef4444;
}

.load-more {
  display: flex;
  justify-content: center;
  margin-top: 2rem;
}

.load-more button {
  padding: 0.75rem 2rem;
  background: #f3f4f6;
  color: #6b7280;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s ease;
}

.load-more button:hover:not(:disabled) {
  background: #e5e7eb;
  color: #4b5563;
}

.load-more button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>