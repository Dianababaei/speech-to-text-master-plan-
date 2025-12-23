@echo off
echo ============================================
echo Audio Converter and Transcription Test
echo ============================================
echo.

echo This script will help you convert and test audio files.
echo.
echo OPTION 1: If you have FFmpeg installed
echo You can convert m4a to mp3 with this command:
echo   ffmpeg -i "C:\Users\digi kaj\Downloads\63322.m4a" "C:\Users\digi kaj\Downloads\63322.mp3"
echo.

echo OPTION 2: Convert online
echo Visit: https://cloudconvert.com/m4a-to-mp3
echo Or: https://online-audio-converter.com/
echo.

echo OPTION 3: Test with the current file anyway
echo (The system is working, but your m4a files may have incompatible codec)
echo.

set /p choice="Do you want to try uploading as MP3? (y/n): "
if /i "%choice%"=="y" (
    set /p mp3file="Enter path to MP3 file: "
    echo.
    echo Uploading...
    curl -X POST "http://127.0.0.1:8080/jobs/" -H "X-API-Key: 1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I" -F "audio_file=@%mp3file%" -F "language=fa" > temp_job.json
    echo.
    echo Job created! Response saved to temp_job.json
    type temp_job.json
    echo.
    echo.

    set /p job_id="Enter the job_id from above: "
    echo.
    echo Waiting 30 seconds for transcription...
    timeout /t 30 /nobreak
    echo.
    echo Checking status...
    curl "http://127.0.0.1:8080/jobs/%job_id%" -H "X-API-Key: 1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I"
    echo.
    echo.
)

pause
