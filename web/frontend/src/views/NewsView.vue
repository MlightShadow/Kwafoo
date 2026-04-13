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
import { api } from '@/api'
import NewsCard from '@/components/NewsCard.vue'

const newsStore = useNewsStore()

const lastUpdateTime = ref<string>(new Date().toLocaleString('zh-CN'))
const currentTab = ref<'all' | 'unread' | 'read'>('all')

const filteredNews = computed(() => {
  let news = newsStore.filteredNews
  
  if (currentTab.value === 'unread') {
    news = news.filter(n => !n.is_read)
  } else if (currentTab.value === 'read') {
    news = news.filter(n => n.is_read)
  }
  
  return news
})

const loading = computed(() => newsStore.loading)
const error = computed(() => newsStore.error)
const newsCount = computed(() => filteredNews.value.length)
const currentCategoryName = computed(() => {
  const tabName = currentTab.value === 'all' ? '全部' : (currentTab.value === 'unread' ? '未读' : '已读')
  const category = newsStore.currentCategory || '全部'
  return `${category} - ${tabName}`
})

async function handleTabChange(tab: 'all' | 'unread' | 'read') {
  currentTab.value = tab
  
  if (tab === 'unread') {
    try {
      loading.value = true
      const response = await api.getUnreadNews(100)
      newsStore.newsList = response.data.data
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
    } catch (error) {
      console.error('获取已读新闻失败:', error)
    } finally {
      loading.value = false
    }
  } else {
    // 全部标签，重新加载新闻
    await newsStore.loadNews()
  }
}

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