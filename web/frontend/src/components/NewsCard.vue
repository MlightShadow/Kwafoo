<template>
  <div class="news-card" :data-id="props.news.id" :class="{ 'ai-processing': aiProcessing }">
    
    <!-- 背景装饰（图片或分类颜色） -->
    <div class="news-card-background" :class="backgroundClass" :style="backgroundStyle">
      <img 
        v-if="showThumbnail && imageUrl"
        :src="imageUrl" 
        :alt="props.news.title" 
        loading="lazy"
        @error="handleImageError"
        class="background-image"
      >
      <div v-if="!showThumbnail" class="category-emoji">{{ categoryEmoji }}</div>
      <div class="background-overlay"></div>
    </div>
    
    <!-- 主要内容区域 -->
    <div class="news-card-main">
      <div class="news-info">
        <h3 
          class="news-title"
          :class="{ truncated: titleTruncated }"
          @mouseenter="handleShowFullTitle" 
          @mouseleave="showFullTitle = false"
          ref="titleRef"
        >{{ props.news.title }}</h3>
        <div class="news-meta-top">
          <div class="meta-left">
            <span 
              v-if="props.news.ai_score !== undefined && props.news.ai_score !== null"
              class="news-score"
              :class="scoreClass"
            >
              🔥 {{ props.news.ai_score.toFixed(1) }}
            </span>
            <span 
              v-for="(category, index) in categoryList" 
              :key="index"
              class="news-category"
              :style="{ background: category.color || '#f3f4f6' }"
            >
              {{ category.name }}
            </span>
          </div>
          <div class="news-actions">
            <a v-if="props.news.url" :href="props.news.url" target="_blank" class="news-link" title="阅读原文">
              🔗
            </a>
            <button 
              @click="handleShowDetail" 
              class="detail-btn"
              title="查看详情"
            >
              📋
            </button>
            <button 
              @click="handleMarkAsRead" 
              class="read-toggle-btn"
              :class="{ read: props.news.is_read }"
              :disabled="markingAsRead"
              :title="props.news.is_read ? '标记为未读' : '标记为已读'"
            >
              {{ props.news.is_read ? '✓' : '○' }}
            </button>
            <!-- 重新分析按钮 -->
            <button 
              @click="handleReanalyze" 
              class="reanalyze-btn"
              :disabled="aiProcessing"
              title="重新分析"
            >
              <span v-if="aiProcessing" class="spinner"></span>
              <span v-else>🔄</span>
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 合并的AI评论和摘要区域 -->
    <div class="combined-summary" :class="{ 'has-content': props.news.ai_comment || props.news.ai_summary || props.news.description }">
      <!-- AI评论部分 -->
      <div v-if="props.news.ai_comment" class="ai-comment-section">
        <span class="comment-icon">⭐</span>
        <span class="comment-content">{{ props.news.ai_comment }}</span>
      </div>
      
      <!-- 分隔线：只有当AI评论和摘要同时存在时才显示 -->
      <hr v-if="props.news.ai_comment && (props.news.ai_summary || props.news.description)" class="summary-divider">
      
      <!-- 摘要部分 -->
      <div class="summary-section">
        <div 
          v-if="props.news.ai_summary"
          ref="summaryHeaderRef"
          class="summary-content" 
          :class="{ truncated: summaryTruncated }"
          @mouseenter="handleShowOriginalSummary" 
          @mouseleave="showOriginalSummary = false"
        >
          <span class="summary-icon">✨</span>
          <span class="summary-label">AI摘要：</span>
          {{ props.news.ai_summary }}
        </div>
        <div 
          v-else-if="props.news.description"
          ref="descriptionRef"
          class="summary-content"
          :class="{ truncated: descriptionTruncated }"
          @mouseenter="handleShowFullDescription" 
          @mouseleave="showFullDescription = false"
        >
          {{ props.news.description }}
        </div>
        <div v-else-if="!props.news.ai_comment" class="summary-placeholder">
          暂无摘要
        </div>
      </div>
    </div>
    
    <!-- 新闻来源和时间（移到摘要下方靠右） -->
    <div class="news-meta-bottom">
      <span class="news-time-source">{{ formatTime(props.news.publish_time) }}（{{ props.news.source }}）</span>
    </div>
  </div>

  <!-- 使用Teleport将tooltip渲染到body下，避免被其他元素遮挡 -->
  <Teleport to="body">
    <div 
      ref="fullTitleTooltipRef"
      v-if="showFullTitle" 
      class="full-title-tooltip"
      :style="titleTooltipStyle"
    >
      <div class="tooltip-header">📰 完整标题</div>
      <div class="tooltip-content">{{ props.news.title }}</div>
    </div>
    <div 
      ref="originalSummaryTooltipRef"
      v-if="showOriginalSummary && props.news.ai_summary" 
      class="original-summary-tooltip"
      :style="tooltipStyle"
    >
      <div class="tooltip-header">✨ AI摘要</div>
      <div class="tooltip-content">{{ props.news.ai_summary }}</div>
    </div>
    <div 
      ref="fullDescriptionTooltipRef"
      v-if="showFullDescription" 
      class="full-description-tooltip"
      :style="descriptionTooltipStyle"
    >
      <div class="tooltip-header">📄 完整摘要</div>
      <div class="tooltip-content">{{ props.news.description }}</div>
    </div>
  </Teleport>

  <!-- 新闻详情模态框 -->
  <NewsDetailModal 
    :is-open="showDetailModal"
    :news-id="props.news.id"
    @close="showDetailModal = false"
    ref="detailModalRef"
  />
</template>

<script setup lang="ts">
import { computed, ref, nextTick, watch, onMounted } from 'vue'
import { useNewsStore } from '@/stores/news'
import { useConfigStore } from '@/stores/config'
import { api } from '@/api'
import type { News } from '@/types/news'
import NewsDetailModal from './NewsDetailModal.vue'

interface Props {
  news: News
}

const props = defineProps<Props>()
const newsStore = useNewsStore()
const configStore = useConfigStore()
const markingAsRead = ref(false)
const aiProcessing = ref(false)
const showFullTitle = ref(false)
const showOriginalSummary = ref(false)
const showFullDescription = ref(false)
const showDetailModal = ref(false)
const imageLoadFailed = ref(false)

// 截断状态
const titleTruncated = ref(false)
const summaryTruncated = ref(false)
const descriptionTruncated = ref(false)

const titleRef = ref<HTMLElement | null>(null)
const summaryHeaderRef = ref<HTMLElement | null>(null)
const descriptionRef = ref<HTMLElement | null>(null)
const fullTitleTooltipRef = ref<HTMLElement | null>(null)
const originalSummaryTooltipRef = ref<HTMLElement | null>(null)
const fullDescriptionTooltipRef = ref<HTMLElement | null>(null)
const detailModalRef = ref<InstanceType<typeof NewsDetailModal> | null>(null)
const titleTooltipStyle = ref<Record<string, string>>({})
const tooltipStyle = ref<Record<string, string>>({})
const descriptionTooltipStyle = ref<Record<string, string>>({})

async function handleShowFullTitle() {
  // 只有当标题被截断时才显示tooltip
  if (titleRef.value) {
    const titleElement = titleRef.value
    
    // 更精确的截断检测
    const isTruncated = titleElement.scrollHeight > titleElement.clientHeight + 5
    
    // 调试信息
    console.log('标题截断检测:', {
      scrollHeight: titleElement.scrollHeight,
      clientHeight: titleElement.clientHeight,
      isTruncated: isTruncated,
      text: titleElement.textContent
    })
    
    if (isTruncated) {
      showFullTitle.value = true
      
      // 等待tooltip渲染完成
      await nextTick()
      
      // 计算tooltip位置
      if (fullTitleTooltipRef.value) {
        const rect = titleElement.getBoundingClientRect()
        const tooltipRect = fullTitleTooltipRef.value.getBoundingClientRect()
        const tooltipWidth = tooltipRect.width
        const tooltipHeight = tooltipRect.height
        
        // 计算tooltip位置
        let top = rect.bottom + 8
        let left = rect.left
        
        // 检查右边界
        if (left + tooltipWidth > window.innerWidth) {
          left = window.innerWidth - tooltipWidth - 16
        }
        
        // 检查底部边界
        if (top + tooltipHeight > window.innerHeight) {
          top = rect.top - tooltipHeight - 8
        }
        
        titleTooltipStyle.value = {
          top: `${top}px`,
          left: `${left}px`,
          zIndex: '9999'
        }
        
        // 调试信息
        console.log('标题tooltip位置:', {
          top: top,
          left: left,
          tooltipWidth: tooltipWidth,
          tooltipHeight: tooltipHeight,
          windowWidth: window.innerWidth,
          windowHeight: window.innerHeight
        })
      } else {
        console.log('fullTitleTooltipRef.value 为 null')
      }
    } else {
      console.log('标题未被截断，不显示tooltip')
    }
  }
}

async function handleShowOriginalSummary() {
  // 只有当AI摘要被截断时才显示tooltip
  if (summaryHeaderRef.value && isTextTruncated(summaryHeaderRef.value)) {
    showOriginalSummary.value = true
    
    // 等待tooltip渲染完成
    await nextTick()
    
    // 计算tooltip位置
    if (originalSummaryTooltipRef.value) {
      const rect = summaryHeaderRef.value.getBoundingClientRect()
      const tooltipRect = originalSummaryTooltipRef.value.getBoundingClientRect()
      const tooltipWidth = tooltipRect.width
      const tooltipHeight = tooltipRect.height
      
      // 计算tooltip位置
      let top = rect.bottom + 8
      let left = rect.left
      
      // 检查右边界
      if (left + tooltipWidth > window.innerWidth) {
        left = window.innerWidth - tooltipWidth - 16
      }
      
      // 检查底部边界
      if (top + tooltipHeight > window.innerHeight) {
        top = rect.top - tooltipHeight - 8
      }
      
      tooltipStyle.value = {
        top: `${top}px`,
        left: `${left}px`,
        zIndex: '9999'
      }
    }
  }
}

async function handleShowFullDescription() {
  // 只有当原文摘要被截断时才显示tooltip
  if (descriptionRef.value && isTextTruncated(descriptionRef.value)) {
    showFullDescription.value = true
    
    // 等待tooltip渲染完成
    await nextTick()
    
    // 计算tooltip位置
    if (fullDescriptionTooltipRef.value) {
      const rect = descriptionRef.value.getBoundingClientRect()
      const tooltipRect = fullDescriptionTooltipRef.value.getBoundingClientRect()
      const tooltipWidth = tooltipRect.width
      const tooltipHeight = tooltipRect.height
      
      // 计算tooltip位置
      let top = rect.bottom + 8
      let left = rect.left
      
      // 检查右边界
      if (left + tooltipWidth > window.innerWidth) {
        left = window.innerWidth - tooltipWidth - 16
      }
      
      // 检查底部边界
      if (top + tooltipHeight > window.innerHeight) {
        top = rect.top - tooltipHeight - 8
      }
      
      descriptionTooltipStyle.value = {
        top: `${top}px`,
        left: `${left}px`,
        zIndex: '9999'
      }
    }
  }
}

const showThumbnail = computed(() => {
  // 只有当图片已下载到本地时才显示缩略图
  return configStore.config?.image_display?.show_thumbnail !== false && 
         (props.news.image_url?.startsWith('/api/images/') || props.news.image_data)
})

const backgroundClass = computed(() => {
  if (showThumbnail.value) {
    const position = configStore.config?.image_display?.position || 'left'
    return `position-${position}`
  }
  return 'category-background'
})

const backgroundStyle = computed(() => {
  if (!showThumbnail.value) {
    const category = props.news.category || '未分类'
    const categories = category.split(',')
    const firstCategory = categories[0].trim()
    
    // 从数组中查找对应的分类配置
    const categoryConfig = newsStore.categories.find(cat => cat.name === firstCategory)
    const color = categoryConfig?.color || '#95a5a6'
    
    return {
      background: color
    }
  }
  return {}
})

const categoryEmoji = computed(() => {
  const category = props.news.category || '未分类'
  const categories = category.split(',')
  const firstCategory = categories[0].trim()
  
  // 从数组中查找对应的分类配置
  const categoryConfig = newsStore.categories.find(cat => cat.name === firstCategory)
  const icon = categoryConfig?.icon || '📰'
  
  return icon
})

async function handleMarkAsRead() {
  if (markingAsRead.value) return
  
  try {
    markingAsRead.value = true
    
    const newStatus = props.news.is_read ? 0 : 1
    await api.markAsRead(props.news.id, newStatus === 1)
    
    const newsItem = newsStore.newsList.find(n => n.id === props.news.id)
    if (newsItem) {
      Object.assign(newsItem, { is_read: newStatus })
    }
  } catch (error) {
    console.error('标记阅读状态失败:', error)
  } finally {
    markingAsRead.value = false
  }
}

async function handleReanalyze() {
  if (aiProcessing.value) return
  
  try {
    aiProcessing.value = true
    await api.processNewsReanalyze(props.news.id)
    // 不在这里设置 aiProcessing.value = false
    // 等待WebSocket更新消息来结束动画
  } catch (error) {
    console.error('重新分析失败:', error)
    aiProcessing.value = false
  }
}

function handleShowDetail() {
  showDetailModal.value = true
  // 加载新闻详情
  nextTick(() => {
    detailModalRef.value?.loadNewsDetail()
  })
}

const imageUrl = computed(() => {
  if (imageLoadFailed.value) {
    return null
  }
  
  // 优先使用本地URL（文件系统模式）
  if (props.news.image_url && props.news.image_url.startsWith('/api/images/')) {
    return props.news.image_url
  }
  
  // 使用base64编码的图片数据
  if (props.news.image_data) {
    return `data:image/jpeg;base64,${props.news.image_data}`
  }
  
  return null
})

const categoryList = computed(() => {
  if (!props.news.category) return []
  
  const categories = props.news.category.split(',')
  const categoryList = categories.map(cat => {
    const categoryName = cat.trim()
    // 从数组中查找对应的分类配置
    const categoryConfig = newsStore.categories.find(c => c.name === categoryName)
    return {
      name: categoryConfig?.name || categoryName,
      color: categoryConfig?.color || '#95a5a6'
    }
  })
  
  return categoryList
})

const scoreClass = computed(() => {
  if (props.news.ai_score === undefined || props.news.ai_score === null) return ''
  
  const score = props.news.ai_score
  if (score >= 80) return 'score-high'
  if (score >= 60) return 'score-medium'
  return 'score-low'
})

function formatTime(timeString?: string): string {
  if (!timeString) return ''
  
  const date = new Date(timeString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`
  
  return date.toLocaleDateString('zh-CN')
}

// 截断检测函数
function isTextTruncated(element: HTMLElement | null): boolean {
  if (!element) return false
  return element.scrollHeight > element.clientHeight + 1
}

// 更新截断状态
function updateTruncationStatus() {
  // 检测标题截断
  if (titleRef.value) {
    titleTruncated.value = isTextTruncated(titleRef.value)
  }
  
  // 检测AI摘要截断
  if (summaryHeaderRef.value) {
    summaryTruncated.value = isTextTruncated(summaryHeaderRef.value)
  }
  
  // 检测原文摘要截断
  if (descriptionRef.value) {
    descriptionTruncated.value = isTextTruncated(descriptionRef.value)
  }
}

// 组件挂载后更新截断状态
onMounted(() => {
  nextTick(() => {
    updateTruncationStatus()
  })
})

// 监听内容变化更新截断状态
watch(() => [props.news.title, props.news.ai_summary, props.news.description], () => {
  nextTick(() => {
    updateTruncationStatus()
  })
})

function handleImageError(event: Event) {
  // 标记图片加载失败，imageUrl computed会自动切换到占位图
  imageLoadFailed.value = true
}

// 监听news的变化，当AI分析完成时自动结束动画
watch(() => props.news.ai_summary, (newSummary, oldSummary) => {
  // 如果AI摘要从无到有，或者从旧值变为新值，说明AI分析完成
  if (aiProcessing.value && newSummary && newSummary !== oldSummary) {
    aiProcessing.value = false
  }
})

watch(() => props.news.category, (newCategory, oldCategory) => {
  // 如果分类从旧值变为新值，说明AI分析完成
  if (aiProcessing.value && newCategory && newCategory !== oldCategory) {
    aiProcessing.value = false
  }
})
</script>

<style scoped>
.news-card {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
  background: white;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  flex-direction: column;
  position: relative;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  height: 300px; /* 固定高度 */
}

.news-card:hover {
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.news-card.ai-processing {
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
}

/* 图片背景装饰 */
.news-card-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  z-index: 0;
}

.news-card-background.position-left {
  left: 0;
}

.news-card-background.position-right {
  right: 0;
}

.news-card-background.category-background {
  opacity: 0.15;
}

.category-emoji {
  position: absolute;
  top: 40%;
  left: 70%;
  transform: translate(-50%, -50%);
  font-size: 21rem;
  opacity: 0.8;
  z-index: 0;
  user-select: none;
}

.background-image {
  width: 100%;
  height: 100%;
  object-fit: fill;
  opacity: 0.25;
  filter: blur(1px);
}

.background-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(
    to bottom,
    rgba(255,255,255,0.35) 0%,
    rgba(255,255,255,0.3) 30%,
    rgba(255,255,255,0.2) 60%,
    rgba(255,255,255,0.1) 100%
  );
}

/* 重新分析按钮特殊样式 */
.reanalyze-btn {
  color: #f59e0b; /* 橙色，与火焰图标呼应 */
}

.reanalyze-btn:hover {
  background: rgba(245, 158, 11, 0.1); /* 橙色悬停效果 */
}

.reanalyze-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(102, 126, 234, 0.3);
  border-radius: 50%;
  border-top-color: #667eea;
  animation: spin 0.8s ease-in-out infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 主要内容区域 */
.news-card-main {
  display: flex;
  padding: 1rem;
  position: relative;
  z-index: 1;
}

.news-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

/* 标题样式 */
.news-title {
  margin: 0 0 0.25rem 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  line-height: 1.4;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  height: 2.8em;
  cursor: help;
  position: relative;
}

/* 标题截断emoji样式 */
.news-title.truncated::after {
  content: "⏬";
  position: absolute;
  right: 0;
  bottom: 0;
  background: white;
  padding: 0 0.25rem 0 0.5rem;
  font-size: 0.875rem;
  color: #6b7280;
}

/* 元数据样式 */
.news-meta-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8125rem;
  color: #6b7280;
  min-height: 28px;
}

.meta-left {
  display: flex;
  gap: 0.375rem;
  flex-wrap: wrap;
  align-items: center;
  flex: 1;
}

.news-actions {
  display: flex;
  gap: 0.5rem;
  flex-shrink: 0;
}

.news-category,
.news-source,
.news-time {
  padding: 0.1875rem 0.5rem;
  border-radius: 9999px;
  background: #f3f4f6;
  font-weight: 500;
  color: #374151;
}

.news-category {
  color: white;
}

/* 评分样式 */
.news-score {
  padding: 0.1875rem 0.5rem;
  border-radius: 9999px;
  background: #f3f4f6;
  font-weight: 600;
  color: #374151;
  font-size: 0.75rem;
}

.news-score.score-high {
  background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
  color: #065f46;
  border: 1px solid #10b981;
}

.news-score.score-medium {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  color: #92400e;
  border: 1px solid #f59e0b;
}

.news-score.score-low {
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
  color: #991b1b;
  border: 1px solid #ef4444;
}

/* 按钮样式 */
.news-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  align-items: center;
}

.news-link,
.read-toggle-btn,
.detail-btn,
.reanalyze-btn {
  padding: 0;
  width: 32px;
  height: 32px;
  border: 1px solid #e5e7eb; /* 统一边框 */
  background: white; /* 统一白色背景 */
  color: #4b5563;
  text-decoration: none;
  border-radius: 6px;
  font-size: 1.125rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1); /* 统一轻微阴影 */
}

.news-link:hover,
.read-toggle-btn:hover,
.detail-btn:hover,
.reanalyze-btn:hover {
  background: #f9fafb; /* 统一悬停背景色 */
  border-color: #d1d5db; /* 悬停时边框变深 */
  transform: translateY(-1px); /* 统一悬停效果 */
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
}

/* 特殊按钮颜色 */
.detail-btn {
  color: #667eea;
}

.read-toggle-btn.read {
  color: #10b981;
}

.reanalyze-btn {
  color: #f59e0b; /* 橙色，与火焰图标呼应 */
}

.read-toggle-btn:disabled,
.reanalyze-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.read-toggle-btn:disabled:hover {
  transform: none;
  background: transparent;
}

/* AI评论部分样式 */
.ai-comment-section {
  display: flex;
  align-items: center; /* 改为居中对齐 */
  margin-bottom: 0.15rem; /* 进一步减小间距 */
  padding: 0;
  min-height: auto;
}

.comment-icon {
  font-size: 0.875rem;
  flex-shrink: 0;
  margin-right: 0.2rem; /* 进一步减小间距 */
}

.comment-content {
  word-break: break-word;
  line-height: 1.2; /* 进一步减小行高 */
  flex: 1;
  margin: 0;
  padding: 0;
}

/* 合并的AI评论和摘要样式 */
.combined-summary {
  padding: 0.75rem 1rem;
  background: rgba(249, 250, 251, 0.5);
  border-radius: 6px;
  font-size: 0.75rem;
  color: #6b7280;
  line-height: 1.5;
  position: relative;
  z-index: 1;
  margin: 0 1rem 0.5rem 1rem;
  height: 140px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 分隔线样式 */
.summary-divider {
  border: none;
  border-top: 1px solid #e5e7eb;
  margin: 0.1rem 0; /* 进一步减小间距 */
  opacity: 0.6;
}

/* 摘要部分样式 */
.summary-section {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.summary-content {
  cursor: help;
  word-break: break-word;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 5; /* 最多显示5行 */
  -webkit-box-orient: vertical;
  max-height: 100px; 
  position: relative;
  flex: 1;
}

/* 摘要截断emoji样式 */
.summary-content.truncated::after {
  content: "⏬";
  position: absolute;
  right: 0;
  bottom: 0;
  background: #f9fafb;
  padding: 0 0.25rem 0 0.5rem;
  font-size: 0.75rem;
  color: #6b7280;
}

.summary-icon {
  font-size: 0.875rem;
  flex-shrink: 0;
  margin-right: 0.25rem;
}

.summary-label {
  font-weight: 600;
  color: #10b981;
  flex-shrink: 0;
  margin-right: 0.25rem;
}

/* 新闻来源和时间底部样式 */
.news-meta-bottom {
  display: flex;
  justify-content: flex-end;
  padding: 0 1rem 0.5rem 1rem;
  font-size: 0.75rem;
  color: #6b7280;
}

.news-time-source {
  font-weight: 400;
}

/* Tooltip样式 */
.full-title-tooltip,
.original-summary-tooltip,
.full-description-tooltip {
  position: fixed;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 9999;
  min-width: 280px;
  max-width: 400px;
  padding: 0.75rem;
  pointer-events: auto;
  overflow: hidden;
}

.tooltip-header {
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.5rem;
  font-size: 1rem;
}

.tooltip-content {
  color: #6b7280;
  font-size: 1rem;
  line-height: 1.5;
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 300px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 10;
  -webkit-box-orient: vertical;
  text-overflow: ellipsis;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .news-card {
    height: auto; /* 移动端自适应高度 */
    min-height: 280px;
  }
  
  .news-card-main {
    padding: 0.875rem;
  }
  
  .news-title {
    font-size: 0.9375rem;
  }
  
  .news-actions {
    flex-direction: row;
    align-items: stretch;
  }
  
  .news-link,
  .read-toggle-btn {
    flex: 1;
  }
  
  .news-summary {
    max-height: 120px; /* 移动端摘要高度稍小 */
    margin: 0 0.75rem 0.75rem 0.75rem;
  }
}
</style>