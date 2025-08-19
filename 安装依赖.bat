@echo off
title 安装 uiautomator2 依赖
echo ============================================
echo 检查 Python 是否安装...
echo ============================================

:: 检查 python 是否可用
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python 并配置到环境变量。
    pause
    exit /b 1
)

echo 已检测到 Python。
python --version

echo.
echo ============================================
echo 开始安装 uiautomator2 ...
echo ============================================

:: 使用 pip 安装
python -m pip install --upgrade pip
python -m pip install -U uiautomator2

if %errorlevel% neq 0 (
    echo [错误] uiautomator2 安装失败！
    pause
    exit /b 1
)

echo.
echo ============================================
echo uiautomator2 安装完成！
echo ============================================
pause
