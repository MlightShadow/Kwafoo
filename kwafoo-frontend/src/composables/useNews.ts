import { ref } from 'vue'
import { api } from '@/api'
import type { NewsItem, NewsListResponse } from '@/types/news'

export function useNews() {
  const newsList = ref<NewsItem[]>([])
  const total = ref(0)
  const loading = ref(false)
  const error = ref('')

  const limit = ref(20)
  const offset = ref(0)
  const selectedCategory = ref('')
  const selectedKeyword = ref('')

  async function fetchNews() {
    loading.value = true
    error.value = ''
    try {
      const res = await api.getNews({
        limit: limit.value,
        offset: offset.value,
        category: selectedCategory.value,
        keyword: selectedKeyword.value,
      })
      newsList.value = res.data
      total.value = res.total
    } catch (e: any) {
      error.value = e.message || '获取新闻失败'
    } finally {
      loading.value = false
    }
  }

  function nextPage() {
    offset.value += limit.value
    fetchNews()
  }

  function prevPage() {
    offset.value = Math.max(0, offset.value - limit.value)
    fetchNews()
  }

  function filterByCategory(category: string) {
    selectedCategory.value = category
    offset.value = 0
    fetchNews()
  }

  return {
    newsList,
    total,
    loading,
    error,
    limit,
    offset,
    selectedCategory,
    selectedKeyword,
    fetchNews,
    nextPage,
    prevPage,
    filterByCategory,
  }
}