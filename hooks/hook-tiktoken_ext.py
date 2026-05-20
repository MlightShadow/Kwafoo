"""
PyInstaller hook for tiktoken_ext
"""
from PyInstaller.utils.hooks import collect_submodules, collect_data_files
import os

# 收集所有子模块
hiddenimports = collect_submodules('tiktoken_ext')

# 收集所有数据文件
datas = collect_data_files('tiktoken_ext', include_py_files=False)

# 确保命名空间包被正确处理
try:
    import tiktoken_ext
    for path in tiktoken_ext.__path__:
        if os.path.exists(path):
            # 添加命名空间包的 __init__.py 文件
            init_file = os.path.join(path, '__init__.py')
            if os.path.exists(init_file):
                datas.append((init_file, 'tiktoken_ext'))
except Exception as e:
    print(f"Warning: Failed to process tiktoken_ext namespace package: {e}")