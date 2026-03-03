@echo off
setlocal
cd /d "%~dp0"
set "PATH=%PATH%;%LOCALAPPDATA%\Microsoft\WinGet\Links"

where uv >nul 2>nul
if errorlevel 1 (
    echo [INFO] uv not found, trying to install via winget...
    where winget >nul 2>nul
    if errorlevel 1 (
        echo [ERROR] winget not found. Please install uv manually.
        pause
        exit /b 1
    )
    winget install --id=astral-sh.uv -e --accept-package-agreements --accept-source-agreements
    if errorlevel 1 (
        echo [ERROR] Failed to install uv automatically.
        pause
        exit /b 1
    )
)

where adb >nul 2>nul
if errorlevel 1 (
    echo [INFO] adb not found, trying to install Android Platform Tools via winget...
    where winget >nul 2>nul
    if errorlevel 1 (
        echo [ERROR] winget not found. Please install adb manually.
        pause
        exit /b 1
    )

    winget install --id=Google.PlatformTools -e --accept-package-agreements --accept-source-agreements
    if errorlevel 1 (
        winget install --id=Google.AndroidSDK.PlatformTools -e --accept-package-agreements --accept-source-agreements
        if errorlevel 1 (
            echo [ERROR] Failed to install adb automatically.
            pause
            exit /b 1
        )
    )
)

uv sync
if errorlevel 1 (
    echo [ERROR] uv sync failed.
    pause
    exit /b 1
)

echo [SUCCESS] Dependencies installed.
pause
