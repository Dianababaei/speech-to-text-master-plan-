@echo off
echo ============================================
echo Testing Speech-to-Text System
echo ============================================
echo.

set API_KEY=1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I
set API_URL=http://localhost:8080

echo [1/4] Testing file: 63148.mp3
echo.
curl -X POST "%API_URL%/jobs/" ^
  -H "X-API-Key: %API_KEY%" ^
  -F "audio_file=@C:\Users\digi kaj\Downloads\63148.mp3" ^
  -F "language=fa"

echo.
echo.
echo [2/4] Testing file: 63322.mp3
echo.
curl -X POST "%API_URL%/jobs/" ^
  -H "X-API-Key: %API_KEY%" ^
  -F "audio_file=@C:\Users\digi kaj\Downloads\63322.mp3" ^
  -F "language=fa"

echo.
echo.
echo [3/4] Waiting 60 seconds for processing...
timeout /t 60 /nobreak

echo.
echo [4/4] Checking transcription files...
echo.
dir transcriptions\*.txt

echo.
echo ============================================
echo Test completed! Check the transcriptions folder
echo Location: %cd%\transcriptions
echo ============================================
pause
