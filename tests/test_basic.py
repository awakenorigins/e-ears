#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick test for E-Ears."""
import sys, os, io, time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, r'C:\Users\Admin\.openclaw\workspace\skills\e-ears')

TEST_FILE = r'C:\Users\Admin\.openclaw\workspace\suno-reforge\output\Nang-v3-male-1.mp3'

print("=== E-EARS TEST ===")
t0 = time.time()

from scripts.utils.audio import load_audio
print("Loading audio...")
y, sr = load_audio(TEST_FILE)
print(f"  Loaded: {len(y)} samples, {sr}Hz, {len(y)/sr:.1f}s")

from scripts.core.features import extract_all
print("Extracting features...")
features = extract_all(y, sr)
print(f"  BPM: {features['bpm']}")
print(f"  Key: {features['key']} (confidence: {features['key_confidence']})")
print(f"  RMS: {features['rms_energy']['mean']:.4f}")

from scripts.core.mood import classify_mood
print("Classifying mood...")
mood = classify_mood(features)
print(f"  Mood: {mood['mood']}")
print(f"  Energy: {mood['energy']}, Dance: {mood['danceability']}, Valence: {mood['valence']}")
print(f"  Tags: {mood['tags']}")

from scripts.core.structure import detect_segments
print("Detecting structure...")
segs = detect_segments(y, sr)
print(f"  Found {len(segs)} segments:")
for s in segs:
    print(f"    {s['start_fmt']}-{s['end_fmt']} [{s['label']}] {s.get('description','')}")

from scripts.core.vocal import analyze_vocals, get_vocal_summary
print("Analyzing vocals...")
vocal = analyze_vocals(y, sr)
print(f"  {get_vocal_summary(vocal)}")
print(f"  Gender: {vocal.get('gender_estimate')}, Register: {vocal.get('register')}")

elapsed = time.time() - t0
print(f"\nTotal time: {elapsed:.1f}s")
print("=== TEST COMPLETE ===")
