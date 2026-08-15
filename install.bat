@echo off
setlocal enabledelayedexpansion

echo =======================================================
echo          DeepWiki CLI - 1-Click Installer
echo =======================================================
echo.

:: Check for Python
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python was not found in PATH!
    echo Please install Python 3.9+ and ensure "Add Python to PATH" is checked.
    pause
    exit /b 1
)

echo [1/2] Installing DeepWiki CLI and dependencies...
python -m pip install -e .
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install deepwiki package.
    pause
    exit /b 1
)

echo.
echo [2/2] Installing Playwright Chromium browser...
python -m playwright install chromium
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Playwright Chromium installation encountered an issue.
)

echo.
echo =======================================================
echo  SUCCESS! DeepWiki CLI is installed.
echo =======================================================
echo.
echo You can now run 'deepwiki' from any terminal:
echo.
echo   deepwiki https://github.com/microsoft/vscode
echo   deepwiki microsoft/vscode -c 10
echo   deepwiki --help
echo.
pause
