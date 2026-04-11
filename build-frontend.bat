@echo off
echo ========================================
echo Kwafoo Vue + TypeScript 前端构建脚本
echo ========================================
echo.

echo [1/3] 检查Node.js环境...
node --version
if errorlevel 1 (
    echo 错误: 未安装Node.js，请先安装Node.js
    pause
    exit /b 1
)
echo Node.js 环境正常
echo.

echo [2/3] 安装依赖...
cd web\frontend
call npm install
if errorlevel 1 (
    echo 错误: 依赖安装失败
    pause
    exit /b 1
)
echo 依赖安装完成
echo.

echo [3/3] 构建前端...
call npm run build
if errorlevel 1 (
    echo 错误: 前端构建失败
    pause
    exit /b 1
)
echo 前端构建完成
echo.

echo ========================================
echo 前端构建成功！
echo ========================================
echo 构建产物位置: web\dist\
echo.
echo 下一步：
echo 1. 运行根目录的 build.bat 进行完整打包
echo 2. 或直接运行 python main.py 启动开发服务器
echo ========================================
pause