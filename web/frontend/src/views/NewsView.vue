<template>
  <div class="news-view">
    <div v-if="loading && displayedCount === 0" class="loading">
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

    <div v-if="loadingMore" class="loading-more">
      加载更多...
    </div>

    <div v-if="!hasMore && filteredNews.length > 0" class="no-more">
      没有更多新闻了
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted, watch } from 'vue'
import { useNewsStore } from '@/stores/news'
import { useConfigStore } from '@/stores/config'
import { api } from '@/api'
import NewsCard from '@/components/NewsCard.vue'

const newsStore = useNewsStore()
const configStore = useConfigStore()

const lastUpdateTime = ref<string>(new Date().toLocaleString('zh-CN'))
const currentPage = ref(0)
const pageSize = ref(30)
const loadingMore = ref(false)
const hasMore = ref(true)

const filteredNews = computed(() => {
  return newsStore.newsList
})

const loading = computed(() => newsStore.loading)
const error = computed(() => newsStore.error)
const totalCount = computed(() => newsStore.newsCount)
const displayedCount = computed(() => filteredNews.value.length)

async function loadMoreNews() {
  if (loadingMore.value || !hasMore.value) return
  
  loadingMore.value = true
  
  const offset = (currentPage.value + 1) * pageSize.value
  currentPage.value++
  
  try {
    const category = newsStore.currentCategory
    
    if (category && category !== '全部') {
      const response = await api.getNewsByCategory(category, pageSize.value, offset)
      if (response.data.success) {
        const newNews = response.data.data
        newsStore.newsList = [...newsStore.newsList, ...newNews]
        
        if (newNews.length < pageSize.value) {
          hasMore.value = false
        }
      }
    } else {
      const response = await api.getNews(pageSize.value, offset)
      if (response.data.success) {
        const newNews = response.data.data
        newsStore.newsList = [...newsStore.newsList, ...newNews]
        
        if (newNews.length < pageSize.value) {
          hasMore.value = false
        }
      }
    }
  } catch (error: any) {
    console.error('加载更多新闻失败:', error)
  } finally {
    loadingMore.value = false
  }
}

function handleScroll() {
  const scrollTop = window.scrollY
  const windowHeight = window.innerHeight
  const documentHeight = document.documentElement.scrollHeight
  
  if (scrollTop + windowHeight >= documentHeight - 500) {
    loadMoreNews()
  }
}

// 监听分类变化，重置分页状态
watch(() => newsStore.currentCategory, () => {
  currentPage.value = 0
  hasMore.value = true
})

onMounted(async () => {
  lastUpdateTime.value = new Date().toLocaleString('zh-CN')
  
  // 加载配置以获取分类信息
  await configStore.loadConfig()
  // 将分类设置到newsStore中
  newsStore.setCategories(configStore.config?.categories || [])
  
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>

<style scoped>
.news-view {
  width: 100%;
  max-width: 100%;
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

.error {
  color: #dc3545;
}

.news-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 1.5rem;
  width: 100%;
}

@media (min-width: 1400px) {
  .news-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (min-width: 768px) and (max-width: 1399px) {
  .news-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 767px) {
  .news-grid {
    grid-template-columns: 1fr;
  }
}

.loading-more {
  text-align: center;
  padding: 2rem;
  color: #666;
  font-size: 1rem;
}

.no-more {
  text-align: center;
  padding: 2rem;
  color: #999;
  font-size: 0.9rem;
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