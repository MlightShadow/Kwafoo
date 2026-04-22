import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置环境变量
os.environ['litellm_local_model_cost_map'] = 'true'
os.environ['LITELLM_LOG'] = 'ERROR'

print('开始导入ai.processor...')
from ai.processor import AINewsProcessor
print('ai.processor导入完成')

print('测试完成！')