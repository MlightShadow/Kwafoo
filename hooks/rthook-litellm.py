"""
Runtime hook for litellm to fix importlib.resources issues
"""
import sys
import os

# 强制 litellm 使用本地备份文件
os.environ['LITELLM_LOCAL_MODEL_COST_MAP'] = 'true'

# 在导入 litellm 之前，确保资源文件可以被正确访问
def fix_litellm_resources():
    try:
        import importlib.resources as resources
        
        # 保存原始的 files 函数
        original_files = resources.files
        
        def patched_files(package):
            try:
                return original_files(package)
            except Exception as e:
                # 如果原始函数失败，尝试使用 PyInstaller 的临时目录
                if hasattr(sys, '_MEIPASS'):
                    # 在 PyInstaller 打包的应用中，资源文件应该位于 sys._MEIPASS 中
                    import pathlib
                    package_path = pathlib.Path(sys._MEIPASS) / package
                    if package_path.exists():
                        # 创建一个简单的 Traversable 对象
                        from importlib.readers import MultiplexedPath
                        return MultiplexedPath(package_path)
                raise
        
        # 替换 files 函数
        resources.files = patched_files
        
        # 修复 pathlib.Path.read_text 方法
        import pathlib
        original_read_text = pathlib.Path.read_text
        
        def patched_read_text(self, encoding=None, errors=None):
            try:
                return original_read_text(self, encoding=encoding, errors=errors)
            except Exception as e:
                # 如果原始方法失败，尝试使用 PyInstaller 的临时目录
                if hasattr(sys, '_MEIPASS'):
                    # 检查是否是 litellm 的资源文件
                    if 'litellm' in str(self) and 'model_prices_and_context_window_backup.json' in str(self):
                        # 尝试从 sys._MEIPASS 中读取文件
                        meipass_path = pathlib.Path(sys._MEIPASS) / 'litellm' / 'model_prices_and_context_window_backup.json'
                        if meipass_path.exists():
                            return meipass_path.read_text(encoding=encoding or 'utf-8', errors=errors)
                raise
        
        pathlib.Path.read_text = patched_read_text
        
    except Exception as e:
        print(f"Warning: Failed to patch importlib.resources: {e}")

fix_litellm_resources()