@echo off
echo.
echo ========================================
echo    Audio Transcription Tool - Additional Files
echo ========================================
echo.

REM Set audio file paths
set AUDIO1=C:\Users\digi kaj\Downloads\V.MG.73406.mp3
set AUDIO2=C:\Users\digi kaj\Downloads\V.CT.26445.mp3

echo [1/2] Uploading: V.MG.73406.m4a
echo.
curl -X POST "http://127.0.0.1:8080/jobs/" -H "X-API-Key: 1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I" -F "audio_file=@%AUDIO1%" -F "language=fa" > result_mg73406.json
echo.
echo Result saved to: result_mg73406.json
echo.

echo.
echo [2/2] Uploading: V.CT.26445.ogg
echo.
curl -X POST "http://127.0.0.1:8080/jobs/" -H "X-API-Key: 1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I" -F "audio_file=@%AUDIO2%" -F "language=fa" > result_ct26445.json
echo.
echo Result saved to: result_ct26445.json
echo.

echo.
echo ========================================
echo Both files submitted for transcription!
echo ========================================
echo.
echo The transcription process will take a few minutes.
echo Results will appear in the 'transcriptions' folder as:
echo   - V.MG.73406.txt
echo   - V.CT.26445.txt
echo.
echo You can check the transcriptions folder or run check_status.bat
echo.
pause
