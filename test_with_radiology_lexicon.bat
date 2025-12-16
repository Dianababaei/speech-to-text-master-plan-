@echo off
echo ============================================
echo Testing with Radiology Lexicon
echo ============================================
echo.

set API_KEY=1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I
set API_URL=http://localhost:8080

echo [1/5] Testing file: 63148.mp3 (WITHOUT lexicon)
echo.
curl -X POST "%API_URL%/jobs/" ^
  -H "X-API-Key: %API_KEY%" ^
  -F "audio_file=@C:\Users\digi kaj\Downloads\63148.mp3" ^
  -F "language=fa"

echo.
echo.
echo [2/5] Testing file: 63148.mp3 (WITH radiology lexicon)
echo.
curl -X POST "%API_URL%/jobs/" ^
  -H "X-API-Key: %API_KEY%" ^
  -F "audio_file=@C:\Users\digi kaj\Downloads\63148.mp3" ^
  -F "language=fa" ^
  -F "lexicon_id=radiology"

echo.
echo.
echo [3/5] Testing file: 63322.mp3 (WITHOUT lexicon)
echo.
curl -X POST "%API_URL%/jobs/" ^
  -H "X-API-Key: %API_KEY%" ^
  -F "audio_file=@C:\Users\digi kaj\Downloads\63322.mp3" ^
  -F "language=fa"

echo.
echo.
echo [4/5] Testing file: 63322.mp3 (WITH radiology lexicon)
echo.
curl -X POST "%API_URL%/jobs/" ^
  -H "X-API-Key: %API_KEY%" ^
  -F "audio_file=@C:\Users\digi kaj\Downloads\63322.mp3" ^
  -F "language=fa" ^
  -F "lexicon_id=radiology"

echo.
echo.
echo [5/5] Waiting 90 seconds for processing...
timeout /t 90 /nobreak

echo.
echo Checking results in database...
docker-compose exec db psql -U user -d transcription -c "SELECT audio_filename, lexicon_version, LEFT(transcription_text, 80) as text_preview, created_at FROM jobs ORDER BY created_at DESC LIMIT 4;"

echo.
echo.
echo Checking transcription files...
dir transcriptions\*.txt

echo.
echo ============================================
echo Test Complete!
echo.
echo Compare transcriptions:
echo - WITHOUT lexicon: Basic transcription only
echo - WITH radiology lexicon: Medical terms translated
echo.
echo Check transcriptions folder for results
echo ============================================
pause
