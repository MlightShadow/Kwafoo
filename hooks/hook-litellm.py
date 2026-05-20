"""
PyInstaller hook for litellm
"""
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, get_package_paths
import os

# 收集所有数据文件
datas = collect_data_files('litellm', include_py_files=False)
hiddenimports = collect_submodules('litellm')

# 确保备份文件被正确打包
try:
    litellm_base, litellm_dir = get_package_paths('litellm')
    backup_file = os.path.join(litellm_dir, 'model_prices_and_context_window_backup.json')
    if os.path.exists(backup_file):
        # 检查是否已经在 datas 中
        already_included = any(src == backup_file for src, _ in datas)
        if not already_included:
            datas.append((backup_file, 'litellm'))
except Exception as e:
    print(f"Warning: Failed to add litellm backup file: {e}")