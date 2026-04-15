import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { News, NewsStats } from '@/types/news'
import type { Category } from '@/types/config'
import { api } from '@/api'

export const useNewsStore = defineStore('news', () => {
  const newsList = ref<News[]>([])
  const currentCategory = ref<string>('')
  const categories = ref<Category[]>([])
  const stats = ref<NewsStats | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const filteredNews = computed(() => {
    if (!currentCategory.value || currentCategory.value === '全部') {
      return newsList.value
    }
    return newsList.value.filter(news => news.category === currentCategory.value)
  })

  const newsCount = computed(() => filteredNews.value.length)

  async function loadNews(category?: string, limit: number = 30, offset: number = 0) {
    loading.value = true
    error.value = null
    try {
      let response
      if (category && category !== '全部') {
        response = await api.getNewsByCategory(category, limit, offset)
      } else {
        response = await api.getNews(limit, offset)
      }

      if (response.data.success) {
        if (offset === 0) {
          newsList.value = response.data.data
        } else {
          newsList.value = [...newsList.value, ...response.data.data]
        }
      }
    } catch (err: any) {
      error.value = err.message || '加载新闻失败'
      console.error('加载新闻失败:', err)
    } finally {
      loading.value = false
    }
  }

  async function searchNews(query: string, limit: number = 10) {
    loading.value = true
    error.value = null
    try {
      const response = await api.searchNews(query, limit)
      if (response.data.success) {
        newsList.value = response.data.data
      }
    } catch (err: any) {
      error.value = err.message || '搜索新闻失败'
      console.error('搜索新闻失败:', err)
    } finally {
      loading.value = false
    }
  }

  async function loadStats() {
    try {
      const response = await api.getNewsStats()
      if (response.data.success) {
        stats.value = response.data.data
      }
    } catch (err: any) {
      console.error('加载统计失败:', err)
    }
  }

  async function clearNews() {
    try {
      const response = await api.clearNews()
      if (response.data.success) {
        await loadNews(currentCategory.value)
        return response.data.message
      }
    } catch (err: any) {
      throw new Error(err.message || '清空新闻失败')
    }
  }

  function setCategory(category: string) {
    currentCategory.value = category
  }

  function setCategories(cats: Category[]) {
    categories.value = cats
  }

  function updateSingleNews(newsId: number, updates: Partial<News>) {
    console.log('更新新闻:', newsId, updates)
    const newsItem = newsList.value.find(n => n.id === newsId)
    console.log('找到的新闻项:', newsItem)
    if (newsItem) {
      console.log('更新前:', newsItem)
      Object.assign(newsItem, updates)
      console.log('更新后:', newsItem)
    } else {
      console.log('未找到新闻项，当前新闻列表:', newsList.value.map(n => n.id))
    }
  }

  return {
    newsList,
    currentCategory,
    categories,
    stats,
    loading,
    error,
    filteredNews,
    newsCount,
    loadNews,
    searchNews,
    loadStats,
    clearNews,
    setCategory,
    setCategories,
    updateSingleNews
  }
})