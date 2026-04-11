<template>
  <div v-if="isOpen" class="chat-modal-overlay" @click="closeModal">
    <div class="chat-modal-content" @click.stop>
      <div class="chat-modal-header">
        <h3>💬 AI 对话</h3>
        <button class="close-button" @click="closeModal">&times;</button>
      </div>
      <div class="chat-modal-body">
        <div class="chat-messages">
          <div 
            v-for="message in messages" 
            :key="message.id" 
            class="chat-message"
            :class="message.role"
          >
            <div class="message-content">
              <strong>{{ message.role === 'user' ? '用户' : 'AI助手' }}：</strong>
              <p>{{ message.content }}</p>
              <span class="message-time">{{ formatTime(message.created_at) }}</span>
            </div>
          </div>
          
          <div v-if="loading" class="chat-message assistant loading">
            <div class="message-content">
              <p>AI正在思考...</p>
            </div>
          </div>
        </div>
        
        <div class="chat-input-area">
          <textarea 
            v-model="inputMessage" 
            placeholder="输入您的问题..." 
            class="chat-input"
            @keypress.enter.prevent="handleSend"
            rows="3"
          ></textarea>
          <button 
            @click="handleSend" 
            class="send-button"
            :disabled="loading || !inputMessage.trim()"
          >
            发送
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useChatStore } from '@/stores/chat'
import { useNewsStore } from '@/stores/news'

interface Props {
  isOpen: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
}>()

const chatStore = useChatStore()
const newsStore = useNewsStore()

const inputMessage = ref('')

const messages = computed(() => chatStore.messages)
const loading = computed(() => chatStore.loading)

function closeModal() {
  emit('close')
}

async function handleSend() {
  if (!inputMessage.value.trim() || loading.value) return
  
  const userMessage = inputMessage.value.trim()
  inputMessage.value = ''
  
  try {
    const response = await chatStore.sendMessage(userMessage, newsStore.currentCategory)
    
    chatStore.messages.push({
      id: Date.now(),
      session_id: parseInt(response.session_id),
      role: 'user',
      content: userMessage,
      created_at: new Date().toISOString()
    })
    
    chatStore.messages.push({
      id: Date.now() + 1,
      session_id: parseInt(response.session_id),
      role: 'assistant',
      content: response.response,
      created_at: new Date().toISOString()
    })
  } catch (error: any) {
    alert('发送失败: ' + error.message)
  }
}

function formatTime(timeString: string): string {
  const date = new Date(timeString)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.chat-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.chat-modal-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.chat-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #e0e0e0;
}

.chat-modal-header h3 {
  margin: 0;
  font-size: 1.2rem;
  color: #333;
}

.close-button {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #666;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background 0.3s ease;
}

.close-button:hover {
  background: #f5f5f5;
}

.chat-modal-body {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-height: 50vh;
}

.chat-message {
  display: flex;
  max-width: 80%;
}

.chat-message.user {
  align-self: flex-end;
}

.chat-message.assistant {
  align-self: flex-start;
}

.chat-message.loading {
  opacity: 0.7;
}

.message-content {
  padding: 1rem;
  border-radius: 12px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.chat-message.user .message-content {
  background: #007bff;
  color: white;
}

.chat-message.assistant .message-content {
  background: #f5f5f5;
  color: #333;
}

.message-content strong {
  display: block;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

.message-content p {
  margin: 0;
  line-height: 1.5;
}

.message-time {
  display: block;
  margin-top: 0.5rem;
  font-size: 0.8rem;
  opacity: 0.7;
}

.chat-input-area {
  padding: 1rem;
  border-top: 1px solid #e0e0e0;
  display: flex;
  gap: 0.5rem;
  align-items: flex-end;
}

.chat-input {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  resize: none;
  font-family: inherit;
  font-size: 1rem;
}

.chat-input:focus {
  outline: none;
  border-color: #007bff;
}

.send-button {
  padding: 0.75rem 1.5rem;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
  transition: background 0.3s ease;
}

.send-button:hover:not(:disabled) {
  background: #0056b3;
}

.send-button:disabled {
  background: #ccc;
  cursor: not-allowed;
}
</style>