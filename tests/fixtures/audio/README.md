# Test Audio Files

This directory contains small sample audio files for testing purposes.

## Files

The following test audio files are available:

### 1. `sample_english.wav` (Mock WAV file)
- **Format:** WAV (RIFF header)
- **Size:** ~500 bytes
- **Duration:** ~1 second (simulated)
- **Content:** Silent/minimal audio data
- **Use Case:** Testing WAV file upload and processing

### 2. `sample_persian.mp3` (Mock MP3 file)
- **Format:** MP3
- **Size:** ~500 bytes
- **Duration:** ~1 second (simulated)
- **Content:** Silent/minimal audio data
- **Use Case:** Testing MP3 file upload and processing

### 3. `sample_medical.m4a` (Mock M4A file)
- **Format:** M4A/AAC
- **Size:** ~500 bytes
- **Duration:** ~1 second (simulated)
- **Content:** Silent/minimal audio data
- **Use Case:** Testing M4A file upload and processing

## Creating Test Audio Files

These are minimal mock audio files created for testing purposes. They contain valid file headers but minimal audio data to keep test suite fast.

### Programmatic Creation

You can create these files programmatically in your test fixtures:

```python
import wave
import struct

def create_minimal_wav(filepath: str, duration: float = 1.0):
    """Create a minimal WAV file for testing."""
    sample_rate = 16000
    num_samples = int(sample_rate * duration)
    
    with wave.open(filepath, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        # Write silence
        for _ in range(num_samples):
            wav_file.writeframes(struct.pack('<h', 0))
```

### Manual Creation (if needed)

For actual audio file testing, you can use tools like:
- `ffmpeg` to generate test tones
- `sox` for audio file manipulation
- Online tone generators

Example with ffmpeg:
```bash
# Generate 1-second silent WAV file
ffmpeg -f lavfi -i anullsrc=r=16000:cl=mono -t 1 -acodec pcm_s16le sample_english.wav

# Convert to MP3
ffmpeg -i sample_english.wav -acodec libmp3lame sample_persian.mp3

# Convert to M4A
ffmpeg -i sample_english.wav -acodec aac sample_medical.m4a
```

## Usage in Tests

Import and use these files in your tests:

```python
import os
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "audio"

def test_audio_upload():
    audio_file_path = FIXTURES_DIR / "sample_english.wav"
    assert audio_file_path.exists()
    
    # Use in your test...
    with open(audio_file_path, 'rb') as f:
        # Upload or process file
        pass
```

## Important Notes

1. **Not Real Audio:** These files contain minimal/silent audio data for speed
2. **Small Size:** Kept under 1KB each to minimize repo size and speed up tests
3. **Valid Headers:** Each file has valid format headers for proper validation
4. **Fast Tests:** Using minimal files keeps test suite execution fast
5. **Mock Transcriptions:** Actual transcription results should be mocked in tests

## Extending

To add more test audio files:

1. Create the file using tools above
2. Keep file size minimal (<1KB if possible)
3. Document the file in this README
4. Update any relevant test fixtures
