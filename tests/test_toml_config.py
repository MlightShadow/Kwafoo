#!/usr/bin/env python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.helpers import config

def test_toml_config():
    print("=" * 60)
    print("测试TOML配置文件")
    print("=" * 60)
    
    print(f"\n数据库路径: {config.get('database.path')}")
    print(f"AI服务地址: {config.get('ai.base_url')}")
    print(f"AI模型: {config.get('ai.model')}")
    print(f"服务器端口: {config.get('server.port')}")
    print(f"日志级别: {config.get('logging.level')}")
    
    print(f"\n新闻源数量:")
    print(f"  RSS: {len(config.get('news_sources.rss', []))}")
    print(f"  API: {len(config.get('news_sources.api', []))}")
    print(f"  Web: {len(config.get('news_sources.web', []))}")
    
    print(f"\n分类数量: {len(config.get('categories', {}))}")
    
    print(f"\n调度器配置:")
    print(f"  抓取间隔: {config.get('scheduler.fetch_interval')}秒")
    print(f"  AI分析间隔: {config.get('scheduler.ai_process_interval')}秒")
    print(f"  自动抓取: {config.get('scheduler.auto_fetch')}")
    print(f"  自动AI分析: {config.get('scheduler.auto_ai_process')}")
    
    print("\n" + "=" * 60)
    print("TOML配置测试完成")
    print("=" * 60)

if __name__ == '__main__':
    try:
        test_toml_config()
        print("\n✓ 测试成功！")
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)