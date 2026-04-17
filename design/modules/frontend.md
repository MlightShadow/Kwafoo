# 前端模块设计

## 模块概述

前端模块基于Vue 3 + TypeScript构建，提供现代化的Web用户界面。模块采用组件化架构，支持响应式设计、实时状态更新、WebSocket通信等功能。

## 技术栈

### 核心框架
- **Vue 3**: 渐进式JavaScript框架
- **TypeScript**: 类型安全的JavaScript超集
- **Vite**: 下一代前端构建工具

### UI组件库
- **Element Plus**: 基于Vue 3的组件库

### 状态管理
- **Pinia**: Vue 3官方推荐的状态管理库

### 路由管理
- **Vue Router**: Vue.js官方路由管理器

### HTTP客户端
- **Axios**: 基于Promise的HTTP客户端

### 构建工具
- **Vite**: 快速的构建工具
- **vue-tsc**: TypeScript类型检查

## 项目结构

```
web/frontend/
├── src/
│   ├── api/              # API客户端
│   │   └── index.ts     # 统一API客户端
│   ├── assets/          # 静态资源
│   ├── components/      # 组件
│   │   ├── NewsCard.vue       # 新闻卡片组件
│   │   ├── CategoryList.vue   # 分类列表组件
│   │   └── ChatModal.vue      # 聊天模态框组件
│   ├── composables/     # 组合式函数
│   │   ├── useNews.ts         # 新闻相关逻辑
│   │   ├── useChat.ts         # 聊天相关逻辑
│   │   └── useWebSocket.ts    # WebSocket连接管理
│   ├── router/          # 路由配置
│   │   └── index.ts     # 路由配置
│   ├── stores/          # 状态管理
│   │   ├── news.ts      # 新闻状态管理
│   │   ├── chat.ts      # 聊天状态管理
│   │   └── config.ts    # 配置状态管理
│   ├── types/           # 类型定义
│   │   ├── news.ts      # 新闻相关类型
│   │   ├── chat.ts      # 聊天相关类型
│   │   └── config.ts    # 配置相关类型
│   ├── utils/           # 工具函数
│   │   └── errorHandler.ts  # 错误处理
│   ├── App.vue          # 主应用组件
│   └── main.ts          # 应用入口
├── index.html           # HTML模板
├── package.json         # 依赖配置
├── tsconfig.json        # TypeScript配置
└── vite.config.ts       # Vite配置
```

## 核心组件

### 1. App.vue（主应用组件）

**功能：**
- 应用布局
- 顶部导航栏
- 侧边栏（分类列表）
- WebSocket集成
- 服务器状态监控
- 系统状态展示

**核心功能：**
- 响应式布局
- 实时状态更新
- WebSocket连接管理
- 错误处理和重连

**代码引用：**
[web/frontend/src/App.vue](../../web/frontend/src/App.vue)

### 2. NewsCard.vue（新闻卡片组件）

**功能：**
- 展示新闻卡片
- AI摘要显示
- 分类标签
- 阅读状态管理
- 图片展示
- 重新分析功能

**核心功能：**
- 支持图片背景或分类颜色背景
- AI摘要悬停显示
- 阅读状态切换
- 重新分析按钮
- 响应式设计

**代码引用：**
[web/frontend/src/components/NewsCard.vue](../../web/frontend/src/components/NewsCard.vue)

### 3. CategoryList.vue（分类列表组件）

**功能：**
- 展示分类列表
- 分类筛选
- 分类统计

**核心功能：**
- 动态分类列表
- 分类图标和颜色
- 分类新闻数量
- 点击切换分类

**代码引用：**
[web/frontend/src/components/CategoryList.vue](../../web/frontend/src/components/CategoryList.vue)

### 4. ChatModal.vue（聊天模态框组件）

**功能：**
- 聊天界面
- 消息展示
- 消息发送
- 对话历史

**核心功能：**
- 模态框界面
- 消息列表
- 输入框
- 发送按钮
- 自动滚动

**代码引用：**
[web/frontend/src/components/ChatModal.vue](../../web/frontend/src/components/ChatModal.vue)

## 视图页面

### 1. NewsView.vue（新闻列表视图）

**功能：**
- 展示新闻列表
- 分类筛选
- 搜索功能
- 分页加载
- 阅读状态过滤

**核心功能：**
- 新闻网格布局
- 分类标签切换
- 搜索框
- 加载更多
- 空状态提示

**代码引用：**
[web/frontend/src/views/NewsView.vue](../../web/frontend/src/views/NewsView.vue)

### 2. AdminView.vue（管理界面）

**功能：**
- 新闻源管理
- 系统配置
- 统计信息
- 快捷操作

**核心功能：**
- 新闻统计卡片
- RSS源配置
- API源配置
- 网页源配置
- 清空数据
- 保存配置

**代码引用：**
[web/frontend/src/views/AdminView.vue](../../web/frontend/src/views/AdminView.vue)

### 3. MonitorView.vue（系统监控界面）

**功能：**
- 任务进度监控
- 系统信息展示
- AI状态监控

**核心功能：**
- 任务列表
- 进度条
- 系统状态
- AI状态
- 实时更新

**代码引用：**
[web/frontend/src/views/MonitorView.vue](../../web/frontend/src/views/MonitorView.vue)

## 状态管理

### 1. news.ts（新闻状态管理）

**功能：**
- 新闻列表管理
- 分类管理
- 统计信息
- 加载状态

**核心状态：**
```typescript
{
  newsList: News[],
  currentCategory: string,
  categories: Category[],
  stats: NewsStats | null,
  loading: boolean,
  error: string | null
}
```

**核心操作：**
- `loadNews()`: 加载新闻
- `searchNews()`: 搜索新闻
- `loadCategories()`: 加载分类
- `loadStats()`: 加载统计

**代码引用：**
[web/frontend/src/stores/news.ts](../../web/frontend/src/stores/news.ts)

### 2. chat.ts（聊天状态管理）

**功能：**
- 聊天消息管理
- 会话管理
- 聊天状态

**核心状态：**
```typescript
{
  messages: ChatMessage[],
  sessionId: string,
  loading: boolean,
  error: string | null
}
```

**核心操作：**
- `sendMessage()`: 发送消息
- `loadHistory()`: 加载历史
- `clearMessages()`: 清空消息

**代码引用：**
[web/frontend/src/stores/chat.ts](../../web/frontend/src/stores/chat.ts)

### 3. config.ts（配置状态管理）

**功能：**
- 配置管理
- 分类配置
- 图片显示配置

**核心状态：**
```typescript
{
  categories: Category[],
  defaultCategory: string,
  enableAICategory: boolean,
  imageDisplay: ImageDisplayConfig
}
```

**核心操作：**
- `loadConfig()`: 加载配置
- `updateConfig()`: 更新配置

**代码引用：**
[web/frontend/src/stores/config.ts](../../web/frontend/src/stores/config.ts)

## API客户端

### index.ts（统一API客户端）

**功能：**
- 封装Axios
- 统一错误处理
- 请求拦截器
- 响应拦截器

**核心方法：**
```typescript
class APIClient {
  // 新闻API
  getNews(limit, offset)
  getNewsByCategory(category, limit, offset)
  searchNews(query, limit)
  getNewsStats()
  clearNews()
  markAsRead(newsId, isRead)
  
  // AI API
  getAIStatus()
  processAINews()
  processAllNewsAI()
  reanalyzeNews(newsId, taskType)
  
  // 聊天API
  chat(message, sessionId, category)
  getChatHistory(sessionId)
  
  // 配置API
  getConfig()
  updateConfig(config)
  
  // 系统API
  getProgress()
  healthCheck()
  manualFetch()
  manualProcessAI()
}
```

**代码引用：**
[web/frontend/src/api/index.ts](../../web/frontend/src/api/index.ts)

## 组合式函数

### 1. useNews.ts（新闻相关逻辑）

**功能：**
- 新闻加载
- 搜索功能
- 分类筛选
- 分页加载

**核心功能：**
- 无限滚动
- 搜索防抖
- 分类切换
- 加载状态管理

**代码引用：**
[web/frontend/src/composables/useNews.ts](../../web/frontend/src/composables/useNews.ts)

### 2. useChat.ts（聊天相关逻辑）

**功能：**
- 消息发送
- 对话历史
- 自动滚动

**核心功能：**
- 消息发送
- 历史加载
- 自动滚动到底部
- 加载状态管理

**代码引用：**
[web/frontend/src/composables/useChat.ts](../../web/frontend/src/composables/useChat.ts)

### 3. useWebSocket.ts（WebSocket连接管理）

**功能：**
- WebSocket连接
- 消息处理
- 重连机制
- 状态管理

**核心功能：**
- 自动连接
- 消息监听
- 自动重连
- 状态更新

**代码引用：**
[web/frontend/src/composables/useWebSocket.ts](../../web/frontend/src/composables/useWebSocket.ts)

## 路由配置

### index.ts（路由配置）

**路由定义：**
```typescript
const routes = [
  {
    path: '/',
    name: 'news',
    component: NewsView
  },
  {
    path: '/monitor',
    name: 'monitor',
    component: MonitorView
  },
  {
    path: '/admin',
    name: 'admin',
    component: AdminView
  }
]
```

**代码引用：**
[web/frontend/src/router/index.ts](../../web/frontend/src/router/index.ts)

## 类型定义

### 1. news.ts（新闻相关类型）

**核心类型：**
```typescript
interface News {
  id: number
  title: string
  description: string
  ai_summary: string
  url: string
  source: string
  category: string
  publish_time: string
  fetch_time: string
  is_visible: number
  ai_processed: number
  image_url: string
  is_read: number
}

interface Category {
  name: string
  icon: string
  color: string
}

interface NewsStats {
  total: number
  active: number
  deleted: number
  processed: number
}
```

**代码引用：**
[web/frontend/src/types/news.ts](../../web/frontend/src/types/news.ts)

### 2. chat.ts（聊天相关类型）

**核心类型：**
```typescript
interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp?: string
}

interface ChatResponse {
  response: string
  context: string
  session_id: string
}
```

**代码引用：**
[web/frontend/src/types/chat.ts](../../web/frontend/src/types/chat.ts)

### 3. config.ts（配置相关类型）

**核心类型：**
```typescript
interface Category {
  name: string
  icon: string
  color: string
}

interface ImageDisplayConfig {
  enabled: boolean
  position: 'left' | 'right' | 'background'
  size: 'small' | 'medium' | 'large'
}
```

**代码引用：**
[web/frontend/src/types/config.ts](../../web/frontend/src/types/config.ts)

## 工具函数

### errorHandler.ts（错误处理）

**功能：**
- 全局错误处理
- 错误提示
- 日志记录

**核心功能：**
- 错误拦截
- 错误提示
- 错误日志

**代码引用：**
[web/frontend/src/utils/errorHandler.ts](../../web/frontend/src/utils/errorHandler.ts)

## WebSocket通信

### 连接管理

**连接流程：**
1. 应用启动时自动连接
2. 连接失败自动重连
3. 连接断开自动重连
4. 心跳检测保持连接

**消息类型：**
- `task_started`: 任务开始
- `progress_update`: 进度更新
- `task_completed`: 任务完成
- `task_failed`: 任务失败

**消息处理：**
- 更新任务状态
- 更新进度条
- 显示任务信息
- 错误提示

## 响应式设计

### 断点设置

```css
/* 移动设备 */
@media (max-width: 768px) {
  /* 单列布局 */
}

/* 平板设备 */
@media (min-width: 769px) and (max-width: 1024px) {
  /* 两列布局 */
}

/* 桌面设备 */
@media (min-width: 1025px) {
  /* 多列布局 */
}
```

### 适配策略

- 移动优先设计
- 弹性布局
- 响应式图片
- 触摸友好

## 性能优化

### 1. 代码分割

使用Vue Router的懒加载：
```typescript
const NewsView = () => import('@/views/NewsView.vue')
```

### 2. 组件懒加载

使用动态导入：
```typescript
const ChatModal = defineAsyncComponent(() => import('@/components/ChatModal.vue'))
```

### 3. 图片优化

- 懒加载
- 响应式图片
- 图片压缩

### 4. 请求优化

- 请求防抖
- 请求缓存
- 并发控制

## 构建配置

### Vite配置

**核心配置：**
```typescript
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': '/src'
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

### TypeScript配置

**核心配置：**
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "strict": true,
    "jsx": "preserve",
    "moduleResolution": "node",
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "forceConsistentCasingInFileNames": true,
    "useDefineForClassFields": true,
    "sourceMap": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  }
}
```

## 代码引用

### 主应用组件
[web/frontend/src/App.vue](../../web/frontend/src/App.vue) - 主应用组件

### 核心组件
[web/frontend/src/components/NewsCard.vue](../../web/frontend/src/components/NewsCard.vue) - 新闻卡片组件
[web/frontend/src/components/CategoryList.vue](../../web/frontend/src/components/CategoryList.vue) - 分类列表组件
[web/frontend/src/components/ChatModal.vue](../../web/frontend/src/components/ChatModal.vue) - 聊天模态框组件

### 视图页面
[web/frontend/src/views/NewsView.vue](../../web/frontend/src/views/NewsView.vue) - 新闻列表视图
[web/frontend/src/views/AdminView.vue](../../web/frontend/src/views/AdminView.vue) - 管理界面
[web/frontend/src/views/MonitorView.vue](../../web/frontend/src/views/MonitorView.vue) - 系统监控界面

### 状态管理
[web/frontend/src/stores/news.ts](../../web/frontend/src/stores/news.ts) - 新闻状态管理
[web/frontend/src/stores/chat.ts](../../web/frontend/src/stores/chat.ts) - 聊天状态管理
[web/frontend/src/stores/config.ts](../../web/frontend/src/stores/config.ts) - 配置状态管理

### API客户端
[web/frontend/src/api/index.ts](../../web/frontend/src/api/index.ts) - 统一API客户端

### 组合式函数
[web/frontend/src/composables/useNews.ts](../../web/frontend/src/composables/useNews.ts) - 新闻相关逻辑
[web/frontend/src/composables/useChat.ts](../../web/frontend/src/composables/useChat.ts) - 聊天相关逻辑
[web/frontend/src/composables/useWebSocket.ts](../../web/frontend/src/composables/useWebSocket.ts) - WebSocket连接管理

### 路由配置
[web/frontend/src/router/index.ts](../../web/frontend/src/router/index.ts) - 路由配置

### 类型定义
[web/frontend/src/types/news.ts](../../web/frontend/src/types/news.ts) - 新闻相关类型
[web/frontend/src/types/chat.ts](../../web/frontend/src/types/chat.ts) - 聊天相关类型
[web/frontend/src/types/config.ts](../../web/frontend/src/types/config.ts) - 配置相关类型

## 注意事项

1. **类型安全**：充分利用TypeScript的类型系统，避免运行时错误
2. **组件复用**：合理拆分组件，提高代码复用性
3. **状态管理**：合理使用Pinia，避免过度使用全局状态
4. **性能优化**：注意组件渲染性能，避免不必要的重新渲染
5. **错误处理**：完善的错误处理机制，提供良好的用户体验
6. **代码规范**：遵循Vue 3和TypeScript的最佳实践
7. **测试覆盖**：编写单元测试和集成测试，确保代码质量
8. **文档维护**：保持代码文档的更新，便于团队协作