import axios, { AxiosInstance, AxiosResponse } from 'axios'
import type { News, NewsStats } from '@/types/news'
import type { ChatResponse } from '@/types/chat'
import type { Config } from '@/types/config'

class APIClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: '/api',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json'
      }
    })

    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Error:', error)
        return Promise.reject(error)
      }
    )
  }

  // News API
  async getNews(): Promise<AxiosResponse<{ success: boolean; data: News[]; count: number }>> {
    return this.client.get('/news')
  }

  async getNewsByCategory(category: string): Promise<AxiosResponse<{ success: boolean; data: News[]; count: number; category: string }>> {
    return this.client.get(`/news/category?category=${encodeURIComponent(category)}`)
  }

  async searchNews(query: string, limit: number = 10): Promise<AxiosResponse<{ success: boolean; data: News[]; count: number; query: string }>> {
    return this.client.get(`/news/search?q=${encodeURIComponent(query)}&limit=${limit}`)
  }

  async getNewsStats(): Promise<AxiosResponse<{ success: boolean; data: NewsStats }>> {
    return this.client.get('/news/stats')
  }

  async clearNews(): Promise<AxiosResponse<{ success: boolean; message: string; count: number }>> {
    return this.client.post('/news/clear')
  }

  // Chat API
  async chat(message: string, category?: string | null, sessionId?: string | null): Promise<AxiosResponse<ChatResponse>> {
    return this.client.post('/chat', {
      message,
      category,
      session_id: sessionId
    })
  }

  // System API
  async getProgress(): Promise<AxiosResponse<{ success: boolean; data: any[] }>> {
    return this.client.get('/progress')
  }

  async healthCheck(): Promise<AxiosResponse<{ success: boolean; status: string; timestamp: string }>> {
    return this.client.get('/health')
  }

  async manualFetch(): Promise<AxiosResponse<{ success: boolean; message: string }>> {
    return this.client.post('/fetch')
  }

  // Config API
  async getConfig(): Promise<AxiosResponse<{ success: boolean; data: Config }>> {
    return this.client.get('/config')
  }

  async updateConfig(configData: Partial<Config>): Promise<AxiosResponse<{ success: boolean; message: string; data: Config }>> {
    return this.client.post('/config', configData)
  }

  // AI API
  async getAIStatus(): Promise<AxiosResponse<{ success: boolean; data: any }>> {
    return this.client.get('/ai/status')
  }

  async processAINews(): Promise<AxiosResponse<{ success: boolean; message: string }>> {
    return this.client.post('/ai/process')
  }
}

export const api = new APIClient()