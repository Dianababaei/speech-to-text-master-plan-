@echo off
echo ============================================
echo Speech-to-Text Transcription Test
echo ============================================
echo.

set API_KEY=1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I

echo Step 1: Convert your M4A file to MP3
echo ============================================
echo.
echo OPTION 1 - Online Converter (Easiest):
echo   1. Open browser and go to: https://cloudconvert.com/m4a-to-mp3
echo   2. Upload: C:\Users\digi kaj\Downloads\63322.m4a
echo   3. Click Convert and Download
echo   4. Save as: C:\Users\digi kaj\Downloads\63322.mp3
echo.
echo OPTION 2 - Using FFmpeg (if installed):
echo   ffmpeg -i "C:\Users\digi kaj\Downloads\63322.m4a" "C:\Users\digi kaj\Downloads\63322.mp3"
echo.
echo ============================================
pause
echo.

echo Step 2: Upload MP3 file for transcription
echo ============================================
set /p MP3_FILE="Enter full path to your MP3 file (or press Enter for default): "

if "%MP3_FILE%"=="" (
    set MP3_FILE=C:\Users\digi kaj\Downloads\63322.mp3
)

echo.
echo Uploading: %MP3_FILE%
echo Please wait...
echo.

curl -X POST "http://localhost:8080/jobs/" -H "X-API-Key: %API_KEY%" -F "audio_file=@%MP3_FILE%" -F "language=fa" > job_response.json
echo.
echo Response saved to job_response.json
echo.
type job_response.json
echo.
echo.

echo Step 3: Extract job ID and check status
echo ============================================
set /p JOB_ID="Copy and paste the job_id from above: "

echo.
echo Waiting 40 seconds for transcription to complete...
echo.
timeout /t 40 /nobreak

echo.
echo Fetching transcription result...
echo ============================================
curl "http://localhost:8080/jobs/%JOB_ID%" -H "X-API-Key: %API_KEY%" > result.json

echo.
echo Result saved to result.json
echo.
type result.json | python -m json.tool 2>nul || type result.json
echo.
echo.

echo ============================================
echo Done!
echo ============================================
echo.
echo If status is "completed":
echo   - Look for "original_text" field above - that's your Persian transcription!
echo.
echo If status is "processing":
echo   - Run this command again in 20 seconds:
echo   curl "http://localhost:8080/jobs/%JOB_ID%" -H "X-API-Key: %API_KEY%"
echo.
echo If status is "failed":
echo   - Check the "error_message" field for details
echo.

pause
