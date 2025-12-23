@echo off
echo ============================================
echo System Status Check
echo ============================================
echo.

echo [1] Checking Docker...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker not found! Please install Docker Desktop.
    goto end
) else (
    echo ✅ Docker installed
)

echo.
echo [2] Checking Docker services...
docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker not running! Please start Docker Desktop.
    goto end
) else (
    echo ✅ Docker running
)

echo.
echo [3] Checking containers...
docker-compose ps

echo.
echo [4] Checking API health...
curl -s http://127.0.0.1:8080/ >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ API not responding
    echo    Try: docker-compose restart web
) else (
    echo ✅ API responding
    curl -s http://127.0.0.1:8080/
)

echo.
echo [5] Checking transcriptions folder...
if exist "transcriptions" (
    echo ✅ Transcriptions folder exists
    echo    Files:
    dir /b transcriptions\*.txt 2>nul
) else (
    echo ⚠️  Transcriptions folder not found (will be created automatically)
)

echo.
echo ============================================
echo Status check complete!
echo ============================================
echo.
echo Quick commands:
echo   Start services:  docker-compose up -d
echo   View logs:       docker-compose logs --tail=20
echo   Test system:     test_both_audios.bat
echo   Full guide:      TESTING_GUIDE.md
echo.
pause

:end
