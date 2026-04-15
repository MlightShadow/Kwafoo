<template>
  <div class="news-card" :data-id="news.id" :class="{ 'ai-processing': aiProcessing }">
    <button 
      @click="handleReanalyze" 
      class="reanalyze-btn"
      :disabled="aiProcessing"
      title="重新分析"
    >
      <span v-if="aiProcessing" class="spinner"></span>
      <span v-else>🔄</span>
    </button>
    <div class="news-card-main">
      <div v-if="showThumbnail" class="news-image">
        <img 
          :src="imageUrl" 
          :alt="news.title" 
          loading="lazy"
          @error="handleImageError"
        >
      </div>
      <div class="news-info">
        <h3 class="news-title">{{ news.title }}</h3>
        <div class="news-meta">
          <span v-if="categoryDisplayName" class="news-category">{{ categoryDisplayName }}</span>
          <span class="news-source">{{ news.source }}</span>
          <span class="news-time">{{ formatTime(news.publish_time) }}</span>
        </div>
        <div class="news-actions">
          <a v-if="news.url" :href="news.url" target="_blank" class="news-link">
            📖 阅读原文
          </a>
          <button 
            @click="handleMarkAsRead" 
            class="read-toggle-btn"
            :class="{ read: news.is_read }"
            :disabled="markingAsRead"
            :title="news.is_read ? '标记为未读' : '标记为已读'"
          >
            {{ news.is_read ? '✓ 已读' : '○ 未读' }}
          </button>
        </div>
      </div>
    </div>
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
</template>

<script setup lang="ts">
import { computed, ref, nextTick, watch } from 'vue'
import { useNewsStore } from '@/stores/news'
import { useConfigStore } from '@/stores/config'
import { api } from '@/api'
import type { News } from '@/types/news'

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
const imageLoadFailed = ref(false)
const summaryHeaderRef = ref<HTMLElement | null>(null)
const descriptionRef = ref<HTMLElement | null>(null)
const originalSummaryTooltipRef = ref<HTMLElement | null>(null)
const fullDescriptionTooltipRef = ref<HTMLElement | null>(null)
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
  return configStore.config?.image_display?.show_thumbnail !== false
})

async function handleMarkAsRead() {
  if (markingAsRead.value) return
  
  try {
    markingAsRead.value = true
    
    const newStatus = props.news.is_read ? 0 : 1
    await api.markAsRead(props.news.id)
    
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

const categoryDefaultImage = computed(() => {
  const category = props.news.category || '未分类'
  
  // 从store中获取分类配置
  const categories = category.split(',')
  const firstCategory = categories[0].trim()
  
  const categoryConfig = newsStore.categories[firstCategory]
  if (!categoryConfig) {
    // 如果没有找到分类配置，返回默认的灰色图片
    return 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTI4IiBoZWlnaHQ9IjEyOCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTI4IiBoZWlnaHQ9IjEyOCIgZmlsbD0iIzk1YTVhNiIvPjwvc3ZnPg=='
  }
  
  // 使用配置中的颜色生成纯色块占位图
  const color = categoryConfig.color || '#95a5a6'
  
  // 创建纯色块SVG
  const svg = `
    <svg width="128" height="128" xmlns="http://www.w3.org/2000/svg">
      <rect width="128" height="128" fill="${color}"/>
    </svg>
  `
  
  const base64 = btoa(svg)
  return `data:image/svg+xml;base64,${base64}`
})

const imageUrl = computed(() => {
  if (imageLoadFailed.value) {
    // 如果图片加载失败，直接返回占位图
    return categoryDefaultImage.value
  }
  
  if (props.news.image_data) {
    return `data:image/jpeg;base64,${props.news.image_data}`
  }
  return props.news.image_url || categoryDefaultImage.value
})

const categoryDisplayName = computed(() => {
  if (!props.news.category) return ''
  
  const categories = props.news.category.split(',')
  const displayNames = categories.map(cat => {
    const categoryConfig = newsStore.categories[cat]
    return categoryConfig?.name || cat
  })
  
  return displayNames.join('、')
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
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
  background: white;
  transition: box-shadow 0.3s ease;
  display: flex;
  flex-direction: column;
  position: relative;
}

.news-card.ai-processing {
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.1);
}

.reanalyze-btn {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.05);
  border: none;
  border-radius: 50%;
  width: 28px;
  height: 28px;
  cursor: pointer;
  opacity: 0.6;
  transition: all 0.3s ease;
  font-size: 0.9rem;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
}

.reanalyze-btn:hover {
  background: rgba(0, 0, 0, 0.1);
  opacity: 1;
  transform: scale(1.1);
}

.reanalyze-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(0, 123, 255, 0.3);
  border-radius: 50%;
  border-top-color: #007bff;
  animation: spin 0.8s ease-in-out infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.news-card-main {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  align-items: flex-start;
}

.news-image {
  width: 128px;
  height: 128px;
  flex-shrink: 0;
  overflow: hidden;
  background: #f5f5f5;
  border-radius: 4px;
}

.news-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.news-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.news-title {
  margin: 0 0 0.5rem 0;
  font-size: 1rem;
  color: #333;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.news-meta {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-bottom: 0.75rem;
  font-size: 0.85rem;
  color: #666;
}

.news-source,
.news-time,
.news-category {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  background: #f5f5f5;
}

.news-summary {
  padding: 0.75rem;
  background: linear-gradient(135deg, #f0fff4 0%, #e6fffa 100%);
  border-left: 3px solid #28a745;
  border-radius: 4px;
  font-size: 0.85rem;
  color: #333;
  line-height: 1.5;
  position: relative;
  z-index: 1;
}

.news-summary.ai-generated {
  color: #28a745;
  font-style: italic;
}

.summary-header {
  display: inline-flex;
  align-items: flex-start;
  gap: 0.25rem;
  cursor: help;
  position: relative;
  flex-wrap: wrap;
}

.summary-icon {
  font-size: 1rem;
  flex-shrink: 0;
}

.summary-label {
  font-weight: 600;
  color: #28a745;
  flex-shrink: 0;
}

.summary-content {
  color: #28a745;
  font-style: italic;
  word-break: break-word;
}

.original-summary-tooltip {
  position: fixed;
  background: white;
  border: 1px solid #e0e0e0;
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
  color: #333;
  margin-bottom: 0.5rem;
  font-size: 0.85rem;
}

.tooltip-content {
  color: #666;
  font-size: 0.8rem;
  line-height: 1.5;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.news-description {
  padding: 0.75rem;
  font-size: 0.85rem;
  color: #666;
  line-height: 1.5;
  background: #f9f9f9;
  border-radius: 4px;
  position: relative;
}

.description-content {
  cursor: help;
}

.full-description-tooltip {
  position: fixed;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 9999;
  min-width: 280px;
  max-width: 400px;
  padding: 0.75rem;
  pointer-events: auto;
}

.news-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
  flex-wrap: wrap;
}

.news-link {
  display: inline-block;
  padding: 0.4rem 0.8rem;
  background: transparent;
  border: 1px solid #007bff;
  color: #007bff;
  text-decoration: none;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
  transition: all 0.3s ease;
  text-align: center;
}

.news-link:hover {
  background: #007bff;
  color: white;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 123, 255, 0.3);
}

.read-toggle-btn {
  padding: 0.4rem 0.8rem;
  background: transparent;
  border: 1px solid #007bff;
  color: #007bff;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.read-toggle-btn:hover {
  background: #007bff;
  color: white;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 123, 255, 0.3);
}

.read-toggle-btn.read {
  background: #007bff;
  color: white;
}

.read-toggle-btn.read:hover {
  background: #0056b3;
}

.read-toggle-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .news-card-main {
    flex-direction: column;
  }
  
  .news-image {
    width: 100%;
    height: 128px;
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