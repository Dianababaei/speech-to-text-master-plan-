# Quick Start Guide

Get your Persian medical speech-to-text system running in 5 minutes.

## Prerequisites

- Docker Desktop installed and running
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

## Step 1: Setup (2 minutes)

```bash
# 1. Configure environment
cp .env.example .env

# 2. Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-...your-key-here

# 3. Start all services
docker-compose up -d

# 4. Wait 10 seconds for services to initialize
```

## Step 2: Verify (30 seconds)

```bash
# Check all services are running
docker-compose ps

# You should see 4 services "Up":
# - web (FastAPI)
# - db (PostgreSQL)
# - redis
# - worker
```

## Step 3: Test It! (2 minutes)

### Submit an Audio File

```bash
curl -X POST "http://localhost:8080/jobs/" \
  -H "X-API-Key: 1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I" \
  -F "audio_file=@C:\path\to\your\audio.mp3" \
  -F "language=fa"
```

**You'll get a response like:**
```json
{
  "job_id": "abc123-def456-...",
  "status": "pending"
}
```

### Check the Result

Wait 10-30 seconds (depending on audio length), then:

```bash
curl -X GET "http://localhost:8080/jobs/abc123-def456-..." \
  -H "X-API-Key: 1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I"
```

**When completed:**
```json
{
  "status": "completed",
  "original_text": "raw whisper output...",
  "processed_text": "cleaned, formatted output...",
  "confidence_score": 0.85
}
```

### Find Your Transcription File

Automatically saved to:
```
transcriptions/your_audio_filename.txt
```

---

## Common Commands

### Start Services
```bash
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f worker
docker-compose logs -f web
```

### Restart Worker (after config changes)
```bash
docker-compose restart worker
```

---

## Windows Users - Easy Batch File Testing

We've included test batch files:

```batch
# Test 3 audio files with language comparison
compare_new_3_files.bat

# Test 5 audio files with FA vs AUTO language modes
compare_language_modes.bat
```

---

## API Endpoints

**Base URL:** `http://localhost:8080`

**Admin API Key:** `1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I`

### Submit Job
```
POST /jobs/
Headers: X-API-Key
Form-data: audio_file, language (optional, default: "fa")
```

### Get Job Status
```
GET /jobs/{job_id}
Headers: X-API-Key
```

### List All Jobs
```
GET /jobs/
Headers: X-API-Key
Query params: skip, limit, status
```

### Interactive API Documentation
Open in browser: **http://localhost:8080/docs**

---

## Quality Tips

### 🎤 Best Audio Quality
- Use a good microphone (USB headset recommended)
- Quiet environment (close windows, turn off fans)
- Speak clearly at normal pace
- High-quality audio files (WAV or 320kbps MP3)

### 📝 Customize for Your Practice

**Add Custom Medical Terms:**

Edit `medical_corrections.csv`:
```csv
term,replacement,category
your_term,correct_term,medical_term
```

Then restart worker:
```bash
docker-compose restart worker
```

---

## Troubleshooting

### Services Won't Start
```bash
# Check what's wrong
docker-compose logs web
docker-compose logs worker

# Common fix: restart everything
docker-compose down
docker-compose up -d
```

### Jobs Stay "pending"
```bash
# Check worker is running
docker-compose ps worker

# Restart worker
docker-compose restart worker
```

### Low Quality Results
1. Check audio quality (most common issue!)
2. Look at `confidence_score` in results (<0.5 = poor audio)
3. Add custom terms to `medical_corrections.csv`

---

## Next Steps

1. **Read the full documentation**: [README.md](README.md)
2. **Customize lexicon**: Add your medical terms to `medical_corrections.csv`
3. **Test with real audio**: Try your actual radiology reports
4. **Monitor quality**: Check confidence scores and adjust

---

## Need Help?

- **Full Documentation**: [README.md](README.md)
- **API Docs**: http://localhost:8080/docs
- **Test Files**: See `*.bat` files for testing examples

---

**That's it! You're ready to transcribe Persian medical audio! 🎉**
