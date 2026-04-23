<template>
  <div class="category-list">
    <!-- 阅读状态筛选 -->
    <div class="filter-section">
      <button 
        :class="['filter-btn', { active: currentFilter === 'all' }]"
        @click="selectFilter('all')"
      >
        全部
      </button>
      <button 
        :class="['filter-btn', { active: currentFilter === 'unread' }]"
        @click="selectFilter('unread')"
      >
        未读
      </button>
      <button 
        :class="['filter-btn', { active: currentFilter === 'read' }]"
        @click="selectFilter('read')"
      >
        已读
      </button>
    </div>
    
    <!-- 新闻类别 -->
    <div class="category-section">
      <div class="section-title">新闻类别</div>
      <button 
        v-for="(category, name) in allCategories" 
        :key="name"
        class="category-btn"
        :class="{ 
          active: currentCategory === name,
          'has-color': category.color && category.color !== '#f3f4f6'
        }"
        :style="currentCategory === name ? {} : { background: category.color || '#f3f4f6' }"
        @click="selectCategory(name)"
      >
        <span class="category-icon">{{ category.icon || '📄' }}</span>
        <span class="category-name">{{ category.name || name }}</span>
      </button>
    </div>
    
    <!-- 新闻状态 -->
    <div class="status-section">
      <div class="status-item">
        <span class="status-label">新闻总数</span>
        <span class="status-value">{{ totalCount }}</span>
      </div>
      <div class="status-item">
        <span class="status-label">已加载</span>
        <span class="status-value">{{ displayedCount }}</span>
      </div>
      <div class="status-item">
        <span class="status-label">最后更新</span>
        <span class="status-value">{{ lastUpdateTime }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useNewsStore } from '@/stores/news'
import { api } from '@/api'

const newsStore = useNewsStore()

const currentFilter = ref<'all' | 'unread' | 'read'>('all')

const allCategories = computed(() => {
  const categories = {
    '全部': { icon: '📰', color: '#f3f4f6' },
    '未分类': { icon: '📋', color: '#95a5a6' }
  }
  
  // 将数组转换为对象
  newsStore.categories.forEach(cat => {
    categories[cat.name] = {
      icon: cat.icon || '📄',
      name: cat.name,
      color: cat.color || '#f3f4f6'
    }
  })
  
  return categories
})

const currentCategory = computed(() => newsStore.currentCategory)
const totalCount = computed(() => newsStore.newsCount)
const displayedCount = computed(() => newsStore.newsList.length)
const lastUpdateTime = computed(() => new Date().toLocaleString('zh-CN'))

async function selectCategory(category: string) {
  newsStore.setCategory(category)
  await newsStore.loadNews(category)
}

async function selectFilter(filter: 'all' | 'unread' | 'read') {
  currentFilter.value = filter
  
  if (filter === 'unread') {
    try {
      const response = await api.getUnreadNews(100)
      newsStore.newsList = response.data.data
    } catch (error) {
      console.error('获取未读新闻失败:', error)
    }
  } else if (filter === 'read') {
    try {
      const response = await api.getReadNews(100)
      newsStore.newsList = response.data.data
    } catch (error) {
      console.error('获取已读新闻失败:', error)
    }
  } else {
    await newsStore.loadNews(newsStore.currentCategory)
  }
}
</script>

<style scoped>
.category-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  overflow-x: hidden;
}

.filter-section {
  display: flex;
  gap: 0.375rem;
  padding: 0.375rem;
  background: #f9fafb;
  border-radius: 6px;
}

.filter-btn {
  flex: 1;
  padding: 0.375rem 0.5rem;
  border: none;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  transition: all 0.2s ease;
  font-weight: 500;
  color: #4b5563;
  font-size: 0.8125rem;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.filter-btn:hover {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
}

.filter-btn.active {
  position: relative;
}

.filter-btn.active::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.15);
  border-radius: 4px;
  pointer-events: none;
  z-index: 1;
}

.category-section {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.section-title {
  font-size: 0.6875rem;
  font-weight: 600;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0 0.125rem;
  margin-bottom: 0.125rem;
}

.category-btn {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 0.625rem;
  border: none;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
  width: 100%;
  font-weight: 500;
  color: #4b5563;
  font-size: 0.8125rem;
  position: relative;
  z-index: 1;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.category-btn:hover {
  transform: translateX(2px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
}

.category-btn.has-color {
  position: relative;
}

.category-btn.has-color::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.85);
  border-radius: 4px;
  pointer-events: none;
  z-index: 0;
}

.category-btn.has-color:hover::before {
  background: rgba(255, 255, 255, 0.75);
}

.category-btn.active {
  position: relative;
}

.category-btn.active::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.15);
  border-radius: 4px;
  pointer-events: none;
  z-index: 1;
}

.category-icon {
  font-size: 1.125rem;
  position: relative;
  z-index: 1;
}

.category-name {
  font-weight: 600;
  position: relative;
  z-index: 1;
}

.status-section {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.5rem 0;
  font-size: 0.8125rem;
  color: #6b7280;
}

.status-item {
  display: flex;
  gap: 0.5rem;
}
</style>