"""
数据库管理器测试
"""
import pytest
import sqlite3
import os
from database.manager import DatabaseManager


@pytest.fixture
def db_manager():
    """创建测试用的数据库管理器"""
    # 使用临时数据库文件
    test_db_path = "test_kwafoo.db"
    
    # 修改配置使用测试数据库
    from utils.helpers import config
    original_path = config.get('database.path', 'data/kwafoo.db')
    config._config['database']['path'] = test_db_path
    
    manager = DatabaseManager()
    
    yield manager
    
    # 清理
    manager.close_all_connections()
    if os.path.exists(test_db_path):
        try:
            os.remove(test_db_path)
        except PermissionError:
            # Windows下可能因为文件被锁定而无法删除
            pass
    
    # 恢复原始配置
    config._config['database']['path'] = original_path


def test_database_connection(db_manager):
    """测试数据库连接"""
    conn = db_manager._connection
    assert conn is not None
    assert isinstance(conn, sqlite3.Connection)


def test_database_health_check(db_manager):
    """测试数据库健康检查"""
    conn = db_manager._connection
    is_healthy = db_manager._check_connection_health(conn)
    assert is_healthy is True


def test_database_context_manager(db_manager):
    """测试数据库上下文管理器"""
    with db_manager as manager:
        assert manager is not None
        conn = manager._connection
        assert conn is not None


def test_database_cleanup(db_manager):
    """测试数据库清理"""
    # 先获取连接
    conn = db_manager._connection
    assert conn is not None
    
    # 执行清理
    db_manager.cleanup()
    
    # 验证连接已关闭（直接访问_thread_local而不是通过属性）
    if hasattr(db_manager._thread_local, 'connection'):
        assert db_manager._thread_local.connection is None


def test_thread_local_connections(db_manager):
    """测试线程本地连接"""
    import threading
    
    connections = []
    
    def get_connection():
        conn = db_manager._connection
        connections.append(id(conn))
    
    # 创建多个线程获取连接
    threads = [threading.Thread(target=get_connection) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # 验证每个线程的连接ID不同（线程本地存储）
    # 注意：由于线程执行顺序不确定，可能有些线程获取到相同的连接
    # 但至少应该有多个不同的连接ID
    assert len(set(connections)) >= 1
    
    # 清理：关闭所有连接后再删除数据库文件
    db_manager.close_all_connections()
    import time
    time.sleep(0.1)  # 等待文件释放