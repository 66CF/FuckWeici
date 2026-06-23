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

    for /f "delims=" %%D in ('dir /s /b "%LOCALAPPDATA%\Microsoft\WinGet\Packages\*adb.exe" 2^>nul') do (
        set "ADB_DIR=%%~dpD"
        goto :found_adb
    )
    goto :adb_not_found_in_path

    :found_adb
    set "PATH=%PATH%;%ADB_DIR%"
    echo [INFO] adb found at: %ADB_DIR%

    echo %PATH% | findstr /I /C:"%ADB_DIR%" >nul 2>nul
    if errorlevel 1 (
        for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "USER_PATH=%%B"
        echo %USER_PATH% | findstr /I /C:"%ADB_DIR%" >nul 2>nul
        if errorlevel 1 (
            setx Path "%USER_PATH%;%ADB_DIR%"
            echo [INFO] adb path added to user PATH permanently.
        )
    )

    where adb >nul 2>nul
    if errorlevel 1 (
        goto :adb_not_found_in_path
    )
    goto :adb_done

    :adb_not_found_in_path
    echo [WARN] adb installed but not in PATH. You may need to restart your terminal.
    echo        If adb still doesn't work, add this to your system PATH:
    echo        %LOCALAPPDATA%\Microsoft\WinGet\Packages\Google.PlatformTools_Microsoft.Winget.Source_8wekyb3d8bbwe\platform-tools
)
:adb_done

where gum >nul 2>nul
if errorlevel 1 (
    echo [INFO] gum not found, trying to install via winget...
    where winget >nul 2>nul
    if errorlevel 1 (
        echo [ERROR] winget not found. Please install gum manually.
        pause
        exit /b 1
    )

    winget install --id=charmbracelet.gum -e --accept-package-agreements --accept-source-agreements
    if errorlevel 1 (
        echo [ERROR] Failed to install gum automatically.
        pause
        exit /b 1
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
