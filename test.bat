@echo off
chcp 65001 >nul
echo ============================================================
echo Kwafoo 项目快速测试
echo ============================================================
echo.

echo 检查服务器状态...
curl -s http://localhost:8000/api/health >nul 2>&1
if errorlevel 1 (
    echo ✗ 服务器未运行，请先运行 start.bat
    pause
    exit /b 1
)

echo ✓ 服务器运行正常
echo.

echo 开始测试...
echo ============================================================
echo.

python test_quick.py

if errorlevel 1 (
    echo.
    echo ✗ 测试失败
    pause
    exit /b 1
) else (
    echo.
    echo ✓ 测试完成
    pause
)