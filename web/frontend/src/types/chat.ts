export interface ChatMessage {
  id: number
  session_id: number
  role: 'user' | 'assistant'
  content: string
  context_news_ids?: string
  created_at: string
}

export interface ChatSession {
  id: number
  session_id: string
  user_id?: string
  created_at: string
  updated_at: string
}

export interface ChatResponse {
  success: boolean
  message: string
  context?: string
  session_id: string
  response: string
}