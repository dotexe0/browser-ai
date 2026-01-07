@echo off
REM Test the automation service

echo ========================================
echo Test Automation Service
echo ========================================
echo.

set SERVICE_EXE=build\bin\Release\automation_service.exe

if not exist "%SERVICE_EXE%" (
    echo ERROR: Service executable not found at:
    echo %SERVICE_EXE%
    echo.
    echo Please build the service first:
    echo   build.bat
    echo.
    pause
    exit /b 1
)

echo Testing service at: %SERVICE_EXE%
echo.

echo Test 1: Ping command
echo ----------------------
echo Sending: {"action":"ping"}
echo {"action":"ping"} | "%SERVICE_EXE%"
echo.

echo Test 2: Get capabilities
echo -------------------------
echo Sending: {"action":"get_capabilities"}
echo {"action":"get_capabilities"} | "%SERVICE_EXE%"
echo.

echo ========================================
echo If you see JSON responses above, the
echo service is working correctly!
echo ========================================
echo.

pause

