import { ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/api'
import type { NewsItem } from '@/types/news'

export const useNewsStore = defineStore('news', () => {
  const newsList = ref<NewsItem[]>([])
  const selectedItem = ref<NewsItem | null>(null)
  const total = ref(0)
  const loading = ref(false)
  const error = ref('')

  async function fetchNews(limit = 20, offset = 0, category = '', keyword = '') {
    loading.value = true
    error.value = ''
    try {
      const res = await api.getNews({ limit, offset, category, keyword })
      newsList.value = res.data
      total.value = res.total
    } catch (e: any) {
      error.value = e.message || '获取新闻失败'
    } finally {
      loading.value = false
    }
  }

  async function fetchDetail(id: number) {
    try {
      selectedItem.value = await api.getNewsDetail(id)
    } catch (e: any) {
      error.value = e.message || '获取详情失败'
    }
  }

  return {
    newsList,
    selectedItem,
    total,
    loading,
    error,
    fetchNews,
    fetchDetail,
  }
})