export interface News {
  id: number
  title: string
  description: string
  ai_summary?: string
  content?: string
  url: string
  source: string
  source_url?: string
  category?: string
  publish_time?: string
  fetch_time: string
  is_visible: number
  ai_processed: number
  image_url?: string
  image_data?: string
  is_deleted: number
}

export interface NewsStats {
  total: number
  active: number
  deleted: number
  processed: number
  by_category: Record<string, number>
  by_source: Record<string, number>
}

export interface Category {
  name: string
  icon?: string
  color?: string
}