@echo off
REM Setup script for Backend AI Proxy Server

echo ========================================
echo Backend AI Proxy - Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    echo.
    echo Please install Python 3.8+ from:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo [1/3] Installing Python dependencies...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [2/3] Checking for .env file...
if not exist .env (
    echo .env not found, creating from template...
    copy env-template.txt .env
    echo.
    echo IMPORTANT - Edit .env and add your API keys!
    echo.
    echo For OpenAI -
    echo   1. Get key from https://platform.openai.com/api-keys
    echo   2. Edit .env and set OPENAI_API_KEY=sk-your-key-here
    echo.
    echo For Ollama ^(local, private, FREE!^) -
    echo   1. Download from https://ollama.ai
    echo   2. Run ollama pull llava
    echo   3. No API key needed!
    echo.
) else (
    echo .env file already exists
)

echo.
echo [3/3] Setup complete!
echo ========================================
echo.
echo Next steps -
echo.
echo 1. Choose your AI provider -
echo.
echo    Option A - OpenAI ^(cloud, fast, ~$0.03/request^)
echo      - Edit .env and add OPENAI_API_KEY=sk-...
echo.
echo    Option B - Ollama ^(local, private, FREE!^)
echo      - Install from https://ollama.ai
echo      - Run ollama pull llava
echo.
echo    Option C - Both ^(recommended!^)
echo      - Set up both and switch in the browser UI
echo.
echo 2. Start the backend server -
echo      python server.py
echo.
echo 3. Test it works -
echo      python test_backend.py
echo.
echo ========================================
pause

