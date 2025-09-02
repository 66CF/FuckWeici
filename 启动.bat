@echo off
:: 设置控制台编码为 UTF-8, 确保颜色和中文字符正确显示
chcp 65001 > nul
setlocal

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

python VictorApp.py