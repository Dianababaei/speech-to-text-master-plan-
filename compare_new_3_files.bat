@echo off
setlocal enabledelayedexpansion

echo ============================================
echo LANGUAGE MODE COMPARISON - 3 NEW FILES
echo Testing: language=fa vs language=None (auto-detect)
echo ============================================
echo.

set API_KEY=1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I
set API_URL=http://127.0.0.1:8080

echo Files to test:
echo   1. V.CT.26413.mp3
echo   2. V.MG.73398.mp3
echo   3. V.MG.73400.mp3
echo.
echo Each file will be processed TWICE:
echo   - With language=fa (Persian mode)
echo   - With language=None (Auto-detect mode)
echo.
echo Total: 6 jobs
echo Expected wait time: ~90 seconds
echo.
pause

REM ============================================
REM SUBMIT JOBS - PERSIAN MODE (language=fa)
REM ============================================

echo.
echo ============================================
echo PHASE 1: Submitting with language=fa
echo ============================================
echo.

echo [1/6] V.CT.26413.mp3 [language=fa]
curl -X POST "%API_URL%/jobs/" -H "X-API-Key: %API_KEY%" -F "audio_file=@C:\Users\digi kaj\Downloads\V.CT.26413.mp3" -F "language=fa" -o job_fa_1.json
powershell -Command "(Get-Content job_fa_1.json | ConvertFrom-Json).job_id" > job_fa_1_id.txt
set /p JOB_FA_1=<job_fa_1_id.txt
echo Job ID: %JOB_FA_1%
echo.

echo [2/6] V.MG.73398.mp3 [language=fa]
curl -X POST "%API_URL%/jobs/" -H "X-API-Key: %API_KEY%" -F "audio_file=@C:\Users\digi kaj\Downloads\V.MG.73398.mp3" -F "language=fa" -o job_fa_2.json
powershell -Command "(Get-Content job_fa_2.json | ConvertFrom-Json).job_id" > job_fa_2_id.txt
set /p JOB_FA_2=<job_fa_2_id.txt
echo Job ID: %JOB_FA_2%
echo.

echo [3/6] V.MG.73400.mp3 [language=fa]
curl -X POST "%API_URL%/jobs/" -H "X-API-Key: %API_KEY%" -F "audio_file=@C:\Users\digi kaj\Downloads\V.MG.73400.mp3" -F "language=fa" -o job_fa_3.json
powershell -Command "(Get-Content job_fa_3.json | ConvertFrom-Json).job_id" > job_fa_3_id.txt
set /p JOB_FA_3=<job_fa_3_id.txt
echo Job ID: %JOB_FA_3%
echo.

REM ============================================
REM SUBMIT JOBS - AUTO-DETECT MODE (language=None)
REM ============================================

echo.
echo ============================================
echo PHASE 2: Submitting with language=None (auto-detect)
echo ============================================
echo.

echo [4/6] V.CT.26413.mp3 [language=None]
curl -X POST "%API_URL%/jobs/" -H "X-API-Key: %API_KEY%" -F "audio_file=@C:\Users\digi kaj\Downloads\V.CT.26413.mp3" -o job_auto_1.json
powershell -Command "(Get-Content job_auto_1.json | ConvertFrom-Json).job_id" > job_auto_1_id.txt
set /p JOB_AUTO_1=<job_auto_1_id.txt
echo Job ID: %JOB_AUTO_1%
echo.

echo [5/6] V.MG.73398.mp3 [language=None]
curl -X POST "%API_URL%/jobs/" -H "X-API-Key: %API_KEY%" -F "audio_file=@C:\Users\digi kaj\Downloads\V.MG.73398.mp3" -o job_auto_2.json
powershell -Command "(Get-Content job_auto_2.json | ConvertFrom-Json).job_id" > job_auto_2_id.txt
set /p JOB_AUTO_2=<job_auto_2_id.txt
echo Job ID: %JOB_AUTO_2%
echo.

echo [6/6] V.MG.73400.mp3 [language=None]
curl -X POST "%API_URL%/jobs/" -H "X-API-Key: %API_KEY%" -F "audio_file=@C:\Users\digi kaj\Downloads\V.MG.73400.mp3" -o job_auto_3.json
powershell -Command "(Get-Content job_auto_3.json | ConvertFrom-Json).job_id" > job_auto_3_id.txt
set /p JOB_AUTO_3=<job_auto_3_id.txt
echo Job ID: %JOB_AUTO_3%
echo.

REM ============================================
REM WAIT FOR PROCESSING
REM ============================================

echo.
echo ============================================
echo All 6 jobs submitted!
echo Waiting 90 seconds for processing...
echo ============================================
timeout /t 90 /nobreak

REM ============================================
REM RETRIEVE ALL RESULTS
REM ============================================

echo.
echo ============================================
echo Retrieving results...
echo ============================================
echo.

REM Persian mode results
curl -X GET "%API_URL%/jobs/%JOB_FA_1%" -H "X-API-Key: %API_KEY%" -o result_fa_1.json
curl -X GET "%API_URL%/jobs/%JOB_FA_2%" -H "X-API-Key: %API_KEY%" -o result_fa_2.json
curl -X GET "%API_URL%/jobs/%JOB_FA_3%" -H "X-API-Key: %API_KEY%" -o result_fa_3.json

REM Auto-detect mode results
curl -X GET "%API_URL%/jobs/%JOB_AUTO_1%" -H "X-API-Key: %API_KEY%" -o result_auto_1.json
curl -X GET "%API_URL%/jobs/%JOB_AUTO_2%" -H "X-API-Key: %API_KEY%" -o result_auto_2.json
curl -X GET "%API_URL%/jobs/%JOB_AUTO_3%" -H "X-API-Key: %API_KEY%" -o result_auto_3.json

echo All results retrieved!
echo.

REM ============================================
REM SAVE TO FILES
REM ============================================

echo Saving transcriptions to comparison_results\...
if not exist "comparison_results" mkdir comparison_results

REM File 1 - V.CT.26413.mp3
powershell -Command "$json = Get-Content result_fa_1.json -Encoding UTF8 | ConvertFrom-Json; [System.IO.File]::WriteAllText('comparison_results\V.CT.26413_FA_processed.txt', $json.processed_text, [System.Text.Encoding]::UTF8)"
powershell -Command "$json = Get-Content result_auto_1.json -Encoding UTF8 | ConvertFrom-Json; [System.IO.File]::WriteAllText('comparison_results\V.CT.26413_AUTO_processed.txt', $json.processed_text, [System.Text.Encoding]::UTF8)"

REM File 2 - V.MG.73398.mp3
powershell -Command "$json = Get-Content result_fa_2.json -Encoding UTF8 | ConvertFrom-Json; [System.IO.File]::WriteAllText('comparison_results\V.MG.73398_FA_processed.txt', $json.processed_text, [System.Text.Encoding]::UTF8)"
powershell -Command "$json = Get-Content result_auto_2.json -Encoding UTF8 | ConvertFrom-Json; [System.IO.File]::WriteAllText('comparison_results\V.MG.73398_AUTO_processed.txt', $json.processed_text, [System.Text.Encoding]::UTF8)"

REM File 3 - V.MG.73400.mp3
powershell -Command "$json = Get-Content result_fa_3.json -Encoding UTF8 | ConvertFrom-Json; [System.IO.File]::WriteAllText('comparison_results\V.MG.73400_FA_processed.txt', $json.processed_text, [System.Text.Encoding]::UTF8)"
powershell -Command "$json = Get-Content result_auto_3.json -Encoding UTF8 | ConvertFrom-Json; [System.IO.File]::WriteAllText('comparison_results\V.MG.73400_AUTO_processed.txt', $json.processed_text, [System.Text.Encoding]::UTF8)"

echo Files saved!
echo.

REM ============================================
REM DISPLAY COMPARISON
REM ============================================

echo.
echo ============================================
echo COMPARISON RESULTS
echo ============================================
echo.

echo ========================================
echo FILE 1: V.CT.26413.mp3
echo ========================================
echo.
echo [PERSIAN MODE - language=fa]:
type comparison_results\V.CT.26413_FA_processed.txt
echo.
echo.
echo [AUTO-DETECT MODE - language=None]:
type comparison_results\V.CT.26413_AUTO_processed.txt
echo.
echo ========================================
echo.
pause

echo ========================================
echo FILE 2: V.MG.73398.mp3
echo ========================================
echo.
echo [PERSIAN MODE - language=fa]:
type comparison_results\V.MG.73398_FA_processed.txt
echo.
echo.
echo [AUTO-DETECT MODE - language=None]:
type comparison_results\V.MG.73398_AUTO_processed.txt
echo.
echo ========================================
echo.
pause

echo ========================================
echo FILE 3: V.MG.73400.mp3
echo ========================================
echo.
echo [PERSIAN MODE - language=fa]:
type comparison_results\V.MG.73400_FA_processed.txt
echo.
echo.
echo [AUTO-DETECT MODE - language=None]:
type comparison_results\V.MG.73400_AUTO_processed.txt
echo.
echo ========================================
echo.
pause

REM ============================================
REM DISPLAY STATISTICS
REM ============================================

echo.
echo ============================================
echo STATISTICS COMPARISON
echo ============================================
echo.

powershell -Command "$fa1 = Get-Content result_fa_1.json | ConvertFrom-Json; $auto1 = Get-Content result_auto_1.json | ConvertFrom-Json; Write-Host 'V.CT.26413.mp3:'; Write-Host '  [FA]   Corrections:' $fa1.correction_count ', Fuzzy:' $fa1.fuzzy_match_count ', Confidence:' $fa1.confidence_score; Write-Host '  [AUTO] Corrections:' $auto1.correction_count ', Fuzzy:' $auto1.fuzzy_match_count ', Confidence:' $auto1.confidence_score; Write-Host ''"

powershell -Command "$fa2 = Get-Content result_fa_2.json | ConvertFrom-Json; $auto2 = Get-Content result_auto_2.json | ConvertFrom-Json; Write-Host 'V.MG.73398.mp3:'; Write-Host '  [FA]   Corrections:' $fa2.correction_count ', Fuzzy:' $fa2.fuzzy_match_count ', Confidence:' $fa2.confidence_score; Write-Host '  [AUTO] Corrections:' $auto2.correction_count ', Fuzzy:' $auto2.fuzzy_match_count ', Confidence:' $auto2.confidence_score; Write-Host ''"

powershell -Command "$fa3 = Get-Content result_fa_3.json | ConvertFrom-Json; $auto3 = Get-Content result_auto_3.json | ConvertFrom-Json; Write-Host 'V.MG.73400.mp3:'; Write-Host '  [FA]   Corrections:' $fa3.correction_count ', Fuzzy:' $fa3.fuzzy_match_count ', Confidence:' $fa3.confidence_score; Write-Host '  [AUTO] Corrections:' $auto3.correction_count ', Fuzzy:' $auto3.fuzzy_match_count ', Confidence:' $auto3.confidence_score; Write-Host ''"

echo.
echo ============================================
echo TEST COMPLETE!
echo ============================================
echo.
echo All results saved to: comparison_results\
echo.
echo Compare files:
echo   V.CT.26413_FA_processed.txt   vs   V.CT.26413_AUTO_processed.txt
echo   V.MG.73398_FA_processed.txt   vs   V.MG.73398_AUTO_processed.txt
echo   V.MG.73400_FA_processed.txt   vs   V.MG.73400_AUTO_processed.txt
echo.
echo Look for:
echo   1. Are English abbreviations written correctly in AUTO mode?
echo   2. Is Persian accuracy maintained in AUTO mode?
echo   3. Which mode gives better overall quality?
echo.
pause
