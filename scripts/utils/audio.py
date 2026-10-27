# -*- coding: utf-8 -*-
"""Audio loading, resampling, and validation utilities."""

import os
import sys
import numpy as np

# Default sample rate for all analysis
DEFAULT_SR = 22050
# Duration limit (seconds) — cap very long files for speed
MAX_DURATION = 600  # 10 minutes


def validate_file(path: str) -> str:
    """Validate that the audio file exists and is a supported format.
    
    Returns the absolute path if valid, raises SystemExit on error.
    """
    path = os.path.abspath(path)
    if not os.path.isfile(path):
        print(f"❌ File not found: {path}", file=sys.stderr)
        sys.exit(1)
    
    ext = os.path.splitext(path)[1].lower()
    supported = {'.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac', '.wma', '.opus'}
    if ext not in supported:
        print(f"❌ Unsupported format '{ext}'. Supported: {', '.join(sorted(supported))}", file=sys.stderr)
        sys.exit(1)
    
    # Check file size
    size_mb = os.path.getsize(path) / (1024 * 1024)
    if size_mb < 0.01:
        print(f"❌ File too small ({size_mb:.2f} MB) — probably corrupt.", file=sys.stderr)
        sys.exit(1)
    
    return path


def load_audio(path: str, sr: int = DEFAULT_SR, mono: bool = True, duration: float = None):
    """Load audio file with librosa. Returns (y, sr).
    
    Args:
        path: Path to audio file
        sr: Target sample rate (default 22050)
        mono: Convert to mono (default True)
        duration: Max duration in seconds (default None = full file)
    
    Returns:
        Tuple of (audio_array, sample_rate)
    """
    import librosa
    
    path = validate_file(path)
    
    try:
        y, sr_out = librosa.load(path, sr=sr, mono=mono, duration=duration)
    except Exception as e:
        print(f"❌ Failed to load audio: {e}", file=sys.stderr)
        sys.exit(1)
    
    if len(y) == 0:
        print("❌ Audio file is empty after loading.", file=sys.stderr)
        sys.exit(1)
    
    return y, sr_out


def get_duration(y, sr: int) -> float:
    """Get duration in seconds."""
    return len(y) / sr


def format_time(seconds: float) -> str:
    """Format seconds to M:SS string."""
    minutes = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{minutes}:{secs:02d}"


def hz_to_note(freq_hz: float) -> str:
    """Convert frequency in Hz to musical note name (e.g., 440 -> A4)."""
    if freq_hz <= 0:
        return "N/A"
    
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    # A4 = 440 Hz, MIDI 69
    midi = 69 + 12 * np.log2(freq_hz / 440.0)
    midi_round = int(round(midi))
    
    note_idx = midi_round % 12
    octave = (midi_round // 12) - 1
    
    return f"{note_names[note_idx]}{octave}"


def safe_mean(arr):
    """Compute mean safely, returning 0.0 for empty arrays."""
    if arr is None or len(arr) == 0:
        return 0.0
    return float(np.mean(arr))


def safe_std(arr):
    """Compute std safely, returning 0.0 for empty arrays."""
    if arr is None or len(arr) == 0:
        return 0.0
    return float(np.std(arr))
