import axios, { AxiosInstance, AxiosResponse } from 'axios'
import type { News, NewsStats } from '@/types/news'
import type { ChatResponse } from '@/types/chat'
import type { Config } from '@/types/config'
import type { Report, GenerateReportParams, GenerateReportResponse, GetReportsParams } from '@/types/report'

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
  async getNews(limit: number = 30, offset: number = 0): Promise<AxiosResponse<{ success: boolean; data: News[]; count: number; limit: number; offset: number }>> {
    return this.client.get(`/news?limit=${limit}&offset=${offset}`)
  }

  async getNewsByCategory(category: string, limit: number = 30, offset: number = 0): Promise<AxiosResponse<{ success: boolean; data: News[]; count: number; category: string; limit: number; offset: number }>> {
    return this.client.get(`/news/category?category=${encodeURIComponent(category)}&limit=${limit}&offset=${offset}`)
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

  async markAsRead(newsId: number, isRead: boolean): Promise<AxiosResponse<{ success: boolean; message: string }>> {
    return this.client.post('/news/mark-read', { news_id: newsId, is_read: isRead })
  }

  async getReadNews(limit: number = 100): Promise<AxiosResponse<{ success: boolean; data: News[]; count: number }>> {
    return this.client.get(`/news/read?limit=${limit}`)
  }

  async getUnreadNews(limit: number = 100): Promise<AxiosResponse<{ success: boolean; data: News[]; count: number }>> {
    return this.client.get(`/news/unread?limit=${limit}`)
  }

  async getNewsDetail(id: number): Promise<AxiosResponse<{ 
    success: boolean; 
    data: News; 
    all_fields: Record<string, string>; 
    debug_info: Record<string, string>;
    ai_history: Array<{
      id: number;
      news_id: number;
      task_type: string;
      status: string;
      priority: number;
      retry_count: number;
      error_message: string | null;
      created_at: string;
      updated_at: string;
    }>
  }>> {
    return this.client.get(`/news/detail?id=${id}`)
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
  async getConfig(): Promise<AxiosResponse<{ success: boolean; data: { categories: any[], default_category: string, enable_ai_category: boolean, image_display: any } }>> {
    return this.client.get('/config')
  }

  async updateConfig(configData: Partial<{ categories: any[], default_category: string, enable_ai_category: boolean, image_display: any }>): Promise<AxiosResponse<{ success: boolean; message: string; data: any }>> {
    return this.client.post('/config', configData)
  }

  // AI API
  async getAIStatus(): Promise<AxiosResponse<{ success: boolean; data: any }>> {
    return this.client.get('/ai/status')
  }

  async processAINews(): Promise<AxiosResponse<{ success: boolean; message: string }>> {
    return this.client.post('/ai/process')
  }

  async processAllNewsAI(): Promise<AxiosResponse<{ success: boolean; message: string }>> {
    return this.client.post('/ai/process/all')
  }

  async processSingleNewsAI(newsId: number, force: boolean = false): Promise<AxiosResponse<{ success: boolean; message: string }>> {
    return this.client.post('/ai/process/single', { news_id: newsId, force })
  }

  async processNewsCategory(newsId: number): Promise<AxiosResponse<{ success: boolean; message: string }>> {
    return this.client.post('/ai/process/category', { news_id: newsId })
  }

  async processNewsSummary(newsId: number): Promise<AxiosResponse<{ success: boolean; message: string }>> {
    return this.client.post('/ai/process/summary', { news_id: newsId })
  }

  async processNewsReanalyze(newsId: number): Promise<AxiosResponse<{ success: boolean; message: string }>> {
    return this.client.post('/ai/process/reanalyze', { news_id: newsId, force: true })
  }

  async getAIQueueStats(): Promise<AxiosResponse<{ success: boolean; data: any }>> {
    return this.client.get('/ai/queue/stats')
  }

  // Report API
  async generateReport(params: GenerateReportParams): Promise<AxiosResponse<GenerateReportResponse>> {
    return this.client.post('/reports/generate', params)
  }

  async getReports(params: GetReportsParams): Promise<AxiosResponse<{ 
    success: boolean; 
    data: Report[]; 
    count: number; 
    type: string; 
    limit: number; 
    offset: number 
  }>> {
    return this.client.get(`/reports?type=${params.type}&limit=${params.limit || 10}&offset=${params.offset || 0}`)
  }

  async getReportDetail(id: number): Promise<AxiosResponse<{ success: boolean; data: Report }>> {
    return this.client.get(`/reports/detail?id=${id}`)
  }

  async deleteReport(id: number): Promise<AxiosResponse<{ success: boolean; message: string }>> {
    return this.client.post('/reports/delete', { id })
  }

  async getLatestReport(type: 'daily' | 'weekly' | 'monthly' = 'daily'): Promise<AxiosResponse<{ success: boolean; data: Report | null }>> {
    return this.client.get(`/reports/latest?type=${type}`)
  }
}

export const api = new APIClient()