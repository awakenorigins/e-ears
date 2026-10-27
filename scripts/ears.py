#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E-Ears — AI Music Analysis CLI
================================
Unified entry point for all E-Ears analysis commands.

Usage:
    python ears.py analyze <file>          Full analysis
    python ears.py quick <file>            Quick scan (BPM + key + mood, ~5s)
    python ears.py compare <f1> <f2> ...   Compare 2+ tracks
    python ears.py lyrics <file>           Lyrics transcription only

Options:
    --format json|text|agent    Output format (default: agent)
    --output <path>             Save output to file
    --language <code>           Whisper language (default: vi)
    --no-lyrics                 Skip lyrics transcription
    --no-vocals                 Skip vocal analysis
"""

import os
import sys
import json
import argparse
import time

# Add scripts directory to path so subpackages resolve
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
# Ensure scripts/ is importable as a top-level package
if SKILL_DIR not in sys.path:
    sys.path.insert(0, SKILL_DIR)
# Also add scripts/ itself for direct subpackage imports
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from scripts.utils.audio import load_audio, validate_file, get_duration, format_time
from scripts.core.features import extract_all, extract_quick
from scripts.core.mood import classify_mood
from scripts.core.structure import detect_segments, get_structure_summary
from scripts.core.vocal import analyze_vocals, get_vocal_summary
from scripts.core.transcribe import transcribe, format_lyrics
from scripts.core.comparison import compare_tracks, format_comparison_text
from scripts.formatters.json_fmt import format_json
from scripts.formatters.text_fmt import format_text
from scripts.formatters.agent_fmt import format_agent


def cmd_analyze(args):
    """Full analysis of a single audio file."""
    file_path = validate_file(args.file)
    filename = os.path.basename(file_path)
    
    print(f"🦻 E-Ears analyzing: {filename}", file=sys.stderr)
    t0 = time.time()
    
    # Load audio
    print("  Loading audio...", file=sys.stderr)
    y, sr = load_audio(file_path)
    
    # Extract features
    print("  Extracting features...", file=sys.stderr)
    features = extract_all(y, sr)
    
    # Classify mood
    print("  Classifying mood...", file=sys.stderr)
    mood = classify_mood(features)
    
    # Detect structure
    print("  Detecting structure...", file=sys.stderr)
    structure = detect_segments(y, sr)
    
    # Vocal analysis
    vocal = {}
    if not args.no_vocals:
        print("  Analyzing vocals...", file=sys.stderr)
        vocal = analyze_vocals(y, sr)
    
    # Lyrics
    lyrics = {}
    if not args.no_lyrics:
        print("  Transcribing lyrics...", file=sys.stderr)
        lyrics = transcribe(file_path, language=args.language)
    
    elapsed = time.time() - t0
    print(f"  Done in {elapsed:.1f}s", file=sys.stderr)
    
    # Build result
    analysis = {
        'filename': filename,
        'file_path': file_path,
        'analysis_time_seconds': round(elapsed, 1),
        'features': features,
        'mood': mood,
        'structure': structure,
        'vocal': vocal,
        'lyrics': lyrics,
    }
    
    # Format output
    output = _format_output(analysis, args.format)
    
    # Write or print
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"  Saved to: {args.output}", file=sys.stderr)
    else:
        print(output)


def cmd_quick(args):
    """Quick scan: BPM + key + mood only."""
    file_path = validate_file(args.file)
    filename = os.path.basename(file_path)
    
    print(f"🦻 E-Ears quick scan: {filename}", file=sys.stderr)
    t0 = time.time()
    
    y, sr = load_audio(file_path)
    features = extract_quick(y, sr)
    mood = classify_mood(features)
    
    elapsed = time.time() - t0
    
    result = {
        'filename': filename,
        'bpm': features['bpm'],
        'key': features['key'],
        'key_mode': features['key_mode'],
        'duration': format_time(features['duration_seconds']),
        'mood': mood['mood'],
        'energy': mood['energy'],
        'danceability': mood['danceability'],
        'valence': mood['valence'],
        'tags': mood['tags'],
        'scan_time': f"{elapsed:.1f}s",
    }
    
    if args.format == 'json':
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"🎵 {filename}")
        print(f"   BPM: {result['bpm']} | Key: {result['key']} | Mood: {result['mood']}")
        print(f"   Energy: {result['energy']} | Dance: {result['danceability']} | Valence: {result['valence']}")
        print(f"   Tags: {', '.join(result['tags'])}")
        print(f"   Duration: {result['duration']} | Scanned in {result['scan_time']}")


def cmd_compare(args):
    """Compare 2+ audio tracks."""
    if len(args.files) < 2:
        print("❌ Need at least 2 files to compare.", file=sys.stderr)
        sys.exit(1)
    
    validated = [validate_file(f) for f in args.files]
    
    print(f"🦻 E-Ears comparing {len(validated)} tracks...", file=sys.stderr)
    t0 = time.time()
    
    result = compare_tracks(validated)
    
    elapsed = time.time() - t0
    print(f"  Done in {elapsed:.1f}s", file=sys.stderr)
    
    if args.format == 'json':
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    else:
        print(format_comparison_text(result))


def cmd_lyrics(args):
    """Transcribe lyrics only."""
    file_path = validate_file(args.file)
    filename = os.path.basename(file_path)
    
    print(f"🦻 E-Ears transcribing: {filename}", file=sys.stderr)
    
    result = transcribe(file_path, language=args.language, model=args.whisper_model)
    
    if args.format == 'json':
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(format_lyrics(result))


def _format_output(analysis: dict, fmt: str) -> str:
    """Format analysis result in requested format."""
    if fmt == 'json':
        return format_json(analysis)
    elif fmt == 'text':
        return format_text(analysis)
    else:  # agent (default)
        return format_agent(analysis)


def main():
    # Fix Windows encoding
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    parser = argparse.ArgumentParser(
        prog='ears',
        description='E-Ears — AI Music Analysis for OpenClaw 🦻',
    )
    subparsers = parser.add_subparsers(dest='command', help='Command')
    
    # analyze
    p_analyze = subparsers.add_parser('analyze', help='Full analysis')
    p_analyze.add_argument('file', help='Audio file path')
    p_analyze.add_argument('--format', choices=['json', 'text', 'agent'], default='agent')
    p_analyze.add_argument('--output', '-o', help='Save output to file')
    p_analyze.add_argument('--language', default='vi', help='Whisper language (default: vi)')
    p_analyze.add_argument('--no-lyrics', action='store_true', help='Skip lyrics')
    p_analyze.add_argument('--no-vocals', action='store_true', help='Skip vocal analysis')
    
    # quick
    p_quick = subparsers.add_parser('quick', help='Quick scan (BPM + key + mood)')
    p_quick.add_argument('file', help='Audio file path')
    p_quick.add_argument('--format', choices=['json', 'text', 'agent'], default='agent')
    
    # compare
    p_compare = subparsers.add_parser('compare', help='Compare 2+ tracks')
    p_compare.add_argument('files', nargs='+', help='Audio files to compare')
    p_compare.add_argument('--format', choices=['json', 'text', 'agent'], default='text')
    
    # lyrics
    p_lyrics = subparsers.add_parser('lyrics', help='Transcribe lyrics')
    p_lyrics.add_argument('file', help='Audio file path')
    p_lyrics.add_argument('--format', choices=['json', 'text'], default='text')
    p_lyrics.add_argument('--language', default='vi', help='Language code')
    p_lyrics.add_argument('--whisper-model', default='small', help='Whisper model size')
    
    args = parser.parse_args()
    
    if args.command == 'analyze':
        cmd_analyze(args)
    elif args.command == 'quick':
        cmd_quick(args)
    elif args.command == 'compare':
        cmd_compare(args)
    elif args.command == 'lyrics':
        cmd_lyrics(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
