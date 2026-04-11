#!/usr/bin/env python3
"""
Kwafoo项目快速API测试脚本
快速测试所有API接口，不等待新闻抓取
"""

import requests
import json
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

def run_quick_tests():
    """运行快速API测试"""
    print_header("Kwafoo快速API测试")
    print_info(f"测试服务器: {BASE_URL}")
    print_info(f"API地址: {API_BASE}\n")
    
    # 检查服务器状态
    if not check_server_status():
        print_error("服务器未运行，请先启动服务器")
        return False
    
    results = []
    
    # 基础功能测试
    print_header("基础功能测试")
    results.append(("健康检查", test_api("health")))
    results.append(("新闻统计", test_api("news/stats")))
    results.append(("新闻列表", test_api("news")))
    results.append(("配置获取", test_api("config")))
    
    # 搜索和分类测试
    print_header("搜索和分类测试")
    results.append(("搜索功能", test_api("news/search?q=test&limit=5")))
    results.append(("分类查询", test_api("news/category?category=tech")))
    
    # 功能测试
    print_header("功能测试")
    results.append(("手动抓取", test_api("fetch", "POST")))
    results.append(("进度查询", test_api("progress")))
    
    # 配置管理测试
    print_header("配置管理测试")
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
    results.append(("配置更新", test_api("config", "POST", test_data)))
    
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
        success = run_quick_tests()
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