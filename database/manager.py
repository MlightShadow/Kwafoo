import sqlite3
import os
import base64
import threading
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone, timedelta
from utils.logger import logger
from utils.helpers import config
from utils.image_processor import image_processor


class DatabaseManager:
    _instance = None
    _thread_local = threading.local()
    _ws_broadcast_callback = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        pass

    @classmethod
    def enable_websocket_broadcast(cls, callback):
        """启用WebSocket广播"""
        cls._ws_broadcast_callback = callback
        logger.info("WebSocket广播已启用")

    def _connect(self):
        """连接数据库"""
        db_path = config.get('database.path', 'data/kwafoo.db')
        db_dir = os.path.dirname(db_path)
        
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        connection = sqlite3.connect(db_path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        logger.info(f"数据库连接成功: {db_path}")
        return connection
    
    def _get_beijing_time(self) -> str:
        """获取北京时间（东8区）的当前时间
        
        Returns:
            格式化的北京时间字符串
        """
        # 创建东8区时区
        beijing_tz = timezone(timedelta(hours=8))
        # 获取当前时间并转换为东8区时间
        beijing_time = datetime.now(beijing_tz)
        # 格式化为字符串
        return beijing_time.strftime('%Y-%m-%d %H:%M:%S')

    @property
    def _connection(self) -> sqlite3.Connection:
        """获取当前线程的数据库连接"""
        if not hasattr(self._thread_local, 'connection') or self._thread_local.connection is None:
            self._thread_local.connection = self._connect()
        return self._thread_local.connection

    def _check_connection_health(self, connection: sqlite3.Connection) -> bool:
        """检查连接是否健康
        
        Args:
            connection: 数据库连接
            
        Returns:
            连接是否健康
        """
        try:
            cursor = connection.cursor()
            cursor.execute('SELECT 1')
            cursor.fetchone()
            return True
        except Exception as e:
            logger.warning(f"数据库连接健康检查失败: {e}")
            return False

    def _reconnect(self) -> bool:
        """重新连接数据库
        
        Returns:
            是否重连成功
        """
        try:
            if hasattr(self._thread_local, 'connection') and self._thread_local.connection:
                try:
                    self._thread_local.connection.close()
                except Exception as e:
                    logger.warning(f"关闭旧连接失败: {e}")
            
            self._thread_local.connection = self._connect()
            logger.info("数据库重连成功")
            return True
        except Exception as e:
            logger.error(f"数据库重连失败: {e}")
            return False

    def _ensure_connection(self) -> sqlite3.Connection:
        """确保连接可用，如果不可用则重连
        
        Returns:
            可用的数据库连接
        """
        connection = self._connection
        if not self._check_connection_health(connection):
            logger.warning("数据库连接不可用，尝试重连")
            if self._reconnect():
                return self._connection
            else:
                raise Exception("数据库连接失败，重连也不成功")
        return connection

    def create_tables(self):
        cursor = self._connection.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                ai_summary TEXT,
                content TEXT,
                url TEXT UNIQUE,
                source TEXT NOT NULL,
                source_url TEXT,
                category TEXT,
                publish_time DATETIME,
                fetch_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_visible BOOLEAN DEFAULT 1,
                ai_processed BOOLEAN DEFAULT 0,
                image_url TEXT,
                image_data BLOB,
                is_deleted BOOLEAN DEFAULT 0,
                is_read BOOLEAN DEFAULT 0
            )
        ''')
        
        # 检查并添加缺失的字段（用于旧数据库升级）
        self._migrate_database()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE UNIQUE,
                file_path TEXT NOT NULL,
                file_size INTEGER,
                news_count INTEGER,
                status TEXT DEFAULT 'pending',
                error_message TEXT,
                ai_processing_time REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE,
                user_id TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                context_news_ids TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE UNIQUE,
                total_news INTEGER,
                by_category TEXT,
                by_source TEXT,
                ai_summary_count INTEGER,
                ai_category_count INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_processing_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                news_id INTEGER NOT NULL,
                task_type TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                priority INTEGER DEFAULT 0,
                retry_count INTEGER DEFAULT 0,
                error_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (news_id) REFERENCES news(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_type TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                time_range_start DATETIME,
                time_range_end DATETIME,
                news_count INTEGER DEFAULT 0,
                ai_model TEXT,
                generation_time REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self._create_indexes()
        self._create_fts_table()
        
        self._connection.commit()
        logger.info("数据库表创建完成")

    def _migrate_database(self):
        """数据库迁移：添加缺失的字段"""
        cursor = self._connection.cursor()
        
        try:
            # 检查表结构
            cursor.execute("PRAGMA table_info(news)")
            columns = [row[1] for row in cursor.fetchall()]
            
            # 添加 image_url 字段
            if 'image_url' not in columns:
                cursor.execute("ALTER TABLE news ADD COLUMN image_url TEXT")
                logger.info("数据库迁移：添加 image_url 字段")
            
            # 添加 image_data 字段
            if 'image_data' not in columns:
                cursor.execute("ALTER TABLE news ADD COLUMN image_data BLOB")
                logger.info("数据库迁移：添加 image_data 字段")
            
            # 添加 is_deleted 字段
            if 'is_deleted' not in columns:
                cursor.execute("ALTER TABLE news ADD COLUMN is_deleted BOOLEAN DEFAULT 0")
                logger.info("数据库迁移：添加 is_deleted 字段")
            
            # 添加 is_read 字段
            if 'is_read' not in columns:
                cursor.execute("ALTER TABLE news ADD COLUMN is_read BOOLEAN DEFAULT 0")
                logger.info("数据库迁移：添加 is_read 字段")
            
            # 添加 compressed_content 字段
            if 'compressed_content' not in columns:
                cursor.execute("ALTER TABLE news ADD COLUMN compressed_content TEXT")
                logger.info("数据库迁移：添加 compressed_content 字段")
            
            # 添加 ai_score 字段
            if 'ai_score' not in columns:
                cursor.execute("ALTER TABLE news ADD COLUMN ai_score FLOAT")
                logger.info("数据库迁移：添加 ai_score 字段")
            
            # 添加 ai_score_topic_relevance 字段（主题相关性）
            if 'ai_score_topic_relevance' not in columns:
                cursor.execute("ALTER TABLE news ADD COLUMN ai_score_topic_relevance FLOAT")
                logger.info("数据库迁移：添加 ai_score_topic_relevance 字段")
            
            # 添加 ai_score_importance 字段（重要性）
            if 'ai_score_importance' not in columns:
                cursor.execute("ALTER TABLE news ADD COLUMN ai_score_importance FLOAT")
                logger.info("数据库迁移：添加 ai_score_importance 字段")
            
            # 移除 ai_score_freshness 字段（SQLite不支持直接删除列，需要重建表）
            if 'ai_score_freshness' in columns:
                logger.info("数据库迁移：移除 ai_score_freshness 字段")
                
                # 备份数据
                cursor.execute('''
                    CREATE TABLE news_backup AS
                    SELECT id, title, description, ai_summary, content, url, source, source_url,
                           category, publish_time, fetch_time, is_visible, ai_processed,
                           image_url, image_data, is_deleted, is_read,
                           compressed_content, keywords, ai_comment, ai_score,
                           ai_score_topic_relevance, ai_score_importance, ai_score_source,
                           ai_score_topic_relevance_reason, ai_score_importance_reason, ai_score_source_reason
                    FROM news
                ''')
                
                # 删除旧表
                cursor.execute('DROP TABLE news')
                
                # 创建新表（包含正确的约束）
                cursor.execute('''
                    CREATE TABLE news (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        description TEXT,
                        ai_summary TEXT,
                        content TEXT,
                        url TEXT UNIQUE,
                        source TEXT NOT NULL,
                        source_url TEXT,
                        category TEXT,
                        publish_time DATETIME,
                        fetch_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                        is_visible BOOLEAN DEFAULT 1,
                        ai_processed BOOLEAN DEFAULT 0,
                        image_url TEXT,
                        image_data BLOB,
                        is_deleted BOOLEAN DEFAULT 0,
                        is_read BOOLEAN DEFAULT 0,
                        compressed_content TEXT,
                        keywords TEXT,
                        ai_comment TEXT,
                        ai_score REAL,
                        ai_score_topic_relevance REAL,
                        ai_score_importance REAL,
                        ai_score_source REAL,
                        ai_score_topic_relevance_reason TEXT,
                        ai_score_importance_reason TEXT,
                        ai_score_source_reason TEXT
                    )
                ''')
                
                # 恢复数据
                cursor.execute('''
                    INSERT INTO news (
                        id, title, description, ai_summary, content, url, source, source_url,
                        category, publish_time, fetch_time, is_visible, ai_processed,
                        image_url, image_data, is_deleted, is_read,
                        compressed_content, keywords, ai_comment, ai_score,
                        ai_score_topic_relevance, ai_score_importance, ai_score_source,
                        ai_score_topic_relevance_reason, ai_score_importance_reason, ai_score_source_reason
                    )
                    SELECT id, title, description, ai_summary, content, url, source, source_url,
                           category, publish_time, fetch_time, is_visible, ai_processed,
                           image_url, image_data, is_deleted, is_read,
                           compressed_content, keywords, ai_comment, ai_score,
                           ai_score_topic_relevance, ai_score_importance, ai_score_source,
                           ai_score_topic_relevance_reason, ai_score_importance_reason, ai_score_source_reason
                    FROM news_backup
                ''')
                
                # 删除备份表
                cursor.execute('DROP TABLE news_backup')
                
                logger.info("数据库迁移完成：已重建news表")
                # 重建表后，重新创建索引
                self._create_indexes()
                self._create_fts_table()
                # 重新获取列信息
                cursor.execute("PRAGMA table_info(news)")
                columns = [row[1] for row in cursor.fetchall()]
            
            # 添加 ai_score_source 字段（来源可信度）
            if 'ai_score_source' not in columns:
                cursor.execute("ALTER TABLE news ADD COLUMN ai_score_source FLOAT")
                logger.info("数据库迁移：添加 ai_score_source 字段")
            
            # 添加打分理由字段
            if 'ai_score_topic_relevance_reason' not in columns:
                cursor.execute("ALTER TABLE news ADD COLUMN ai_score_topic_relevance_reason TEXT")
                logger.info("数据库迁移：添加 ai_score_topic_relevance_reason 字段")
            
            if 'ai_score_importance_reason' not in columns:
                cursor.execute("ALTER TABLE news ADD COLUMN ai_score_importance_reason TEXT")
                logger.info("数据库迁移：添加 ai_score_importance_reason 字段")
            
            if 'ai_score_source_reason' not in columns:
                cursor.execute("ALTER TABLE news ADD COLUMN ai_score_source_reason TEXT")
                logger.info("数据库迁移：添加 ai_score_source_reason 字段")
            
            # 添加 ai_comment 字段（AI评价）
            if 'ai_comment' not in columns:
                cursor.execute("ALTER TABLE news ADD COLUMN ai_comment TEXT")
                logger.info("数据库迁移：添加 ai_comment 字段")
            
            # 添加 keywords 字段（AI提取的关键字）
            if 'keywords' not in columns:
                cursor.execute("ALTER TABLE news ADD COLUMN keywords TEXT")
                logger.info("数据库迁移：添加 keywords 字段")
            
            # 修复 NULL 值：将 is_deleted 和 is_read 的 NULL 值更新为 0
            cursor.execute("UPDATE news SET is_deleted = 0 WHERE is_deleted IS NULL")
            affected_deleted = cursor.rowcount
            if affected_deleted > 0:
                logger.info(f"数据库迁移：修复 {affected_deleted} 条新闻的 is_deleted NULL 值")
            
            cursor.execute("UPDATE news SET is_read = 0 WHERE is_read IS NULL")
            affected_read = cursor.rowcount
            if affected_read > 0:
                logger.info(f"数据库迁移：修复 {affected_read} 条新闻的 is_read NULL 值")
            
            self._connection.commit()
            
        except Exception as e:
            logger.error(f"数据库迁移失败: {e}")
            self._connection.rollback()

    def _create_indexes(self):
        cursor = self._connection.cursor()
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_publish_time 
            ON news(publish_time DESC)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_category 
            ON news(category)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_is_visible 
            ON news(is_visible)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_fetch_time 
            ON news(fetch_time DESC)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_category_visible 
            ON news(category, is_visible)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_daily_stats_date 
            ON daily_stats(date DESC)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_chat_messages_session 
            ON chat_messages(session_id, created_at)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_reports_type 
            ON reports(report_type, created_at DESC)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_reports_created 
            ON reports(created_at DESC)
        ''')
        
        logger.info("数据库索引创建完成")

    def _create_fts_table(self):
        cursor = self._connection.cursor()
        
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS news_fts 
            USING fts5(title, description, ai_summary, content, content_rowid=rowid)
        ''')
        
        logger.info("全文搜索表创建完成")

    def insert_news(self, news_data: Dict[str, Any]) -> int:
        cursor = self._connection.cursor()
        
        try:
            # 处理图片
            image_url = news_data.get('image_url')
            image_data = None
            
            if image_url:
                # 下载并压缩图片
                result = image_processor.fetch_and_process_image(image_url)
                if result:
                    new_image_url, new_image_data = result
                    # 如果image_url被更新为本地路径，说明下载成功
                    if new_image_url != image_url:
                        image_url = new_image_url
                        # 文件系统模式下，不存储image_data（因为图片在文件系统中）
                        if image_processor.storage_mode == 'filesystem':
                            image_data = None
                        else:
                            image_data = new_image_data
                    else:
                        # 下载失败或使用原始URL，不存储image_data
                        image_url = None
                        image_data = None
            
            # 获取北京时间
            fetch_time = self._get_beijing_time()
            
            cursor.execute('''
                INSERT INTO news (
                    title, description, ai_summary, content, compressed_content, url, 
                    source, source_url, category, publish_time, is_visible, is_deleted, is_read, image_url, image_data, fetch_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                news_data.get('title'),
                news_data.get('description'),
                news_data.get('ai_summary'),
                news_data.get('content'),
                news_data.get('compressed_content'),
                news_data.get('url'),
                news_data.get('source'),
                news_data.get('source_url'),
                news_data.get('category'),
                news_data.get('publish_time'),
                news_data.get('is_visible', 1),
                news_data.get('is_deleted', 0),
                news_data.get('is_read', 0),
                image_url,
                image_data,
                fetch_time
            ))
            
            news_id = cursor.lastrowid
            self._connection.commit()
            logger.debug(f"新闻插入成功: {news_data.get('title')} (ID: {news_id})")
            return news_id
            
        except sqlite3.IntegrityError:
            # 检查是否是因为URL重复
            cursor.execute('''
                SELECT id, is_deleted FROM news WHERE url = ?
            ''', (news_data.get('url'),))
            
            result = cursor.fetchone()
            if result and result[1] == 1:
                # 如果是被标记为删除的记录，则更新它
                news_id = result[0]
                
                # 获取北京时间
                fetch_time = self._get_beijing_time()
                
                cursor.execute('''
                    UPDATE news SET
                        title = ?,
                        description = ?,
                        ai_summary = NULL,
                        content = ?,
                        compressed_content = ?,
                        source = ?,
                        source_url = ?,
                        category = ?,
                        publish_time = ?,
                        is_visible = ?,
                        is_deleted = 0,
                        is_read = 0,
                        ai_comment = NULL,
                        ai_score = NULL,
                        ai_score_topic_relevance = NULL,
                        ai_score_importance = NULL,
                        ai_score_source = NULL,
                        ai_score_topic_relevance_reason = NULL,
                        ai_score_importance_reason = NULL,
                        ai_score_source_reason = NULL,
                        image_url = ?,
                        image_data = ?,
                        fetch_time = ?
                    WHERE id = ?
                ''', (
                    news_data.get('title'),
                    news_data.get('description'),
                    news_data.get('content'),
                    news_data.get('compressed_content'),
                    news_data.get('source'),
                    news_data.get('source_url'),
                    news_data.get('category'),
                    news_data.get('publish_time'),
                    news_data.get('is_visible', 1),
                    image_url,
                    image_data,
                    fetch_time,
                    news_id
                ))
                
                self._connection.commit()
                logger.info(f"新闻已恢复: {news_data.get('title')} (ID: {news_id})")
                return news_id
            else:
                logger.warning(f"新闻已存在: {news_data.get('url')}")
                return -1
        except Exception as e:
            logger.error(f"新闻插入失败: {e}")
            self._connection.rollback()
            return -1

    def _convert_row(self, row: Dict) -> Dict:
        """
        转换数据库行数据，将图片数据转换为base64
        
        Args:
            row: 数据库行数据
            
        Returns:
            转换后的行数据
        """
        # 如果有图片数据，转换为base64
        if row.get('image_data'):
            try:
                row['image_data'] = base64.b64encode(row['image_data']).decode('utf-8')
            except Exception as e:
                logger.error(f"图片数据转换失败: {e}")
                row['image_data'] = None
        
        return row

    def get_news_by_category(self, category: str, limit: int = None, offset: int = 0) -> List[Dict]:
        cursor = self._connection.cursor()
        
        if category == '全部':
            query = '''
                SELECT * FROM news 
                WHERE is_visible = 1 AND is_deleted = 0
                ORDER BY publish_time DESC
            '''
            params = []
        elif category == '未分类':
            query = '''
                SELECT * FROM news 
                WHERE (category IS NULL OR category = '未分类')
                AND is_visible = 1 AND is_deleted = 0
                ORDER BY publish_time DESC
            '''
            params = []
        else:
            query = '''
                SELECT * FROM news 
                WHERE category = ? 
                AND is_visible = 1 AND is_deleted = 0
                ORDER BY publish_time DESC
            '''
            params = [category]
        
        if limit is not None:
            query += ' LIMIT ? OFFSET ?'
            params.extend([limit, offset])
        
        cursor.execute(query, params)
        
        return [self._convert_row(dict(row)) for row in cursor.fetchall()]

    def get_news_by_id(self, news_id: int) -> List[Dict]:
        cursor = self._connection.cursor()
        
        cursor.execute('''
            SELECT * FROM news 
            WHERE id = ?
        ''', (news_id,))
        
        return [dict(row) for row in cursor.fetchall()]

    def search_news(self, query: str, limit: int = 10) -> List[Dict]:
        cursor = self._connection.cursor()
        
        cursor.execute('''
            SELECT n.* FROM news n
            INNER JOIN news_fts fts ON n.id = fts.rowid
            WHERE news_fts MATCH ?
            AND n.is_visible = 1
            ORDER BY publish_time DESC
            LIMIT ?
        ''', (query, limit))
        
        return [dict(row) for row in cursor.fetchall()]

    def save_snapshot(self, snapshot_data: Dict[str, Any]) -> int:
        cursor = self._connection.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO snapshots (
                    date, file_path, file_size, news_count, 
                    status, error_message, ai_processing_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                snapshot_data.get('date'),
                snapshot_data.get('file_path'),
                snapshot_data.get('file_size'),
                snapshot_data.get('news_count'),
                snapshot_data.get('status', 'pending'),
                snapshot_data.get('error_message'),
                snapshot_data.get('ai_processing_time')
            ))
            
            snapshot_id = cursor.lastrowid
            self._connection.commit()
            logger.info(f"快照保存成功: {snapshot_data.get('date')} (ID: {snapshot_id})")
            return snapshot_id
            
        except Exception as e:
            logger.error(f"快照保存失败: {e}")
            self._connection.rollback()
            return -1

    def get_snapshot(self, date: str) -> Optional[Dict]:
        cursor = self._connection.cursor()
        
        cursor.execute('''
            SELECT * FROM snapshots WHERE date = ?
        ''', (date,))
        
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_snapshots_list(self, limit: int = 30) -> List[Dict]:
        cursor = self._connection.cursor()
        
        cursor.execute('''
            SELECT * FROM snapshots 
            ORDER BY date DESC 
            LIMIT ?
        ''', (limit,))
        
        return [dict(row) for row in cursor.fetchall()]

    def create_chat_session(self, session_id: str, user_id: Optional[str] = None) -> int:
        cursor = self._connection.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO chat_sessions (session_id, user_id)
                VALUES (?, ?)
            ''', (session_id, user_id))
            
            session_id_db = cursor.lastrowid
            self._connection.commit()
            logger.debug(f"对话会话创建成功: {session_id} (ID: {session_id_db})")
            return session_id_db
            
        except Exception as e:
            logger.error(f"对话会话创建失败: {e}")
            self._connection.rollback()
            return -1

    def add_chat_message(self, session_id: int, role: str, content: str, 
                       context_news_ids: Optional[str] = None) -> int:
        cursor = self._connection.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO chat_messages (session_id, role, content, context_news_ids)
                VALUES (?, ?, ?, ?)
            ''', (session_id, role, content, context_news_ids))
            
            message_id = cursor.lastrowid
            self._connection.commit()
            logger.debug(f"对话消息添加成功: {role} (ID: {message_id})")
            return message_id
            
        except Exception as e:
            logger.error(f"对话消息添加失败: {e}")
            self._connection.rollback()
            return -1

    def get_chat_history(self, session_id: int, limit: int = 50) -> List[Dict]:
        cursor = self._connection.cursor()
        
        cursor.execute('''
            SELECT * FROM chat_messages 
            WHERE session_id = ?
            ORDER BY created_at ASC
            LIMIT ?
        ''', (session_id, limit))
        
        return [dict(row) for row in cursor.fetchall()]

    def get_unprocessed_news(self, limit: int = 100) -> List[Dict]:
        cursor = self._connection.cursor()
        
        cursor.execute('''
            SELECT * FROM news 
            WHERE ai_processed = 0 AND is_visible = 1 AND is_deleted = 0
            ORDER BY fetch_time DESC
            LIMIT ?
        ''', (limit,))
        
        return [dict(row) for row in cursor.fetchall()]

    def update_news_ai_status(self, news_id: int, ai_processed: bool = True) -> bool:
        try:
            cursor = self._connection.cursor()
            cursor.execute('''
                UPDATE news 
                SET ai_processed = ?
                WHERE id = ?
            ''', (1 if ai_processed else 0, news_id))
            
            self._connection.commit()
            logger.debug(f"新闻AI状态更新成功: ID={news_id}, ai_processed={ai_processed}")
            return True
            
        except Exception as e:
            logger.error(f"新闻AI状态更新失败: {e}")
            try:
                self._connection.rollback()
            except Exception as rollback_error:
                logger.error(f"数据库回滚失败: {rollback_error}")
            return False

    def update_news_category(self, news_id: int, category: str) -> bool:
        logger.info(f"开始更新新闻分类: ID={news_id}, category={category}")
        try:
            cursor = self._connection.cursor()
            cursor.execute('''
                UPDATE news 
                SET category = ?
                WHERE id = ?
            ''', (category, news_id))
            
            self._connection.commit()
            logger.info(f"新闻分类更新成功: ID={news_id}, category={category}")
            
            # WebSocket广播
            if self._ws_broadcast_callback:
                logger.info(f"WebSocket广播回调已设置，准备广播: ID={news_id}")
                try:
                    logger.info(f"准备广播新闻更新: ID={news_id}, category={category}")
                    self._ws_broadcast_callback({
                        'type': 'news_updated',
                        'news_id': news_id,
                        'updates': {'category': category}
                    })
                    logger.info(f"已发送WebSocket广播: ID={news_id}")
                except Exception as e:
                    logger.warning(f"WebSocket广播失败: {e}")
            else:
                logger.warning(f"WebSocket广播回调未设置，跳过广播: ID={news_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"新闻分类更新失败: {e}")
            try:
                self._connection.rollback()
            except Exception as rollback_error:
                logger.error(f"数据库回滚失败: {rollback_error}")
            return False

    def update_news_summary(self, news_id: int, ai_summary: str) -> bool:
        logger.info(f"开始更新新闻摘要: ID={news_id}, summary_length={len(ai_summary)}")
        try:
            cursor = self._connection.cursor()
            cursor.execute('''
                UPDATE news 
                SET ai_summary = ?
                WHERE id = ?
            ''', (ai_summary, news_id))
            
            self._connection.commit()
            logger.info(f"新闻摘要更新成功: ID={news_id}")
            
            # WebSocket广播
            if self._ws_broadcast_callback:
                logger.info(f"WebSocket广播回调已设置，准备广播: ID={news_id}")
                try:
                    logger.info(f"准备广播新闻更新: ID={news_id}")
                    self._ws_broadcast_callback({
                        'type': 'news_updated',
                        'news_id': news_id,
                        'updates': {'ai_summary': ai_summary}
                    })
                    logger.info(f"已发送WebSocket广播: ID={news_id}")
                except Exception as e:
                    logger.warning(f"WebSocket广播失败: {e}")
            else:
                logger.warning(f"WebSocket广播回调未设置，跳过广播: ID={news_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"新闻摘要更新失败: {e}")
            try:
                self._connection.rollback()
            except Exception as rollback_error:
                logger.error(f"数据库回滚失败: {rollback_error}")
            return False

    def update_news_score(self, news_id: int, ai_score: float, 
                        topic_relevance: float = None,
                        importance: float = None,
                        source_score: float = None,
                        topic_relevance_reason: str = None,
                        importance_reason: str = None,
                        source_reason: str = None) -> bool:
        """更新新闻AI评分
        
        Args:
            news_id: 新闻ID
            ai_score: AI评分（总分）
            topic_relevance: 关联度评分
            importance: 重要程度评分
            source_score: 来源可信度评分
            topic_relevance_reason: 关联度评分理由
            importance_reason: 重要程度评分理由
            source_reason: 来源可信度评分理由
            
        Returns:
            是否成功
        """
        try:
            cursor = self._connection.cursor()
            
            # 构建更新SQL
            update_fields = ["ai_score = ?"]
            params = [ai_score]
            
            if topic_relevance is not None:
                update_fields.append("ai_score_topic_relevance = ?")
                params.append(topic_relevance)
            
            if importance is not None:
                update_fields.append("ai_score_importance = ?")
                params.append(importance)
            
            if source_score is not None:
                update_fields.append("ai_score_source = ?")
                params.append(source_score)
            
            if topic_relevance_reason is not None:
                update_fields.append("ai_score_topic_relevance_reason = ?")
                params.append(topic_relevance_reason)
            
            if importance_reason is not None:
                update_fields.append("ai_score_importance_reason = ?")
                params.append(importance_reason)
            
            if source_reason is not None:
                update_fields.append("ai_score_source_reason = ?")
                params.append(source_reason)
            
            params.append(news_id)
            
            cursor.execute(f'''
                UPDATE news 
                SET {', '.join(update_fields)}
                WHERE id = ?
            ''', params)
            
            self._connection.commit()
            logger.info(f"新闻评分更新成功: ID={news_id}, score={ai_score}, "
                       f"关联度={topic_relevance}, 重要程度={importance}, "
                       f"来源={source_score}")
            
            # WebSocket广播
            if self._ws_broadcast_callback:
                logger.info(f"WebSocket广播回调已设置，准备广播评分更新: ID={news_id}")
                try:
                    logger.info(f"准备广播新闻评分更新: ID={news_id}")
                    self._ws_broadcast_callback({
                        'type': 'news_updated',
                        'news_id': news_id,
                        'updates': {
                            'ai_score': ai_score,
                            'ai_score_topic_relevance': topic_relevance,
                            'ai_score_importance': importance,
                            'ai_score_source': source_score
                        }
                    })
                    logger.info(f"已发送WebSocket广播: ID={news_id}")
                except Exception as e:
                    logger.warning(f"WebSocket广播失败: {e}")
            else:
                logger.warning(f"WebSocket广播回调未设置，跳过广播: ID={news_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"新闻评分更新失败: {e}")
            try:
                self._connection.rollback()
            except Exception as rollback_error:
                logger.error(f"数据库回滚失败: {rollback_error}")
            return False

    def update_news_comment(self, news_id: int, comment: str) -> bool:
        """更新新闻AI评价
        
        Args:
            news_id: 新闻ID
            comment: AI评价
            
        Returns:
            是否成功
        """
        try:
            cursor = self._connection.cursor()
            cursor.execute('''
                UPDATE news 
                SET ai_comment = ?
                WHERE id = ?
            ''', (comment, news_id))
            
            self._connection.commit()
            logger.info(f"新闻AI评价更新成功: ID={news_id}, comment={comment[:50]}...")
            
            # WebSocket广播
            if self._ws_broadcast_callback:
                logger.info(f"WebSocket广播回调已设置，准备广播评价更新: ID={news_id}")
                try:
                    logger.info(f"准备广播新闻评价更新: ID={news_id}")
                    self._ws_broadcast_callback({
                        'type': 'news_updated',
                        'news_id': news_id,
                        'updates': {'ai_comment': comment}
                    })
                    logger.info(f"已发送WebSocket广播: ID={news_id}")
                except Exception as e:
                    logger.warning(f"WebSocket广播失败: {e}")
            else:
                logger.warning(f"WebSocket广播回调未设置，跳过广播: ID={news_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"新闻AI评价更新失败: {e}")
            try:
                self._connection.rollback()
            except Exception as rollback_error:
                logger.error(f"数据库回滚失败: {rollback_error}")
            return False

    def update_news_keywords(self, news_id: int, keywords: str) -> bool:
        """更新新闻AI提取的关键字
        
        Args:
            news_id: 新闻ID
            keywords: 关键字（逗号分隔）
            
        Returns:
            是否成功
        """
        try:
            cursor = self._connection.cursor()
            cursor.execute('''
                UPDATE news 
                SET keywords = ?
                WHERE id = ?
            ''', (keywords, news_id))
            
            self._connection.commit()
            logger.info(f"新闻关键字更新成功: ID={news_id}, keywords={keywords[:50]}...")
            
            return True
            
        except Exception as e:
            logger.error(f"新闻关键字更新失败: {e}")
            try:
                self._connection.rollback()
            except Exception as rollback_error:
                logger.error(f"数据库回滚失败: {rollback_error}")
            return False

    def update_news_content(self, news_id: int, content: str = None,
                            compressed_content: str = None) -> bool:
        """
        更新新闻正文相关字段
        
        Args:
            news_id: 新闻ID
            content: 完整正文
            compressed_content: 压缩后的正文
            
        Returns:
            是否更新成功
        """
        try:
            cursor = self._connection.cursor()
            
            # 构建更新SQL
            update_fields = []
            params = []
            
            if content is not None:
                update_fields.append("content = ?")
                params.append(content)
            
            if compressed_content is not None:
                update_fields.append("compressed_content = ?")
                params.append(compressed_content)
            
            if not update_fields:
                logger.warning("没有需要更新的字段")
                return False
            
            params.append(news_id)
            
            sql = f"UPDATE news SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(sql, params)
            
            self._connection.commit()
            logger.info(f"新闻内容更新成功: ID={news_id}")
            
            # WebSocket广播
            if self._ws_broadcast_callback:
                try:
                    updates = {}
                    if content is not None:
                        updates['content'] = content
                    if compressed_content is not None:
                        updates['compressed_content'] = compressed_content
                    
                    self._ws_broadcast_callback({
                        'type': 'news_updated',
                        'news_id': news_id,
                        'updates': updates
                    })
                except Exception as e:
                    logger.warning(f"WebSocket广播失败: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"新闻内容更新失败: {e}")
            try:
                self._connection.rollback()
            except Exception as rollback_error:
                logger.error(f"数据库回滚失败: {rollback_error}")
            return False

    def mark_all_news_deleted(self) -> int:
        """
        标记所有新闻为已删除状态
        
        Returns:
            被标记的新闻数量
        """
        try:
            cursor = self._connection.cursor()
            
            # 先统计数量
            cursor.execute('''
                SELECT COUNT(*) FROM news WHERE is_deleted = 0
            ''')
            count = cursor.fetchone()[0]
            
            # 标记所有未删除的新闻为已删除
            cursor.execute('''
                UPDATE news SET is_deleted = 1 WHERE is_deleted = 0
            ''')
            
            self._connection.commit()
            logger.info(f"已标记 {count} 条新闻为删除状态")
            return count
            
        except Exception as e:
            logger.error(f"标记新闻删除状态失败: {e}")
            try:
                self._connection.rollback()
            except Exception as rollback_error:
                logger.error(f"数据库回滚失败: {rollback_error}")
            return 0

    def get_news_stats(self) -> Dict[str, int]:
        """
        获取新闻统计信息
        
        Returns:
            包含统计信息的字典
        """
        try:
            cursor = self._connection.cursor()
            
            # 总新闻数（包括已删除）
            cursor.execute('SELECT COUNT(*) FROM news')
            total = cursor.fetchone()[0]
            
            # 未删除的新闻数
            cursor.execute('SELECT COUNT(*) FROM news WHERE is_deleted = 0')
            active = cursor.fetchone()[0]
            
            # 已删除的新闻数
            cursor.execute('SELECT COUNT(*) FROM news WHERE is_deleted = 1')
            deleted = cursor.fetchone()[0]
            
            # 已处理的新闻数
            cursor.execute('SELECT COUNT(*) FROM news WHERE ai_processed = 1 AND is_deleted = 0')
            processed = cursor.fetchone()[0]
            
            return {
                'total': total,
                'active': active,
                'deleted': deleted,
                'processed': processed,
                'unprocessed': active - processed
            }
            
        except Exception as e:
            logger.error(f"获取新闻统计失败: {e}")
            return {
                'total': 0,
                'active': 0,
                'deleted': 0,
                'processed': 0,
                'unprocessed': 0
            }

    def clear_ai_status(self, news_id: int) -> bool:
        """
        清除新闻的AI处理状态，允许重新处理

        Args:
            news_id: 新闻ID

        Returns:
            是否成功
        """
        try:
            cursor = self._connection.cursor()
            cursor.execute('''
                UPDATE news 
                SET ai_processed = 0,
                    ai_summary = NULL,
                    category = NULL,
                    keywords = NULL,
                    ai_comment = NULL,
                    ai_score = NULL,
                    ai_score_topic_relevance = NULL,
                    ai_score_importance = NULL,
                    ai_score_source = NULL,
                    ai_score_topic_relevance_reason = NULL,
                    ai_score_importance_reason = NULL,
                    ai_score_source_reason = NULL
                WHERE id = ?
            ''', (news_id,))
            self._connection.commit()
            logger.info(f"已清除新闻AI处理状态: news_id={news_id}")
            return True
        except Exception as e:
            logger.error(f"清除AI处理状态失败: {e}")
            self._connection.rollback()
            return False

    def add_to_ai_queue(self, news_id: int, task_type: str = 'all', priority: int = 0) -> int:
        """
        添加任务到AI处理队列

        Args:
            news_id: 新闻ID
            task_type: 任务类型 ('category', 'summary', 'all')
            priority: 优先级 (0=普通, 1=高)

        Returns:
            任务ID，如果新闻已存在于队列中则返回-1
        """
        try:
            cursor = self._connection.cursor()
            
            # 检查新闻ID是否已经存在于AI待处理队列中
            cursor.execute('''
                SELECT id FROM ai_processing_queue
                WHERE news_id = ? AND status IN ('pending', 'processing')
            ''', (news_id,))
            
            existing_task = cursor.fetchone()
            if existing_task:
                logger.info(f"新闻已存在于AI队列中，跳过添加: news_id={news_id}")
                return -1
            
            # 添加任务到队列
            cursor.execute('''
                INSERT INTO ai_processing_queue (news_id, task_type, status, priority)
                VALUES (?, ?, 'pending', ?)
            ''', (news_id, task_type, priority))
            task_id = cursor.lastrowid
            self._connection.commit()
            logger.info(f"AI任务已添加到队列: task_id={task_id}, news_id={news_id}, task_type={task_type}")
            return task_id
        except Exception as e:
            logger.error(f"添加AI任务到队列失败: {e}")
            self._connection.rollback()
            return -1

    def get_next_ai_task(self) -> Optional[Dict]:
        """
        获取下一个待处理的AI任务

        Returns:
            任务字典或None
        """
        try:
            cursor = self._connection.cursor()
            cursor.execute('''
                SELECT * FROM ai_processing_queue
                WHERE status = 'pending'
                ORDER BY priority DESC, created_at ASC
                LIMIT 1
            ''')
            row = cursor.fetchone()
            if row:
                task = dict(row)
                # 更新状态为处理中
                self.update_ai_task_status(task['id'], 'processing')
                return task
            return None
        except Exception as e:
            logger.error(f"获取下一个AI任务失败: {e}")
            return None

    def update_ai_task_status(self, task_id: int, status: str, error_message: str = None) -> bool:
        """
        更新AI任务状态

        Args:
            task_id: 任务ID
            status: 新状态 ('pending', 'processing', 'completed', 'failed')
            error_message: 错误信息（可选）

        Returns:
            是否成功
        """
        try:
            cursor = self._connection.cursor()
            if error_message:
                cursor.execute('''
                    UPDATE ai_processing_queue
                    SET status = ?, error_message = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (status, error_message, task_id))
            else:
                cursor.execute('''
                    UPDATE ai_processing_queue
                    SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (status, task_id))
            self._connection.commit()
            logger.debug(f"AI任务状态更新: task_id={task_id}, status={status}")
            return True
        except Exception as e:
            logger.error(f"更新AI任务状态失败: {e}")
            self._connection.rollback()
            return False

    def get_ai_processing_history(self, news_id: int) -> List[Dict]:
        """
        获取新闻的AI处理历史记录

        Args:
            news_id: 新闻ID

        Returns:
            AI处理历史列表
        """
        try:
            cursor = self._connection.cursor()
            cursor.execute('''
                SELECT * FROM ai_processing_queue
                WHERE news_id = ?
                ORDER BY created_at DESC
            ''', (news_id,))
            
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"获取AI处理历史失败: {e}")
            return []

    def get_ai_queue_stats(self) -> Dict[str, int]:
        """
        获取AI队列统计信息

        Returns:
            统计信息字典
        """
        try:
            cursor = self._connection.cursor()
            stats = {}

            # 待处理
            cursor.execute("SELECT COUNT(*) FROM ai_processing_queue WHERE status = 'pending'")
            stats['pending'] = cursor.fetchone()[0]

            # 处理中
            cursor.execute("SELECT COUNT(*) FROM ai_processing_queue WHERE status = 'processing'")
            stats['processing'] = cursor.fetchone()[0]

            # 已完成
            cursor.execute("SELECT COUNT(*) FROM ai_processing_queue WHERE status = 'completed'")
            stats['completed'] = cursor.fetchone()[0]

            # 失败
            cursor.execute("SELECT COUNT(*) FROM ai_processing_queue WHERE status = 'failed'")
            stats['failed'] = cursor.fetchone()[0]

            return stats
        except Exception as e:
            logger.error(f"获取AI队列统计失败: {e}")
            return {'pending': 0, 'processing': 0, 'completed': 0, 'failed': 0}

    def reset_stuck_ai_tasks(self) -> int:
        """
        重置卡住的AI任务（状态为processing的任务）

        Returns:
            被重置的任务数量
        """
        try:
            cursor = self._connection.cursor()

            # 先统计数量
            cursor.execute("SELECT COUNT(*) FROM ai_processing_queue WHERE status = 'processing'")
            count = cursor.fetchone()[0]

            if count > 0:
                # 重置状态为pending
                cursor.execute('''
                    UPDATE ai_processing_queue
                    SET status = 'pending',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE status = 'processing'
                ''')
                self._connection.commit()
                logger.info(f"已重置 {count} 个卡住的AI任务")

            return count

        except Exception as e:
            logger.error(f"重置卡住的AI任务失败: {e}")
            self._connection.rollback()
            return 0

    def mark_news_as_read(self, news_id: int, is_read: bool = True) -> bool:
        """
        标记新闻的阅读状态

        Args:
            news_id: 新闻ID
            is_read: 是否已读 (True=已读, False=未读)

        Returns:
            是否成功
        """
        try:
            cursor = self._connection.cursor()
            cursor.execute('''
                UPDATE news SET is_read = ? WHERE id = ?
            ''', (1 if is_read else 0, news_id))
            self._connection.commit()
            logger.debug(f"新闻阅读状态已更新: ID={news_id}, is_read={is_read}")
            
            # 通过WebSocket广播更新
            if self._ws_broadcast_callback:
                try:
                    self._ws_broadcast_callback({
                        'type': 'news_updated',
                        'news_id': news_id,
                        'updates': {'is_read': 1 if is_read else 0}
                    })
                    logger.debug(f"已发送WebSocket广播: ID={news_id}, is_read={is_read}")
                except Exception as e:
                    logger.error(f"WebSocket广播失败: {e}")
            
            return True
        except Exception as e:
            logger.error(f"标记新闻阅读状态失败: {e}")
            self._connection.rollback()
            return False

    def get_read_news(self, limit: int = 100) -> List[Dict]:
        """
        获取已读新闻

        Args:
            limit: 限制数量

        Returns:
            新闻列表
        """
        try:
            cursor = self._connection.cursor()
            cursor.execute('''
                SELECT * FROM news
                WHERE is_read = 1 AND is_visible = 1 AND is_deleted = 0
                ORDER BY publish_time DESC
                LIMIT ?
            ''', (limit,))
            return [self._convert_row(dict(row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"获取已读新闻失败: {e}")
            return []

    def get_unread_news(self, limit: int = 100) -> List[Dict]:
        """
        获取未读新闻

        Args:
            limit: 限制数量

        Returns:
            新闻列表
        """
        try:
            cursor = self._connection.cursor()
            cursor.execute('''
                SELECT * FROM news
                WHERE is_read = 0 AND is_visible = 1 AND is_deleted = 0
                ORDER BY publish_time DESC
                LIMIT ?
            ''', (limit,))
            return [self._convert_row(dict(row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"获取未读新闻失败: {e}")
            return []

    def get_news_by_time_range(self, start_time: str, end_time: str) -> List[Dict]:
        """按时间范围获取新闻
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            新闻列表
        """
        try:
            cursor = self._connection.cursor()
            cursor.execute('''
                SELECT * FROM news
                WHERE is_visible = 1 AND is_deleted = 0
                AND publish_time >= ? AND publish_time <= ?
                ORDER BY publish_time DESC
            ''', (start_time, end_time))
            return [self._convert_row(dict(row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"按时间范围获取新闻失败: {e}")
            return []

    def get_news_by_score(self, start_time: str, end_time: str, limit: int = 20) -> List[Dict]:
        """按评分获取新闻（用于报告生成）
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            limit: 限制数量
            
        Returns:
            新闻列表（按ai_score降序排序）
        """
        try:
            cursor = self._connection.cursor()
            cursor.execute('''
                SELECT * FROM news
                WHERE is_visible = 1 AND is_deleted = 0
                AND publish_time >= ? AND publish_time <= ?
                AND ai_score IS NOT NULL
                ORDER BY ai_score DESC
                LIMIT ?
            ''', (start_time, end_time, limit))
            return [self._convert_row(dict(row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"按评分获取新闻失败: {e}")
            return []

    def create_report(self, report_data: Dict[str, Any]) -> int:
        """创建报告
        
        Args:
            report_data: 报告数据
            
        Returns:
            报告ID
        """
        try:
            cursor = self._connection.cursor()
            
            created_at = self._get_beijing_time()
            
            cursor.execute('''
                INSERT INTO reports (
                    report_type, title, content, time_range_start, time_range_end,
                    news_count, ai_model, generation_time, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                report_data.get('report_type'),
                report_data.get('title'),
                report_data.get('content'),
                report_data.get('time_range_start'),
                report_data.get('time_range_end'),
                report_data.get('news_count', 0),
                report_data.get('ai_model'),
                report_data.get('generation_time'),
                created_at
            ))
            
            report_id = cursor.lastrowid
            self._connection.commit()
            logger.info(f"报告创建成功: {report_data.get('title')} (ID: {report_id})")
            return report_id
            
        except Exception as e:
            logger.error(f"报告创建失败: {e}")
            self._connection.rollback()
            return -1

    def get_reports_by_type(self, report_type: str, limit: int = None, offset: int = 0) -> List[Dict]:
        """按类型获取报告列表
        
        Args:
            report_type: 报告类型（daily/weekly/monthly）
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            报告列表
        """
        try:
            cursor = self._connection.cursor()
            
            query = '''
                SELECT * FROM reports
                WHERE report_type = ?
                ORDER BY created_at DESC
            '''
            params = [report_type]
            
            if limit is not None:
                query += ' LIMIT ? OFFSET ?'
                params.extend([limit, offset])
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"获取报告列表失败: {e}")
            return []

    def get_report_by_id(self, report_id: int) -> Optional[Dict]:
        """获取报告详情
        
        Args:
            report_id: 报告ID
            
        Returns:
            报告详情
        """
        try:
            cursor = self._connection.cursor()
            cursor.execute('''
                SELECT * FROM reports WHERE id = ?
            ''', (report_id,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"获取报告详情失败: {e}")
            return None

    def delete_report(self, report_id: int) -> bool:
        """删除报告
        
        Args:
            report_id: 报告ID
            
        Returns:
            是否成功
        """
        try:
            cursor = self._connection.cursor()
            cursor.execute('''
                DELETE FROM reports WHERE id = ?
            ''', (report_id,))
            
            self._connection.commit()
            logger.info(f"报告删除成功: ID={report_id}")
            return True
        except Exception as e:
            logger.error(f"报告删除失败: {e}")
            self._connection.rollback()
            return False

    def get_latest_report(self, report_type: str) -> Optional[Dict]:
        """获取最新报告
        
        Args:
            report_type: 报告类型
            
        Returns:
            最新报告
        """
        try:
            cursor = self._connection.cursor()
            cursor.execute('''
                SELECT * FROM reports
                WHERE report_type = ?
                ORDER BY created_at DESC
                LIMIT 1
            ''', (report_type,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"获取最新报告失败: {e}")
            return None

    def close(self):
        """关闭当前线程的数据库连接"""
        if hasattr(self._thread_local, 'connection') and self._thread_local.connection:
            self._thread_local.connection.close()
            self._thread_local.connection = None
            logger.info("数据库连接关闭")

    def close_all_connections(self):
        """关闭所有线程的数据库连接（清理资源）"""
        try:
            if hasattr(self._thread_local, 'connection') and self._thread_local.connection:
                self._thread_local.connection.close()
                self._thread_local.connection = None
            logger.info("所有数据库连接已关闭")
        except Exception as e:
            logger.error(f"关闭数据库连接失败: {e}")

    def cleanup(self):
        """清理所有资源"""
        try:
            if hasattr(self._thread_local, 'connection') and self._thread_local.connection:
                self._thread_local.connection.close()
                self._thread_local.connection = None
            logger.info("所有数据库连接已关闭")
        except Exception as e:
            logger.error(f"关闭数据库连接失败: {e}")
        logger.info("数据库资源清理完成")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.cleanup()
        return False


db = DatabaseManager()