@echo off
title AI Arena - 安装程序
color 0A

echo.
echo    ╔══════════════════════════════════════╗
echo    ║     AI Arena 安装程序 v0.1.0        ║
echo    ╚══════════════════════════════════════╝
echo.

REM 检查 Python
echo    [1/4] 检查 Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo    ❌ 未找到 Python！
    echo.
    echo    请先安装 Python 3.10+：
    echo    https://www.python.org/downloads/
    echo.
    echo    安装时请勾选 "Add Python to PATH"
    echo.
    pause
    start https://www.python.org/downloads/
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo    ✅ %PYVER%

REM 安装依赖
echo.
echo    [2/4] 安装 Python 依赖...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo    ⚠️ 部分依赖安装失败，尝试继续...
) else (
    echo    ✅ 依赖安装完成
)

REM 创建桌面快捷方式
echo.
echo    [3/4] 创建桌面快捷方式...
set SCRIPT_DIR=%~dp0
set DESKTOP=%USERPROFILE%\Desktop

(
echo [InternetShortcut]
echo URL=file:///%SCRIPT_DIR:~0,-1%/AI Arena.bat
echo IconFile=%SCRIPT_DIR:~0,-1%\static\icon.ico
echo IconIndex=0
) > "%DESKTOP%\AI Arena.url" 2>nul

if exist "%DESKTOP%\AI Arena.url" (
    echo    ✅ 桌面快捷方式已创建
) else (
    echo    ⚠️ 快捷方式创建失败（不影响使用）
)

REM 完成
echo.
echo    [4/4] 安装完成！
echo.
echo    ══════════════════════════════════════
echo    启动方式：
echo      1. 双击 "AI Arena.bat"
echo      2. 或双击桌面的 "AI Arena" 快捷方式
echo.
echo    首次使用：
echo      1. 启动后浏览器会自动打开
echo      2. 在"配置"页面添加你的 AI API Key
echo      3. 选择场景，开始对战！
echo    ══════════════════════════════════════
echo.
pause
