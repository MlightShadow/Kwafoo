import { ref } from 'vue'
import { api } from '@/api'
import type { TaskStatus, TaskResult } from '@/types/task'

export function useTasks() {
  const taskStatus = ref<TaskStatus | null>(null)
  const loading = ref(false)
  const message = ref('')

  async function fetchStatus() {
    loading.value = true
    try {
      taskStatus.value = await api.getStats()
    } catch (e: any) {
      message.value = e.message || '获取状态失败'
    } finally {
      loading.value = false
    }
  }

  async function triggerCrawl(sourceName?: string) {
    loading.value = true
    message.value = ''
    try {
      const result = await api.triggerCrawl(sourceName)
      message.value = result.message
      return result
    } catch (e: any) {
      message.value = e.message || '触发爬虫失败'
    } finally {
      loading.value = false
    }
  }

  async function triggerProcess() {
    loading.value = true
    message.value = ''
    try {
      const result = await api.triggerProcess()
      message.value = result.message
      return result
    } catch (e: any) {
      message.value = e.message || '触发处理失败'
    } finally {
      loading.value = false
    }
  }

  async function triggerPipeline() {
    loading.value = true
    message.value = ''
    try {
      const result = await api.triggerPipeline()
      message.value = result.message
      return result
    } catch (e: any) {
      message.value = e.message || '触发管道失败'
    } finally {
      loading.value = false
    }
  }

  return {
    taskStatus,
    loading,
    message,
    fetchStatus,
    triggerCrawl,
    triggerProcess,
    triggerPipeline,
  }
}