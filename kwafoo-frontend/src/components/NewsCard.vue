<template>
  <div class="news-card" @click="$emit('click')">
    <div class="card-image" v-if="news.image_url">
      <div class="image-placeholder" :style="{ backgroundImage: `url(${news.image_url})` }" />
    </div>
    <div class="card-body">
      <h3 class="card-title">{{ news.title }}</h3>
      <p class="card-comment" v-if="news.ai_comment">{{ news.ai_comment }}</p>
      <div class="card-meta">
        <span class="source">{{ news.source }}</span>
        <span class="time">{{ formatTime(news.publish_time) }}</span>
      </div>
      <div class="card-tags" v-if="news.category && news.category.length">
        <span class="tag" v-for="cat in news.category" :key="cat">{{ cat }}</span>
      </div>
      <div class="card-scores" v-if="news.relevance_score || news.importance_score">
        <span class="score" v-if="news.relevance_score">关联 {{ news.relevance_score }}</span>
        <span class="score" v-if="news.importance_score">重要 {{ news.importance_score }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { NewsItem } from '@/types/news'

defineProps<{
  news: NewsItem
}>()

defineEmits<{
  click: []
}>()

function formatTime(time: string): string {
  if (!time) return ''
  try {
    const d = new Date(time)
    return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  } catch {
    return time
  }
}
</script>

<style scoped>
.news-card {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  cursor: pointer;
  transition: box-shadow 0.2s;
}

.news-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

.image-placeholder {
  height: 160px;
  background-size: cover;
  background-position: center;
  background-color: #e8e8e8;
}

.card-body {
  padding: 16px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  line-height: 1.4;
  margin-bottom: 8px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-comment {
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
}

.card-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #999;
  margin-bottom: 8px;
}

.card-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 8px;
}

.tag {
  padding: 2px 8px;
  background: #e8f0fe;
  color: #1a73e8;
  border-radius: 10px;
  font-size: 12px;
}

.card-scores {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #888;
}

.score {
  padding: 2px 6px;
  background: #f5f5f5;
  border-radius: 4px;
}
</style>