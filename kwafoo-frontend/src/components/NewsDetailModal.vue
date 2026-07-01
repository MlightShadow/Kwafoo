<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <button class="close-btn" @click="$emit('close')">&times;</button>

      <h2 class="title">{{ news.title }}</h2>

      <div class="meta">
        <span class="source">{{ news.source }}</span>
        <span class="time">{{ news.publish_time }}</span>
        <span class="score" v-if="news.relevance_score">关联度 {{ news.relevance_score }}</span>
      </div>

      <div class="comment" v-if="news.ai_comment">
        {{ news.ai_comment }}
      </div>

      <div class="section" v-if="news.ai_summary">
        <h3>AI摘要</h3>
        <p>{{ news.ai_summary }}</p>
      </div>

      <div class="section" v-if="news.description">
        <h3>原文描述</h3>
        <p>{{ news.description }}</p>
      </div>

      <div class="section tags" v-if="news.keywords && news.keywords.length">
        <h3>关键字</h3>
        <div class="tag-list">
          <span class="tag" v-for="kw in news.keywords" :key="kw">{{ kw }}</span>
        </div>
      </div>

      <a :href="news.url" target="_blank" class="source-link">阅读原文</a>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { NewsItem } from '@/types/news'

defineProps<{
  news: NewsItem
}>()

defineEmits<{
  close: []
}>()
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 16px;
}

.modal-content {
  background: #fff;
  border-radius: 16px;
  max-width: 680px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  padding: 32px;
  position: relative;
}

.close-btn {
  position: absolute;
  top: 12px;
  right: 16px;
  border: none;
  background: none;
  font-size: 28px;
  cursor: pointer;
  color: #999;
}

.title {
  font-size: 20px;
  line-height: 1.4;
  margin-bottom: 12px;
  padding-right: 32px;
}

.meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #999;
  margin-bottom: 16px;
}

.comment {
  background: #f0f7ff;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
  margin-bottom: 20px;
  color: #1a73e8;
}

.section {
  margin-bottom: 20px;
}

.section h3 {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #555;
}

.section p {
  font-size: 14px;
  line-height: 1.6;
  color: #333;
}

.tag-list {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.tag {
  padding: 4px 12px;
  background: #e8f0fe;
  color: #1a73e8;
  border-radius: 12px;
  font-size: 13px;
}

.source-link {
  display: inline-block;
  margin-top: 8px;
  color: #1a73e8;
  text-decoration: none;
  font-size: 14px;
}

.source-link:hover {
  text-decoration: underline;
}

.score {
  color: #1a73e8;
  font-weight: 500;
}
</style>