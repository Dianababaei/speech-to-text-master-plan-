# Persian Medical Speech-to-Text System

Production-ready Persian medical transcription service with advanced post-processing pipeline, API authentication, and quality optimization.

## 🎯 Quick Start

**New user?** Start here: [QUICKSTART.md](QUICKSTART.md)

## ✨ Features

### Core Transcription
- **OpenAI Whisper API** - High-quality speech recognition
- **Persian Language Optimized** - Medical terminology support
- **Mixed Language Support** - Handles Persian + English abbreviations (RUL, CT, MRI, etc.)
- **Medical Context Prompt** - Guides Whisper for better medical term recognition

### Advanced Post-Processing Pipeline (5 Steps)
1. **Whisper Transcription** - Initial speech-to-text with medical context
2. **Lexicon Correction** - 200+ medical term corrections (exact matching)
3. **Fuzzy Matching** - Handles typos and variations (Levenshtein distance)
4. **GPT-4o-mini Cleanup** - Removes artifacts, fixes grammar, formats professionally
5. **Quality Metrics** - Confidence scoring and correction tracking

### Quality Improvements
- **60+ Persian Error Corrections** - Common transcription mistakes automatically fixed
- **140+ Medical Abbreviations** - Phonetic Persian → English (ریوئل → RUL)
- **Conversational Filler Removal** - Removes dictation artifacts and informal speech
- **Professional Formatting** - Proper Persian punctuation, ZWNJ, spacing

### Enterprise Features
- **API Key Authentication** - Secure access control
- **Background Processing** - Redis queue + dedicated worker
- **Auto Storage Cleanup** - Scheduled cleanup of old audio files
- **Audit Trail** - Complete logging of all operations
- **Docker Deployment** - Easy setup and scaling
- **Text File Export** - Each transcription saved as `.txt` in `transcriptions/` folder

---

## 📋 Table of Contents

- [Architecture](#architecture)
- [Processing Pipeline](#processing-pipeline)
- [Installation](#installation)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Configuration](#configuration)
- [Testing](#testing)
- [Quality Optimization](#quality-optimization)
- [Troubleshooting](#troubleshooting)

---

## 🏗️ Architecture

```
┌──────────────────┐
│   FastAPI Web    │  Port 8080 - REST API
│   (API Server)   │
└─────────┬────────┘
          │
    ┌─────┴──────┬──────────────┬───────────┐
    │            │              │           │
┌───▼───┐  ┌────▼────┐  ┌──────▼─────┐  ┌─▼──────┐
│  DB   │  │  Redis  │  │   Worker   │  │ OpenAI │
│ (PG)  │  │  Queue  │  │ (RQ Worker)│  │Whisper │
└───────┘  └─────────┘  └────────────┘  └────────┘
     │                         │              │
     │                         │              │
  Jobs, Keys           Transcription      Whisper API
  Lexicon Terms        Background Jobs    GPT-4o-mini
```

### Components

1. **Web API (FastAPI)** - HTTP REST API for job submission and management
2. **PostgreSQL** - Persistent storage for jobs, API keys, lexicon terms
3. **Redis** - Message queue for background job processing
4. **Worker** - Background processor for transcription pipeline
5. **OpenAI Integration** - Whisper for transcription, GPT-4o-mini for cleanup

---

## 🔄 Processing Pipeline

Each audio file goes through a 5-step pipeline:

```
Audio File
    ↓
[1] Whisper Transcription (with medical context prompt)
    ↓
[2] Lexicon Correction (200+ medical terms, exact match)
    ↓
[3] Fuzzy Matching (handles typos, Levenshtein distance)
    ↓
[4] GPT-4o-mini Cleanup (removes artifacts, formats text)
    ↓
[5] Quality Metrics (confidence score, correction count)
    ↓
Final Transcription + Text File
```

### Pipeline Details

#### Step 1: Whisper Transcription
- **Model**: `whisper-1` (OpenAI API)
- **Language**: Persian (`fa`)
- **Prompt**: Medical context with example report
- **Output**: Raw transcription with medical terminology

#### Step 2: Lexicon Correction
- **200+ entries** including:
  - Common errors: خاندگ → خانوادگی, سانوگرافی → سونوگرافی
  - Medical terms: کنترست → کنتراست, دنسیدی → دانسیته
  - English abbreviations: ریوئل → RUL, سی تی → CT
- **Method**: Exact string matching
- **Speed**: ~1ms per document

#### Step 3: Fuzzy Matching
- **Algorithm**: Levenshtein distance (max distance: 2)
- **Purpose**: Catches typos and phonetic variations
- **Examples**: کنترسط → کنتراست, خانوادگگی → خانوادگی

#### Step 4: GPT-4o-mini Cleanup
- **Model**: `gpt-4o-mini` (temperature=0)
- **Tasks**:
  - Remove conversational fillers ("رو ای بزنید و ببینیم")
  - Fix grammar and spacing (می شود → می‌شود)
  - Format patient IDs and report structure
  - Preserve medical findings exactly as dictated
- **Cost**: ~$0.001 per report

#### Step 5: Quality Metrics
- **Confidence Score**: 0-1 scale based on corrections needed
- **Correction Count**: Number of lexicon fixes applied
- **Fuzzy Match Count**: Number of fuzzy corrections
- **Tracking**: All metrics stored in database

---

## 📦 Installation

### Prerequisites
- Docker & Docker Compose
- OpenAI API key

### Setup

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd speech-to-text-master-plan-
```

2. **Configure environment**
```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:
```env
OPENAI_API_KEY=sk-...your-key-here
```

3. **Start services**
```bash
docker-compose up -d
```

4. **Verify services**
```bash
docker-compose ps
```

All services should show "Up" status.

---

## 🚀 Usage

### 1. Get Your API Key

**Admin Key** (pre-configured):
```
1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I
```

### 2. Submit Audio for Transcription

```bash
curl -X POST "http://localhost:8080/jobs/" \
  -H "X-API-Key: 1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I" \
  -F "audio_file=@path/to/audio.mp3" \
  -F "language=fa"
```

Response:
```json
{
  "job_id": "abc123...",
  "status": "pending",
  "created_at": "2025-12-26T..."
}
```

### 3. Check Job Status

```bash
curl -X GET "http://localhost:8080/jobs/{job_id}" \
  -H "X-API-Key: 1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I"
```

Response (completed):
```json
{
  "job_id": "abc123...",
  "status": "completed",
  "original_text": "روبا حسینی 723398 سکرین...",
  "processed_text": "روبا حسینی (723398)\nسکرین سابق خانوادگی منفی...",
  "correction_count": 5,
  "fuzzy_match_count": 2,
  "confidence_score": 0.85
}
```

### 4. Find Transcription File

Processed text automatically saved to:
```
transcriptions/{original_filename}.txt
```

Example:
```
Audio: report_63148.mp3
Text:  transcriptions/report_63148.txt
```

---

## 📚 API Documentation

### Base URL
```
http://localhost:8080
```

### Authentication
All endpoints require `X-API-Key` header.

### Endpoints

#### Jobs

**POST /jobs/**
- Submit audio for transcription
- Form data: `audio_file` (required), `language` (optional, default: "fa")
- Returns: Job object with `job_id`

**GET /jobs/{job_id}**
- Get job status and results
- Returns: Complete job object with transcription if completed

**GET /jobs/**
- List all jobs for your API key
- Query params: `skip`, `limit`, `status`

#### Admin (requires admin API key)

**POST /admin/api-keys/**
- Create new API key
- Body: `{"name": "Key Name", "is_admin": false}`

**GET /admin/api-keys/**
- List all API keys

**DELETE /admin/api-keys/{key_id}**
- Revoke API key

**Interactive API Docs**: http://localhost:8080/docs

---

## ⚙️ Configuration

### Environment Variables

See `.env.example` for all options. Key settings:

```env
# OpenAI
OPENAI_API_KEY=sk-...           # Required
OPENAI_MODEL=whisper-1           # Whisper model

# Database
POSTGRES_USER=transcribe_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=transcription_db

# Redis
REDIS_URL=redis://redis:6379/0

# Storage
AUDIO_STORAGE_DIR=/app/audio_files
STORAGE_CLEANUP_DAYS=7           # Auto-delete files older than 7 days
```

### Lexicon Configuration

Edit `medical_corrections.csv` to add custom corrections:

```csv
term,replacement,category
خاندگ,خانوادگی,medical_term
ریوئل,RUL,medical_term
```

After editing, restart worker:
```bash
docker-compose restart worker
```

### GPT Cleanup Customization

Edit `app/services/postprocessing_service.py` to customize GPT behavior.

---

## 🧪 Testing

### Run All Tests
```bash
docker-compose exec web pytest
```

### Run Specific Tests
```bash
# Unit tests only
docker-compose exec web pytest tests/unit/

# Integration tests
docker-compose exec web pytest tests/integration/

# With coverage
docker-compose exec web pytest --cov=app tests/
```

### Test Files Included
- `tests/README.md` - Testing documentation
- `tests/conftest.py` - Shared fixtures
- `tests/unit/` - Unit tests for services
- `tests/integration/` - API endpoint tests

---

## 📈 Quality Optimization

### Current Optimizations

1. **200+ Lexicon Entries**
   - Common Persian transcription errors
   - Medical terminology corrections
   - English abbreviation mappings

2. **Medical Context Prompt**
   - Guides Whisper with example medical report
   - Improves recognition of medical terms
   - Better formatting from the start

3. **GPT-4o-mini Cleanup**
   - Removes conversational artifacts
   - Fixes grammar and spacing
   - Professional formatting

### Improving Quality Further

#### 1. Audio Quality (Most Important!)
- Use high-quality microphone
- Quiet recording environment
- Clear, well-articulated speech
- High-bitrate audio files (320kbps MP3 or WAV)

#### 2. Expand Lexicon
Add terms specific to your practice in `medical_corrections.csv`

#### 3. Upgrade GPT Model
For critical reports, upgrade from GPT-4o-mini to GPT-4:
```python
# In app/services/postprocessing_service.py
model="gpt-4"  # Instead of "gpt-4o-mini"
```
**Note**: 8x more expensive but significantly better quality

#### 4. Custom Whisper Fine-tuning (Advanced)
For 100+ hours of labeled data, consider fine-tuning Whisper on your specific medical vocabulary.

---

## 🔧 Troubleshooting

### Services Won't Start

**Check logs:**
```bash
docker-compose logs web
docker-compose logs worker
```

**Common issues:**
- Missing `.env` file → Copy from `.env.example`
- Port 8080 already in use → Change in `docker-compose.yml`
- OpenAI API key invalid → Check `.env` file

### Jobs Stuck in "pending"

**Check worker status:**
```bash
docker-compose logs worker
```

**Restart worker:**
```bash
docker-compose restart worker
```

### Low Transcription Quality

1. **Check audio quality** - Most common issue
2. **Review confidence score** - <0.5 indicates poor audio
3. **Check lexicon matches** - Are corrections being applied?
4. **Review GPT cleanup** - Is it helping or hurting?

### Database Issues

**Reset database:**
```bash
docker-compose down -v
docker-compose up -d
```
**Warning**: This deletes all data!

---

## 📁 Project Structure

```
speech-to-text-master-plan-/
├── app/
│   ├── api/endpoints/       # REST API routes
│   ├── models/              # Database models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   │   ├── openai_service.py        # Whisper integration
│   │   ├── lexicon_service.py       # Lexicon corrections
│   │   ├── postprocessing_service.py # GPT cleanup
│   │   └── fuzzy_matching_service.py # Fuzzy matching
│   └── workers/             # Background workers
├── alembic/                 # Database migrations
├── tests/                   # Test suite
├── medical_corrections.csv  # Lexicon data
├── docker-compose.yml       # Service orchestration
├── README.md               # This file
└── QUICKSTART.md           # Quick start guide
```

---

## 📝 License

[Your License Here]

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

---

## 📞 Support

- **Documentation**: See [QUICKSTART.md](QUICKSTART.md)
- **API Docs**: http://localhost:8080/docs
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)

---

**Built with ❤️ for Persian medical transcription**
