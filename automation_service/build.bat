@echo off
REM Build script for Browser AI Automation Service

echo ========================================
echo Browser AI Automation Service - Build
echo ========================================
echo.

REM Check for CMake
where cmake >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: CMake not found in PATH
    echo Please install CMake from: https://cmake.org/download/
    echo Or install via Visual Studio Installer
    exit /b 1
)

REM Check for Visual Studio
where cl.exe >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Visual Studio C++ compiler not found
    echo.
    echo Please install Visual Studio 2019 or later with:
    echo - Desktop development with C++
    echo - Windows 10/11 SDK
    echo.
    echo Or run this from a "Developer Command Prompt for VS"
    exit /b 1
)

REM Create build directory
if not exist build mkdir build
cd build

echo.
echo [1/3] Configuring with CMake...
cmake .. -G "Visual Studio 17 2022" -A x64
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: CMake configuration failed
    cd ..
    exit /b 1
)

echo.
echo [2/3] Building Release configuration...
cmake --build . --config Release
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Build failed
    cd ..
    exit /b 1
)

echo.
echo [3/3] Build complete!
echo.
echo Output: %CD%\bin\Release\automation_service.exe
echo Manifest: %CD%\bin\manifest.json
echo.

cd ..

echo ========================================
echo Build successful!
echo ========================================
echo.
echo Next steps:
echo 1. Test the service: build\bin\Release\automation_service.exe
echo 2. Register manifest: run register-manifest.bat
echo.

pause

