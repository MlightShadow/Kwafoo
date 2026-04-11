import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ChatMessage, ChatResponse } from '@/types/chat'
import { api } from '@/api'

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMessage[]>([])
  const sessionId = ref<string | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function sendMessage(message: string, category?: string | null) {
    loading.value = true
    error.value = null

    try {
      const response = await api.chat(message, category, sessionId.value)
      if (response.data.success) {
        sessionId.value = response.data.session_id
        return response.data
      }
    } catch (err: any) {
      error.value = err.message || '发送消息失败'
      console.error('发送消息失败:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  function clearChat() {
    messages.value = []
    sessionId.value = null
  }

  return {
    messages,
    sessionId,
    loading,
    error,
    sendMessage,
    clearChat
  }
})