# Quick Command Reference

Complete guide to all commands for running and testing your speech-to-text system.

## 🚀 Getting Started

### 1. Initial Setup (First Time Only)

```bash
# Make sure Docker Desktop is running first!

# Start all services
docker-compose up -d

# Wait 30 seconds for services to initialize
# Then check status
check_status.bat
```

**Expected Output:**
```
✅ Docker installed
✅ Docker running
✅ API responding
✅ Transcriptions folder exists
```

---

## 🔄 Daily Operations

### Start/Stop Services

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart web
docker-compose restart worker
```

### Check System Status

```bash
# Quick health check
check_status.bat

# Check API is responding
curl http://localhost:8080/

# Check all running containers
docker-compose ps

# Expected output:
# db      - Up (healthy)
# redis   - Up (healthy)
# web     - Up
# worker  - Up
```

---

## 🧪 Testing Commands

### Automated Tests

```bash
# Test with your two Persian audio files
test_both_audios.bat

# Test lexicon pipeline with medical terms
test_lexicon_pipeline.bat

# Check system status
check_status.bat
```

### Manual Testing

#### 1. Test API Health
```bash
curl http://localhost:8080/
```

**Expected Output:**
```json
{
  "service": "Speech-to-Text Transcription Service",
  "version": "1.0.0",
  "status": "running"
}
```

#### 2. Upload Audio for Transcription
```bash
# Basic transcription (no lexicon)
curl -X POST "http://localhost:8080/jobs/" ^
  -H "X-API-Key: 1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I" ^
  -F "audio_file=@C:\Users\digi kaj\Downloads\63148.mp3" ^
  -F "language=fa"

# With lexicon
curl -X POST "http://localhost:8080/jobs/" ^
  -H "X-API-Key: 1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I" ^
  -F "audio_file=@C:\Users\digi kaj\Downloads\63322.mp3" ^
  -F "language=fa" ^
  -F "lexicon_id=medical"
```

**Expected Output:**
```json
{
  "job_id": "abc-123-def",
  "status": "pending",
  "message": "Job queued for processing"
}
```

#### 3. Check Job Status
```bash
# Replace {job_id} with actual job ID from step 2
curl "http://localhost:8080/jobs/{job_id}" ^
  -H "X-API-Key: 1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I"
```

**Status Values:**
- `pending` - Waiting in queue
- `processing` - Currently transcribing
- `completed` - Finished successfully
- `failed` - Error occurred

---

## 📊 Viewing Results

### Check Text Files

```bash
# List all transcription files
dir transcriptions\*.txt

# View specific file
type transcriptions\63148.txt

# Open folder in Explorer
explorer transcriptions
```

### Check Database

```bash
# View recent jobs
docker-compose exec db psql -U user -d transcription -c "SELECT job_id, status, audio_filename, created_at FROM jobs ORDER BY created_at DESC LIMIT 5;"

# View specific job details
docker-compose exec db psql -U user -d transcription -c "SELECT job_id, status, audio_filename, LEFT(transcription_text, 100) as preview FROM jobs WHERE job_id = 'YOUR_JOB_ID';"

# View all completed jobs
docker-compose exec db psql -U user -d transcription -c "SELECT job_id, audio_filename, created_at FROM jobs WHERE status = 'completed' ORDER BY created_at DESC;"

# Count jobs by status
docker-compose exec db psql -U user -d transcription -c "SELECT status, COUNT(*) FROM jobs GROUP BY status;"
```

---

## 📚 Lexicon Management

### Create/Import Lexicon

#### Create via API (JSON)
```bash
curl -X POST "http://localhost:8080/lexicons/" ^
  -H "X-API-Key: 1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I" ^
  -H "Content-Type: application/json" ^
  -d "{\"name\": \"medical\", \"language\": \"fa\", \"description\": \"Medical terminology\", \"replacements\": {\"سی تی\": \"CT\", \"ام آر آی\": \"MRI\", \"لنف نود\": \"lymph node\"}}"
```

#### Import from JSON file
```bash
# Create terms.json file first:
# [
#   {"term": "سی تی", "replacement": "CT"},
#   {"term": "ام آر آی", "replacement": "MRI"}
# ]

curl -X POST "http://localhost:8080/lexicons/medical/import" ^
  -H "X-API-Key: 1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I" ^
  -F "file=@terms.json"
```

#### Import from CSV file
```bash
# Create terms.csv file first:
# term,replacement
# سی تی,CT
# ام آر آی,MRI

curl -X POST "http://localhost:8080/lexicons/medical/import" ^
  -H "X-API-Key: 1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I" ^
  -F "file=@terms.csv"
```

### Export Lexicon

```bash
# Export as JSON
curl -X GET "http://localhost:8080/lexicons/medical/export?format=json" ^
  -H "X-API-Key: 1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I" ^
  -o medical_terms.json

# Export as CSV
curl -X GET "http://localhost:8080/lexicons/medical/export?format=csv" ^
  -H "X-API-Key: 1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I" ^
  -o medical_terms.csv
```

### View Lexicon Terms in Database

```bash
# List all lexicons
docker-compose exec db psql -U user -d transcription -c "SELECT DISTINCT lexicon_id, COUNT(*) as term_count FROM lexicon_terms WHERE is_active = true GROUP BY lexicon_id;"

# View specific lexicon terms
docker-compose exec db psql -U user -d transcription -c "SELECT term, replacement FROM lexicon_terms WHERE lexicon_id = 'medical' AND is_active = true ORDER BY term;"

# Count active terms per lexicon
docker-compose exec db psql -U user -d transcription -c "SELECT lexicon_id, COUNT(*) FROM lexicon_terms WHERE is_active = true GROUP BY lexicon_id;"
```

---

## 🔑 API Key Management

### List API Keys

```bash
curl -X GET "http://localhost:8080/admin/api-keys" ^
  -H "X-Admin-Key: A-R_BZ52dg1C9yymHj9566gGMjFCVaaqe0Nis9FX1QU"
```

### Create New API Key

```bash
curl -X POST "http://localhost:8080/admin/api-keys" ^
  -H "X-Admin-Key: A-R_BZ52dg1C9yymHj9566gGMjFCVaaqe0Nis9FX1QU" ^
  -H "Content-Type: application/json" ^
  -d "{\"description\": \"New client key\", \"is_admin\": false}"
```

### View API Keys in Database

```bash
docker-compose exec db psql -U user -d transcription -c "SELECT id, description, is_admin, is_active, created_at FROM api_keys ORDER BY created_at DESC;"
```

---

## 🔍 Monitoring & Logs

### View Logs

```bash
# All services (last 50 lines)
docker-compose logs --tail=50

# Specific service
docker-compose logs web --tail=50
docker-compose logs worker --tail=50
docker-compose logs db --tail=50
docker-compose logs redis --tail=50

# Follow logs in real-time
docker-compose logs -f web
docker-compose logs -f worker

# Search logs for errors
docker-compose logs web | findstr "error"
docker-compose logs worker | findstr "failed"
```

### Monitor Job Processing

```bash
# Watch worker logs in real-time
docker-compose logs -f worker

# Check Redis queue status
docker-compose exec redis redis-cli LLEN rq:queue:transcription

# View recent worker activity
docker-compose logs worker --tail=100 | findstr "Processing"
```

### Check Resource Usage

```bash
# Container stats (CPU, memory)
docker stats

# Disk usage
docker system df

# Database size
docker-compose exec db psql -U user -d transcription -c "SELECT pg_size_pretty(pg_database_size('transcription'));"
```

---

## 🛠️ Troubleshooting Commands

### Services Not Starting

```bash
# Check Docker is running
docker ps

# Check for port conflicts
netstat -ano | findstr "8080"
netstat -ano | findstr "5432"
netstat -ano | findstr "6500"

# View full service logs
docker-compose logs web
docker-compose logs worker

# Restart specific service
docker-compose restart web
docker-compose restart worker
```

### Job Stuck in Pending

```bash
# Check worker is running
docker-compose ps worker

# Check worker logs
docker-compose logs worker --tail=50

# Restart worker
docker-compose restart worker

# Check Redis connection
docker-compose exec redis redis-cli ping
```

### Database Issues

```bash
# Connect to database shell
docker-compose exec db psql -U user -d transcription

# Inside psql shell:
# \dt              - List all tables
# \d jobs          - Describe jobs table
# \q               - Quit

# Check database connectivity
docker-compose exec db psql -U user -d transcription -c "SELECT version();"

# View recent errors in jobs
docker-compose exec db psql -U user -d transcription -c "SELECT job_id, error_message, created_at FROM jobs WHERE status = 'failed' ORDER BY created_at DESC LIMIT 5;"
```

### Clear Everything and Start Fresh

```bash
# Stop all services
docker-compose down

# Remove volumes (WARNING: Deletes all data!)
docker-compose down -v

# Rebuild containers
docker-compose build --no-cache

# Start fresh
docker-compose up -d
```

---

## 📁 File Operations

### Cleanup Old Files

```bash
# List old transcription files
dir transcriptions\*.txt /O:D

# Delete files older than 24 hours (manual)
# Review files first, then delete individually

# Check audio storage
dir audio_storage

# View disk usage
dir /s transcriptions
```

### Backup Database

```bash
# Backup database to file
docker-compose exec db pg_dump -U user -d transcription > backup.sql

# Restore from backup
docker-compose exec -T db psql -U user -d transcription < backup.sql
```

---

## 🔐 Security Commands

### View API Key Usage

```bash
# Count jobs per API key
docker-compose exec db psql -U user -d transcription -c "SELECT api_key_id, COUNT(*) as job_count FROM jobs GROUP BY api_key_id ORDER BY job_count DESC;"

# View recent API activity
docker-compose exec db psql -U user -d transcription -c "SELECT j.job_id, j.created_at, k.description FROM jobs j JOIN api_keys k ON j.api_key_id = k.id ORDER BY j.created_at DESC LIMIT 10;"
```

### Deactivate API Key

```bash
curl -X DELETE "http://localhost:8080/admin/api-keys/{key_id}" ^
  -H "X-Admin-Key: A-R_BZ52dg1C9yymHj9566gGMjFCVaaqe0Nis9FX1QU"
```

---

## 📊 Statistics & Reports

### Job Statistics

```bash
# Total jobs
docker-compose exec db psql -U user -d transcription -c "SELECT COUNT(*) as total_jobs FROM jobs;"

# Jobs by status
docker-compose exec db psql -U user -d transcription -c "SELECT status, COUNT(*) as count FROM jobs GROUP BY status;"

# Average processing time
docker-compose exec db psql -U user -d transcription -c "SELECT AVG(processing_time_seconds) as avg_time_seconds FROM jobs WHERE status = 'completed';"

# Jobs today
docker-compose exec db psql -U user -d transcription -c "SELECT COUNT(*) FROM jobs WHERE created_at > CURRENT_DATE;"

# Most used lexicons
docker-compose exec db psql -U user -d transcription -c "SELECT lexicon_version, COUNT(*) as usage_count FROM jobs WHERE lexicon_version IS NOT NULL GROUP BY lexicon_version ORDER BY usage_count DESC;"
```

### Audio File Statistics

```bash
# Total audio processed (in MB)
docker-compose exec db psql -U user -d transcription -c "SELECT SUM(audio_size_bytes)/1024/1024 as total_mb FROM jobs;"

# Average audio duration
docker-compose exec db psql -U user -d transcription -c "SELECT AVG(audio_duration) as avg_duration_seconds FROM jobs WHERE audio_duration IS NOT NULL;"

# Audio formats used
docker-compose exec db psql -U user -d transcription -c "SELECT audio_format, COUNT(*) FROM jobs GROUP BY audio_format;"
```

---

## 🎯 Your Credentials

```bash
# Admin API Key (for management operations)
X-Admin-Key: A-R_BZ52dg1C9yymHj9566gGMjFCVaaqe0Nis9FX1QU

# Client API Key (for transcription)
X-API-Key: 1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I
```

---

## 🚀 Quick Reference

| Task | Command |
|------|---------|
| Start system | `docker-compose up -d` |
| Check status | `check_status.bat` |
| Test transcription | `test_both_audios.bat` |
| Test lexicon | `test_lexicon_pipeline.bat` |
| View logs | `docker-compose logs --tail=50` |
| Stop system | `docker-compose down` |
| Restart | `docker-compose restart` |
| View results | `dir transcriptions\*.txt` |

---

## 📞 Need Help?

1. **Check logs**: `docker-compose logs --tail=50`
2. **Restart services**: `docker-compose restart`
3. **View documentation**: [README.md](README.md)
4. **System architecture**: [HOW_IT_WORKS.md](HOW_IT_WORKS.md)

---

**All commands ready to use!** 🎉

Copy and paste any command directly into your terminal.
