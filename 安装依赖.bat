@echo off
title ��װ uiautomator2 ����
echo ============================================
echo ��� Python �Ƿ�װ...
echo ============================================

:: ��� python �Ƿ����
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [����] δ��⵽ Python�����Ȱ�װ Python �����õ�����������
    pause
    exit /b 1
)

echo �Ѽ�⵽ Python��
python --version

echo.
echo ============================================
echo ��ʼ��װ uiautomator2 ...
echo ============================================

:: ʹ�� pip ��װ
python -m pip install --upgrade pip
python -m pip install -U uiautomator2

if %errorlevel% neq 0 (
    echo [����] uiautomator2 ��װʧ�ܣ�
    pause
    exit /b 1
)

echo.
echo ============================================
echo uiautomator2 ��װ��ɣ�
echo ============================================
pause
