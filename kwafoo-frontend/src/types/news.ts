export interface NewsItem {
  id: number
  title: string
  description: string
  url: string
  source: string
  publish_time: string
  fetch_time: string
  image_url: string
  category_from_source: string
  is_read: boolean
  category: string[]
  keywords: string[]
  ai_summary: string
  ai_comment: string
  ai_summary_en: string
  relevance_score: number
  importance_score: number
  source_score: number
}

export interface NewsListResponse {
  data: NewsItem[]
  total: number
  limit: number
  offset: number
}

export interface CategoryConfig {
  name: string
  keywords: string[]
}