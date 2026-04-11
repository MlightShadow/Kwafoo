import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_ai_summary_api():
    print("测试AI摘要API...")
    
    # 获取新闻列表
    response = requests.get(f"{BASE_URL}/api/news")
    if response.status_code == 200:
        data = response.json()
        if data.get('success') and data.get('data'):
            news_list = data['data']
            print(f"找到 {len(news_list)} 条新闻")
            
            if news_list:
                # 选择第一条新闻进行测试
                first_news = news_list[0]
                news_id = first_news['id']
                print(f"\n测试新闻ID: {news_id}")
                print(f"标题: {first_news['title']}")
                print(f"原始摘要: {first_news.get('description', '无')[:100]}...")
                
                # 调用AI摘要API
                print(f"\n调用AI摘要API...")
                summary_response = requests.post(
                    f"{BASE_URL}/api/ai/summarize",
                    json={"news_id": news_id},
                    headers={"Content-Type": "application/json"}
                )
                
                if summary_response.status_code == 200:
                    summary_data = summary_response.json()
                    if summary_data.get('success'):
                        print(f"✅ AI摘要生成成功!")
                        print(f"AI摘要: {summary_data.get('summary', '无')}")
                    else:
                        print(f"❌ AI摘要生成失败: {summary_data.get('error', '未知错误')}")
                else:
                    print(f"❌ API调用失败: {summary_response.status_code}")
        else:
            print("❌ 没有找到新闻数据")
    else:
        print(f"❌ 获取新闻列表失败: {response.status_code}")

def test_news_display():
    print("\n测试新闻显示...")
    
    response = requests.get(f"{BASE_URL}/api/news")
    if response.status_code == 200:
        data = response.json()
        if data.get('success') and data.get('data'):
            news_list = data['data']
            print(f"找到 {len(news_list)} 条新闻")
            
            for i, news in enumerate(news_list[:5], 1):
                print(f"\n新闻 {i}:")
                print(f"  ID: {news['id']}")
                print(f"  标题: {news['title']}")
                
                # 检查摘要长度
                ai_summary = news.get('ai_summary', '')
                description = news.get('description', '')
                
                if ai_summary:
                    print(f"  AI摘要: {ai_summary[:100]}...")
                    if len(ai_summary) > 140:
                        print(f"  ⚠️ AI摘要超过140字: {len(ai_summary)}字")
                    else:
                        print(f"  ✅ AI摘要长度符合要求: {len(ai_summary)}字")
                elif description:
                    print(f"  描述: {description[:100]}...")
                    if len(description) > 140:
                        print(f"  ⚠️ 描述超过140字: {len(description)}字 (需要AI摘要)")
                    else:
                        print(f"  ✅ 描述长度符合要求: {len(description)}字")
                else:
                    print(f"  ❌ 无摘要")
                    
                print(f"  分类: {news.get('category', '未分类')}")
                print(f"  来源: {news.get('source', '未知')}")
        else:
            print("❌ 没有找到新闻数据")
    else:
        print(f"❌ 获取新闻列表失败: {response.status_code}")

if __name__ == "__main__":
    print("=" * 60)
    print("测试前端优化功能")
    print("=" * 60)
    
    try:
        # 测试新闻显示
        test_news_display()
        
        # 测试AI摘要API
        test_ai_summary_api()
        
        print("\n" + "=" * 60)
        print("测试完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()