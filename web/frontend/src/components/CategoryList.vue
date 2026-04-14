<template>
  <div class="category-list">
    <button 
      v-for="(category, name) in allCategories" 
      :key="name"
      class="category-btn"
      :class="{ active: currentCategory === name }"
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
    '全部': { icon: '📰' },
    '未分类': { icon: '📋' }
  }
  
  // 将数组转换为对象
  newsStore.categories.forEach(cat => {
    categories[cat.name] = {
      icon: cat.icon || '📄',
      name: cat.name
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
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: left;
  width: 100%;
}

.category-btn:hover {
  background: #f5f5f5;
  border-color: #007bff;
}

.category-btn.active {
  background: #007bff;
  color: white;
  border-color: #007bff;
}

.category-icon {
  font-size: 1.2rem;
}

.category-name {
  font-weight: 500;
}
</style>