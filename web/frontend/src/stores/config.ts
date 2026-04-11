import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Config } from '@/types/config'
import { api } from '@/api'

export const useConfigStore = defineStore('config', () => {
  const config = ref<Config | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function loadConfig() {
    loading.value = true
    error.value = null
    try {
      const response = await api.getConfig()
      if (response.data.success) {
        config.value = response.data.data
      }
    } catch (err: any) {
      error.value = err.message || '加载配置失败'
      console.error('加载配置失败:', err)
    } finally {
      loading.value = false
    }
  }

  async function updateConfig(configData: Partial<Config>) {
    loading.value = true
    error.value = null
    try {
      const response = await api.updateConfig(configData)
      if (response.data.success) {
        config.value = response.data.data
        return response.data.message
      }
    } catch (err: any) {
      error.value = err.message || '更新配置失败'
      console.error('更新配置失败:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    config,
    loading,
    error,
    loadConfig,
    updateConfig
  }
})