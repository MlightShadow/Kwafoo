<template>
  <div class="news-card" :data-id="news.id" :class="{ 'ai-processing': aiProcessing }">
    <!-- 图片背景装饰 -->
    <div v-if="showThumbnail && imageUrl" class="news-card-background" :class="imagePositionClass">
      <img 
        :src="imageUrl" 
        :alt="news.title" 
        loading="lazy"
        @error="handleImageError"
        class="background-image"
      >
      <div class="background-overlay"></div>
    </div>
    
    <!-- 分类颜色背景（无图片时） -->
    <div v-else class="news-card-background category-background" :style="categoryBackgroundStyle">
      <div class="background-overlay"></div>
    </div>
    
    <!-- 重新分析按钮 -->
    <button 
      @click="handleReanalyze" 
      class="reanalyze-btn"
      :disabled="aiProcessing"
      title="重新分析"
    >
      <span v-if="aiProcessing" class="spinner"></span>
      <span v-else>🔄</span>
    </button>
    
    <!-- 主要内容区域 -->
    <div class="news-card-main">
      <div class="news-info">
        <h3 class="news-title">{{ news.title }}</h3>
        <div class="news-meta">
          <div class="meta-left">
            <span class="news-source">{{ news.source }}</span>
            <span class="news-time">{{ formatTime(news.publish_time) }}</span>
            <span 
              v-for="(category, index) in categoryList" 
              :key="index"
              class="news-category"
              :style="{ background: category.color || '#f3f4f6' }"
            >
              {{ category.name }}
            </span>
          </div>
          <div class="news-actions">
            <a v-if="news.url" :href="news.url" target="_blank" class="news-link" title="阅读原文">
              🔗
            </a>
            <button 
              @click="handleShowDetail" 
              class="detail-btn"
              title="查看详情"
            >
              📋
            </button>
            <button 
              @click="handleMarkAsRead" 
              class="read-toggle-btn"
              :class="{ read: news.is_read }"
              :disabled="markingAsRead"
              :title="news.is_read ? '标记为未读' : '标记为已读'"
            >
              {{ news.is_read ? '✓' : '○' }}
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- AI摘要或描述 -->
    <div v-if="news.ai_summary" class="news-summary ai-generated">
      <div 
        ref="summaryHeaderRef"
        class="summary-header" 
        @mouseenter="handleShowOriginalSummary" 
        @mouseleave="showOriginalSummary = false"
      >
        <span class="summary-icon">✨</span>
        <span class="summary-label">AI摘要：</span>
        <span class="summary-content">{{ news.ai_summary }}</span>
      </div>
    </div>
    <div v-else-if="news.description" class="news-description">
      <div 
        ref="descriptionRef"
        class="description-content"
        @mouseenter="handleShowFullDescription" 
        @mouseleave="showFullDescription = false"
      >
        {{ truncateText(news.description, 140) }}
      </div>
    </div>
  </div>

  <!-- 使用Teleport将tooltip渲染到body下，避免被其他元素遮挡 -->
  <Teleport to="body">
    <div 
      ref="originalSummaryTooltipRef"
      v-if="showOriginalSummary && news.description" 
      class="original-summary-tooltip"
      :style="tooltipStyle"
    >
      <div class="tooltip-header">📄 原文摘要</div>
      <div class="tooltip-content">{{ news.description }}</div>
    </div>
    <div 
      ref="fullDescriptionTooltipRef"
      v-if="showFullDescription" 
      class="full-description-tooltip"
      :style="descriptionTooltipStyle"
    >
      <div class="tooltip-header">📄 完整摘要</div>
      <div class="tooltip-content">{{ news.description }}</div>
    </div>
  </Teleport>

  <!-- 新闻详情模态框 -->
  <NewsDetailModal 
    :is-open="showDetailModal"
    :news-id="news.id"
    @close="showDetailModal = false"
    ref="detailModalRef"
  />
</template>

<script setup lang="ts">
import { computed, ref, nextTick, watch } from 'vue'
import { useNewsStore } from '@/stores/news'
import { useConfigStore } from '@/stores/config'
import { api } from '@/api'
import type { News } from '@/types/news'
import NewsDetailModal from './NewsDetailModal.vue'

interface Props {
  news: News
}

const props = defineProps<Props>()
const newsStore = useNewsStore()
const configStore = useConfigStore()
const markingAsRead = ref(false)
const aiProcessing = ref(false)
const showOriginalSummary = ref(false)
const showFullDescription = ref(false)
const showDetailModal = ref(false)
const imageLoadFailed = ref(false)
const summaryHeaderRef = ref<HTMLElement | null>(null)
const descriptionRef = ref<HTMLElement | null>(null)
const originalSummaryTooltipRef = ref<HTMLElement | null>(null)
const fullDescriptionTooltipRef = ref<HTMLElement | null>(null)
const detailModalRef = ref<InstanceType<typeof NewsDetailModal> | null>(null)
const tooltipStyle = ref<Record<string, string>>({})
const descriptionTooltipStyle = ref<Record<string, string>>({})

async function handleShowOriginalSummary() {
  showOriginalSummary.value = true
  
  // 等待tooltip渲染完成
  await nextTick()
  
  // 计算tooltip位置
  if (summaryHeaderRef.value && originalSummaryTooltipRef.value) {
    const rect = summaryHeaderRef.value.getBoundingClientRect()
    const tooltipRect = originalSummaryTooltipRef.value.getBoundingClientRect()
    const tooltipWidth = tooltipRect.width
    const tooltipHeight = tooltipRect.height
    
    // 计算tooltip位置
    let top = rect.bottom + 8
    let left = rect.left
    
    // 检查右边界
    if (left + tooltipWidth > window.innerWidth) {
      left = window.innerWidth - tooltipWidth - 16
    }
    
    // 检查底部边界
    if (top + tooltipHeight > window.innerHeight) {
      top = rect.top - tooltipHeight - 8
    }
    
    tooltipStyle.value = {
      top: `${top}px`,
      left: `${left}px`,
      zIndex: '9999'
    }
  }
}

async function handleShowFullDescription() {
  showFullDescription.value = true
  
  // 等待tooltip渲染完成
  await nextTick()
  
  // 计算tooltip位置
  if (descriptionRef.value && fullDescriptionTooltipRef.value) {
    const rect = descriptionRef.value.getBoundingClientRect()
    const tooltipRect = fullDescriptionTooltipRef.value.getBoundingClientRect()
    const tooltipWidth = tooltipRect.width
    const tooltipHeight = tooltipRect.height
    
    // 计算tooltip位置
    let top = rect.bottom + 8
    let left = rect.left
    
    // 检查右边界
    if (left + tooltipWidth > window.innerWidth) {
      left = window.innerWidth - tooltipWidth - 16
    }
    
    // 检查底部边界
    if (top + tooltipHeight > window.innerHeight) {
      top = rect.top - tooltipHeight - 8
    }
    
    descriptionTooltipStyle.value = {
      top: `${top}px`,
      left: `${left}px`,
      zIndex: '9999'
    }
  }
}

const showThumbnail = computed(() => {
  return configStore.config?.image_display?.show_thumbnail !== false && 
         (props.news.image_data || props.news.image_url)
})

const imagePositionClass = computed(() => {
  const position = configStore.config?.image_display?.position || 'left'
  return `position-${position}`
})

const categoryBackgroundStyle = computed(() => {
  const category = props.news.category || '未分类'
  const categories = category.split(',')
  const firstCategory = categories[0].trim()
  
  // 从数组中查找对应的分类配置
  const categoryConfig = newsStore.categories.find(cat => cat.name === firstCategory)
  const color = categoryConfig?.color || '#95a5a6'
  
  return {
    background: color
  }
})

async function handleMarkAsRead() {
  if (markingAsRead.value) return
  
  try {
    markingAsRead.value = true
    
    const newStatus = props.news.is_read ? 0 : 1
    await api.markAsRead(props.news.id, newStatus === 1)
    
    const newsItem = newsStore.newsList.find(n => n.id === props.news.id)
    if (newsItem) {
      Object.assign(newsItem, { is_read: newStatus })
    }
  } catch (error) {
    console.error('标记阅读状态失败:', error)
  } finally {
    markingAsRead.value = false
  }
}

async function handleReanalyze() {
  if (aiProcessing.value) return
  
  try {
    aiProcessing.value = true
    await api.processNewsReanalyze(props.news.id)
    // 不在这里设置 aiProcessing.value = false
    // 等待WebSocket更新消息来结束动画
  } catch (error) {
    console.error('重新分析失败:', error)
    aiProcessing.value = false
  }
}

function handleShowDetail() {
  showDetailModal.value = true
  // 加载新闻详情
  nextTick(() => {
    detailModalRef.value?.loadNewsDetail()
  })
}

const imageUrl = computed(() => {
  if (imageLoadFailed.value) {
    return null
  }
  
  if (props.news.image_data) {
    return `data:image/jpeg;base64,${props.news.image_data}`
  }
  return props.news.image_url || null
})

const categoryList = computed(() => {
  if (!props.news.category) return []
  
  const categories = props.news.category.split(',')
  const categoryList = categories.map(cat => {
    const categoryName = cat.trim()
    // 从数组中查找对应的分类配置
    const categoryConfig = newsStore.categories.find(c => c.name === categoryName)
    return {
      name: categoryConfig?.name || categoryName,
      color: categoryConfig?.color || '#95a5a6'
    }
  })
  
  return categoryList
})

function formatTime(timeString?: string): string {
  if (!timeString) return ''
  
  const date = new Date(timeString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`
  
  return date.toLocaleDateString('zh-CN')
}

function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

function handleImageError(event: Event) {
  // 标记图片加载失败，imageUrl computed会自动切换到占位图
  imageLoadFailed.value = true
}

// 监听news的变化，当AI分析完成时自动结束动画
watch(() => props.news.ai_summary, (newSummary, oldSummary) => {
  // 如果AI摘要从无到有，或者从旧值变为新值，说明AI分析完成
  if (aiProcessing.value && newSummary && newSummary !== oldSummary) {
    aiProcessing.value = false
  }
})

watch(() => props.news.category, (newCategory, oldCategory) => {
  // 如果分类从旧值变为新值，说明AI分析完成
  if (aiProcessing.value && newCategory && newCategory !== oldCategory) {
    aiProcessing.value = false
  }
})
</script>

<style scoped>
.news-card {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
  background: white;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  flex-direction: column;
  position: relative;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.news-card:hover {
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.news-card.ai-processing {
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
}

/* 图片背景装饰 */
.news-card-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  z-index: 0;
}

.news-card-background.position-left {
  left: 0;
}

.news-card-background.position-right {
  right: 0;
}

.news-card-background.category-background {
  opacity: 0.15;
}

.background-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0.25;
  filter: blur(1px);
}

.background-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(
    to bottom,
    rgba(255,255,255,0.35) 0%,
    rgba(255,255,255,0.3) 30%,
    rgba(255,255,255,0.2) 60%,
    rgba(255,255,255,0.1) 100%
  );
}

/* 重新分析按钮 */
.reanalyze-btn {
  position: absolute;
  bottom: 0.75rem;
  right: 0.75rem;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #e5e7eb;
  border-radius: 50%;
  width: 28px;
  height: 28px;
  cursor: pointer;
  opacity: 0;
  transition: all 0.3s ease;
  font-size: 0.75rem;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.news-card:hover .reanalyze-btn {
  opacity: 1;
}

.reanalyze-btn:hover {
  background: white;
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.reanalyze-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(102, 126, 234, 0.3);
  border-radius: 50%;
  border-top-color: #667eea;
  animation: spin 0.8s ease-in-out infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 主要内容区域 */
.news-card-main {
  display: flex;
  padding: 1rem;
  position: relative;
  z-index: 1;
}

.news-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

/* 标题样式 */
.news-title {
  margin: 0 0 0.5rem 0;
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

/* 元数据样式 */
.news-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.625rem;
  font-size: 0.75rem;
  color: #6b7280;
}

.meta-left {
  display: flex;
  gap: 0.375rem;
  flex-wrap: wrap;
  align-items: center;
}

.news-category,
.news-source,
.news-time {
  padding: 0.1875rem 0.5rem;
  border-radius: 9999px;
  background: #f3f4f6;
  font-weight: 500;
  color: #374151;
}

.news-category {
  color: white;
}

/* 按钮样式 */
.news-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  align-items: center;
}

.news-link,
.read-toggle-btn,
.detail-btn {
  padding: 0;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  color: #4b5563;
  text-decoration: none;
  border-radius: 6px;
  font-size: 1.125rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.news-link:hover,
.read-toggle-btn:hover,
.detail-btn:hover {
  background: rgba(0, 0, 0, 0.05);
  transform: scale(1.05);
}

.detail-btn {
  color: #667eea;
}

.detail-btn:hover {
  background: rgba(102, 126, 234, 0.1);
}

.read-toggle-btn.read {
  color: #10b981;
}

.read-toggle-btn.read:hover {
  background: rgba(16, 185, 129, 0.1);
}

.read-toggle-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.read-toggle-btn:disabled:hover {
  transform: none;
  background: transparent;
}

/* AI摘要样式 */
.news-summary {
  padding: 0.625rem 1rem;
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
  border-left: 3px solid #10b981;
  border-radius: 6px;
  font-size: 0.75rem;
  color: #166534;
  line-height: 1.5;
  position: relative;
  z-index: 1;
  margin: 0 1rem 1rem 1rem;
}

.news-summary.ai-generated {
  font-style: italic;
}

.summary-header {
  display: inline-flex;
  align-items: flex-start;
  gap: 0.1875rem;
  cursor: help;
  position: relative;
  flex-wrap: wrap;
}

.summary-icon {
  font-size: 0.875rem;
  flex-shrink: 0;
}

.summary-label {
  font-weight: 600;
  color: #166534;
  flex-shrink: 0;
}

.summary-content {
  color: #166534;
  font-style: italic;
  word-break: break-word;
}

/* 描述样式 */
.news-description {
  padding: 0.625rem 1rem;
  font-size: 0.75rem;
  color: #6b7280;
  line-height: 1.5;
  background: #f9fafb;
  border-radius: 6px;
  position: relative;
  z-index: 1;
  margin: 0 1rem 1rem 1rem;
}

.description-content {
  cursor: help;
}

/* Tooltip样式 */
.original-summary-tooltip,
.full-description-tooltip {
  position: fixed;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 9999;
  min-width: 280px;
  max-width: 400px;
  padding: 0.75rem;
  pointer-events: auto;
}

.tooltip-header {
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
}

.tooltip-content {
  color: #6b7280;
  font-size: 0.875rem;
  line-height: 1.5;
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .news-card-main {
    padding: 0.875rem;
  }
  
  .news-title {
    font-size: 0.9375rem;
  }
  
  .news-actions {
    flex-direction: row;
    align-items: stretch;
  }
  
  .news-link,
  .read-toggle-btn {
    flex: 1;
  }
}
</style>