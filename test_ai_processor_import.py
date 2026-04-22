import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置环境变量
os.environ['LITELLM_LOG'] = 'ERROR'
os.environ['LITELLM_DROP_PARAMS'] = 'true'
os.environ['LITELLM_MAX_RETRIES'] = '0'
os.environ['LITELLM_LOCAL_MODEL_COST_MAP'] = 'true'
os.environ['LITELLM_CACHE'] = 'false'
os.environ['LITELLM_REQUEST_TIMEOUT'] = '10'

print('开始导入ai.processor...')
from ai.processor import AINewsProcessor
print('ai.processor导入完成！')

print('测试完成！')