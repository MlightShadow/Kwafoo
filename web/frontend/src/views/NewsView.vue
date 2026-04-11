<template>
  <div class="news-view">
    <div class="news-header">
      <h2>{{ currentCategoryName }}</h2>
      <div class="news-stats">
        <span>{{ newsCount }} 条新闻</span>
        <span>最后更新: {{ lastUpdateTime }}</span>
      </div>
    </div>

    <div v-if="loading" class="loading">
      加载中...
    </div>

    <div v-else-if="error" class="error">
      {{ error }}
    </div>

    <div v-else-if="filteredNews.length === 0" class="empty">
      暂无新闻
    </div>

    <div v-else class="news-grid">
      <NewsCard 
        v-for="news in filteredNews" 
        :key="news.id" 
        :news="news" 
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useNewsStore } from '@/stores/news'
import NewsCard from '@/components/NewsCard.vue'

const newsStore = useNewsStore()

const lastUpdateTime = ref<string>(new Date().toLocaleString('zh-CN'))

const filteredNews = computed(() => newsStore.filteredNews)
const loading = computed(() => newsStore.loading)
const error = computed(() => newsStore.error)
const newsCount = computed(() => newsStore.newsCount)
const currentCategoryName = computed(() => {
  return newsStore.currentCategory || '全部'
})

onMounted(() => {
  lastUpdateTime.value = new Date().toLocaleString('zh-CN')
})
</script>

<style scoped>
.news-view {
  width: 100%;
}

.news-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e0e0e0;
}

.news-header h2 {
  font-size: 1.8rem;
  color: #333;
}

.news-stats {
  display: flex;
  gap: 1rem;
  color: #666;
  font-size: 0.9rem;
}

.loading,
.error,
.empty {
  text-align: center;
  padding: 3rem;
  font-size: 1.2rem;
  color: #666;
}

.error {
  color: #dc3545;
}

.news-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(600px, 1fr));
  gap: 1.5rem;
  width: 100%;
}

@media (max-width: 768px) {
  .news-grid {
    grid-template-columns: 1fr;
  }
  
  .news-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
}
</style>