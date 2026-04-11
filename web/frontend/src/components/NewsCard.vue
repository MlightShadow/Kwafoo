<template>
  <div class="news-card" :data-id="news.id">
    <div v-if="news.image_data || news.image_url" class="news-image">
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
        <span v-if="news.category" class="news-category">{{ news.category }}</span>
      </div>
      <div v-if="news.ai_summary" class="news-summary ai-generated">
        <strong>AI摘要：</strong>{{ news.ai_summary }}
      </div>
      <div v-else-if="news.description" class="news-description">
        {{ truncateText(news.description, 140) }}
      </div>
      <a v-if="news.url" :href="news.url" target="_blank" class="news-link">
        阅读原文
      </a>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { News } from '@/types/news'

interface Props {
  news: News
}

const props = defineProps<Props>()

const imageUrl = computed(() => {
  if (props.news.image_data) {
    return `data:image/jpeg;base64,${props.news.image_data}`
  }
  return props.news.image_url || 'https://via.placeholder.com/256'
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
  img.src = 'https://via.placeholder.com/256'
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

.news-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.news-image {
  width: 100%;
  height: 200px;
  overflow: hidden;
  background: #f5f5f5;
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
</style>