import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置环境变量
os.environ['litellm_local_model_cost_map'] = 'true'
os.environ['LITELLM_LOG'] = 'ERROR'

# 尝试找到litellm的安装位置并创建本地模型成本映射文件
import site
site_packages = site.getsitepackages()
for pkg_path in site_packages:
    litellm_path = os.path.join(pkg_path, 'litellm')
    if os.path.exists(litellm_path):
        print(f'找到litellm路径: {litellm_path}')
        
        # 检查是否存在备份文件
        backup_file = os.path.join(litellm_path, 'model_prices_and_context_window_backup.json')
        if os.path.exists(backup_file):
            print(f'备份文件已存在: {backup_file}')
        else:
            print(f'备份文件不存在: {backup_file}')
            
        # 创建一个简单的模型成本映射
        model_cost = {
            "nvidia/nemotron-3-nano-4b": {
                "input_cost_per_token": 0.000001,
                "output_cost_per_token": 0.000001,
                "max_tokens": 4096
            }
        }
        
        # 写入备份文件
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(model_cost, f, ensure_ascii=False, indent=2)
        print(f'已创建模型成本映射文件: {backup_file}')
        break

print('开始导入litellm...')
import litellm
print('litellm导入完成！')

print('测试完成！')