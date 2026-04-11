#!/usr/bin/env python3
"""
Kwafoo项目自动化测试脚本
自动测试所有主要功能，无需手动操作
"""

import requests
import json
import time
import sys
from typing import Dict, Any

# 配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_success(message: str):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message: str):
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_info(message: str):
    print(f"{Colors.BLUE}ℹ {message}{Colors.END}")

def print_header(message: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def test_api(endpoint: str, method: str = "GET", data: Dict = None, 
            expected_success: bool = True) -> bool:
    """测试API接口"""
    try:
        url = f"{API_BASE}/{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            print_error(f"不支持的HTTP方法: {method}")
            return False
        
        result = response.json()
        success = result.get('success', False) == expected_success
        
        if success:
            print_success(f"{method} {endpoint} - 状态码: {response.status_code}")
        else:
            print_error(f"{method} {endpoint} - 预期: {expected_success}, 实际: {result.get('success')}")
            if 'error' in result:
                print(f"  错误: {result['error']}")
        
        return success
        
    except Exception as e:
        print_error(f"{method} {endpoint} - 异常: {str(e)}")
        return False

def test_health_check():
    """测试健康检查"""
    print_header("1. 健康检查测试")
    return test_api("health")

def test_news_stats():
    """测试新闻统计"""
    print_header("2. 新闻统计测试")
    return test_api("news/stats")

def test_news_list():
    """测试新闻列表"""
    print_header("3. 新闻列表测试")
    return test_api("news")

def test_config():
    """测试配置获取"""
    print_header("4. 配置获取测试")
    return test_api("config")

def test_manual_fetch():
    """测试手动抓取"""
    print_header("5. 手动抓取测试")
    result = test_api("fetch", "POST")
    if result:
        print_info("等待5秒让抓取任务执行...")
        time.sleep(5)
    return result

def test_progress():
    """测试进度查询"""
    print_header("6. 进度查询测试")
    return test_api("progress")

def test_search():
    """测试搜索功能"""
    print_header("7. 搜索功能测试")
    return test_api("news/search?q=test&limit=5")

def test_category():
    """测试分类查询"""
    print_header("8. 分类查询测试")
    return test_api("news/category?category=tech")

def test_config_update():
    """测试配置更新"""
    print_header("9. 配置更新测试")
    test_data = {
        "categories": {
            "tech": {
                "name": "科技",
                "keywords": ["人工智能", "科技"],
                "icon": "💻",
                "color": "#3498db"
            }
        }
    }
    return test_api("config", "POST", test_data)

def test_clear_news():
    """测试清空新闻"""
    print_header("10. 清空新闻测试")
    return test_api("news/clear", "POST")

def wait_for_news():
    """等待新闻抓取完成"""
    print_header("等待新闻抓取完成")
    max_wait = 60  # 最多等待60秒
    waited = 0
    
    while waited < max_wait:
        try:
            response = requests.get(f"{API_BASE}/news/stats", timeout=5)
            result = response.json()
            total = result.get('data', {}).get('total', 0)
            
            if total > 0:
                print_success(f"抓取完成！共获取 {total} 条新闻")
                return True
            
            print_info(f"等待中... ({waited}s)")
            time.sleep(5)
            waited += 5
            
        except Exception as e:
            print_error(f"查询失败: {e}")
            time.sleep(5)
            waited += 5
    
    print_error("等待超时，未获取到新闻")
    return False

def check_server_status():
    """检查服务器状态"""
    print_header("检查服务器状态")
    try:
        response = requests.get(BASE_URL, timeout=5)
        if response.status_code == 200:
            print_success("服务器运行正常")
            return True
        else:
            print_error(f"服务器状态异常: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"无法连接到服务器: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    print_header("Kwafoo自动化测试开始")
    print_info(f"测试服务器: {BASE_URL}")
    print_info(f"API地址: {API_BASE}\n")
    
    # 检查服务器状态
    if not check_server_status():
        print_error("服务器未运行，请先启动服务器")
        return False
    
    results = []
    
    # 基础功能测试
    results.append(("健康检查", test_health_check()))
    results.append(("新闻统计", test_news_stats()))
    results.append(("新闻列表", test_news_list()))
    results.append(("配置获取", test_config()))
    results.append(("搜索功能", test_search()))
    results.append(("分类查询", test_category()))
    
    # 功能测试
    results.append(("手动抓取", test_manual_fetch()))
    
    # 等待抓取完成
    if results[-1][1]:  # 如果抓取启动成功
        wait_result = wait_for_news()
        results.append(("等待抓取", wait_result))
        
        if wait_result:
            # 抓取完成后的测试
            results.append(("进度查询", test_progress()))
            results.append(("新闻统计(抓取后)", test_news_stats()))
            results.append(("新闻列表(抓取后)", test_news_list()))
    
    # 配置管理测试
    results.append(("配置更新", test_config_update()))
    
    # 汇总结果
    print_header("测试结果汇总")
    
    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed
    
    for name, result in results:
        if result:
            print_success(f"{name}")
        else:
            print_error(f"{name}")
    
    print(f"\n总计: {len(results)} 个测试")
    print(f"{Colors.GREEN}通过: {passed}{Colors.END}")
    print(f"{Colors.RED}失败: {failed}{Colors.END}")
    
    if failed == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 所有测试通过！{Colors.END}")
        return True
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ 有 {failed} 个测试失败{Colors.END}")
        return False

def main():
    """主函数"""
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_info("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print_error(f"测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()