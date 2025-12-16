@echo off
echo ============================================
echo Testing Lexicon + Post-Processing Pipeline
echo ============================================
echo.

set API_KEY=1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I
set ADMIN_KEY=A-R_BZ52dg1C9yymHj9566gGMjFCVaaqe0Nis9FX1QU
set API_URL=http://localhost:8080

echo [Step 1] Checking Radiology Lexicon in Database
echo.
docker-compose exec db psql -U user -d transcription -c "SELECT DISTINCT lexicon_id, COUNT(*) as term_count FROM lexicon_terms WHERE is_active = true GROUP BY lexicon_id;"

echo.
echo.
echo [Step 2] Sample Radiology Terms
echo.
docker-compose exec db psql -U user -d transcription -c "SELECT term, replacement FROM lexicon_terms WHERE lexicon_id = 'radiology' AND is_active = true LIMIT 10;"

echo.
echo.
echo [Step 3] Testing WITHOUT Lexicon
echo (Basic post-processing only)
echo.
curl -X POST "%API_URL%/jobs/" ^
  -H "X-API-Key: %API_KEY%" ^
  -F "audio_file=@C:\Users\digi kaj\Downloads\63322.mp3" ^
  -F "language=fa"

echo.
echo.
echo [Step 4] Testing WITH Radiology Lexicon
echo (Full post-processing with term replacements)
echo.
curl -X POST "%API_URL%/jobs/" ^
  -H "X-API-Key: %API_KEY%" ^
  -F "audio_file=@C:\Users\digi kaj\Downloads\63322.mp3" ^
  -F "language=fa" ^
  -F "lexicon_id=radiology"

echo.
echo.
echo [Step 5] Waiting 90 seconds for processing...
timeout /t 90 /nobreak

echo.
echo [Step 6] Comparing Results
echo.
echo Checking database for original vs processed text...
docker-compose exec db psql -U user -d transcription -c "SELECT audio_filename, lexicon_version, LEFT(transcription_text, 80) as original, created_at FROM jobs ORDER BY created_at DESC LIMIT 2;"

echo.
echo.
echo [Step 7] Checking Text Files
echo.
dir transcriptions\*.txt

echo.
echo ============================================
echo Test Complete!
echo.
echo Compare the two transcriptions:
echo 1. Without lexicon: Basic cleanup only
echo 2. With 'radiology' lexicon: Medical terms replaced
echo.
echo Check: transcriptions\ folder for .txt files
echo ============================================
pause
