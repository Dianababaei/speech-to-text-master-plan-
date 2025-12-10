@echo off
chcp 65001 >nul
echo ============================================
echo Testing Transcription with Persian Display
echo ============================================
echo.

set API_KEY=1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I

echo Uploading MP3 file...
echo.
curl -X POST "http://localhost:8080/jobs/" -H "X-API-Key: %API_KEY%" -F "audio_file=@C:\Users\digi kaj\Downloads\63218.mp3" -F "language=fa" > test_job.json

echo.
echo Job created:
type test_job.json
echo.
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
echo JSON Response (encoded):
type test_result.json
echo.
echo.

echo ============================================
echo Persian Text (from database):
echo ============================================
docker-compose exec db psql -U user -d transcription -c "SELECT transcription_text FROM jobs WHERE job_id = '%JOB_ID%';"
echo.
echo.

echo ============================================
echo Done!
echo ============================================
echo.

pause
