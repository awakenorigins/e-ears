# E-Ears — AI Music Analysis Skill 🦻

> "Tao không nghe nhạc bằng tai — tao đọc nó bằng data."

## Description

Phân tích audio/nhạc toàn diện — BPM, key, mood, structure, vocal quality, lyrics transcription, track comparison. Biến AI agent từ "điếc" thành "có tai nghe nhạc".

**Triggers:** analyze music, music analysis, e-ears, nghe nhạc, phân tích bài hát, so sánh bài hát, compare tracks, lyrics, BPM, key detection

## Requirements

- Python 3.12+
- Libraries: librosa, soundfile, numpy, scipy (đã cài sẵn)
- Whisper CLI: `whisper`
- GPU: Optional (Whisper dùng CUDA nếu có)

## Usage

### Quick Scan (~5 giây)
```bash
python scripts/ears.py quick <file.mp3>
```
Output: BPM, key, mood, energy, danceability

### Full Analysis (~60 giây)
```bash
python scripts/ears.py analyze <file.mp3>                    # Agent format (~500 tokens)
python scripts/ears.py analyze <file.mp3> --format json      # Full JSON
python scripts/ears.py analyze <file.mp3> --format text      # Human-readable report
python scripts/ears.py analyze <file.mp3> --no-lyrics        # Skip Whisper (faster)
python scripts/ears.py analyze <file.mp3> --no-vocals        # Skip vocal analysis
python scripts/ears.py analyze <file.mp3> -o report.json     # Save to file
```

### Compare Tracks
```bash
python scripts/ears.py compare <file1.mp3> <file2.mp3>      # Side-by-side comparison
python scripts/ears.py compare <f1> <f2> <f3> --format json  # JSON output
```

### Lyrics Only
```bash
python scripts/ears.py lyrics <file.mp3>                     # Vietnamese (default)
python scripts/ears.py lyrics <file.mp3> --language en        # English
python scripts/ears.py lyrics <file.mp3> --whisper-model medium  # Better accuracy
```

## Agent Integration

Khi agent cần "nghe" bài hát, chạy:
```bash
cd ~/.openclaw/workspace/skills/e-ears
python scripts/ears.py analyze <file> --format agent
```

Output ~500 tokens, bao gồm:
- BPM, Key, Mood, Energy, Danceability, Valence
- Song structure (timestamps + section labels)
- Vocal analysis (gender, quality, range)
- Production notes (mix quality, tone, dynamics)
- Verdict (brief assessment)

Agent đọc output → suy luận nhận xét bằng ngôn ngữ tự nhiên.

## Features

| Module | Chức năng |
|---|---|
| `core/features.py` | BPM, key (Krumhansl-Kessler), time signature, spectral, MFCC, RMS, HNR |
| `core/mood.py` | Rule-based mood (16 categories), energy, danceability, valence |
| `core/structure.py` | Segment detection + labeling (intro/verse/chorus/bridge/outro) |
| `core/vocal.py` | Vocal presence, gender, register, range, quality (breathy/clear/warm/harsh) |
| `core/comparison.py` | Multi-track comparison with scoring + recommendation |
| `core/transcribe.py` | Lyrics via Whisper CLI with timestamps |
| `formatters/agent_fmt.py` | LLM-optimized output (~500 tokens) |
| `formatters/text_fmt.py` | Human-readable report |
| `formatters/json_fmt.py` | Full JSON output |

## Architecture

```
skills/e-ears/
├── SKILL.md                    # This file
├── package.json                # Metadata
├── scripts/
│   ├── ears.py                 # CLI entry point
│   ├── __init__.py
│   ├── core/
│   │   ├── features.py         # Feature extraction (librosa)
│   │   ├── structure.py        # Song structure detection
│   │   ├── mood.py             # Mood classifier
│   │   ├── vocal.py            # Vocal analysis
│   │   ├── comparison.py       # Track comparison
│   │   └── transcribe.py       # Whisper lyrics
│   ├── formatters/
│   │   ├── agent_fmt.py        # Agent-optimized output
│   │   ├── text_fmt.py         # Human-readable
│   │   └── json_fmt.py         # JSON
│   └── utils/
│       └── audio.py            # Audio loading + helpers
├── references/
│   ├── audio-features-guide.md
│   └── mood-mapping.md
└── tests/
    └── test_basic.py
```

## Key Detection

Sử dụng Krumhansl-Kessler key profiles — tương quan chroma features với major/minor profiles cho 12 keys. Confidence > 0.8 = đáng tin.

## Mood Classification

Rule-based, 16 mood categories:
- **Melancholic** (BPM < 100, minor, low energy)
- **Somber** (BPM < 80, minor, medium energy)
- **Tender** (BPM < 85, major, low energy)
- **Dark** (BPM < 100, minor, dark spectral)
- **Warm** (BPM 80-120, major, medium energy)
- **Bittersweet** (BPM 80-110, minor, medium energy)
- **Energetic** (BPM > 120, high energy)
- **Euphoric** (BPM > 130, major, very high energy)
- **Uplifting** (BPM > 100, major, high energy)
- **Intense** (BPM > 100, minor, high energy)
- **Ambient** (dark spectral, very low energy)
- **Calm** (very low energy)
- **Bright** (bright spectral, high energy)
- **Neutral** (fallback)

## BPM Fix

librosa đôi khi detect double tempo (ví dụ 152 thay vì 76). E-Ears tự fix: nếu BPM > 140, chia đôi nếu half-tempo nằm trong khoảng 55-120.

## Limitations

- Mood classification là rule-based, không phải ML model — có thể sai với genre đặc biệt
- Vocal analysis dùng HPSS (harmonic/percussive separation) — không phải vocal isolation thực sự
- Structure detection dựa trên energy + spectral change — không nhận biết lyrics structure
- Whisper transcription phụ thuộc vào audio quality
