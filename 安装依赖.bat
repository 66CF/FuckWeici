@echo off
chcp 65001 > nul
title VictorApp Dependency Installer
setlocal
cd /d "%~dp0"

echo [INFO] 正在检查 uv 环境...
uv --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 未在系统中找到 uv。请先安装 uv: https://docs.astral.sh/uv/getting-started/installation/
    pause
    exit /b 1
)

echo [INFO] 找到 uv，正在准备 Python 3.12 与虚拟环境...
set UV_DEFAULT_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple
uv python install 3.12
if %errorlevel% neq 0 (
    echo [ERROR] Python 3.12 安装失败，请检查网络或重试。
    pause
    exit /b 1
)

uv sync
if %errorlevel% neq 0 (
    echo [ERROR] 依赖同步失败，请根据上面的报错信息排查。
    pause
    exit /b 1
)

echo [INFO] 首次使用建议执行设备初始化: uv run python -m uiautomator2 init

echo.
echo [SUCCESS] 依赖安装完成!
pause
