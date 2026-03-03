@echo off
:: 设置控制台编码为 UTF-8, 确保颜色和中文字符正确显示
chcp 65001 > nul
setlocal
cd /d "%~dp0"

:: 设置窗口标题
title VictorApp Launcher

:: 清理屏幕
cls

:: 显示欢迎横幅
echo.
echo   _   ___     __           ___           
echo  ^| ^| / (_)___/ /____  ____/ _ ^| ___  ___ 
echo  ^| ^|/ / / __/ __/ _ \/ __/ __ ^|/ _ \/ _ \
echo  ^|___/_/\__/\__/\___/_/ /_/ ^|_/ .__/ .__/
echo                              /_/  /_/    
echo.

uv --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 未找到 uv，请先运行安装依赖.bat 或先安装 uv。
    pause
    exit /b 1
)

uv run python VictorApp.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] 启动失败。可先执行安装依赖.bat 或运行: uv sync
    pause
    exit /b 1
)
