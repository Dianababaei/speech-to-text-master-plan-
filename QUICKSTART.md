# Speech-to-Text System - Complete Quick Start Guide

Complete guide to get your Persian speech-to-text transcription system up and running.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Prerequisites](#prerequisites)
3. [Initial Setup](#initial-setup)
4. [Start Services](#start-services)
5. [Transcribe Audio](#transcribe-audio)
6. [Admin API Management](#admin-api-management)
7. [View Results](#view-results)
8. [Troubleshooting](#troubleshooting)

---

## System Overview

**What you have:**
- ✅ FastAPI web service (port 8080)
- ✅ PostgreSQL database
- ✅ Redis queue system
- ✅ Background worker for transcription
- ✅ OpenAI Whisper API integration
- ✅ API key authentication system
- ✅ Admin API for key management
- ✅ Persian language support with English words
- ✅ **Automatic transcription file saving** - Each transcription is saved as a `.txt` file

**Your Credentials:**
- **Admin Key:** `A-R_BZ52dg1C9yymHj9566gGMjFCVaaqe0Nis9FX1QU`
- **Client API Key:** `1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I`

---

## Prerequisites

✅ You already have:
- Docker Desktop running
- All services configured
- Database initialized
- API keys generated

---

## Initial Setup

### 1. Verify Docker is Running

```cmd
docker --version
docker-compose --version
```

### 2. Check Services Status

```cmd
cd "c:\Users\digi kaj\Desktop\speech-to-text\speech-to-text-master-plan-"
docker-compose ps
```

You should see 4 services running:
- `db` (PostgreSQL)
- `redis` (Queue)
- `web` (API server)
- `worker` (Transcription processor)

---

## Start Services

### If Services Are Not Running

```cmd
cd "c:\Users\digi kaj\Desktop\speech-to-text\speech-to-text-master-plan-"
docker-compose up -d
```

### Restart Services

```cmd
docker-compose restart
```

### Stop Services

```cmd
docker-compose down
```

### View Logs

```cmd
# Web API logs
docker-compose logs web --tail=30

# Worker logs
docker-compose logs worker --tail=30

# All logs
docker-compose logs --tail=50
```

---

## Transcribe Audio

### Option 1: Use the Automated Script

```cmd
test_fixed.bat
```

This will:
1. Upload your MP3 file
2. Wait for processing
3. Display results

### Option 2: Manual Commands

#### Step 1: Upload Audio File

**Important:** Audio must be in MP3 format.

```cmd
curl -X POST "http://localhost:8080/jobs/" ^
  -H "X-API-Key: 1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I" ^
  -F "audio_file=@C:\Users\digi kaj\Downloads\YOUR_FILE.mp3" ^
  -F "language=fa"
```

**Response:**
```json
{
  "job_id": "abc123-def456-...",
  "status": "pending",
  "created_at": "2025-12-03T10:00:00Z"
}
```

**Copy the `job_id` from the response!**

#### Step 2: Wait for Processing

Wait 30-60 seconds for the transcription to complete.

#### Step 3: Check Result

```cmd
curl "http://localhost:8080/jobs/YOUR_JOB_ID" ^
  -H "X-API-Key: 1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I"
```

**Response (Processing):**
```json
{
  "job_id": "abc123...",
  "status": "processing",
  "created_at": "2025-12-03T10:00:00Z",
  "completed_at": null,
  "original_text": null,
  "processed_text": null,
  "error_message": null
}
```

**Response (Completed):**
```json
{
  "job_id": "abc123...",
  "status": "completed",
  "created_at": "2025-12-03T10:00:00Z",
  "completed_at": "2025-12-03T10:00:35Z",
  "original_text": "شکی با برشی 6218 سینوس یک جهته بدون تدریب...",
  "processed_text": "شکی با برشی 6218 سینوس یک جهته بدون تدریب...",
  "error_message": null
}
```

### Convert M4A to MP3 (If Needed)

Your M4A files need conversion to MP3 first.

**Option 1: Online Converter (Easiest)**
1. Go to: https://cloudconvert.com/m4a-to-mp3
2. Upload your M4A file
3. Click Convert
4. Download the MP3

**Option 2: FFmpeg (If Installed)**
```cmd
ffmpeg -i "input.m4a" "output.mp3"
```

---

## Admin API Management

Manage API keys using the admin endpoints.

### 1. List All API Keys

```cmd
curl -X GET "http://localhost:8080/admin/api-keys" ^
  -H "X-Admin-Key: A-R_BZ52dg1C9yymHj9566gGMjFCVaaqe0Nis9FX1QU"
```

**With Filters:**
```cmd
# Only active keys
curl -X GET "http://localhost:8080/admin/api-keys?is_active=true" ^
  -H "X-Admin-Key: A-R_BZ52dg1C9yymHj9566gGMjFCVaaqe0Nis9FX1QU"

# Only inactive keys
curl -X GET "http://localhost:8080/admin/api-keys?is_active=false" ^
  -H "X-Admin-Key: A-R_BZ52dg1C9yymHj9566gGMjFCVaaqe0Nis9FX1QU"

# Pagination
curl -X GET "http://localhost:8080/admin/api-keys?limit=5&offset=0" ^
  -H "X-Admin-Key: A-R_BZ52dg1C9yymHj9566gGMjFCVaaqe0Nis9FX1QU"
```

### 2. Create New API Key

```cmd
curl -X POST "http://localhost:8080/admin/api-keys" ^
  -H "X-Admin-Key: A-R_BZ52dg1C9yymHj9566gGMjFCVaaqe0Nis9FX1QU" ^
  -H "Content-Type: application/json" ^
  -d "{\"project_name\": \"My New Project\", \"description\": \"Production key\", \"rate_limit\": 1000}"
```

**⚠️ Important:** Save the returned API key immediately - it's shown only once!

**Response:**
```json
{
  "api_key": "f0zZkGWpNlekr1381aQCbGNUHjlQnhaIVK3wph044PM",
  "key_id": 3,
  "project_name": "My New Project",
  "rate_limit": 1000,
  "created_at": "2025-12-03T10:00:00Z",
  "warning": "This API key will only be shown once..."
}
```

### 3. Update API Key

```cmd
# Update rate limit
curl -X PATCH "http://localhost:8080/admin/api-keys/1" ^
  -H "X-Admin-Key: A-R_BZ52dg1C9yymHj9566gGMjFCVaaqe0Nis9FX1QU" ^
  -H "Content-Type: application/json" ^
  -d "{\"rate_limit\": 2000}"

# Update multiple fields
curl -X PATCH "http://localhost:8080/admin/api-keys/1" ^
  -H "X-Admin-Key: A-R_BZ52dg1C9yymHj9566gGMjFCVaaqe0Nis9FX1QU" ^
  -H "Content-Type: application/json" ^
  -d "{\"project_name\": \"Updated Name\", \"rate_limit\": 1500, \"is_active\": true}"
```

### 4. Delete (Deactivate) API Key

```cmd
curl -X DELETE "http://localhost:8080/admin/api-keys/1" ^
  -H "X-Admin-Key: A-R_BZ52dg1C9yymHj9566gGMjFCVaaqe0Nis9FX1QU"
```

**Note:** This is a soft delete (sets `is_active=false`). Keys can be reactivated using PATCH.

### 5. Admin Health Check

```cmd
curl -X GET "http://localhost:8080/admin/health" ^
  -H "X-Admin-Key: A-R_BZ52dg1C9yymHj9566gGMjFCVaaqe0Nis9FX1QU"
```

---

## View Results

### Option 1: Text Files (Recommended - Best for Persian)

**All transcriptions are automatically saved as `.txt` files in the `transcriptions/` folder!**

Each audio file gets a corresponding text file:
- `63148.mp3` → `transcriptions/63148.txt`
- `63322.mp3` → `transcriptions/63322.txt`

**How to view:**
1. Open File Explorer
2. Navigate to: `c:\Users\digi kaj\Desktop\speech-to-text\speech-to-text-master-plan-\transcriptions\`
3. Open any `.txt` file with Notepad, VS Code, or any text editor

**List all transcription files:**
```cmd
dir transcriptions
```

### Option 2: From API Response

The transcription appears in the `original_text` field when status is "completed".

### Option 3: From Database

**View specific job:**
```cmd
docker-compose exec db psql -U user -d transcription -c "SELECT transcription_text FROM jobs WHERE job_id = 'YOUR_JOB_ID';"
```

**View most recent transcription:**
```cmd
docker-compose exec db psql -U user -d transcription -c "SELECT job_id, status, transcription_text, created_at FROM jobs ORDER BY created_at DESC LIMIT 1;"
```

**View last 5 transcriptions:**
```cmd
docker-compose exec db psql -U user -d transcription -c "SELECT job_id, LEFT(transcription_text, 50) as preview, created_at FROM jobs ORDER BY created_at DESC LIMIT 5;"
```

**View all API keys:**
```cmd
docker-compose exec db psql -U user -d transcription -c "SELECT id, name, is_active, rate_limit, created_at FROM api_keys;"
```

**View all jobs:**
```cmd
docker-compose exec db psql -U user -d transcription -c "SELECT job_id, status, language, audio_filename, created_at FROM jobs ORDER BY created_at DESC LIMIT 10;"
```

---

## Troubleshooting

### Services Not Running

**Check status:**
```cmd
docker-compose ps
```

**Restart all services:**
```cmd
docker-compose restart
```

**View logs for errors:**
```cmd
docker-compose logs --tail=50
```

### Job Stays "Pending" Too Long

**Check worker is running:**
```cmd
docker-compose logs worker --tail=30
```

**Restart worker:**
```cmd
docker-compose restart worker
```

### "Invalid API key" Error

**Verify your API key:**
```cmd
docker-compose exec db psql -U user -d transcription -c "SELECT id, name, is_active FROM api_keys;"
```

**If needed, create a new key:**
```cmd
curl -X POST "http://localhost:8080/admin/api-keys" ^
  -H "X-Admin-Key: A-R_BZ52dg1C9yymHj9566gGMjFCVaaqe0Nis9FX1QU" ^
  -H "Content-Type: application/json" ^
  -d "{\"project_name\": \"New Key\", \"rate_limit\": 1000}"
```

### M4A Files Rejected

Convert to MP3 first using:
- Online: https://cloudconvert.com/m4a-to-mp3
- FFmpeg: `ffmpeg -i input.m4a output.mp3`

### Database Connection Issues

**Restart database:**
```cmd
docker-compose restart db
```

**Check database logs:**
```cmd
docker-compose logs db --tail=30
```

### View All System Logs

```cmd
# Web service
docker-compose logs web --tail=50

# Worker
docker-compose logs worker --tail=50

# Database
docker-compose logs db --tail=30

# Redis
docker-compose logs redis --tail=30

# All services
docker-compose logs --tail=100
```

---

## Complete Workflow Example

### Example: Transcribe a Persian Audio File

**1. Convert audio to MP3 (if needed)**
- Visit https://cloudconvert.com/m4a-to-mp3
- Upload your M4A file
- Download the MP3

**2. Upload for transcription**
```cmd
curl -X POST "http://localhost:8080/jobs/" ^
  -H "X-API-Key: 1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I" ^
  -F "audio_file=@C:\Users\digi kaj\Downloads\63218.mp3" ^
  -F "language=fa"
```

**3. Copy the job_id from response**
Example: `"job_id": "3d11a2e8-1a90-47ac-8840-c40a3a2717be"`

**4. Wait 30-60 seconds**

**5. Check result**
```cmd
curl "http://localhost:8080/jobs/3d11a2e8-1a90-47ac-8840-c40a3a2717be" ^
  -H "X-API-Key: 1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I"
```

**6. View Persian text properly**
```cmd
docker-compose exec db psql -U user -d transcription -c "SELECT transcription_text FROM jobs WHERE job_id = '3d11a2e8-1a90-47ac-8840-c40a3a2717be';"
```

**Result:**
```
شکی با برشی 6218 سینوس یک جهته بدون تدریب انحرافی سپتامی بینی به چپ همراه به اسپور فارمیشن OMU در دو طرف نرو یه نفس استخدامات مخاطب جوزی در سینس مارک زیلای راست بقیهش هم نرمال
```

---

## Quick Reference

### Your Credentials
```
Admin Key: A-R_BZ52dg1C9yymHj9566gGMjFCVaaqe0Nis9FX1QU
Client API Key: 1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I
Base URL: http://localhost:8080
```

### Common Commands

**Start services:**
```cmd
docker-compose up -d
```

**Stop services:**
```cmd
docker-compose down
```

**Restart services:**
```cmd
docker-compose restart
```

**View logs:**
```cmd
docker-compose logs --tail=50
```

**Transcribe audio:**
```cmd
test_fixed.bat
```

**List API keys:**
```cmd
curl -X GET "http://localhost:8080/admin/api-keys" ^
  -H "X-Admin-Key: A-R_BZ52dg1C9yymHj9566gGMjFCVaaqe0Nis9FX1QU"
```

**View recent transcriptions:**
```cmd
docker-compose exec db psql -U user -d transcription -c "SELECT job_id, LEFT(transcription_text, 50) as preview, created_at FROM jobs ORDER BY created_at DESC LIMIT 5;"
```

---

## System Status

✅ **All systems operational:**
- FastAPI web service on port 8080
- PostgreSQL database
- Redis queue system
- Background worker processing
- OpenAI Whisper API integration
- API key authentication
- Admin API management
- Persian transcription with English words
- Audio file storage and cleanup

Your speech-to-text system is ready to use! 🎉

---

## Support

**Check system health:**
```cmd
curl http://localhost:8080/
curl http://localhost:8080/health
curl "http://localhost:8080/admin/health" ^
  -H "X-Admin-Key: A-R_BZ52dg1C9yymHj9566gGMjFCVaaqe0Nis9FX1QU"
```

**View all services:**
```cmd
docker-compose ps
```

**Restart everything:**
```cmd
docker-compose restart
```
