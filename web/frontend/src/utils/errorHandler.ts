import { App } from 'vue'
import { api } from '@/api'

interface ErrorResponse {
  success: false
  error: {
    code: string
    message: string
    status_code: number
  }
}

interface ApiError extends Error {
  response?: {
    data: ErrorResponse
    status: number
  }
}

export class APIError extends Error {
  code: string
  status: number
  message: string

  constructor(message: string, code: string = 'API_ERROR', status: number = 500) {
    super(message)
    this.name = 'APIError'
    this.code = code
    this.status = status
    this.message = message
  }
}

export class ValidationError extends APIError {
  constructor(message: string) {
    super(message, 'VALIDATION_ERROR', 400)
  }
}

export class NotFoundError extends APIError {
  constructor(message: string = '资源未找到') {
    super(message, 'NOT_FOUND', 404)
  }
}

export class UnauthorizedError extends APIError {
  constructor(message: string = '未授权') {
    super(message, 'UNAUTHORIZED', 401)
  }
}

export class ForbiddenError extends APIError {
  constructor(message: string = '禁止访问') {
    super(message, 'FORBIDDEN', 403)
  }
}

export class RateLimitError extends APIError {
  constructor(message: string = '请求过于频繁') {
    super(message, 'RATE_LIMIT_EXCEEDED', 429)
  }
}

export class ServiceUnavailableError extends APIError {
  constructor(message: string = '服务暂时不可用') {
    super(message, 'SERVICE_UNAVAILABLE', 503)
  }
}

export function handleApiError(error: any): APIError {
  if (error instanceof APIError) {
    return error
  }

  if (error.response) {
    const response = error.response
    
    if (response.data && response.data.error) {
      const errorData = response.data.error
      
      switch (errorData.code) {
        case 'VALIDATION_ERROR':
          return new ValidationError(errorData.message)
        case 'NOT_FOUND':
          return new NotFoundError(errorData.message)
        case 'UNAUTHORIZED':
          return new UnauthorizedError(errorData.message)
        case 'FORBIDDEN':
          return new ForbiddenError(errorData.message)
        case 'RATE_LIMIT_EXCEEDED':
          return new RateLimitError(errorData.message)
        case 'SERVICE_UNAVAILABLE':
          return new ServiceUnavailableError(errorData.message)
        default:
          return new APIError(errorData.message, errorData.code, errorData.status_code)
      }
    }
    
    // 没有标准错误格式，使用状态码判断
    switch (response.status) {
      case 400:
        return new ValidationError('请求参数错误')
      case 401:
        return new UnauthorizedError()
      case 403:
        return new ForbiddenError()
      case 404:
        return new NotFoundError()
      case 429:
        return new RateLimitError()
      case 503:
        return new ServiceUnavailableError()
      default:
        return new APIError('服务器错误', 'INTERNAL_ERROR', response.status)
    }
  }

  if (error.request) {
    // 请求已发送但没有收到响应
    return new ServiceUnavailableError('网络连接失败，请检查网络设置')
  }

  // 其他错误
  return new APIError(error.message || '未知错误', 'UNKNOWN_ERROR', 500)
}

export function setupGlobalErrorHandler(app: App) {
  app.config.errorHandler = (error, instance, info) => {
    console.error('全局错误:', error)
    console.error('错误信息:', info)
    
    // 可以在这里添加错误上报逻辑
    // 例如：发送到错误监控服务
  }

  window.addEventListener('unhandledrejection', (event) => {
    console.error('未处理的Promise拒绝:', event.reason)
    
    // 可以在这里添加错误上报逻辑
  })

  window.addEventListener('error', (event) => {
    console.error('全局错误:', event.error)
    
    // 可以在这里添加错误上报逻辑
  })
}

export function showErrorToast(error: APIError | Error, duration: number = 3000) {
  // 这里可以集成Element Plus的ElMessage或其他通知组件
  console.error('错误:', error.message)
  
  // 简单实现，实际项目中可以使用更好的通知组件
  const toast = document.createElement('div')
  toast.className = 'error-toast'
  toast.textContent = error.message
  toast.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 12px 20px;
    background: #f56c6c;
    color: white;
    border-radius: 4px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
    z-index: 9999;
    animation: slideIn 0.3s ease;
  `
  
  document.body.appendChild(toast)
  
  setTimeout(() => {
    toast.style.animation = 'slideOut 0.3s ease'
    setTimeout(() => {
      document.body.removeChild(toast)
    }, 300)
  }, duration)
}

export function showSuccessToast(message: string, duration: number = 3000) {
  const toast = document.createElement('div')
  toast.className = 'success-toast'
  toast.textContent = message
  toast.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 12px 20px;
    background: #67c23a;
    color: white;
    border-radius: 4px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
    z-index: 9999;
    animation: slideIn 0.3s ease;
  `
  
  document.body.appendChild(toast)
  
  setTimeout(() => {
    toast.style.animation = 'slideOut 0.3s ease'
    setTimeout(() => {
      document.body.removeChild(toast)
    }, 300)
  }, duration)
}

// 添加动画样式
const style = document.createElement('style')
style.textContent = `
  @keyframes slideIn {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
  
  @keyframes slideOut {
    from {
      transform: translateX(0);
      opacity: 1;
    }
    to {
      transform: translateX(100%);
      opacity: 0;
    }
  }
`
document.head.appendChild(style)