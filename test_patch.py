import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置环境变量
os.environ['litellm_local_model_cost_map'] = 'true'
os.environ['LITELLM_LOG'] = 'ERROR'

# 尝试通过monkey patch来阻止网络请求
import urllib.request
original_urlopen = urllib.request.urlopen

def patched_urlopen(*args, **kwargs):
    """阻止所有urllib请求"""
    raise Exception("Network request blocked during import")

urllib.request.urlopen = patched_urlopen

print('开始导入litellm...')
try:
    import litellm
    print('litellm导入成功！')
except Exception as e:
    print(f'litellm导入失败: {e}')
    # 恢复原始函数
    urllib.request.urlopen = original_urlopen
    import litellm
    print('litellm导入成功（恢复网络后）')

# 恢复原始函数
urllib.request.urlopen = original_urlopen

print('测试完成！')