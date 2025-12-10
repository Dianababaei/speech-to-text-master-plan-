@echo off
echo ============================================
echo Testing Transcription Fix
echo ============================================
echo.

set API_KEY=1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I

echo Uploading MP3 file...
echo.
curl -X POST "http://localhost:8080/jobs/" -H "X-API-Key: %API_KEY%" -F "audio_file=@C:\Users\digi kaj\Downloads\63148.mp3" -F "language=fa" > test_job.json

echo.
echo Job created:
type test_job.json | python -m json.tool 2>nul || type test_job.json
echo.

echo Extracting job_id...
echo.
echo Please copy the job_id from above and paste it below:
set /p JOB_ID="Enter job_id: "
echo.
echo Using job_id: %JOB_ID%
echo.

echo Waiting 40 seconds for processing...
timeout /t 40 /nobreak

echo.
echo Checking result...
echo ============================================
curl "http://localhost:8080/jobs/%JOB_ID%" -H "X-API-Key: %API_KEY%" > test_result.json

echo.
type test_result.json | python -m json.tool 2>nul || type test_result.json
echo.
echo.

echo ============================================
echo If you see transcription text above, the fix worked!
echo ============================================
echo.

pause
