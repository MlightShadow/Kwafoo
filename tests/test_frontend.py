#!/usr/bin/env python3
import requests
import json
import time

def test_frontend_access():
    """测试前端访问"""
    print("测试前端访问...")
    
    # 测试主页
    response = requests.get('http://localhost:8000/')
    print(f"主页状态码: {response.status_code}")
    
    # 检查关键元素
    content = response.text
    checks = {
        'newsList': 'newsList' in content,
        'categoryList': 'categoryList' in content,
        'chatMessages': 'chatMessages' in content,
        'progressBar': 'progressBar' in content,
        'serverStatus': 'serverStatus' in content,
        'aiStatus': 'aiStatus' in content,
        'loadingIndicator': 'loadingIndicator' in content,
    }
    
    print("\nHTML元素检查:")
    for element, found in checks.items():
        status = "✓" if found else "✗"
        print(f"  {status} {element}")
    
    # 测试JavaScript文件
    js_files = [
        '/js/modules/api.js',
        '/js/modules/ui.js',
        '/js/modules/events.js',
        '/js/app-modular.js',
        '/css/style.css'
    ]
    
    print("\n静态资源检查:")
    for js_file in js_files:
        response = requests.get(f'http://localhost:8000{js_file}')
        status = "✓" if response.status_code == 200 else "✗"
        print(f"  {status} {js_file} ({response.status_code})")
    
    # 测试API接口
    print("\nAPI接口检查:")
    api_tests = [
        ('/api/health', '健康检查'),
        ('/api/news', '新闻列表'),
        ('/api/news/stats', '新闻统计'),
        ('/api/config', '配置获取'),
    ]
    
    for endpoint, name in api_tests:
        try:
            response = requests.get(f'http://localhost:8000{endpoint}')
            data = response.json()
            status = "✓" if response.status_code == 200 and data.get('success') else "✗"
            print(f"  {status} {name}")
        except Exception as e:
            print(f"  ✗ {name} - {str(e)}")
    
    print("\n✓ 前端访问测试完成")

if __name__ == '__main__':
    test_frontend_access()