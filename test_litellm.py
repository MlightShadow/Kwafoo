import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置环境变量
os.environ['litellm_local_model_cost_map'] = 'true'
os.environ['LITELLM_LOG'] = 'ERROR'
os.environ['LITELLM_DROP_PARAMS'] = 'True'
os.environ['LITELLM_MAX_RETRIES'] = '0'
os.environ['LITELLM_CACHE'] = 'False'
os.environ['LITELLM_REQUEST_TIMEOUT'] = '10'

print('环境变量已设置')
print(f"litellm_local_model_cost_map = {os.environ.get('litellm_local_model_cost_map')}")

print('开始导入litellm...')
import litellm
print('litellm导入完成')

print('开始导入completion...')
from litellm import completion
print('completion导入完成')

print('测试完成！')