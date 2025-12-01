#!/usr/bin/env python3
"""
Basic usage examples for OpenAI Whisper API integration.

This script demonstrates various ways to use the transcription service.
Make sure to set OPENAI_API_KEY environment variable before running.
"""
import logging
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.exceptions import (
    APIKeyError,
    AudioFormatError,
    MaxRetriesExceededError,
    RateLimitError,
    TranscriptionError,
)
from app.services.openai_service import transcribe_audio, OpenAITranscriptionService


def setup_logging():
    """Configure logging to see service activity."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def example_1_basic_transcription():
    """Example 1: Basic audio transcription."""
    print("\n=== Example 1: Basic Transcription ===")
    
    # Replace with your actual audio file path
    audio_file = "path/to/your/audio.mp3"
    
    try:
        text = transcribe_audio(audio_file)
        print(f"Transcription: {text}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please provide a valid audio file path.")
    except TranscriptionError as e:
        print(f"Transcription error: {e}")


def example_2_with_language():
    """Example 2: Transcription with explicit language."""
    print("\n=== Example 2: Transcription with Language ===")
    
    audio_file = "path/to/spanish/audio.mp3"
    
    try:
        # Specify Spanish language for better accuracy
        text = transcribe_audio(audio_file, language="es")
        print(f"Spanish transcription: {text}")
    except FileNotFoundError as e:
        print(f"Error: {e}")


def example_3_error_handling():
    """Example 3: Comprehensive error handling."""
    print("\n=== Example 3: Error Handling ===")
    
    audio_file = "path/to/your/audio.mp3"
    
    try:
        text = transcribe_audio(audio_file)
        print(f"Success: {text[:100]}...")  # Print first 100 chars
        
    except APIKeyError as e:
        print(f"API Key Error: {e}")
        print("Please set OPENAI_API_KEY environment variable.")
        
    except AudioFormatError as e:
        print(f"Audio Format Error: {e}")
        print("Supported formats: WAV, MP3, M4A, MP4, MPEG, MPGA, WebM, OGG, FLAC")
        
    except RateLimitError as e:
        print(f"Rate Limit Error: {e}")
        if e.retry_after:
            print(f"Retry after {e.retry_after} seconds")
        
    except MaxRetriesExceededError as e:
        print(f"Max Retries Exceeded: {e}")
        print(f"Last error: {e.last_error}")
        
    except FileNotFoundError as e:
        print(f"File Not Found: {e}")
        
    except TranscriptionError as e:
        print(f"Transcription Error: {e}")


def example_4_service_class():
    """Example 4: Using the service class directly."""
    print("\n=== Example 4: Using Service Class ===")
    
    try:
        # Create service instance
        service = OpenAITranscriptionService()
        
        # Transcribe multiple files
        audio_files = [
            "path/to/audio1.mp3",
            "path/to/audio2.wav",
            "path/to/audio3.m4a",
        ]
        
        for audio_file in audio_files:
            try:
                text = service.transcribe_audio(audio_file)
                print(f"\n{Path(audio_file).name}:")
                print(f"  {text[:80]}...")  # Print first 80 chars
            except FileNotFoundError:
                print(f"\n{Path(audio_file).name}: File not found (skipping)")
                
    except APIKeyError as e:
        print(f"Service initialization error: {e}")


def example_5_multilingual():
    """Example 5: Multilingual and code-switching audio."""
    print("\n=== Example 5: Multilingual Audio ===")
    
    # Example with code-switching (English + Spanish)
    audio_file = "path/to/multilingual/audio.mp3"
    
    try:
        # Let Whisper auto-detect languages
        text = transcribe_audio(audio_file)
        print(f"Multilingual transcription: {text}")
        print("\nNote: Whisper preserves original language/script for each word")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")


def example_6_batch_processing():
    """Example 6: Batch processing with progress tracking."""
    print("\n=== Example 6: Batch Processing ===")
    
    audio_files = [
        "path/to/audio1.mp3",
        "path/to/audio2.mp3",
        "path/to/audio3.mp3",
    ]
    
    results = []
    
    for i, audio_file in enumerate(audio_files, 1):
        print(f"\nProcessing {i}/{len(audio_files)}: {Path(audio_file).name}")
        
        try:
            text = transcribe_audio(audio_file)
            results.append({
                "file": audio_file,
                "status": "success",
                "text": text
            })
            print(f"  ✓ Success ({len(text)} chars)")
            
        except FileNotFoundError:
            results.append({
                "file": audio_file,
                "status": "not_found",
                "text": None
            })
            print(f"  ✗ File not found")
            
        except TranscriptionError as e:
            results.append({
                "file": audio_file,
                "status": "error",
                "text": None,
                "error": str(e)
            })
            print(f"  ✗ Error: {e}")
    
    # Summary
    print(f"\n\nSummary:")
    print(f"  Total: {len(results)}")
    print(f"  Success: {sum(1 for r in results if r['status'] == 'success')}")
    print(f"  Errors: {sum(1 for r in results if r['status'] == 'error')}")


def main():
    """Run all examples."""
    setup_logging()
    
    print("OpenAI Whisper API Integration - Usage Examples")
    print("=" * 60)
    
    # Note: Update audio file paths in each example before running
    print("\nNote: Update audio file paths in the examples before running.")
    print("These examples demonstrate the API usage patterns.\n")
    
    # Uncomment the examples you want to run:
    
    # example_1_basic_transcription()
    # example_2_with_language()
    # example_3_error_handling()
    # example_4_service_class()
    # example_5_multilingual()
    # example_6_batch_processing()
    
    print("\n" + "=" * 60)
    print("Examples complete!")


if __name__ == "__main__":
    main()
