@echo off
echo.
echo ========================================
echo    Audio Transcription Tool
echo ========================================
echo.

REM Set audio file paths
set AUDIO1=C:\Users\digi kaj\Downloads\V.DX.62268.mp3
set AUDIO2=C:\Users\digi kaj\Downloads\V.CT.52622.mp3

echo Uploading first audio: V.DX.62268.mp3
echo.
curl -X POST "http://127.0.0.1:8080/jobs/" -H "X-API-Key: 1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I" -F "audio_file=@%AUDIO1%" -F "language=fa" > result1.json
echo.
echo Result saved to: result1.json
echo.

timeout /t 120 /nobreak
echo.

echo Uploading second audio: V.CT.52622.mp3
echo.
curl -X POST "http://127.0.0.1:8080/jobs/" -H "X-API-Key: 1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I" -F "audio_file=@%AUDIO2%" -F "language=fa" > result2.json
echo.
echo Result saved to: result2.json
echo.

pause
