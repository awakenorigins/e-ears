# -*- coding: utf-8 -*-
"""Lyrics transcription via Whisper CLI."""

import os
import sys
import json
import subprocess
import tempfile

WHISPER_PATH = r"C:\Users\Admin\AppData\Local\Programs\Python\Python312\Scripts\whisper.exe"


def transcribe(file_path: str, language: str = 'vi', model: str = 'small') -> dict:
    """Transcribe audio file using Whisper CLI.
    
    Args:
        file_path: Path to audio file
        language: Language code (default: 'vi' for Vietnamese)
        model: Whisper model size (default: 'small')
    
    Returns:
        Dict with 'text', 'segments', 'language', 'duration'
    """
    file_path = os.path.abspath(file_path)
    
    if not os.path.isfile(file_path):
        return {'error': f'File not found: {file_path}', 'text': '', 'segments': []}
    
    if not os.path.isfile(WHISPER_PATH):
        return {
            'error': f'Whisper not found at {WHISPER_PATH}',
            'text': '',
            'segments': [],
            'hint': 'Install whisper: pip install openai-whisper',
        }
    
    try:
        # Use temp directory for output
        with tempfile.TemporaryDirectory() as tmpdir:
            cmd = [
                WHISPER_PATH,
                file_path,
                '--language', language,
                '--model', model,
                '--output_format', 'json',
                '--output_dir', tmpdir,
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                encoding='utf-8',
                errors='replace',
            )
            
            if result.returncode != 0:
                return {
                    'error': f'Whisper failed: {result.stderr[:500]}',
                    'text': '',
                    'segments': [],
                }
            
            # Find the JSON output file
            json_files = [f for f in os.listdir(tmpdir) if f.endswith('.json')]
            if not json_files:
                return {
                    'error': 'No JSON output from Whisper',
                    'text': '',
                    'segments': [],
                }
            
            json_path = os.path.join(tmpdir, json_files[0])
            with open(json_path, 'r', encoding='utf-8') as f:
                whisper_output = json.load(f)
            
            # Parse segments
            segments = []
            for seg in whisper_output.get('segments', []):
                segments.append({
                    'start': round(seg.get('start', 0), 2),
                    'end': round(seg.get('end', 0), 2),
                    'text': seg.get('text', '').strip(),
                })
            
            full_text = whisper_output.get('text', '').strip()
            
            return {
                'text': full_text,
                'segments': segments,
                'language': language,
                'model': model,
                'segment_count': len(segments),
            }
    
    except subprocess.TimeoutExpired:
        return {'error': 'Whisper timed out (>5 minutes)', 'text': '', 'segments': []}
    except Exception as e:
        return {'error': f'Transcription failed: {str(e)}', 'text': '', 'segments': []}


def format_lyrics(result: dict) -> str:
    """Format transcription result as readable lyrics with timestamps."""
    if result.get('error'):
        return f"❌ Transcription error: {result['error']}"
    
    if not result.get('text'):
        return "⚠️ No lyrics detected."
    
    lines = []
    lines.append("📝 LYRICS TRANSCRIPTION")
    lines.append(f"Language: {result.get('language', 'unknown')} | Model: {result.get('model', 'unknown')}")
    lines.append("─" * 40)
    
    for seg in result.get('segments', []):
        start = seg['start']
        minutes = int(start) // 60
        secs = int(start) % 60
        timestamp = f"[{minutes}:{secs:02d}]"
        lines.append(f"{timestamp} {seg['text']}")
    
    lines.append("─" * 40)
    lines.append(f"Total segments: {result.get('segment_count', 0)}")
    
    return '\n'.join(lines)
