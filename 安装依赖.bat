@echo off
chcp 65001 > nul
title VictorApp Dependency Installer

echo [INFO] 正在检查 Python 环境...
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 未在系统中找到 Python。请先安装 Python 3 并将其添加到系统 PATH。
    pause
    exit
)

echo [INFO] 找到 Python, 开始从 requirements.txt 安装依赖...
echo [INFO] 使用清华大学镜像源加速下载...

pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

echo.
echo [SUCCESS] 依赖安装完成!
pause