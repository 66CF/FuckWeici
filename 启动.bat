@echo off
setlocal
cd /d "%~dp0"
title VictorApp Launcher
cls
set "PATH=%PATH%;%LOCALAPPDATA%\Microsoft\WinGet\Links"

where adb >nul 2>nul
if errorlevel 1 (
    for /f "delims=" %%D in ('dir /s /b "%LOCALAPPDATA%\Microsoft\WinGet\Packages\*adb.exe" 2^>nul') do (
        set "PATH=%PATH%;%%~dpD"
    )
)

where adb >nul 2>nul
if errorlevel 1 (
    echo [WARN] adb not found. Run the dependency installer BAT first, or install Android Platform Tools.
)

where uv >nul 2>nul
if errorlevel 1 goto :uv_missing

where gum >nul 2>nul
if errorlevel 1 goto :gum_missing

set "UV_CACHE_DIR=%~dp0.tmp\uv-cache"
if not exist "%UV_CACHE_DIR%" mkdir "%UV_CACHE_DIR%" >nul 2>nul
set "UV_PYTHON_INSTALL_DIR=%~dp0.tmp\uv-python"
if not exist "%UV_PYTHON_INSTALL_DIR%" mkdir "%UV_PYTHON_INSTALL_DIR%" >nul 2>nul

uv run python main.py
if errorlevel 1 goto :run_fail
exit /b 0

:uv_missing
echo [ERROR] uv not found. Run the dependency installer BAT first.
pause
exit /b 1

:gum_missing
echo [ERROR] gum not found. Run the dependency installer BAT first.
pause
exit /b 1

:run_fail
echo.
echo [ERROR] App failed to start.
echo         Try running the dependency installer BAT, then retry.
pause
exit /b 1
