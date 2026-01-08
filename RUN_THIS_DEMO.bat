@echo off
REM ========================================
REM SIMPLE AUTOMATION DEMO
REM ========================================
REM
REM This opens Notepad and types text.
REM Watch your screen to see it happen!
REM ========================================

cd /d "%~dp0"

echo.
echo ========================================
echo SIMPLE AUTOMATION DEMO
echo ========================================
echo.
echo This will:
echo   1. Press Win+R to open Run dialog
echo   2. Type "notepad" and press Enter
echo   3. Wait for Notepad to open
echo   4. Type a message
echo.
echo You should SEE this happen on your screen!
echo.

pause

python test\demo_automation.py

pause

