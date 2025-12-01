#!/usr/bin/env python3
"""
Test script for the transcription API endpoint.
Demonstrates how to submit audio files for transcription.
"""

import requests
import sys
from pathlib import Path


def test_transcribe_endpoint(
    api_url: str = "http://localhost:8000/transcribe",
    audio_file_path: str = "test_audio.wav",
    api_key: str = "your-secret-api-key-here",
    lexicon: str = "radiology"
):
    """
    Test the /transcribe endpoint with an audio file.
    
    Args:
        api_url: URL of the transcription endpoint
        audio_file_path: Path to the audio file to upload
        api_key: Your API key
        lexicon: Lexicon to use for transcription
    """
    
    # Check if file exists
    audio_file = Path(audio_file_path)
    if not audio_file.exists():
        print(f"❌ Error: Audio file not found: {audio_file_path}")
        print("Create a test audio file or provide a valid path.")
        return False
    
    # Prepare request
    headers = {
        "X-API-Key": api_key,
        "X-Lexicon-ID": lexicon
    }
    
    files = {
        "audio": open(audio_file, "rb")
    }
    
    print(f"📤 Submitting audio file: {audio_file.name}")
    print(f"   Size: {audio_file.stat().st_size / 1024:.2f} KB")
    print(f"   Lexicon: {lexicon}")
    print(f"   Endpoint: {api_url}")
    
    try:
        # Make request
        response = requests.post(api_url, headers=headers, files=files)
        
        # Check response
        if response.status_code == 202:
            print("\n✅ Success! Job submitted.")
            data = response.json()
            print(f"   Job ID: {data['job_id']}")
            print(f"   Status: {data['status']}")
            print(f"   Created: {data['created_at']}")
            return True
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(f"   {response.json()}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API server")
        print("   Make sure the server is running (docker-compose up)")
        return False
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False


def test_invalid_format(api_url: str = "http://localhost:8000/transcribe", api_key: str = "your-secret-api-key-here"):
    """Test that invalid file formats are rejected."""
    print("\n\n🧪 Testing invalid file format handling...")
    
    # Create a fake text file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is not an audio file")
        temp_path = f.name
    
    headers = {"X-API-Key": api_key}
    files = {"audio": open(temp_path, "rb")}
    
    try:
        response = requests.post(api_url, headers=headers, files=files)
        if response.status_code == 400:
            print("✅ Invalid format correctly rejected (400)")
            print(f"   Error: {response.json()['detail']}")
        else:
            print(f"❌ Expected 400, got {response.status_code}")
    finally:
        Path(temp_path).unlink()


def test_no_api_key(api_url: str = "http://localhost:8000/transcribe"):
    """Test that requests without API key are rejected."""
    print("\n\n🧪 Testing authentication requirement...")
    
    import tempfile
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.wav', delete=False) as f:
        f.write(b"fake audio data")
        temp_path = f.name
    
    files = {"audio": open(temp_path, "rb")}
    
    try:
        response = requests.post(api_url, files=files)
        if response.status_code == 401:
            print("✅ Missing API key correctly rejected (401)")
            print(f"   Error: {response.json()['detail']}")
        else:
            print(f"❌ Expected 401, got {response.status_code}")
    finally:
        Path(temp_path).unlink()


if __name__ == "__main__":
    print("=" * 60)
    print("Audio Transcription API - Test Suite")
    print("=" * 60)
    
    # You can customize these values
    API_URL = "http://localhost:8000/transcribe"
    API_KEY = "your-secret-api-key-here"
    
    # Test 1: Valid upload (if you have an audio file)
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
        test_transcribe_endpoint(API_URL, audio_file, API_KEY)
    else:
        print("\n💡 Usage: python test_api.py <path-to-audio-file>")
        print("   Example: python test_api.py sample.wav")
    
    # Test 2: Invalid format
    test_invalid_format(API_URL, API_KEY)
    
    # Test 3: Missing authentication
    test_no_api_key(API_URL)
    
    print("\n" + "=" * 60)
    print("Test suite completed")
    print("=" * 60)
