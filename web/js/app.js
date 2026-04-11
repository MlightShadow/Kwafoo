class KwafooApp {
    constructor() {
        this.currentCategory = '';
        this.sessionId = null;
        this.currentPage = 'news';
        this.categories = [];
        this.isServerOnline = true;
        this.retryCount = 0;
        this.maxRetries = 3;
        this.userClosedOfflineMessage = false;  // 用户是否关闭过离线提示框
        this.init();
    }

    init() {
        this.checkServerStatus();
        this.loadConfig();
        this.bindEvents();
        this.loadNews();
        this.loadSystemStatus();
        this.startAutoRefresh();
        this.startProgressMonitor();
        this.startServerMonitor();
    }

    async checkServerStatus() {
        try {
            const response = await fetch('/api/health', {
                method: 'GET',
                cache: 'no-cache'
            });
            
            if (response.ok) {
                this.isServerOnline = true;
                this.hideServerOfflineMessage();
                this.removeReconnectButton();
                this.retryCount = 0;
                this.userClosedOfflineMessage = false;  // 重置用户关闭标志
            } else {
                throw new Error('Server returned error');
            }
        } catch (error) {
            this.isServerOnline = false;
            // 只在用户没有关闭过提示框时显示
            if (!this.userClosedOfflineMessage) {
                this.showServerOfflineMessage();
            }
            this.showReconnectButton();
            console.error('服务器连接失败:', error);
        }
    }

    removeReconnectButton() {
        const reconnectBtn = document.getElementById('reconnectButton');
        if (reconnectBtn) {
            reconnectBtn.remove();
        }
    }

    startServerMonitor() {
        // 每30秒检查一次服务器状态
        setInterval(() => {
            this.checkServerStatus();
        }, 30000);
    }

    showServerOfflineMessage() {
        let messageDiv = document.getElementById('serverOfflineMessage');
        
        if (!messageDiv) {
            messageDiv = document.createElement('div');
            messageDiv.id = 'serverOfflineMessage';
            messageDiv.className = 'server-offline-message';
            messageDiv.innerHTML = `
                <div class="offline-content">
                    <div class="offline-icon">⚠️</div>
                    <div class="offline-text">
                        <h3>服务器连接失败</h3>
                        <p>无法连接到服务器，请检查：</p>
                        <ul>
                            <li>服务器是否正在运行</li>
                            <li>网络连接是否正常</li>
                            <li>浏览器控制台是否有错误信息</li>
                        </ul>
                        <div class="offline-buttons">
                            <button onclick="window.kwafooApp.retryConnection()" class="retry-button">
                                🔄 重新连接
                            </button>
                            <button onclick="window.kwafooApp.closeOfflineMessage()" class="close-button">
                                ✕ 关闭提示
                            </button>
                        </div>
                    </div>
                </div>
            `;
            document.body.insertBefore(messageDiv, document.body.firstChild);
        }
    }

    closeOfflineMessage() {
        const messageDiv = document.getElementById('serverOfflineMessage');
        if (messageDiv) {
            messageDiv.remove();
            this.userClosedOfflineMessage = true;  // 标记用户已关闭提示框
        }
    }

    showReconnectButton() {
        // 在系统状态区域显示重连按钮
        const statusDiv = document.getElementById('systemStatus');
        if (statusDiv && !document.getElementById('reconnectButton')) {
            const reconnectBtn = document.createElement('button');
            reconnectBtn.id = 'reconnectButton';
            reconnectBtn.className = 'reconnect-button';
            reconnectBtn.innerHTML = '🔄 重新连接';
            reconnectBtn.onclick = () => this.retryConnection();
            statusDiv.appendChild(reconnectBtn);
        }
    }

    hideServerOfflineMessage() {
        const messageDiv = document.getElementById('serverOfflineMessage');
        if (messageDiv) {
            messageDiv.remove();
        }
    }

    async retryConnection() {
        this.retryCount++;
        
        if (this.retryCount > this.maxRetries) {
            alert('重试次数过多，请稍后再试或联系管理员');
            return;
        }

        const retryButton = document.querySelector('.retry-button');
        if (retryButton) {
            retryButton.disabled = true;
            retryButton.textContent = '⏳ 连接中...';
        }

        await this.checkServerStatus();
        
        if (this.isServerOnline) {
            // 服务器恢复，重新加载所有数据
            this.loadConfig();
            this.loadNews();
            this.loadSystemStatus();
        } else {
            const retryButton = document.querySelector('.retry-button');
            if (retryButton) {
                retryButton.disabled = false;
                retryButton.textContent = '🔄 重新连接';
            }
        }
    }

    async safeFetch(url, options = {}) {
        try {
            const timeout = options.timeout || 120000; // 默认120秒超时
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), timeout);
            
            const response = await fetch(url, {
                ...options,
                cache: 'no-cache',
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`请求失败 [${url}]:`, error);
            
            // 如果是网络错误，检查服务器状态
            if (error.name === 'TypeError' || error.message.includes('Failed to fetch') || error.name === 'AbortError') {
                this.isServerOnline = false;
                this.showServerOfflineMessage();
            }
            
            throw error;
        }
    }

    async loadConfig() {
        try {
            const data = await this.safeFetch('/api/config');

            if (data.success) {
                // 处理分类配置（新格式包含icon和color）
                const categoriesConfig = data.data.categories || {};
                this.categories = Object.keys(categoriesConfig).map(catName => ({
                    name: catName,
                    icon: categoriesConfig[catName].icon || '📰',
                    color: categoriesConfig[catName].color || '#95a5a6',
                    keywords: categoriesConfig[catName].keywords || []
                }));
                console.log('分类配置加载成功:', this.categories);
                this.renderCategories();
            }
        } catch (error) {
            console.error('加载配置失败:', error);
        }
    }

    startProgressMonitor() {
        // 每3秒检查一次任务进度
        setInterval(() => {
            this.checkTaskCompletion();
        }, 3000);
    }

    async checkTaskCompletion() {
        try {
            const data = await this.safeFetch('/api/progress');

            if (data.success && data.data) {
                const tasks = data.data;
                
                // 检查是否有刚完成的任务
                for (const taskId in tasks) {
                    const task = tasks[taskId];
                    
                    // 如果任务刚刚完成且我们还没有通知过
                    if (task.status === 'completed' && !this.notifiedTasks?.includes(taskId)) {
                        this.showTaskNotification(task);
                        this.notifiedTasks = this.notifiedTasks || [];
                        this.notifiedTasks.push(taskId);
                    }
                }
            }
        } catch (error) {
            console.error('检查任务进度失败:', error);
        }
    }

    showTaskNotification(task) {
        // 显示任务完成通知
        const notification = document.createElement('div');
        notification.className = 'task-notification';
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-icon">✅</span>
                <span class="notification-text">${task.task_name}完成</span>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        document.body.appendChild(notification);
        
        // 5秒后自动消失
        setTimeout(() => {
            notification.remove();
        }, 5000);
        
        // 如果在新闻页面，刷新新闻列表
        if (this.currentPage === 'news') {
            this.loadNews();
        }
    }

    renderCategories() {
        const categoryList = document.getElementById('categoryList');
        const allCategories = [
            { name: '全部', icon: '📰', color: '#667eea' },
            ...this.categories
        ];

        categoryList.innerHTML = allCategories.map(cat => {
            const categoryValue = cat.name === '全部' ? '' : cat.name;
            const activeClass = this.currentCategory === categoryValue ? 'active' : '';
            return `
                <li class="${activeClass}" data-category="${categoryValue}" style="--category-color: ${cat.color}">
                    <span class="category-icon">${cat.icon}</span>
                    <span class="category-name">${cat.name}</span>
                </li>
            `;
        }).join('');

        document.querySelectorAll('.category-list li').forEach(item => {
            item.addEventListener('click', (e) => {
                this.switchCategory(e.currentTarget.dataset.category);
            });
        });
    }

    bindEvents() {
        document.getElementById('fetchButton').addEventListener('click', () => {
            this.manualFetch();
        });

        document.getElementById('aiProcessButton').addEventListener('click', () => {
            this.manualAiProcess();
        });

        document.getElementById('clearNewsButton').addEventListener('click', () => {
            this.clearNews();
        });

        document.getElementById('chatFab').addEventListener('click', () => {
            this.openChat();
        });

        document.getElementById('closeChat').addEventListener('click', () => {
            this.closeChat();
        });

        document.getElementById('sendChat').addEventListener('click', () => {
            this.sendChat();
        });

        document.getElementById('chatInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendChat();
            }
        });
    }

    async manualFetch() {
        const button = document.getElementById('fetchButton');
        button.disabled = true;
        button.textContent = '⏳ 抓取中...';

        try {
            const data = await this.safeFetch('/api/fetch', {
                method: 'POST'
            });

            if (data.success) {
                // 任务已启动，等待通知
                console.log('抓取任务已启动:', data.message);
            } else {
                // 任务正在运行中
                alert(data.message || '任务正在运行中，请稍后再试');
            }
        } catch (error) {
            console.error('抓取失败:', error);
            alert('新闻抓取失败：' + error.message);
        } finally {
            // 3秒后恢复按钮状态
            setTimeout(() => {
                button.disabled = false;
                button.textContent = '🔄 手动抓取新闻';
            }, 3000);
        }
    }

    async manualAiProcess() {
        const button = document.getElementById('aiProcessButton');
        button.disabled = true;
        button.textContent = '⏳ 分析中...';

        try {
            const data = await this.safeFetch('/api/ai/process', {
                method: 'POST'
            });

            if (data.success) {
                // 任务已启动，等待通知
                console.log('AI分析任务已启动:', data.message);
            } else {
                // 任务正在运行中
                alert(data.message || '任务正在运行中，请稍后再试');
            }
        } catch (error) {
            console.error('AI分析启动失败:', error);
            alert('AI分析启动失败：' + error.message);
        } finally {
            // 3秒后恢复按钮状态
            setTimeout(() => {
                button.disabled = false;
                button.textContent = '🤖 AI分析新闻';
            }, 3000);
        }
    }

    async clearNews() {
        if (!confirm('确定要清空所有新闻数据吗？\n\n此操作将标记所有新闻为删除状态，但不会从数据库中删除。\n相同的新闻URL可以重新插入。')) {
            return;
        }

        const button = document.getElementById('clearNewsButton');
        button.disabled = true;
        button.textContent = '⏳ 清空中...';

        try {
            const data = await this.safeFetch('/api/news/clear', {
                method: 'POST'
            });

            if (data.success) {
                alert(`成功标记 ${data.count} 条新闻为删除状态`);
                this.loadNews();
                this.loadNewsStats();
            } else {
                alert('清空新闻失败：' + (data.error || '未知错误'));
            }
        } catch (error) {
            console.error('清空新闻失败:', error);
            alert('清空新闻失败：' + error.message);
        } finally {
            // 3秒后恢复按钮状态
            setTimeout(() => {
                button.disabled = false;
                button.textContent = '🗑️ 清空新闻数据';
            }, 3000);
        }
    }

    showPage(pageName) {
        this.currentPage = pageName;

        document.querySelectorAll('.page').forEach(page => {
            page.style.display = 'none';
            page.classList.remove('active');
        });

        const targetPage = document.getElementById(pageName + 'Page');
        if (targetPage) {
            targetPage.style.display = 'block';
            targetPage.classList.add('active');
        }

        if (pageName === 'monitor') {
            this.loadMonitor();
        }

        return false;
    }

    async loadNews() {
        const newsList = document.getElementById('newsList');
        newsList.innerHTML = '<div class="loading">加载中...</div>';

        try {
            let url = '/api/news';
            if (this.currentCategory) {
                url = `/api/news/category?category=${encodeURIComponent(this.currentCategory)}`;
            }

            const data = await this.safeFetch(url);

            if (data.success) {
                this.renderNews(data.data);
                this.updateStats(data.count);
            } else {
                newsList.innerHTML = '<div class="loading">加载失败</div>';
            }
        } catch (error) {
            console.error('加载新闻失败:', error);
            newsList.innerHTML = '<div class="loading">加载失败</div>';
        }
    }

    renderNews(newsList) {
        const container = document.getElementById('newsList');
        
        if (!newsList || newsList.length === 0) {
            container.innerHTML = '<div class="loading">暂无新闻</div>';
            return;
        }

        container.innerHTML = newsList.map(news => this.renderNewsItem(news)).join('');
    }

    renderNewsItem(news) {
        let summary = '';
        let isAiSummary = false;
        
        if (news.ai_summary) {
            // AI摘要已经是处理过的，不需要再截断
            summary = news.ai_summary;
            isAiSummary = true;
        } else if (news.description) {
            // 原始描述需要截断
            summary = news.description;
            if (summary.length > 140) {
                summary = summary.substring(0, 140) + '...';
            }
        } else {
            summary = '暂无摘要';
        }
        
        const categories = news.category ? news.category.split(',') : ['未分类'];
        const categoryTags = categories.map(cat => 
            `<span class="category-tag">${cat}</span>`
        ).join('');

        const publishTime = news.publish_time ? 
            new Date(news.publish_time).toLocaleString('zh-CN') : 
            '未知时间';

        // AI摘要不需要再次截断，原始描述已经在上面处理过了
        const summaryText = summary;

        // 获取分类的icon和color
        const categoryInfo = this.getCategoryInfo(categories[0]);

        // 处理图片显示
        let imageHtml = '';
        if (news.image_data) {
            // 如果有图片数据，显示为base64
            imageHtml = `<img src="data:image/jpeg;base64,${news.image_data}" alt="${this.escapeHtml(news.title)}" class="news-image">`;
        } else {
            // 否则显示默认图片或空白
            imageHtml = `<div class="news-image-placeholder">${categoryInfo.icon}</div>`;
        }

        // AI摘要标识 - 使用title属性实现悬停效果
        const aiIndicator = isAiSummary ? 
            `<span class="ai-indicator" title="${this.escapeHtml(news.description || '')}">🤖</span>` : '';

        return `
            <div class="news-item" data-news-id="${news.id}">
                <div class="news-image-container">
                    ${imageHtml}
                </div>
                <div class="news-content">
                    <h3 class="news-title">${this.escapeHtml(news.title)}</h3>
                    <p class="news-summary">
                        ${this.escapeHtml(summaryText)}
                        ${aiIndicator}
                    </p>
                    <div class="news-meta">
                        <span>📰 ${this.escapeHtml(news.source)}</span>
                        <span>🕐 ${publishTime}</span>
                    </div>
                    <div class="news-categories">
                        ${categoryTags}
                    </div>
                    <div class="news-links">
                        <a href="${news.url}" target="_blank">查看原文</a>
                        ${news.source_url ? `<a href="${news.source_url}" target="_blank">来源</a>` : ''}
                    </div>
                </div>
            </div>
        `;
    }

    getCategoryInfo(categoryName) {
        // 获取分类的icon和color
        const category = this.categories.find(cat => cat.name === categoryName);
        return {
            icon: category ? category.icon : '📰',
            color: category ? category.color : '#95a5a6'
        };
    }

    switchCategory(category) {
        this.currentCategory = category;
        
        document.querySelectorAll('.category-list li').forEach(item => {
            item.classList.remove('active');
            if (item.dataset.category === category) {
                item.classList.add('active');
            }
        });

        const categoryNames = {
            '': '全部新闻',
            '科技': '科技新闻',
            '财经': '财经新闻',
            '国际': '国际新闻',
            '体育': '体育新闻',
            '娱乐': '娱乐新闻',
            '未分类': '未分类新闻'
        };

        document.getElementById('currentCategory').textContent = categoryNames[category] || '新闻';
        this.loadNews();
    }

    async loadSystemStatus() {
        try {
            const data = await this.safeFetch('/api/progress');

            if (data.success) {
                this.renderSystemStatus(data.data);
            }
        } catch (error) {
            console.error('加载系统状态失败:', error);
        }
    }

    renderSystemStatus(tasks) {
        const container = document.getElementById('systemStatus');
        
        // 如果服务器离线，显示离线状态
        if (!this.isServerOnline) {
            container.innerHTML = '<p>❌ 服务器离线</p>';
            return;
        }
        
        if (!tasks || Object.keys(tasks).length === 0) {
            container.innerHTML = '<p>✅ 系统运行正常</p>';
            return;
        }

        const runningTasks = Object.values(tasks).filter(task => task.status === 'running');
        
        if (runningTasks.length > 0) {
            const taskNames = runningTasks.map(task => task.task_name).join(', ');
            container.innerHTML = `<p>⏳ ${taskNames}</p>`;
        } else {
            container.innerHTML = '<p>✅ 系统运行正常</p>';
        }
    }

    async loadMonitor() {
        this.loadSystemStatus();
        this.loadSystemInfo();
        this.loadNewsStats();
    }

    async loadNewsStats() {
        try {
            const data = await this.safeFetch('/api/news/stats');

            if (data.success) {
                this.renderNewsStats(data.data);
            }
        } catch (error) {
            console.error('加载新闻统计失败:', error);
        }
    }

    renderNewsStats(stats) {
        document.getElementById('totalNews').textContent = stats.total || 0;
        document.getElementById('activeNews').textContent = stats.active || 0;
        document.getElementById('deletedNews').textContent = stats.deleted || 0;
        document.getElementById('processedNews').textContent = stats.processed || 0;
        document.getElementById('unprocessedNews').textContent = stats.unprocessed || 0;
    }

    async loadSystemInfo() {
        try {
            const data = await this.safeFetch('/api/health');

            if (data.success) {
                this.renderSystemInfo(data);
            }
        } catch (error) {
            console.error('加载系统信息失败:', error);
        }
    }

    renderSystemInfo(info) {
        const container = document.getElementById('systemInfo');
        
        container.innerHTML = `
            <div class="info-item">
                <strong>状态:</strong> ${info.status}
            </div>
            <div class="info-item">
                <strong>时间:</strong> ${new Date(info.timestamp).toLocaleString('zh-CN')}
            </div>
            <div class="info-item">
                <strong>服务器:</strong> http://localhost:8000
            </div>
        `;
    }

    updateStats(count) {
        document.getElementById('newsCount').textContent = `${count} 条新闻`;
        document.getElementById('lastUpdate').textContent = 
            `最后更新: ${new Date().toLocaleString('zh-CN')}`;
    }

    openChat() {
        document.getElementById('chatModal').style.display = 'block';
        document.getElementById('chatInput').focus();
    }

    closeChat() {
        document.getElementById('chatModal').style.display = 'none';
    }

    async sendChat() {
        const input = document.getElementById('chatInput');
        const message = input.value.trim();
        
        if (!message) return;

        const chatMessages = document.getElementById('chatMessages');
        
        chatMessages.innerHTML += `
            <div class="chat-message user">
                ${this.escapeHtml(message)}
            </div>
        `;

        input.value = '';
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            const data = await this.safeFetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    category: this.currentCategory || null,
                    session_id: this.sessionId
                })
            });

            if (data.success) {
                this.sessionId = data.session_id;
                
                chatMessages.innerHTML += `
                    <div class="chat-message assistant">
                        ${this.escapeHtml(data.response)}
                    </div>
                `;
            } else {
                chatMessages.innerHTML += `
                    <div class="chat-message assistant">
                        对话失败，请重试
                    </div>
                `;
            }

            chatMessages.scrollTop = chatMessages.scrollHeight;
        } catch (error) {
            console.error('对话失败:', error);
            chatMessages.innerHTML += `
                <div class="chat-message assistant">
                    对话失败，请重试
                </div>
            `;
        }
    }

    startAutoRefresh() {
        setInterval(() => {
            this.loadSystemStatus();
        }, 30000);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.kwafooApp = new KwafooApp();
});