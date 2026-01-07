@echo off
REM Start Ollama service

echo ========================================
echo Starting Ollama Service
echo ========================================
echo.
echo This will start Ollama in the background.
echo Keep this window open while using Ollama.
echo.
echo Press Ctrl+C to stop Ollama
echo ========================================
echo.

REM Check if ollama command exists
where ollama >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR - Ollama not found!
    echo.
    echo Please install Ollama from https://ollama.ai
    echo.
    pause
    exit /b 1
)

echo Starting Ollama...
echo.

ollama serve

