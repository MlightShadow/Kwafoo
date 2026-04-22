import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 先设置所有环境变量
os.environ['LITELLM_LOG'] = 'ERROR'
os.environ['LITELLM_DROP_PARAMS'] = 'True'
os.environ['LITELLM_MAX_RETRIES'] = '0'
os.environ['litellm_local_model_cost_map'] = 'true'
os.environ['LITELLM_CACHE'] = 'False'
os.environ['LITELLM_REQUEST_TIMEOUT'] = '10'

print('环境变量已设置')
print(f"litellm_local_model_cost_map = {os.environ.get('litellm_local_model_cost_map')}")

# 逐步导入模块
print('开始导入database...')
from database import db
print('database导入完成')

print('开始导入scheduler...')
from scheduler.scheduler import scheduler
print('scheduler导入完成')

print('开始导入web.server...')
from web.server import http_server
print('web.server导入完成')

print('所有导入完成！')