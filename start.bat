@echo off
chcp 65001 >nul
echo ============================================================
echo Kwafoo 项目一键启动和测试
echo ============================================================
echo.

echo [1/3] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ✗ Python未安装或不在PATH中
    pause
    exit /b 1
)
echo ✓ Python环境正常
echo.

echo [2/3] 检查依赖...
pip show requests >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ✗ 依赖安装失败
        pause
        exit /b 1
    )
)
echo ✓ 依赖检查完成
echo.

echo [3/3] 启动服务器...
echo.
echo ============================================================
echo 服务器启动中，请稍候...
echo ============================================================
echo.
echo 服务器地址: http://localhost:8000
echo WebSocket地址: ws://localhost:8001
echo.
echo 按 Ctrl+C 可以停止服务器
echo.

python main.py

if errorlevel 1 (
    echo.
    echo ✗ 服务器启动失败
    pause
    exit /b 1
)