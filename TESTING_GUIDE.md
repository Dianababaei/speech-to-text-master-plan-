# Complete Testing Guide

## Prerequisites Checklist

Before running tests, ensure:

- [ ] Docker Desktop is running
- [ ] All services are up: `docker-compose ps`
- [ ] API is responding: `curl http://localhost:8080/`
- [ ] Audio files exist:
  - `C:\Users\digi kaj\Downloads\63148.mp3`
  - `C:\Users\digi kaj\Downloads\63322.mp3`

## Quick Test Commands

### 1. Start Docker Services

```cmd
cd "c:\Users\digi kaj\Desktop\speech-to-text\speech-to-text-master-plan-"
docker-compose up -d
```

### 2. Verify Services

```cmd
docker-compose ps
```

Expected output: All services showing "Up"

### 3. Check Logs

```cmd
# Web API
docker-compose logs web --tail=50

# Worker
docker-compose logs worker --tail=50

# All services
docker-compose logs --tail=50
```

### 4. Test API Health

```cmd
curl http://localhost:8080/
curl http://localhost:8080/health
```

### 5. Run Automated Tests

```cmd
# Test both audio files automatically
test_both_audios.bat
```

OR manually:

```cmd
# Test first file
curl -X POST "http://localhost:8080/jobs/" ^
  -H "X-API-Key: 1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I" ^
  -F "audio_file=@C:\Users\digi kaj\Downloads\63148.mp3" ^
  -F "language=fa"

# Test second file
curl -X POST "http://localhost:8080/jobs/" ^
  -H "X-API-Key: 1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I" ^
  -F "audio_file=@C:\Users\digi kaj\Downloads\63322.mp3" ^
  -F "language=fa"
```

### 6. Wait for Processing

Processing takes about 30-60 seconds per file. Monitor progress:

```cmd
# Watch worker logs in real-time
docker-compose logs worker -f
```

Press `Ctrl+C` to stop watching.

### 7. View Results

**Option A: Check transcription files (Easiest)**

```cmd
dir transcriptions
type transcriptions\63148.txt
type transcriptions\63322.txt
```

**Option B: Query database**

```cmd
docker-compose exec db psql -U user -d transcription -c "SELECT audio_filename, transcription_text FROM jobs ORDER BY created_at DESC LIMIT 2;"
```

**Option C: Use API to check job status**

Copy the `job_id` from the initial response, then:

```cmd
curl http://localhost:8080/jobs/{job_id}
```

## Testing Features

### Test 1: Basic Transcription ✅

**What it tests:** Audio upload, transcription, and text file generation

**Steps:**
1. Run `test_both_audios.bat`
2. Wait 60 seconds
3. Check `transcriptions/` folder for `.txt` files
4. Open files and verify Persian text is readable

**Expected:** Two `.txt` files with Persian transcriptions

---

### Test 2: API Key Authentication ✅

**What it tests:** API security

**Test with valid key:**
```cmd
curl -X GET "http://localhost:8080/jobs/" ^
  -H "X-API-Key: 1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I"
```

**Expected:** List of jobs (200 OK)

**Test with invalid key:**
```cmd
curl -X GET "http://localhost:8080/jobs/" ^
  -H "X-API-Key: invalid-key-123"
```

**Expected:** 403 Forbidden error

---

### Test 3: Admin API ✅

**What it tests:** Admin key management

**List all API keys:**
```cmd
curl -X GET "http://localhost:8080/admin/api-keys" ^
  -H "X-Admin-Key: A-R_BZ52dg1C9yymHj9566gGMjFCVaaqe0Nis9FX1QU"
```

**Create new API key:**
```cmd
curl -X POST "http://localhost:8080/admin/api-keys" ^
  -H "X-Admin-Key: A-R_BZ52dg1C9yymHj9566gGMjFCVaaqe0Nis9FX1QU" ^
  -H "Content-Type: application/json" ^
  -d "{\"project_name\": \"Test Project\", \"description\": \"Testing key creation\"}"
```

**Expected:** New API key returned (only shown once!)

---

### Test 4: Job Status Tracking ✅

**What it tests:** Job lifecycle

1. Submit a job and save the `job_id`
2. Check status immediately:
```cmd
curl http://localhost:8080/jobs/{job_id}
```
**Expected:** Status = "pending"

3. Wait 10 seconds, check again:
**Expected:** Status = "processing"

4. Wait another 30 seconds, check again:
**Expected:** Status = "completed" with transcription_text

---

### Test 5: Database Queries ✅

**What it tests:** Data persistence

**View all jobs:**
```cmd
docker-compose exec db psql -U user -d transcription -c "SELECT job_id, status, audio_filename, created_at FROM jobs ORDER BY created_at DESC LIMIT 5;"
```

**View transcriptions:**
```cmd
docker-compose exec db psql -U user -d transcription -c "SELECT audio_filename, LEFT(transcription_text, 100) as preview FROM jobs WHERE status='completed';"
```

**Count jobs by status:**
```cmd
docker-compose exec db psql -U user -d transcription -c "SELECT status, COUNT(*) FROM jobs GROUP BY status;"
```

---

### Test 6: Error Handling ✅

**What it tests:** System robustness

**Test with non-existent file:**
```cmd
curl -X POST "http://localhost:8080/jobs/" ^
  -H "X-API-Key: 1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I" ^
  -F "audio_file=@nonexistent.mp3" ^
  -F "language=fa"
```

**Expected:** Error response (400 or 404)

---

### Test 7: Lexicon Management ✅

**What it tests:** Custom vocabulary (new feature from merge)

**Create a lexicon:**
```cmd
curl -X POST "http://localhost:8080/lexicons/" ^
  -H "X-API-Key: 1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I" ^
  -H "Content-Type: application/json" ^
  -d "{\"name\": \"medical\", \"language\": \"fa\", \"replacements\": {\"سی تی\": \"CT\", \"ام آر آی\": \"MRI\"}}"
```

**List lexicons:**
```cmd
curl -X GET "http://localhost:8080/lexicons/" ^
  -H "X-API-Key: 1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I"
```

---

## Troubleshooting

### Problem: Docker not running
**Solution:** Start Docker Desktop and wait for it to fully initialize

### Problem: Port 8080 already in use
**Solution:**
```cmd
docker-compose down
docker-compose up -d
```

### Problem: Services won't start
**Solution:**
```cmd
# Check logs
docker-compose logs

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Problem: Worker not processing jobs
**Solution:**
```cmd
# Check worker logs
docker-compose logs worker

# Restart worker
docker-compose restart worker
```

### Problem: Database connection failed
**Solution:**
```cmd
# Check database is running
docker-compose ps db

# Restart database
docker-compose restart db

# Wait 10 seconds then restart web and worker
timeout /t 10 /nobreak
docker-compose restart web worker
```

### Problem: Transcription file not created
**Solution:**
1. Check worker logs: `docker-compose logs worker`
2. Check job status in database
3. Verify `transcriptions/` folder exists
4. Check file permissions

---

## Performance Benchmarks

**Expected processing times:**
- Job submission: < 1 second
- Audio file upload: 1-3 seconds
- Transcription (1 minute audio): 20-40 seconds
- Total time per job: 30-60 seconds

**System resources:**
- CPU: Normal during processing
- Memory: ~2GB for all containers
- Disk: ~500MB for Docker images + audio storage

---

## Clean Up

### Remove old transcription files
```cmd
del transcriptions\*.txt
```

### Clear audio storage
```cmd
docker-compose exec web python -c "from app.database import get_db; from app.services.storage import cleanup_old_audio_files; db=next(get_db()); print(cleanup_old_audio_files(db)); db.close()"
```

### Reset database (WARNING: Deletes all data)
```cmd
docker-compose down -v
docker-compose up -d
```

### Stop all services
```cmd
docker-compose down
```

---

## Success Criteria

Your system is working correctly if:

✅ All Docker containers are running
✅ API responds to health checks
✅ Jobs are created successfully
✅ Worker processes transcriptions
✅ Transcriptions saved to database
✅ `.txt` files created in `transcriptions/` folder
✅ Persian text displays correctly in files
✅ Admin API can manage keys
✅ Authentication works (valid/invalid keys)

---

## Quick Reference

**Your Credentials:**
- Admin Key: `A-R_BZ52dg1C9yymHj9566gGMjFCVaaqe0Nis9FX1QU`
- Client API Key: `1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I`

**Important Endpoints:**
- API Root: `http://localhost:8080/`
- Health Check: `http://localhost:8080/health`
- Submit Job: `POST http://localhost:8080/jobs/`
- Check Job: `GET http://localhost:8080/jobs/{job_id}`
- Admin Keys: `GET http://localhost:8080/admin/api-keys`
- Lexicons: `GET http://localhost:8080/lexicons/`

**Transcription Output:**
- Folder: `transcriptions/`
- Format: `{audio_filename}.txt`
- Encoding: UTF-8 (supports Persian)
