<template>
  <div class="news-card" :data-id="news.id" :class="imagePositionClass">
    <div v-if="showThumbnail" class="news-image">
      <img 
        :src="imageUrl" 
        :alt="news.title" 
        loading="lazy"
        @error="handleImageError"
      >
    </div>
    <div class="news-content">
      <h3 class="news-title">{{ news.title }}</h3>
      <div class="news-meta">
        <span class="news-source">{{ news.source }}</span>
        <span class="news-time">{{ formatTime(news.publish_time) }}</span>
        <span v-if="categoryDisplayName" class="news-category">{{ categoryDisplayName }}</span>
      </div>
      <div v-if="news.ai_summary" class="news-summary ai-generated">
        <strong>AI摘要：</strong>{{ news.ai_summary }}
      </div>
      <div v-else-if="news.description" class="news-description">
        {{ truncateText(news.description, 140) }}
      </div>
      <div class="news-actions">
        <a v-if="news.url" :href="news.url" target="_blank" class="news-link">
          阅读原文
        </a>
        <button 
          @click="handleAIProcess" 
          class="ai-process-btn"
          :disabled="aiProcessing"
        >
          🤖 {{ aiProcessing ? '处理中...' : (news.ai_processed ? '重新分析' : 'AI分析') }}
        </button>
        <button 
          v-if="!news.is_read" 
          @click="handleMarkAsRead" 
          class="mark-read-btn"
          :disabled="markingAsRead"
        >
          ✓ {{ markingAsRead ? '处理中...' : '阅读标记' }}
        </button>
      </div>
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

const imagePositionClass = computed(() => {
  const position = configStore.config?.image_display?.position || 'right'
  return `image-${position}`
})

const showThumbnail = computed(() => {
  return configStore.config?.image_display?.show_thumbnail !== false
})

async function handleMarkAsRead() {
  if (markingAsRead.value) return
  
  try {
    markingAsRead.value = true
    await api.markAsRead(props.news.id)
    
    // 更新本地状态 - 使用Object.assign确保响应式更新
    const newsItem = newsStore.newsList.find(n => n.id === props.news.id)
    if (newsItem) {
      Object.assign(newsItem, { is_read: 1 })
    }
    
    // 显示成功提示
    alert('已标记为已读')
  } catch (error) {
    console.error('标记为已读失败:', error)
    alert('标记失败，请重试')
  } finally {
    markingAsRead.value = false
  }
}

async function handleAIProcess() {
  if (aiProcessing.value) return
  
  try {
    aiProcessing.value = true
    await api.processSingleNewsAI(props.news.id, true)
    alert('已将新闻添加到AI队列')
  } catch (error) {
    console.error('AI分析失败:', error)
    alert('AI分析失败，请重试')
  } finally {
    aiProcessing.value = false
  }
}

const imageUrl = computed(() => {
  if (props.news.image_data) {
    return `data:image/jpeg;base64,${props.news.image_data}`
  }
  return props.news.image_url || 'https://placehold.co/400x200/e0e0e0/999999?text=No+Image'
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
  const img = event.target as HTMLImageElement
  img.src = 'https://placehold.co/400x200/e0e0e0/999999?text=No+Image'
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
  height: 100%;
}

.news-card.image-right {
  flex-direction: row;
}

.news-card.image-left {
  flex-direction: row-reverse;
}

.news-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.news-image {
  width: 100%;
  height: 200px;
  overflow: hidden;
  background: #f5f5f5;
}

.news-card.image-right .news-image,
.news-card.image-left .news-image {
  width: 200px;
  flex-shrink: 0;
}

.news-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.news-content {
  padding: 1rem;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.news-title {
  margin: 0 0 0.5rem 0;
  font-size: 1.1rem;
  color: #333;
  line-height: 1.4;
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
  margin-bottom: 0.75rem;
  padding: 0.75rem;
  background: linear-gradient(135deg, #f0fff4 0%, #e6fffa 100%);
  border-left: 3px solid #28a745;
  border-radius: 4px;
  font-size: 0.9rem;
  color: #333;
  line-height: 1.5;
}

.news-summary.ai-generated {
  color: #28a745;
  font-style: italic;
}

.news-description {
  margin-bottom: 0.75rem;
  font-size: 0.9rem;
  color: #666;
  line-height: 1.5;
  flex: 1;
}

.news-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  flex-wrap: wrap;
}

.news-link {
  display: inline-block;
  padding: 0.5rem 1rem;
  background: #007bff;
  color: white;
  text-decoration: none;
  border-radius: 4px;
  transition: background 0.3s ease;
  align-self: flex-start;
}

.news-link:hover {
  background: #0056b3;
}

.ai-process-btn {
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 500;
  align-self: flex-start;
}

.ai-process-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #5568d3 0%, #654391 100%);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.4);
}

.ai-process-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.mark-read-btn {
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, #ffc107 0%, #e0a800 100%);
  color: #333;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 500;
  align-self: flex-start;
}

.mark-read-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #e0a800 0%, #d39e00 100%);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(255, 193, 7, 0.4);
}

.mark-read-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>