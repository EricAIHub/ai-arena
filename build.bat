@echo off
title AI Arena - 打包程序
echo.
echo ========================================
echo   AI Arena 打包程序 v0.2.0
echo ========================================
echo.

:: 切换到项目目录
cd /d "%~dp0"

echo [1/5] 检查 Python...
python --version
if errorlevel 1 (
    echo [X] 需要 Python 3.10+
    pause
    exit /b 1
)

echo.
echo [2/5] 检查 Node.js...
node --version
if errorlevel 1 (
    echo [X] 需要 Node.js 18+
    pause
    exit /b 1
)

echo.
echo [3/5] 安装 PyInstaller...
pip install pyinstaller --quiet
if errorlevel 1 (
    echo [X] PyInstaller 安装失败
    pause
    exit /b 1
)

echo.
echo [4/5] 打包 Python 后端...
echo   正在运行 PyInstaller...
pyinstaller ai-arena.spec --distpath dist --workpath build --clean -y
if errorlevel 1 (
    echo [X] Python 后端打包失败
    pause
    exit /b 1
)
echo   Python 后端打包完成！

echo.
echo [5/5] 打包 Electron 安装包...
echo   正在运行 electron-builder...
:: 设置镜像源（国内网络优化）
set ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/
set ELECTRON_BUILDER_BINARIES_MIRROR=https://npmmirror.com/mirrors/electron-builder-binaries/
npm run build:app
if errorlevel 1 (
    echo [X] Electron 打包失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo   [OK] 打包完成！
echo ========================================
echo.
echo   安装包位置: release\AI Arena Setup 0.2.0.exe
echo.
echo   打包产物:
echo     - Python 后端: dist\AI Arena Server\
echo     - 安装程序:   release\
echo.
pause
