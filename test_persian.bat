@echo off
echo ============================================
echo Speech-to-Text Persian Test Script
echo ============================================
echo.

set API_KEY=1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I
set /p AUDIO_FILE="Enter full path to your audio file: "

echo.
echo Step 1: Uploading audio file...
echo ============================================
curl -X POST "http://localhost:8080/jobs" -H "X-API-Key: %API_KEY%" -F "audio_file=@%AUDIO_FILE%" -F "language=fa" > temp_response.json

echo.
echo Response saved to temp_response.json
type temp_response.json
echo.

echo.
echo Step 2: Extract job_id and check status...
echo ============================================
set /p JOB_ID="Enter the job_id from above response: "

echo.
echo Checking job status...
curl "http://localhost:8080/jobs/%JOB_ID%" -H "X-API-Key: %API_KEY%"

echo.
echo.
echo ============================================
echo To check status again, run:
echo curl "http://localhost:8080/jobs/%JOB_ID%" -H "X-API-Key: %API_KEY%"
echo ============================================
pause
