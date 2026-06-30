@echo off
setlocal
cd /d "%~dp0"
set "PATH=%PATH%;%LOCALAPPDATA%\Microsoft\WinGet\Links"
set "UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple"
set "PIP_INDEX_URL=%UV_INDEX_URL%"
set "PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn"

echo [INFO] Using CN mirror: %UV_INDEX_URL%

rem ── 检查 winget ──
where winget >nul 2>nul
if errorlevel 1 (
    echo [ERROR] winget not found. Please install uv, adb, and gum manually.
    pause
    exit /b 1
)

rem ── 安装 uv ──
where uv >nul 2>nul
if errorlevel 1 (
    echo [INFO] uv not found, installing via winget...
    winget install --id=astral-sh.uv -e --accept-package-agreements --accept-source-agreements
    if errorlevel 1 (
        echo [ERROR] Failed to install uv.
        pause
        exit /b 1
    )
)

rem ── 安装 adb ──
where adb >nul 2>nul
if errorlevel 1 (
    echo [INFO] adb not found, installing Android Platform Tools via winget...
    winget install --id=Google.PlatformTools -e --accept-package-agreements --accept-source-agreements
    if errorlevel 1 (
        winget install --id=Google.AndroidSDK.PlatformTools -e --accept-package-agreements --accept-source-agreements
        if errorlevel 1 (
            echo [ERROR] Failed to install adb.
            pause
            exit /b 1
        )
    )
)

rem ── 补救 PATH（WinGet 安装后可能不在 PATH）──
where adb >nul 2>nul
if errorlevel 1 (
    for /f "delims=" %%D in ('dir /s /b "%LOCALAPPDATA%\Microsoft\WinGet\Packages\*adb.exe" 2^>nul') do (
        set "PATH=%PATH%;%%~dpD"
    )
    where adb >nul 2>nul
    if errorlevel 1 (
        echo [WARN] adb installed but not in PATH. You may need to restart your terminal.
    )
)

rem ── 安装 gum ──
where gum >nul 2>nul
if errorlevel 1 (
    echo [INFO] gum not found, installing via winget...
    winget install --id=charmbracelet.gum -e --accept-package-agreements --accept-source-agreements
    if errorlevel 1 (
        echo [ERROR] Failed to install gum.
        pause
        exit /b 1
    )
)

rem ── 补救 gum PATH ──
where gum >nul 2>nul
if errorlevel 1 (
    for /f "delims=" %%D in ('dir /s /b "%LOCALAPPDATA%\Microsoft\WinGet\Packages\*gum.exe" 2^>nul') do (
        set "PATH=%PATH%;%%~dpD"
    )
    where gum >nul 2>nul
    if errorlevel 1 (
        echo [WARN] gum installed but not in PATH. You may need to restart your terminal.
    )
)

rem ── 同步依赖 ──
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
