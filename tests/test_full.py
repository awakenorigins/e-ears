#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Full analysis test — agent format output."""
import sys, os, io, time, json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, r'C:\Users\Admin\.openclaw\workspace\skills\e-ears')

TEST_FILE = r'C:\Users\Admin\.openclaw\workspace\suno-reforge\output\Nang-v3-male-1.mp3'

from scripts.utils.audio import load_audio
from scripts.core.features import extract_all
from scripts.core.mood import classify_mood
from scripts.core.structure import detect_segments
from scripts.core.vocal import analyze_vocals
from scripts.formatters.agent_fmt import format_agent

t0 = time.time()

y, sr = load_audio(TEST_FILE)
features = extract_all(y, sr)
mood = classify_mood(features)
structure = detect_segments(y, sr)
vocal = analyze_vocals(y, sr)

analysis = {
    'filename': os.path.basename(TEST_FILE),
    'features': features,
    'mood': mood,
    'structure': structure,
    'vocal': vocal,
}

output = format_agent(analysis)
elapsed = time.time() - t0

print(output)
print(f"\n[Analysis time: {elapsed:.1f}s]")
