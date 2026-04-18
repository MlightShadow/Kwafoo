export interface Report {
  id: number
  report_type: 'daily' | 'weekly' | 'monthly'
  title: string
  content: ReportContent | null
  time_range_start: string
  time_range_end: string
  news_count: number
  ai_model: string
  generation_time: number
  created_at: string
  updated_at: string
}

export interface ReportContent {
  summary: string
  topics: ReportTopic[]
}

export interface ReportTopic {
  topic_title: string
  topic_summary: string
  reasoning: string
  news_items: ReportNewsItem[]
}

export interface ReportNewsItem {
  id: number
  title: string
  ai_summary: string
  category: string
  publish_time: string
  source: string
  url: string
}

export interface GenerateReportParams {
  report_type: 'daily' | 'weekly' | 'monthly'
  hours: number
}

export interface GetReportsParams {
  type: 'daily' | 'weekly' | 'monthly'
  limit?: number
  offset?: number
}