<template>
  <div class="news-view">
    <div class="news-header">
      <h2>{{ currentCategoryName }}</h2>
      <div class="news-tabs">
        <button 
          :class="['tab-btn', { active: currentTab === 'all' }]"
          @click="handleTabChange('all')"
        >
          全部
        </button>
        <button 
          :class="['tab-btn', { active: currentTab === 'unread' }]"
          @click="handleTabChange('unread')"
        >
          未读
        </button>
        <button 
          :class="['tab-btn', { active: currentTab === 'read' }]"
          @click="handleTabChange('read')"
        >
          已读
        </button>
      </div>
      <div class="news-stats">
        <span>{{ totalCount }} 条新闻</span>
        <span>已加载: {{ displayedCount }}</span>
        <span>最后更新: {{ lastUpdateTime }}</span>
      </div>
    </div>

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
const currentTab = ref<'all' | 'unread' | 'read'>('all')
const currentPage = ref(0)
const pageSize = ref(30)
const loadingMore = ref(false)
const hasMore = ref(true)

const filteredNews = computed(() => {
  let news = newsStore.newsList
  
  if (currentTab.value === 'unread') {
    news = news.filter(n => !n.is_read)
  } else if (currentTab.value === 'read') {
    news = news.filter(n => n.is_read)
  }
  
  return news
})

const loading = computed(() => newsStore.loading)
const error = computed(() => newsStore.error)
const totalCount = computed(() => newsStore.newsCount)
const displayedCount = computed(() => filteredNews.value.length)
const currentCategoryName = computed(() => {
  const tabName = currentTab.value === 'all' ? '全部' : (currentTab.value === 'unread' ? '未读' : '已读')
  const category = newsStore.currentCategory || '全部'
  return `${category} - ${tabName}`
})

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

async function handleTabChange(tab: 'all' | 'unread' | 'read') {
  currentTab.value = tab
  currentPage.value = 0
  hasMore.value = true
  
  if (tab === 'unread') {
    try {
      loading.value = true
      const response = await api.getUnreadNews(100)
      newsStore.newsList = response.data.data
      hasMore.value = false
    } catch (error) {
      console.error('获取未读新闻失败:', error)
    } finally {
      loading.value = false
    }
  } else if (tab === 'read') {
    try {
      loading.value = true
      const response = await api.getReadNews(100)
      newsStore.newsList = response.data.data
      hasMore.value = false
    } catch (error) {
      console.error('获取已读新闻失败:', error)
    } finally {
      loading.value = false
    }
  } else {
    await newsStore.loadNews(newsStore.currentCategory)
    currentPage.value = 0
    hasMore.value = true
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

.news-tabs {
  display: flex;
  gap: 0.5rem;
}

.tab-btn {
  padding: 0.5rem 1rem;
  border: 1px solid #e0e0e0;
  background: white;
  color: #666;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.9rem;
}

.tab-btn:hover {
  background: #f5f5f5;
  color: #333;
}

.tab-btn.active {
  background: #007bff;
  color: white;
  border-color: #007bff;
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