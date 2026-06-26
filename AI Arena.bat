@echo off
title AI Arena
echo.
echo    AI Arena - 启动中...
echo.

cd /d "%~dp0"

REM 检查 Electron
if not exist "node_modules\electron\dist\electron.exe" (
    echo    首次启动，安装 Electron...
    set ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/
    npm install electron --save-dev
)

REM 启动
echo    启动 AI Arena...
set ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/
npx electron .
