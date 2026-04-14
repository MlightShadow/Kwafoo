<template>
  <div class="news-card" :data-id="news.id">
    <button 
      @click="handleReanalyze" 
      class="reanalyze-btn"
      :disabled="aiProcessing"
      title="重新分析"
    >
      🔄
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
      <div class="summary-header" @mouseenter="showOriginalSummary = true" @mouseleave="showOriginalSummary = false">
        <span class="summary-icon">✨</span>
        <strong>AI摘要：</strong>{{ news.ai_summary }}
      </div>
      <div v-if="showOriginalSummary && news.description" class="original-summary-tooltip">
        <div class="tooltip-header">📄 原文摘要</div>
        <div class="tooltip-content">{{ truncateText(news.description, 300) }}</div>
      </div>
    </div>
    <div v-else-if="news.description" class="news-description">
      {{ truncateText(news.description, 140) }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
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
const imageLoadFailed = ref(false)

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
  } catch (error) {
    console.error('重新分析失败:', error)
  } finally {
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
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: help;
  position: relative;
}

.summary-icon {
  font-size: 1rem;
}

.original-summary-tooltip {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  min-width: 280px;
  max-width: 350px;
  padding: 0.75rem;
  pointer-events: auto;
}

.tooltip-header {
  font-weight: 600;
  color: #333;
  margin-bottom: 0.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #e0e0e0;
  font-size: 0.85rem;
}

.tooltip-content {
  color: #666;
  font-size: 0.8rem;
  line-height: 1.5;
}

.news-description {
  padding: 0.75rem;
  font-size: 0.85rem;
  color: #666;
  line-height: 1.5;
  background: #f9f9f9;
  border-radius: 4px;
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