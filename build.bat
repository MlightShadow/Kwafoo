@echo off
echo ========================================
echo Kwafoo 新闻聚合系统 - 完整构建脚本
echo ========================================
echo.

echo [1/5] 检查Node.js环境...
node --version
if errorlevel 1 (
    echo 警告: 未安装Node.js，跳过前端构建
    echo 提示: 如需构建Vue前端，请先安装Node.js
    set SKIP_FRONTEND=1
) else (
    echo Node.js 环境正常
    set SKIP_FRONTEND=0
)
echo.

if "%SKIP_FRONTEND%"=="0" (
    echo [2/5] 构建Vue前端...
    cd web\frontend
    call npm install
    if errorlevel 1 (
        echo 错误: 前端依赖安装失败
        pause
        exit /b 1
    )
    call npm run build
    if errorlevel 1 (
        echo 错误: 前端构建失败
        pause
        exit /b 1
    )
    cd ..\..
    echo 前端构建完成
    echo.
) else (
    echo [2/5] 跳过前端构建
    echo.
)

echo [3/5] 检查Python依赖...
python -m pip install pyinstaller --quiet
if errorlevel 1 (
    echo 错误: PyInstaller 安装失败
    pause
    exit /b 1
)
echo PyInstaller 安装完成
echo.

echo [4/5] 清理旧的打包文件...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
echo 清理完成
echo.

echo [5/5] 开始打包...
pyinstaller kwafoo.spec --clean
if errorlevel 1 (
    echo 错误: 打包失败
    pause
    exit /b 1
)
echo 打包完成
echo.

echo ========================================
echo 构建完成！
echo ========================================
echo 可执行文件位置: dist\kwafoo\kwafoo.exe
echo.
echo 使用说明:
echo 1. 将整个 dist\kwafoo 文件夹复制到目标位置
echo 2. 双击 kwafoo.exe 启动系统
echo 3. 访问 http://localhost:8000 使用Web界面
echo 4. 可以通过 config.toml 修改配置
echo ========================================
pause