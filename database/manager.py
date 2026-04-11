import sqlite3
import os
import base64
from typing import List, Dict, Optional, Any
from datetime import datetime
from utils.logger import logger
from utils.helpers import config
from utils.image_processor import image_processor


class DatabaseManager:
    _instance = None
    _connection = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._connection is None:
            self._connect()

    def _connect(self):
        db_path = config.get('database.path', 'data/kwafoo.db')
        db_dir = os.path.dirname(db_path)
        
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        self._connection = sqlite3.connect(db_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        logger.info(f"数据库连接成功: {db_path}")

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
                is_deleted BOOLEAN DEFAULT 0
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
                    image_url, image_data = result
            
            cursor.execute('''
                INSERT INTO news (
                    title, description, ai_summary, content, url, 
                    source, source_url, category, publish_time, is_visible, image_url, image_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                news_data.get('title'),
                news_data.get('description'),
                news_data.get('ai_summary'),
                news_data.get('content'),
                news_data.get('url'),
                news_data.get('source'),
                news_data.get('source_url'),
                news_data.get('category'),
                news_data.get('publish_time'),
                news_data.get('is_visible', 1),
                image_url,
                image_data
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
                cursor.execute('''
                    UPDATE news SET
                        title = ?,
                        description = ?,
                        ai_summary = ?,
                        content = ?,
                        source = ?,
                        source_url = ?,
                        category = ?,
                        publish_time = ?,
                        is_visible = ?,
                        image_url = ?,
                        image_data = ?,
                        is_deleted = 0,
                        fetch_time = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (
                    news_data.get('title'),
                    news_data.get('description'),
                    news_data.get('ai_summary'),
                    news_data.get('content'),
                    news_data.get('source'),
                    news_data.get('source_url'),
                    news_data.get('category'),
                    news_data.get('publish_time'),
                    news_data.get('is_visible', 1),
                    image_url,
                    image_data,
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

    def get_news_by_date(self, date: str) -> List[Dict]:
        cursor = self._connection.cursor()
        
        cursor.execute('''
            SELECT * FROM news 
            WHERE DATE(fetch_time) = ? AND is_visible = 1 AND is_deleted = 0
            ORDER BY publish_time DESC
        ''', (date,))
        
        return [self._convert_row(dict(row)) for row in cursor.fetchall()]

    def get_news_by_category(self, category: str) -> List[Dict]:
        cursor = self._connection.cursor()
        
        cursor.execute('''
            SELECT * FROM news 
            WHERE (category = ? OR category LIKE ? OR category LIKE ? OR category LIKE ?) 
            AND is_visible = 1 AND is_deleted = 0
            ORDER BY publish_time DESC
        ''', (category, f"{category}%", f"%,{category}", f"%,{category}%"))
        
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
        try:
            cursor = self._connection.cursor()
            cursor.execute('''
                UPDATE news 
                SET category = ?
                WHERE id = ?
            ''', (category, news_id))
            
            self._connection.commit()
            logger.debug(f"新闻分类更新成功: ID={news_id}, category={category}")
            return True
            
        except Exception as e:
            logger.error(f"新闻分类更新失败: {e}")
            try:
                self._connection.rollback()
            except Exception as rollback_error:
                logger.error(f"数据库回滚失败: {rollback_error}")
            return False

    def update_news_summary(self, news_id: int, ai_summary: str) -> bool:
        try:
            cursor = self._connection.cursor()
            cursor.execute('''
                UPDATE news 
                SET ai_summary = ?
                WHERE id = ?
            ''', (ai_summary, news_id))
            
            self._connection.commit()
            logger.debug(f"新闻摘要更新成功: ID={news_id}")
            return True
            
        except Exception as e:
            logger.error(f"新闻摘要更新失败: {e}")
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

    def close(self):
        if self._connection:
            self._connection.close()
            logger.info("数据库连接关闭")


db = DatabaseManager()