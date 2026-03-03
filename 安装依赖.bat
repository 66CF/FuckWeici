@echo off
setlocal
cd /d "%~dp0"
set "PATH=%PATH%;%LOCALAPPDATA%\Microsoft\WinGet\Links"
set "UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple"
set "PIP_INDEX_URL=%UV_INDEX_URL%"
set "PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn"

echo [INFO] Using CN mirror: %UV_INDEX_URL%

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

echo [INFO] Running uv sync with CN mirror...
uv sync
if errorlevel 1 (
    echo [ERROR] uv sync failed. Mirror used: %UV_INDEX_URL%
    echo [HINT] If this keeps failing, run:
    echo        set UV_INDEX_URL=%UV_INDEX_URL%
    echo        uv cache clean
    echo        uv sync -v
    pause
    exit /b 1
)

echo [SUCCESS] Dependencies installed.
pause
