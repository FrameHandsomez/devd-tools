@echo off
chcp 65001 > nul
echo ========================================
echo   Building jr-dev.exe
echo ========================================
echo.

cd /d %~dp0..

echo [1/4] Closing running instances...
taskkill /F /IM jr-dev.exe /T >nul 2>&1

echo [2/4] Activating virtual environment...
call .venv\Scripts\activate.bat

echo [3/4] Running PyInstaller...
pyinstaller --clean --noconfirm jr-dev.spec

if errorlevel 1 (
    echo.
    echo ❌ Build failed!
    pause
    exit /b 1
)

echo.
echo [4/4] Build complete!
echo.
echo ========================================
echo   Output: dist\jr-dev.exe
echo ========================================
echo.
pause
