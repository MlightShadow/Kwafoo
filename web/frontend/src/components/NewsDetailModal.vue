<template>
  <div v-if="isOpen" class="news-detail-modal-overlay" @click="closeModal">
    <div class="news-detail-modal-content" @click.stop>
      <div class="news-detail-modal-header">
        <div class="header-left">
          <h3>📰 新闻详情</h3>
        </div>
        <div class="header-right">
          <a v-if="newsDetail?.url" :href="newsDetail.url" target="_blank" class="icon-button" title="阅读原文">
            <svg class="icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 4.5C7 4.5 2.75 7 2.75 7s-2.25-2.25-2.25-2.25S7 4.5 12 4.5zm0 1.5c2.21 0 4 1.79 4 4s-1.79 4-4 4-4-1.79-4-4 4-4 1.79-4 4-4zm-2 9c-.55 0-1 .45-1 1v1c0 .55.45 1 1 1h4c.55 0 1-.45 1-1v-1c0-.55-.45-1-1-1h-4zm0-4c-.55 0-1 .45-1 1v1c0 .55.45 1 1 1h4c.55 0 1-.45 1-1v-1c0-.55-.45-1-1-1h-4z" fill="currentColor"/>
            </svg>
          </a>
          <button class="close-button" @click="closeModal" title="关闭">
            <svg class="icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" fill="currentColor"/>
            </svg>
          </button>
        </div>
      </div>
      
      <div class="news-detail-modal-body">
        <!-- 标题和基本信息 -->
        <div class="news-detail-header">
          <h2 class="news-detail-title">{{ newsDetail?.title }}</h2>
          <div class="news-detail-meta">
            <span class="news-detail-source">{{ newsDetail?.source }}</span>
            <span class="news-detail-time">{{ formatTime(newsDetail?.publish_time) }}</span>
          </div>
        </div>

        <!-- 标签页 -->
        <div class="news-detail-tabs">
          <button 
            v-for="tab in tabs" 
            :key="tab.key"
            @click="activeTab = tab.key"
            class="tab-button"
            :class="{ active: activeTab === tab.key }"
          >
            {{ tab.label }}
          </button>
        </div>

        <!-- 内容区域 -->
        <div class="news-detail-content">
          <!-- AI摘要 -->
          <div v-if="activeTab === 'ai_summary'" class="content-section">
            <div v-if="newsDetail?.ai_summary" class="ai-summary-content">
              <div class="content-label">✨ AI摘要</div>
              <div class="content-text">{{ newsDetail.ai_summary }}</div>
            </div>
            <div v-else class="empty-content">
              <p>暂无AI摘要</p>
            </div>
          </div>

          <!-- 原文摘要 -->
          <div v-if="activeTab === 'description'" class="content-section">
            <div v-if="newsDetail?.description" class="description-content">
              <div class="content-label">📄 原文摘要</div>
              <div class="content-text">{{ newsDetail.description }}</div>
            </div>
            <div v-else class="empty-content">
              <p>暂无原文摘要</p>
            </div>
          </div>

          <!-- 正文 -->
          <div v-if="activeTab === 'content'" class="content-section">
            <div v-if="newsDetail?.content" class="content-content">
              <div class="content-label">📝 正文内容</div>
              <div class="content-text">{{ newsDetail.content }}</div>
            </div>
            <div v-else class="empty-content">
              <p>暂无正文内容</p>
            </div>
          </div>

          <!-- 压缩正文 -->
          <div v-if="activeTab === 'compressed_content'" class="content-section">
            <div v-if="newsDetail?.compressed_content" class="compressed-content-content">
              <div class="content-label">📦 压缩正文</div>
              <div class="content-text">{{ newsDetail.compressed_content }}</div>
            </div>
            <div v-else class="empty-content">
              <p>暂无压缩正文</p>
            </div>
          </div>

          <!-- AI评分 -->
          <div v-if="activeTab === 'ai_score'" class="content-section">
            <div v-if="newsDetail?.ai_score !== undefined && newsDetail?.ai_score !== null" class="ai-score-content">
              <div class="content-label">⭐ AI评分</div>
              
              <!-- 总分 -->
              <div class="score-total-section">
                <div class="score-total-label">总分</div>
                <div class="score-total-value" :class="getScoreClass(newsDetail.ai_score)">
                  {{ newsDetail.ai_score.toFixed(1) }}
                </div>
              </div>

              <!-- 维度评分 -->
              <div class="score-dimensions">
                <div class="score-dimension-item">
                  <div class="score-dimension-label">主题相关性</div>
                  <div class="score-dimension-value" :class="getScoreClass(newsDetail.ai_score_topic_relevance)">
                    {{ newsDetail.ai_score_topic_relevance?.toFixed(1) || 'N/A' }}
                  </div>
                  <div class="score-dimension-bar">
                    <div class="score-dimension-bar-fill" :style="{ width: (newsDetail.ai_score_topic_relevance || 0) + '%' }"></div>
                  </div>
                  <div v-if="newsDetail.ai_score_topic_relevance_reason" class="score-dimension-reason">
                    {{ newsDetail.ai_score_topic_relevance_reason }}
                  </div>
                </div>

                <div class="score-dimension-item">
                  <div class="score-dimension-label">重要性</div>
                  <div class="score-dimension-value" :class="getScoreClass(newsDetail.ai_score_importance)">
                    {{ newsDetail.ai_score_importance?.toFixed(1) || 'N/A' }}
                  </div>
                  <div class="score-dimension-bar">
                    <div class="score-dimension-bar-fill" :style="{ width: (newsDetail.ai_score_importance || 0) + '%' }"></div>
                  </div>
                  <div v-if="newsDetail.ai_score_importance_reason" class="score-dimension-reason">
                    {{ newsDetail.ai_score_importance_reason }}
                  </div>
                </div>

                <div class="score-dimension-item">
                  <div class="score-dimension-label">AI感官分</div>
                  <div class="score-dimension-value" :class="getScoreClass(newsDetail.ai_score_freshness)">
                    {{ newsDetail.ai_score_freshness?.toFixed(1) || 'N/A' }}
                  </div>
                  <div class="score-dimension-bar">
                    <div class="score-dimension-bar-fill" :style="{ width: (newsDetail.ai_score_freshness || 0) + '%' }"></div>
                  </div>
                </div>

                <div class="score-dimension-item">
                  <div class="score-dimension-label">来源可信度</div>
                  <div class="score-dimension-value" :class="getScoreClass(newsDetail.ai_score_source)">
                    {{ newsDetail.ai_score_source?.toFixed(1) || 'N/A' }}
                  </div>
                  <div class="score-dimension-bar">
                    <div class="score-dimension-bar-fill" :style="{ width: (newsDetail.ai_score_source || 0) + '%' }"></div>
                  </div>
                  <div v-if="newsDetail.ai_score_source_reason" class="score-dimension-reason">
                    {{ newsDetail.ai_score_source_reason }}
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="empty-content">
              <p>暂无AI评分</p>
            </div>
          </div>

          <!-- 调试信息 -->
          <div v-if="activeTab === 'debug'" class="content-section">
            <div class="debug-info-content">
              <div class="content-label">🔧 调试信息</div>
              <div class="debug-info-grid">
                <div v-for="(value, key) in debugInfo" :key="key" class="debug-info-item">
                  <div class="debug-info-label">{{ key }}</div>
                  <div class="debug-info-value">{{ value }}</div>
                </div>
              </div>
            </div>
          </div>

          <!-- 所有字段 -->
          <div v-if="activeTab === 'all_fields'" class="content-section">
            <div class="all-fields-content">
              <div class="content-label">📋 所有字段</div>
              <div v-if="Object.keys(allFields).length === 0" class="empty-content">
                <p>暂无字段数据</p>
              </div>
              <div v-else class="all-fields-list">
                <div v-for="(value, key) in allFields" :key="key" class="all-fields-row">
                  <div class="all-fields-header">
                    <div class="all-fields-label">{{ key }}</div>
                    <button 
                      v-if="shouldShowFieldCollapseButton(value)"
                      @click="toggleFieldCollapse(key)"
                      class="field-collapse-button"
                    >
                      {{ isFieldCollapsed(key) ? '展开' : '收起' }}
                    </button>
                  </div>
                  <div class="all-fields-value" :class="{ collapsible: shouldShowFieldCollapseButton(value), collapsed: isFieldCollapsed(key) }">
                    {{ value }}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- AI处理历史 -->
          <div v-if="activeTab === 'ai_history'" class="content-section">
            <div class="ai-history-content">
              <div class="content-label">🤖 AI处理历史</div>
              <div v-if="aiHistory.length === 0" class="empty-content">
                <p>暂无AI处理历史</p>
              </div>
              <div v-else class="ai-history-list">
                <div v-for="record in aiHistory" :key="record.id" class="ai-history-item">
                  <div class="ai-history-header">
                    <span class="ai-history-task-type">{{ record.task_type }}</span>
                    <span class="ai-history-status" :class="record.status">
                      {{ getStatusText(record.status) }}
                    </span>
                  </div>
                  <div class="ai-history-details">
                    <div class="ai-history-detail">
                      <span class="detail-label">任务ID:</span>
                      <span class="detail-value">{{ record.id }}</span>
                    </div>
                    <div class="ai-history-detail">
                      <span class="detail-label">优先级:</span>
                      <span class="detail-value">{{ record.priority }}</span>
                    </div>
                    <div class="ai-history-detail">
                      <span class="detail-label">重试次数:</span>
                      <span class="detail-value">{{ record.retry_count }}</span>
                    </div>
                    <div class="ai-history-detail">
                      <span class="detail-label">创建时间:</span>
                      <span class="detail-value">{{ formatTime(record.created_at) }}</span>
                    </div>
                    <div class="ai-history-detail">
                      <span class="detail-label">更新时间:</span>
                      <span class="detail-value">{{ formatTime(record.updated_at) }}</span>
                    </div>
                    <div v-if="record.error_message" class="ai-history-error">
                      <span class="detail-label">错误信息:</span>
                      <span class="detail-value error">{{ record.error_message }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { api } from '@/api'
import type { News } from '@/types/news'

interface Props {
  isOpen: boolean
  newsId: number | null
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
}>()

const activeTab = ref('ai_summary')
const newsDetail = ref<News | null>(null)
const allFields = ref<Record<string, string>>({})
const debugInfo = ref<Record<string, string>>({})
const aiHistory = ref<Array<{
  id: number;
  news_id: number;
  task_type: string;
  status: string;
  priority: number;
  retry_count: number;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}>>([])

const tabs = [
  { key: 'ai_summary', label: 'AI摘要' },
  { key: 'description', label: '原文摘要' },
  { key: 'content', label: '正文' },
  { key: 'compressed_content', label: '压缩正文' },
  { key: 'ai_score', label: 'AI评分' },
  { key: 'all_fields', label: '所有字段' },
  { key: 'ai_history', label: 'AI处理历史' },
  { key: 'debug', label: '调试信息' }
]

async function loadNewsDetail() {
  if (!props.newsId) return
  
  try {
    const response = await api.getNewsDetail(props.newsId)
    if (response.data.success) {
      newsDetail.value = response.data.data
      allFields.value = response.data.all_fields
      debugInfo.value = response.data.debug_info
      aiHistory.value = response.data.ai_history
      
      console.log('新闻详情加载成功:', {
        newsDetail: newsDetail.value,
        allFields: allFields.value,
        debugInfo: debugInfo.value,
        aiHistory: aiHistory.value
      })
    }
  } catch (error) {
    console.error('加载新闻详情失败:', error)
  }
}

function closeModal() {
  emit('close')
}

function formatTime(timeString?: string): string {
  if (!timeString) return ''
  
  const date = new Date(timeString)
  return date.toLocaleString('zh-CN', { 
    year: 'numeric', 
    month: '2-digit', 
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function getStatusText(status: string): string {
  const statusMap: Record<string, string> = {
    'pending': '等待中',
    'processing': '处理中',
    'completed': '已完成',
    'failed': '失败'
  }
  return statusMap[status] || status
}

function getScoreClass(score?: number): string {
  if (score === undefined || score === null) return ''
  if (score >= 80) return 'score-high'
  if (score >= 60) return 'score-medium'
  return 'score-low'
}

// 字段折叠状态管理
const collapsedFields = ref<Record<string, boolean>>({})

function isFieldCollapsed(key: string): boolean {
  return collapsedFields.value[key] !== false
}

function shouldShowFieldCollapseButton(value?: any): boolean {
  if (!value) return false
  const text = String(value)
  // 估算行数：假设每行约20个字符，超过100字符（约5行）才显示折叠按钮
  return text.length > 100
}

function toggleFieldCollapse(key: string) {
  collapsedFields.value[key] = !collapsedFields.value[key]
}

defineExpose({
  loadNewsDetail
})
</script>

<style scoped>
.news-detail-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 1rem;
}

.news-detail-modal-content {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 1200px;
  height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

.news-detail-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #e0e0e0;
  flex-shrink: 0;
}

.header-left h3 {
  margin: 0;
  font-size: 1.2rem;
  color: #333;
}

.header-right {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.icon-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  padding: 0;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #4b5563;
  text-decoration: none;
}

.icon-button:hover {
  background: #e5e7eb;
  border-color: #d1d5db;
  transform: translateY(-1px);
}

.icon-button .icon {
  width: 20px;
  height: 20px;
}

.close-button {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #666;
  padding: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  transition: background 0.3s ease;
}

.close-button:hover {
  background: #f5f5f5;
}

.close-button .icon {
  width: 20px;
  height: 20px;
}

.news-detail-modal-body {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
  padding: 1.5rem;
  min-height: 0;
}

.news-detail-header {
  margin-bottom: 1.5rem;
  flex-shrink: 0;
}

.news-detail-title {
  margin: 0 0 0.75rem 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: #1f2937;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.news-detail-meta {
  display: flex;
  gap: 1rem;
  align-items: center;
  flex-wrap: wrap;
  font-size: 0.875rem;
  color: #6b7280;
}

.news-detail-source {
  padding: 0.25rem 0.75rem;
  background: #f3f4f6;
  border-radius: 9999px;
  font-weight: 500;
}

.news-detail-time {
  color: #6b7280;
}

.news-detail-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
  border-bottom: 1px solid #e0e0e0;
  padding-bottom: 0.5rem;
  overflow-x: auto;
  flex-shrink: 0;
}

.tab-button {
  padding: 0.5rem 1rem;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 0.875rem;
  color: #6b7280;
  border-radius: 6px;
  transition: all 0.2s ease;
  white-space: nowrap;
  flex-shrink: 0;
}

.tab-button:hover {
  background: #f5f5f5;
}

.tab-button.active {
  background: #667eea;
  color: white;
}

.news-detail-content {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
  max-height: calc(90vh - 280px);
  padding-right: 0.5rem;
}

.news-detail-content::-webkit-scrollbar {
  width: 6px;
}

.news-detail-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.news-detail-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.news-detail-content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.content-section {
  padding: 1rem;
}

.content-label {
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.75rem;
  font-size: 1rem;
}

.content-text {
  color: #374151;
  line-height: 1.8;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: 0.9375rem;
}

.ai-summary-content {
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
  border-left: 3px solid #10b981;
  border-radius: 6px;
  padding: 1rem;
}

.description-content {
  background: #f9fafb;
  border-left: 3px solid #6b7280;
  border-radius: 6px;
  padding: 1rem;
}

.content-content {
  background: #ffffff;
  border-left: 3px solid #667eea;
  border-radius: 6px;
  padding: 1rem;
  border: 1px solid #e5e7eb;
}

.compressed-content-content {
  background: #fef3c7;
  border-left: 3px solid #f59e0b;
  border-radius: 6px;
  padding: 1rem;
}

.debug-info-content {
  background: #1f2937;
  border-radius: 6px;
  padding: 1rem;
}

.debug-info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 0.75rem;
}

.debug-info-item {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  padding: 0.75rem;
}

.debug-info-label {
  font-size: 0.75rem;
  color: #9ca3af;
  margin-bottom: 0.25rem;
}

.debug-info-value {
  font-size: 0.875rem;
  color: #f3f4f6;
  word-break: break-word;
}

/* 所有字段样式 */
.all-fields-content {
  background: #f0f9ff;
  border-left: 3px solid #0ea5e9;
  border-radius: 6px;
  padding: 1rem;
}

.all-fields-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.all-fields-row {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  background: white;
  border-radius: 6px;
  padding: 0.875rem;
  border: 1px solid #e5e7eb;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.all-fields-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
}

.all-fields-label {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 600;
}

.all-fields-value {
  font-size: 0.9375rem;
  color: #1f2937;
  word-break: break-word;
  line-height: 1.6;
  white-space: pre-wrap;
}

/* 所有字段折叠功能样式 */
.all-fields-value.collapsible {
  transition: max-height 0.3s ease;
  overflow: hidden;
}

.all-fields-value.collapsible.collapsed {
  max-height: 72px; /* 3行高度：line-height 1.6 * font-size 0.9375rem ≈ 24px/行 * 3行 = 72px */
  position: relative;
}

.all-fields-value.collapsible.collapsed::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 30px;
  background: linear-gradient(transparent, rgba(255, 255, 255, 0.95));
  pointer-events: none;
}

.field-collapse-button {
  padding: 0.25rem 0.625rem;
  font-size: 0.75rem;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 4px;
  cursor: pointer;
  color: #3b82f6;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.field-collapse-button:hover {
  background: #dbeafe;
  border-color: #93c5fd;
}

.field-collapse-button:active {
  transform: scale(0.98);
}

/* AI处理历史样式 */
.ai-history-content {
  background: #fefce8;
  border-left: 3px solid #eab308;
  border-radius: 6px;
  padding: 1rem;
}

.ai-history-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.ai-history-item {
  background: white;
  border-radius: 8px;
  padding: 1rem;
  border: 1px solid #e5e7eb;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.ai-history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.ai-history-task-type {
  font-weight: 600;
  color: #1f2937;
  font-size: 0.9375rem;
}

.ai-history-status {
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 500;
}

.ai-history-status.pending {
  background: #fef3c7;
  color: #92400e;
}

.ai-history-status.processing {
  background: #dbeafe;
  color: #1e40af;
}

.ai-history-status.completed {
  background: #dcfce7;
  color: #166534;
}

.ai-history-status.failed {
  background: #fee2e2;
  color: #991b1b;
}

.ai-history-details {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.ai-history-detail {
  display: flex;
  gap: 0.5rem;
  font-size: 0.875rem;
}

.ai-history-error {
  display: flex;
  gap: 0.5rem;
  font-size: 0.875rem;
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: #fef2f2;
  border-radius: 4px;
}

.detail-label {
  color: #6b7280;
  font-weight: 500;
  min-width: 80px;
}

.detail-value {
  color: #1f2937;
  word-break: break-word;
  flex: 1;
}

.detail-value.error {
  color: #dc2626;
}

.empty-content {
  text-align: center;
  padding: 3rem 1rem;
  color: #9ca3af;
}

.empty-content p {
  margin: 0;
  font-size: 1rem;
}

/* AI评分样式 */
.ai-score-content {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border-left: 3px solid #f59e0b;
  border-radius: 6px;
  padding: 1.5rem;
}

.score-total-section {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.score-total-label {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
}

.score-total-value {
  font-size: 2rem;
  font-weight: 700;
  padding: 0.5rem 1.5rem;
  border-radius: 8px;
  min-width: 100px;
  text-align: center;
}

.score-total-value.score-high {
  background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
  color: #166534;
  border: 2px solid #22c55e;
}

.score-total-value.score-medium {
  background: linear-gradient(135deg, #fef9c3 0%, #fef08a 100%);
  color: #854d0e;
  border: 2px solid #eab308;
}

.score-total-value.score-low {
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
  color: #991b1b;
  border: 2px solid #ef4444;
}

.score-dimensions {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.score-dimension-item {
  background: white;
  border-radius: 8px;
  padding: 1rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.score-dimension-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #6b7280;
}

.score-dimension-value {
  font-size: 1.5rem;
  font-weight: 600;
  padding: 0.25rem 0.75rem;
  border-radius: 6px;
  text-align: center;
}

.score-dimension-value.score-high {
  background: #dcfce7;
  color: #166534;
  border: 1px solid #22c55e;
}

.score-dimension-value.score-medium {
  background: #fef9c3;
  color: #854d0e;
  border: 1px solid #eab308;
}

.score-dimension-value.score-low {
  background: #fee2e2;
  color: #991b1b;
  border: 1px solid #ef4444;
}

.score-dimension-bar {
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
  margin-top: 0.25rem;
}

.score-dimension-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  border-radius: 4px;
  transition: width 0.5s ease;
}

.score-dimension-reason {
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: #f9fafb;
  border-left: 3px solid #667eea;
  border-radius: 4px;
  font-size: 0.875rem;
  color: #4b5563;
  line-height: 1.5;
}

@media (max-width: 768px) {
  .news-detail-modal-content {
    max-height: 95vh;
    border-radius: 8px;
  }
  
  .news-detail-modal-body {
    padding: 1rem;
  }
  
  .news-detail-title {
    font-size: 1.25rem;
  }
  
  .news-detail-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .news-detail-tabs {
    flex-wrap: nowrap;
    overflow-x: auto;
  }
  
  .debug-info-grid {
    grid-template-columns: 1fr;
  }
}
</style>