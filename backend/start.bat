@echo off
REM Start the Backend AI Proxy Server

echo ========================================
echo Backend AI Proxy - Starting Server
echo ========================================
echo.

REM Check if dependencies are installed
python -c "import flask" 2>nul
if %errorlevel% neq 0 (
    echo ERROR - Dependencies not installed!
    echo.
    echo Run setup.bat first -
    echo   setup.bat
    echo.
    pause
    exit /b 1
)

REM Check if .env exists
if not exist .env (
    echo WARNING - No .env file found!
    echo.
    echo Creating from template...
    copy env-template.txt .env
    echo.
    echo IMPORTANT - Edit .env and add your API keys before using!
    echo.
)

echo Starting server on http://localhost:5000
echo.
echo Press Ctrl+C to stop
echo ========================================
echo.

python server.py

