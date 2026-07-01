<template>
  <div class="news-view">
    <header class="news-header">
      <h1>Kwafoo 新闻聚合</h1>
      <nav>
        <router-link to="/">新闻</router-link>
        <router-link to="/admin">管理</router-link>
      </nav>
    </header>

    <div v-if="error" class="error-message">{{ error }}</div>

    <div class="news-grid">
      <NewsCard
        v-for="item in newsList"
        :key="item.id"
        :news="item"
        @click="showDetail(item)"
      />
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-if="!loading && newsList.length === 0 && !error" class="empty">
      暂无新闻数据
    </div>

    <div class="pagination" v-if="total > limit">
      <button @click="prevPage" :disabled="offset === 0">上一页</button>
      <span>{{ Math.floor(offset / limit) + 1 }} / {{ Math.ceil(total / limit) }}</span>
      <button @click="nextPage" :disabled="offset + limit >= total">下一页</button>
    </div>

    <NewsDetailModal
      v-if="selectedNews"
      :news="selectedNews"
      @close="selectedNews = null"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useNews } from '@/composables/useNews'
import NewsCard from '@/components/NewsCard.vue'
import NewsDetailModal from '@/components/NewsDetailModal.vue'
import type { NewsItem } from '@/types/news'

const {
  newsList,
  total,
  loading,
  error,
  limit,
  offset,
  fetchNews,
  nextPage,
  prevPage,
} = useNews()

const selectedNews = ref<NewsItem | null>(null)

function showDetail(item: NewsItem) {
  selectedNews.value = item
}

onMounted(() => {
  fetchNews()
})
</script>

<style scoped>
.news-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 16px;
}

.news-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e0e0e0;
}

.news-header h1 {
  font-size: 24px;
  color: #1a1a1a;
}

.news-header nav a {
  margin-left: 16px;
  color: #666;
  text-decoration: none;
}

.news-header nav a:hover,
.news-header nav a.router-link-active {
  color: #1a73e8;
}

.news-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 16px;
}

.loading,
.empty {
  text-align: center;
  padding: 48px;
  color: #999;
}

.error-message {
  background: #fff0f0;
  color: #d32f2f;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 24px;
}

.pagination button {
  padding: 8px 16px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>