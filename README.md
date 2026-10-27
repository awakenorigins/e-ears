# e-ears — AI-powered music analysis for agents

> Drop in an audio file and get back BPM, key, mood, energy, and transcribed lyrics. Built on a battle-tested Python audio stack so your agent can actually "hear" music.

[![OpenClaw Skill](https://img.shields.io/badge/OpenClaw-Skill-blueviolet)](https://github.com/NachaFromMars)

## Overview
e-ears gives OpenClaw agents the ability to analyze audio like a producer. It uses librosa, soundfile, numpy, and scipy for signal analysis, and Whisper for lyric transcription. Three modes: a fast quick scan (~5s), a deep full analysis (~60s), and side-by-side track comparison. Output formats suit both automation pipelines and conversational replies.

## Features
- **Quick scan (~5s):** BPM, key, mood, energy, danceability
- **Full analysis (~60s):** complete audio features + vocal quality + lyrics
- **Compare tracks:** side-by-side analysis of two audio files
- **Lyrics transcription:** Whisper-powered vocal-to-text
- **Output formats:** `--format json/text/agent`
- **Toggles:** `--no-lyrics`, `--no-vocals`, `-o` output file

## Usage / Quick Start
```bash
# Fast overview
python scripts/ears.py quick song.mp3

# Full analysis with lyrics
python scripts/ears.py analyze song.mp3 --format agent

# Lyrics only
python scripts/ears.py lyrics song.mp3 --language en

# Compare two tracks
python scripts/ears.py compare track_a.mp3 track_b.mp3
```

## Trigger Keywords (OpenClaw)
analyze music, music analysis, e-ears, BPM, key detection, lyrics transcription, compare tracks

## Related Skills
- [edge-tts](https://github.com/NachaFromMars/edge-tts) — text-to-speech generation

---
Part of the [NachaFromMars](https://github.com/NachaFromMars) OpenClaw skill ecosystem.
