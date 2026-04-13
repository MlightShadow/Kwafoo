export interface Config {
  categories: Record<string, {
    icon?: string
    color?: string
  }>
  default_category: string
  enable_ai_category: boolean
  image_display: {
    position: 'left' | 'right'
    show_thumbnail: boolean
  }
}

export interface SystemConfig {
  database: {
    path: string
  }
  server: {
    host: string
    port: number
    enable_websocket: boolean
  }
  scheduler: {
    fetch_interval: number
    ai_process_interval: number
    auto_fetch: boolean
    auto_ai_process: boolean
    auto_ai_after_fetch: boolean
  }
  ai: {
    base_url: string
    model: string
    api_key: string
    max_tokens: number
    temperature: number
    max_workers: number
    batch_size: number
    enable_summary: boolean
  }
}