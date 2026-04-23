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
  overflow-x: hidden;
}

.category-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 0.875rem;
  border: none;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
  width: 100%;
  font-weight: 500;
  color: #4b5563;
  font-size: 0.875rem;
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
  border-radius: 6px;
  pointer-events: none;
  z-index: 0;
}

.category-btn.has-color:hover::before {
  background: rgba(255, 255, 255, 0.75);
}

.category-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.category-icon {
  font-size: 1.25rem;
  position: relative;
  z-index: 1;
}

.category-name {
  font-weight: 600;
  position: relative;
  z-index: 1;
}
</style>