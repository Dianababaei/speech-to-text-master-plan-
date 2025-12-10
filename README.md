# Speech-to-Text Transcription System

Production-ready speech-to-text transcription service with Persian language support, API key authentication, and admin management.

## 🚀 Quick Start

**Everything you need is in one place:**

👉 **[QUICKSTART.md](QUICKSTART.md)** - Complete guide with all commands

## Features

✅ **OpenAI Whisper Integration** - High-quality transcription
✅ **Persian Language Support** - With English word recognition
✅ **API Key Authentication** - Secure access control
✅ **Admin API** - Full key lifecycle management
✅ **Background Processing** - Redis queue + worker
✅ **Auto Storage Cleanup** - Scheduled cleanup of old files
✅ **Docker Deployment** - Easy setup and scaling
✅ **Audit Trail** - Complete logging of all actions
✅ **Automatic Text File Export** - Each transcription saved as `.txt` file in `transcriptions/` folder

## Architecture

```
┌─────────────────┐
│  FastAPI Web    │  Port 8080
│  (API Server)   │
└────────┬────────┘
         │
    ┌────┴────┬─────────────┬──────────┐
    │         │             │          │
┌───▼──┐  ┌──▼───┐  ┌──────▼───┐  ┌──▼────┐
│ DB   │  │Redis │  │  Worker  │  │OpenAI │
│(Pg)  │  │Queue │  │(RQ)      │  │Whisper│
└──────┘  └──────┘  └──────────┘  └───────┘
```

## System Status

✅ All services running:
- **Web API**: http://localhost:8080
- **PostgreSQL**: Database for jobs and API keys
- **Redis**: Queue for background jobs
- **Worker**: Transcription processor

## Your Credentials

**Admin Key:**
```
A-R_BZ52dg1C9yymHj9566gGMjFCVaaqe0Nis9FX1QU
```

**Client API Key:**
```
1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I
```

## Common Commands

### Start System
```bash
docker-compose up -d
```

### Transcribe Audio
```bash
test_fixed.bat
```

### List API Keys
```bash
curl -X GET "http://localhost:8080/admin/api-keys" ^
  -H "X-Admin-Key: A-R_BZ52dg1C9yymHj9566gGMjFCVaaqe0Nis9FX1QU"
```

### View Results
```bash
docker-compose exec db psql -U user -d transcription -c "SELECT job_id, LEFT(transcription_text, 50) as preview, created_at FROM jobs ORDER BY created_at DESC LIMIT 5;"
```

### View Logs
```bash
docker-compose logs --tail=50
```

## API Endpoints

### Transcription API
- `POST /jobs/` - Upload audio for transcription
- `GET /jobs/{job_id}` - Get transcription status/result
- `GET /health` - System health check

### Admin API
- `POST /admin/api-keys` - Create new API key
- `GET /admin/api-keys` - List all keys (with filters)
- `PATCH /admin/api-keys/{id}` - Update key metadata
- `DELETE /admin/api-keys/{id}` - Deactivate key
- `GET /admin/health` - Admin health check

## Example Usage

**1. Upload audio:**
```bash
curl -X POST "http://localhost:8080/jobs/" ^
  -H "X-API-Key: 1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I" ^
  -F "audio_file=@audio.mp3" ^
  -F "language=fa"
```

**2. Check result:**
```bash
curl "http://localhost:8080/jobs/{job_id}" ^
  -H "X-API-Key: 1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I"
```

## Audio Format

**Supported:** MP3, WAV, M4A (with compatible codec), MP4, MPEG, MPGA, OGG, WEBM, FLAC

**Note:** If M4A files are rejected, convert to MP3:
- Online: https://cloudconvert.com/m4a-to-mp3
- FFmpeg: `ffmpeg -i input.m4a output.mp3`

## Troubleshooting

**Services not running:**
```bash
docker-compose restart
```

**View logs:**
```bash
docker-compose logs web --tail=30
docker-compose logs worker --tail=30
```

**Job stuck in pending:**
```bash
docker-compose restart worker
```

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Complete quick start guide with all commands

## Tech Stack

- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Relational database
- **Redis + RQ** - Background job processing
- **SQLAlchemy** - ORM for database
- **OpenAI Whisper** - Speech-to-text API
- **Docker** - Containerization
- **Bcrypt** - Secure password hashing

## Security

- ✅ API key authentication for all endpoints
- ✅ Admin key for management operations
- ✅ Bcrypt hashing for API keys
- ✅ Soft delete for audit trail
- ✅ Complete action logging
- ✅ Rate limiting per API key

## Support

For questions or issues:
1. Check [QUICKSTART.md](QUICKSTART.md)
2. View logs: `docker-compose logs --tail=50`
3. Restart services: `docker-compose restart`

---

**Ready to use!** 🎉

See [QUICKSTART.md](QUICKSTART.md) for detailed instructions.
