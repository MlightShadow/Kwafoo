<template>
  <div class="modal-overlay" @click="close">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h2 class="modal-title">{{ report.title }}</h2>
        <button class="close-button" @click="close">✕</button>
      </div>

      <div class="modal-body">
        <div v-if="loading" class="loading">
          <div class="spinner"></div>
          <p>加载中...</p>
        </div>

        <div v-else-if="report.content" class="report-content">
          <div class="report-summary">
            <h3>📋 整体综述</h3>
            <p>{{ report.content.summary }}</p>
          </div>

          <div class="topics-section">
            <h3>📰 话题分组</h3>
            <div
              v-for="(topic, index) in report.content.topics"
              :key="index"
              class="topic-card"
            >
              <div class="topic-header">
                <h4 class="topic-title">{{ topic.topic_title }}</h4>
              </div>

              <div class="topic-summary">
                <h5>📝 话题综述</h5>
                <p>{{ topic.topic_summary }}</p>
              </div>

              <div class="topic-reasoning">
                <h5>🔍 梳理原因</h5>
                <p>{{ topic.reasoning }}</p>
              </div>

              <div class="topic-news">
                <h5>📰 涉及新闻 ({{ topic.news_items.length }})</h5>
                <div class="news-items">
                  <div
                    v-for="item in topic.news_items"
                    :key="item.id"
                    class="news-item"
                  >
                    <div class="news-item-header">
                      <span class="news-item-category">{{ item.category }}</span>
                      <span class="news-item-time">{{ formatTime(item.publish_time) }}</span>
                    </div>
                    <h6 class="news-item-title">{{ item.title }}</h6>
                    <p class="news-item-summary">{{ item.ai_summary }}</p>
                    <div class="news-item-footer">
                      <span class="news-item-source">{{ item.source }}</span>
                      <a
                        v-if="item.url"
                        :href="item.url"
                        target="_blank"
                        class="news-item-link"
                      >
                        查看原文 →
                      </a>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="report-meta">
            <div class="meta-row">
              <span class="meta-label">生成时间：</span>
              <span class="meta-value">{{ formatTime(report.created_at) }}</span>
            </div>
            <div class="meta-row">
              <span class="meta-label">新闻数量：</span>
              <span class="meta-value">{{ report.news_count }}</span>
            </div>
            <div class="meta-row">
              <span class="meta-label">生成耗时：</span>
              <span class="meta-value">{{ report.generation_time.toFixed(2) }}秒</span>
            </div>
            <div class="meta-row">
              <span class="meta-label">AI模型：</span>
              <span class="meta-value">{{ report.ai_model }}</span>
            </div>
          </div>
        </div>

        <div v-else class="error-state">
          <div class="error-icon">⚠️</div>
          <p>报告内容加载失败</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { api } from '@/api'
import type { Report } from '@/types/report'

const props = defineProps<{
  report: Report
}>()

const emit = defineEmits<{
  close: []
}>()

const loading = ref(false)
const report = ref<Report>(props.report)

watch(() => props.report, (newReport) => {
  report.value = newReport
  if (newReport && !newReport.content) {
    loadReportDetail(newReport.id)
  }
}, { immediate: true })

async function loadReportDetail(reportId: number) {
  loading.value = true
  try {
    const response = await api.getReportDetail(reportId)
    if (response.data.success) {
      report.value = response.data.data
    }
  } catch (error) {
    console.error('加载报告详情失败:', error)
  } finally {
    loading.value = false
  }
}

function close() {
  emit('close')
}

function formatTime(time: string): string {
  const date = new Date(time)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 1rem;
}

.modal-content {
  background: white;
  border-radius: 12px;
  max-width: 900px;
  max-height: 90vh;
  width: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.modal-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.close-button {
  width: 32px;
  height: 32px;
  border: none;
  background: #f3f4f6;
  border-radius: 50%;
  cursor: pointer;
  font-size: 1.25rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.close-button:hover {
  background: #e5e7eb;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
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

.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem;
  color: #6b7280;
}

.error-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.report-content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.report-summary {
  background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
  padding: 1.5rem;
  border-radius: 8px;
  border-left: 4px solid #667eea;
}

.report-summary h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 0.75rem 0;
}

.report-summary p {
  color: #4b5563;
  line-height: 1.6;
  margin: 0;
}

.topics-section {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.topics-section h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.topic-card {
  background: #f9fafb;
  border-radius: 8px;
  padding: 1.5rem;
  border: 1px solid #e5e7eb;
}

.topic-header {
  margin-bottom: 1rem;
}

.topic-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.topic-summary,
.topic-reasoning,
.topic-news {
  margin-bottom: 1.5rem;
}

.topic-summary h5,
.topic-reasoning h5,
.topic-news h5 {
  font-size: 0.875rem;
  font-weight: 600;
  color: #6b7280;
  margin: 0 0 0.5rem 0;
}

.topic-summary p,
.topic-reasoning p {
  color: #4b5563;
  line-height: 1.6;
  margin: 0;
}

.news-items {
  display: grid;
  gap: 1rem;
}

.news-item {
  background: white;
  padding: 1rem;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.news-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.news-item-category {
  padding: 0.25rem 0.5rem;
  background: #667eea;
  color: white;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

.news-item-time {
  font-size: 0.75rem;
  color: #6b7280;
}

.news-item-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 0.5rem 0;
}

.news-item-summary {
  font-size: 0.875rem;
  color: #4b5563;
  line-height: 1.5;
  margin: 0 0 0.75rem 0;
}

.news-item-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.news-item-source {
  font-size: 0.75rem;
  color: #6b7280;
}

.news-item-link {
  font-size: 0.75rem;
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
}

.news-item-link:hover {
  text-decoration: underline;
}

.report-meta {
  background: #f9fafb;
  padding: 1rem;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.meta-row {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  border-bottom: 1px solid #e5e7eb;
}

.meta-row:last-child {
  border-bottom: none;
}

.meta-label {
  color: #6b7280;
  font-size: 0.875rem;
}

.meta-value {
  color: #1f2937;
  font-weight: 600;
  font-size: 0.875rem;
}
</style>