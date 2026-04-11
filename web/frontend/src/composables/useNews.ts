import { ref, computed } from 'vue'
import { useNewsStore } from '@/stores/news'
import { api } from '@/api'

export function useNews() {
  const newsStore = useNewsStore()
  const loading = ref(false)
  const error = ref<string | null>(null)

  const newsList = computed(() => newsStore.newsList)
  const currentCategory = computed(() => newsStore.currentCategory)
  const categories = computed(() => newsStore.categories)
  const stats = computed(() => newsStore.stats)
  const filteredNews = computed(() => newsStore.filteredNews)
  const newsCount = computed(() => newsStore.newsCount)

  async function loadNews(category?: string) {
    loading.value = true
    error.value = null
    try {
      await newsStore.loadNews(category)
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
      await newsStore.searchNews(query, limit)
    } catch (err: any) {
      error.value = err.message || '搜索新闻失败'
      console.error('搜索新闻失败:', err)
    } finally {
      loading.value = false
    }
  }

  async function loadStats() {
    try {
      await newsStore.loadStats()
    } catch (err: any) {
      console.error('加载统计失败:', err)
    }
  }

  async function clearNews() {
    try {
      const message = await newsStore.clearNews()
      return message
    } catch (err: any) {
      throw new Error(err.message || '清空新闻失败')
    }
  }

  function setCategory(category: string) {
    newsStore.setCategory(category)
  }

  function setCategories(cats: Record<string, { icon?: string; color?: string }>) {
    newsStore.setCategories(cats)
  }

  return {
    newsList,
    currentCategory,
    categories,
    stats,
    filteredNews,
    newsCount,
    loading,
    error,
    loadNews,
    searchNews,
    loadStats,
    clearNews,
    setCategory,
    setCategories
  }
}