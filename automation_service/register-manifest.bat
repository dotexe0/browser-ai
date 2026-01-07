@echo off
REM Register Native Messaging manifest for Browser AI Automation Service

echo ========================================
echo Register Native Messaging Manifest
echo ========================================
echo.

REM Get absolute path to manifest
set SCRIPT_DIR=%~dp0
set MANIFEST_PATH=%SCRIPT_DIR%build\bin\manifest.json

REM Check if manifest exists
if not exist "%MANIFEST_PATH%" (
    echo ERROR: Manifest not found at:
    echo %MANIFEST_PATH%
    echo.
    echo Please build the service first:
    echo   build.bat
    echo.
    pause
    exit /b 1
)

echo Manifest location: %MANIFEST_PATH%
echo.

REM Create registry key
echo Creating registry key...
reg add "HKCU\Software\Google\Chrome\NativeMessagingHosts\com.browser_ai.automation" /ve /t REG_SZ /d "%MANIFEST_PATH%" /f

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo SUCCESS! Manifest registered
    echo ========================================
    echo.
    echo The automation service is now registered with Chrome.
    echo.
    echo To verify:
    echo 1. Open Registry Editor
    echo 2. Navigate to: HKCU\Software\Google\Chrome\NativeMessagingHosts\com.browser_ai.automation
    echo 3. Check that the path points to: %MANIFEST_PATH%
    echo.
) else (
    echo.
    echo ERROR: Failed to register manifest
    echo Make sure you have permission to modify the registry
    echo.
)

pause

