#!/usr/bin/env python3
"""
Generate minimal test audio files for testing.

Creates small, valid audio files in WAV, MP3, and M4A formats
that can be used in tests without requiring actual audio content.
"""
import wave
import struct
from pathlib import Path


def create_minimal_wav(filepath: Path, duration: float = 0.1, sample_rate: int = 16000):
    """
    Create a minimal WAV file with silence.
    
    Args:
        filepath: Path where to save the WAV file
        duration: Duration in seconds (default 0.1s for minimal size)
        sample_rate: Sample rate in Hz (default 16000)
    """
    num_samples = int(sample_rate * duration)
    
    with wave.open(str(filepath), 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        # Write silence (zeros)
        for _ in range(num_samples):
            wav_file.writeframes(struct.pack('<h', 0))
    
    print(f"Created {filepath.name} ({filepath.stat().st_size} bytes)")


def create_minimal_mp3(filepath: Path):
    """
    Create a minimal valid MP3 file.
    
    This creates a file with a valid MP3 header but minimal data.
    For actual MP3 encoding, you would need a library like pydub.
    This creates a minimal stub that passes format validation.
    
    Args:
        filepath: Path where to save the MP3 file
    """
    # Minimal MP3 frame header (ID3v2 tag + one audio frame)
    # This is a simplified version that creates a valid-looking MP3
    mp3_data = bytearray([
        # ID3v2 header
        0x49, 0x44, 0x33,  # "ID3"
        0x03, 0x00,        # Version 2.3
        0x00,              # Flags
        0x00, 0x00, 0x00, 0x00,  # Size (synchsafe integer)
        # Minimal MP3 frame header (MPEG1 Layer3)
        0xFF, 0xFB,        # Frame sync + MPEG1 Layer3
        0x90, 0x00,        # Bitrate + Samplerate
        # Padding with zeros
    ] + [0x00] * 100)
    
    filepath.write_bytes(bytes(mp3_data))
    print(f"Created {filepath.name} ({filepath.stat().st_size} bytes)")


def create_minimal_m4a(filepath: Path):
    """
    Create a minimal valid M4A/AAC file.
    
    This creates a file with a valid M4A container (MP4) header.
    
    Args:
        filepath: Path where to save the M4A file
    """
    # Minimal M4A/MP4 container with required atoms
    # ftyp atom (file type)
    ftyp = bytearray([
        0x00, 0x00, 0x00, 0x20,  # atom size (32 bytes)
        0x66, 0x74, 0x79, 0x70,  # "ftyp"
        0x4D, 0x34, 0x41, 0x20,  # "M4A "
        0x00, 0x00, 0x00, 0x00,  # minor version
        0x4D, 0x34, 0x41, 0x20,  # compatible brand "M4A "
        0x69, 0x73, 0x6F, 0x6D,  # compatible brand "isom"
        0x00, 0x00, 0x00, 0x00,  # padding
    ])
    
    # mdat atom (media data) - minimal
    mdat = bytearray([
        0x00, 0x00, 0x00, 0x08,  # atom size (8 bytes - just header)
        0x6D, 0x64, 0x61, 0x74,  # "mdat"
    ])
    
    m4a_data = bytes(ftyp + mdat)
    filepath.write_bytes(m4a_data)
    print(f"Created {filepath.name} ({filepath.stat().st_size} bytes)")


def main():
    """Generate all test audio files."""
    # Get the directory where this script is located
    audio_dir = Path(__file__).parent
    
    print("Generating test audio files...")
    print(f"Output directory: {audio_dir}")
    print()
    
    # Create WAV file
    wav_path = audio_dir / "sample_english.wav"
    create_minimal_wav(wav_path)
    
    # Create MP3 file
    mp3_path = audio_dir / "sample_persian.mp3"
    create_minimal_mp3(mp3_path)
    
    # Create M4A file
    m4a_path = audio_dir / "sample_medical.m4a"
    create_minimal_m4a(m4a_path)
    
    print()
    print("✓ All test audio files created successfully!")
    print()
    print("Files created:")
    for file in [wav_path, mp3_path, m4a_path]:
        if file.exists():
            print(f"  - {file.name}: {file.stat().st_size} bytes")


if __name__ == "__main__":
    main()
