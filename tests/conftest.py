"""
Pytest配置文件
"""
import pytest
import sys
import os


# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture(scope="session")
def test_config():
    """测试配置fixture"""
    from utils.helpers import config
    
    # 修改配置为测试配置
    config._config = {
        'database': {
            'path': 'test_kwafoo.db'
        },
        'ai': {
            'base_url': 'http://localhost:1234',
            'model': 'test-model',
            'max_tokens': 4096,
            'temperature': 0.7,
            'max_workers': 1,
            'batch_size': 1,
            'enable_summary': True,
            'summary_threshold': 140,
            'max_input_length': 2000,
            'timeout': 120
        },
        'scheduler': {
            'fetch_interval': 1800,
            'ai_process_interval': 600,
            'auto_fetch': False,
            'auto_ai_process': False,
            'auto_ai_after_fetch': False,
            'max_fetch_workers': 20
        },
        'server': {
            'host': '0.0.0.0',
            'port': 8000,
            'enable_websocket': True
        },
        'network': {
            'enable_proxy': False,
            'proxy_url': ''
        },
        'image': {
            'enable_fetch': True,
            'storage_mode': 'filesystem',
            'storage_path': 'test_images'
        },
        'logging': {
            'level': 'INFO',
            'file': 'test_kwafoo.log',
            'max_size': 10485760,
            'backup_count': 5
        },
        'rag': {
            'top_k': 5,
            'use_fts': True
        },
        'categories': [
            {
                'name': '科技',
                'description': '科技相关内容',
                'keywords': ['科技', '人工智能'],
                'icon': '💻',
                'color': '#3498db'
            },
            {
                'name': '财经',
                'description': '财经相关内容',
                'keywords': ['财经', '股票'],
                'icon': '💰',
                'color': '#27ae60'
            }
        ],
        'default_category': '未分类'
    }
    
    # 初始化测试数据库
    from database import db
    db.create_tables()
    
    return config


@pytest.fixture(autouse=True)
def setup_test_environment(test_config):
    """自动应用的测试环境设置"""
    # 设置测试环境变量
    os.environ['TESTING'] = 'true'
    
    yield
    
    # 清理测试环境
    if 'TESTING' in os.environ:
        del os.environ['TESTING']


@pytest.fixture
def mock_logger():
    """Mock日志记录器"""
    from unittest.mock import Mock
    from utils.logger import logger
    
    original_info = logger.info
    original_debug = logger.debug
    original_warning = logger.warning
    original_error = logger.error
    
    logger.info = Mock()
    logger.debug = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    
    yield logger
    
    # 恢复原始方法
    logger.info = original_info
    logger.debug = original_debug
    logger.warning = original_warning
    logger.error = original_error


# Pytest配置
def pytest_configure(config):
    """Pytest配置钩子"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


def pytest_collection_modifyitems(config, items):
    """修改测试收集"""
    # 自动标记测试类型
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(pytest.mark.integration)
        else:
            item.add_marker(pytest.mark.unit)