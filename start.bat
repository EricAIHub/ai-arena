@echo off
echo ========================================
echo    AI Arena - 多 AI 对战平台
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

REM 检查依赖
echo [1/3] 检查依赖...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo [2/3] 安装依赖...
    pip install -r requirements.txt
) else (
    echo [2/3] 依赖已安装
)

REM 启动服务
echo [3/3] 启动 AI Arena...
echo.
echo 访问地址: http://localhost:8000
echo 按 Ctrl+C 停止
echo.

start http://localhost:8000
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
