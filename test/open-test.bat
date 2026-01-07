@echo off
REM Open the Layer 1 test page in default browser

echo ========================================
echo Opening Layer 1 Test Page
echo ========================================
echo.

REM Check if server is running
echo Checking if test server is running...
curl -s http://localhost:8000/test/ >nul 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo WARNING: Test server doesn't appear to be running!
    echo.
    echo Please start it first:
    echo   cd test
    echo   python -m http.server 8000
    echo.
    echo Or run: run-test-server.sh
    echo.
    pause
    exit /b 1
)

echo Test server is running!
echo.
echo Opening test page in your default browser...
echo URL: http://localhost:8000/test/layer1-test.html
echo.

REM Open in default browser
start http://localhost:8000/test/layer1-test.html

echo.
echo ========================================
echo Test page should now be open!
echo ========================================
echo.
echo What you should see:
echo - Tests running automatically
echo - Green checkmarks for passing tests
echo - Interactive AI Panel demo
echo.
echo Try:
echo 1. Click the Settings gear icon
echo 2. Select different AI providers
echo 3. Enter a prompt in the text box
echo 4. Explore the UI components
echo.
echo All tests should pass (30+)!
echo.

pause

