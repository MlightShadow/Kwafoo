import { ref, onMounted, onUnmounted } from 'vue'
import { api } from '@/api'

export interface WebSocketMessage {
  type: string
  data?: any
  timestamp: string
}

export function useWebSocket(url: string = 'ws://localhost:8001') {
  const isConnected = ref(false)
  const messages = ref<WebSocketMessage[]>([])
  const error = ref<string | null>(null)
  
  let ws: WebSocket | null = null
  let reconnectTimer: number | null = null
  const reconnectDelay = 3000
  const maxReconnectAttempts = 10
  let reconnectAttempts = 0

  function connect() {
    if (ws && ws.readyState === WebSocket.OPEN) {
      return
    }

    try {
      ws = new WebSocket(url)
      
      ws.onopen = () => {
        isConnected.value = true
        error.value = null
        reconnectAttempts = 0
        console.log('WebSocket连接成功')
      }
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          messages.value.push({
            type: data.type,
            data: data,
            timestamp: new Date().toISOString()
          })
          
          // 触发自定义事件
          window.dispatchEvent(new CustomEvent('websocket-message', { detail: data }))
        } catch (e) {
          console.error('解析WebSocket消息失败:', e)
        }
      }
      
      ws.onerror = (event) => {
        console.error('WebSocket错误:', event)
        error.value = 'WebSocket连接错误'
      }
      
      ws.onclose = () => {
        isConnected.value = false
        console.log('WebSocket连接关闭')
        
        // 自动重连
        if (reconnectAttempts < maxReconnectAttempts) {
          reconnectAttempts++
          console.log(`尝试重连 (${reconnectAttempts}/${maxReconnectAttempts})...`)
          reconnectTimer = window.setTimeout(() => {
            connect()
          }, reconnectDelay)
        } else {
          error.value = 'WebSocket连接失败，已达到最大重连次数'
        }
      }
    } catch (e) {
      console.error('创建WebSocket连接失败:', e)
      error.value = '创建WebSocket连接失败'
    }
  }

  function disconnect() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    
    if (ws) {
      ws.close()
      ws = null
    }
    
    isConnected.value = false
  }

  function send(message: any) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket未连接，无法发送消息')
    }
  }

  function onMessage(callback: (message: any) => void) {
    const handler = (event: Event) => {
      const customEvent = event as CustomEvent
      callback(customEvent.detail)
    }
    
    window.addEventListener('websocket-message', handler)
    
    return () => {
      window.removeEventListener('websocket-message', handler)
    }
  }

  onMounted(() => {
    connect()
  })

  onUnmounted(() => {
    disconnect()
  })

  return {
    isConnected,
    messages,
    error,
    connect,
    disconnect,
    send,
    onMessage
  }
}