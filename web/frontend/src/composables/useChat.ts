import { ref, computed } from 'vue'
import { useChatStore } from '@/stores/chat'
import { useNewsStore } from '@/stores/news'

export function useChat() {
  const chatStore = useChatStore()
  const newsStore = useNewsStore()

  const loading = ref(false)
  const error = ref<string | null>(null)

  const messages = computed(() => chatStore.messages)
  const sessionId = computed(() => chatStore.sessionId)

  async function sendMessage(message: string, category?: string | null) {
    if (!message.trim() || loading.value) return

    loading.value = true
    error.value = null

    try {
      const response = await chatStore.sendMessage(message, category)
      
      // 添加用户消息
      chatStore.messages.push({
        id: Date.now(),
        session_id: parseInt(response.session_id),
        role: 'user',
        content: message,
        created_at: new Date().toISOString()
      })
      
      // 添加AI回复
      chatStore.messages.push({
        id: Date.now() + 1,
        session_id: parseInt(response.session_id),
        role: 'assistant',
        content: response.response,
        created_at: new Date().toISOString()
      })
      
      return response
    } catch (err: any) {
      error.value = err.message || '发送消息失败'
      console.error('发送消息失败:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  function clearChat() {
    chatStore.clearChat()
  }

  function formatTime(timeString: string): string {
    const date = new Date(timeString)
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }

  return {
    messages,
    sessionId,
    loading,
    error,
    sendMessage,
    clearChat,
    formatTime
  }
}