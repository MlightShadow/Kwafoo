<template>
  <div class="category-list">
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
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useNewsStore } from '@/stores/news'

const newsStore = useNewsStore()

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

async function selectCategory(category: string) {
  newsStore.setCategory(category)
  await newsStore.loadNews(category)
}
</script>

<style scoped>
.category-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.category-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 0.875rem;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
  width: 100%;
  font-weight: 500;
  color: #4b5563;
  font-size: 0.875rem;
}

.category-btn:hover {
  background: #f9fafb;
  border-color: #d1d5db;
  transform: translateX(4px);
}

.category-btn.has-color:hover {
  background: rgba(255, 255, 255, 0.8);
  border-color: rgba(0, 0, 0, 0.1);
}

.category-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: transparent;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.category-btn.has-color.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: transparent;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.category-icon {
  font-size: 1.25rem;
}

.category-name {
  font-weight: 600;
}
</style>