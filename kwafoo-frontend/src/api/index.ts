const API_BASE = '/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })

  if (!res.ok) {
    const errorText = await res.text()
    throw new Error(`API Error ${res.status}: ${errorText}`)
  }

  return res.json()
}

export const api = {
  getNews: (params: {
    limit?: number
    offset?: number
    category?: string
    keyword?: string
  }) => {
    const query = new URLSearchParams()
    if (params.limit) query.set('limit', String(params.limit))
    if (params.offset) query.set('offset', String(params.offset))
    if (params.category) query.set('category', params.category)
    if (params.keyword) query.set('keyword', params.keyword)
    return request<import('../types/news').NewsListResponse>(`/news/?${query}`)
  },

  getNewsDetail: (id: number) =>
    request<import('../types/news').NewsItem>(`/news/${id}`),

  getStats: () =>
    request<import('../types/task').TaskStatus>('/tasks/status'),

  triggerCrawl: (sourceName?: string) =>
    request<import('../types/task').TaskResult>('/tasks/crawl', {
      method: 'POST',
      body: JSON.stringify({ source_name: sourceName }),
    }),

  triggerProcess: () =>
    request<import('../types/task').TaskResult>('/tasks/process', {
      method: 'POST',
    }),

  triggerPipeline: () =>
    request<import('../types/task').TaskResult>('/tasks/pipeline', {
      method: 'POST',
    }),

  getCategories: () =>
    request<{ categories: import('../types/news').CategoryConfig[] }>('/config/categories'),

  getAiTasks: () =>
    request<{ tasks: Array<{ name: string; version: string; description: string }> }>('/config/ai/tasks'),
}