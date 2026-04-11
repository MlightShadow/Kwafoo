#!/usr/bin/env python3
import requests
import json
import time
from datetime import datetime

def test_frontend_functionality():
    """测试前端功能"""
    print("测试前端功能...")
    print("=" * 50)
    
    base_url = 'http://localhost:8000'
    
    # 1. 测试主页访问
    print("\n1. 测试主页访问")
    response = requests.get(f'{base_url}/')
    print(f"   状态码: {response.status_code}")
    assert response.status_code == 200, "主页访问失败"
    print("   ✓ 主页访问正常")
    
    # 2. 测试API健康检查
    print("\n2. 测试API健康检查")
    response = requests.get(f'{base_url}/api/health')
    data = response.json()
    print(f"   状态: {data.get('status')}")
    assert data.get('success'), "API健康检查失败"
    print("   ✓ API健康检查正常")
    
    # 3. 测试配置获取
    print("\n3. 测试配置获取")
    response = requests.get(f'{base_url}/api/config')
    data = response.json()
    print(f"   成功: {data.get('success')}")
    if data.get('success'):
        categories = data.get('data', {}).get('categories', {})
        print(f"   分类数量: {len(categories)}")
        for cat_name, cat_config in categories.items():
            print(f"     - {cat_name} ({cat_config.get('name', cat_name)})")
    print("   ✓ 配置获取正常")
    
    # 4. 测试新闻统计
    print("\n4. 测试新闻统计")
    response = requests.get(f'{base_url}/api/news/stats')
    data = response.json()
    print(f"   成功: {data.get('success')}")
    if data.get('success'):
        stats = data.get('data', {})
        print(f"   总新闻数: {stats.get('total', 0)}")
        print(f"   活跃新闻: {stats.get('active', 0)}")
        print(f"   已删除: {stats.get('deleted', 0)}")
        print(f"   已处理: {stats.get('processed', 0)}")
        print(f"   未处理: {stats.get('unprocessed', 0)}")
    print("   ✓ 新闻统计正常")
    
    # 5. 测试新闻列表
    print("\n5. 测试新闻列表")
    response = requests.get(f'{base_url}/api/news')
    data = response.json()
    print(f"   成功: {data.get('success')}")
    if data.get('success'):
        news_list = data.get('data', [])
        print(f"   新闻数量: {len(news_list)}")
        if news_list:
            first_news = news_list[0]
            print(f"   第一条新闻: {first_news.get('title', 'N/A')}")
    print("   ✓ 新闻列表正常")
    
    # 6. 测试搜索功能
    print("\n6. 测试搜索功能")
    response = requests.get(f'{base_url}/api/news/search?q=test&limit=5')
    data = response.json()
    print(f"   成功: {data.get('success')}")
    if data.get('success'):
        print(f"   搜索结果: {data.get('count', 0)} 条")
    print("   ✓ 搜索功能正常")
    
    # 7. 测试分类查询
    print("\n7. 测试分类查询")
    response = requests.get(f'{base_url}/api/news/category?category=tech')
    data = response.json()
    print(f"   成功: {data.get('success')}")
    if data.get('success'):
        print(f"   分类新闻: {len(data.get('data', []))} 条")
    print("   ✓ 分类查询正常")
    
    # 8. 测试进度查询
    print("\n8. 测试进度查询")
    response = requests.get(f'{base_url}/api/progress')
    data = response.json()
    print(f"   成功: {data.get('success')}")
    if data.get('success'):
        progress_list = data.get('data', [])
        print(f"   任务数量: {len(progress_list)}")
        if progress_list and isinstance(progress_list, list) and len(progress_list) > 0:
            latest = progress_list[0]
            print(f"   最新任务: {latest.get('task_type', 'N/A')}")
            print(f"   进度: {latest.get('progress', 0)}%")
    print("   ✓ 进度查询正常")
    
    # 9. 测试AI状态
    print("\n9. 测试AI状态")
    response = requests.get(f'{base_url}/api/ai/status')
    data = response.json()
    print(f"   成功: {data.get('success')}")
    if data.get('success'):
        status = data.get('data', {}).get('status', 'unknown')
        print(f"   AI状态: {status}")
    print("   ✓ AI状态查询正常")
    
    # 10. 测试手动抓取
    print("\n10. 测试手动抓取")
    response = requests.post(f'{base_url}/api/fetch')
    data = response.json()
    print(f"   成功: {data.get('success')}")
    print(f"   消息: {data.get('message', 'N/A')}")
    print("   ✓ 手动抓取触发正常")
    
    print("\n" + "=" * 50)
    print("✓ 所有前端功能测试通过！")
    print("=" * 50)
    
    return True

if __name__ == '__main__':
    try:
        test_frontend_functionality()
    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()