import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置环境变量
os.environ['litellm_local_model_cost_map'] = 'true'
os.environ['LITELLM_LOG'] = 'ERROR'

print('开始导入schedule...')
import schedule
print('schedule导入完成')

print('开始导入database...')
from database import db
print('database导入完成')

print('开始导入scheduler...')
from scheduler.scheduler import Scheduler
print('Scheduler类导入完成')

print('创建Scheduler实例...')
s = Scheduler()
print('Scheduler实例创建完成')

print('所有测试完成！')