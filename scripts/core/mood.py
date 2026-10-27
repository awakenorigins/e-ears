# -*- coding: utf-8 -*-
"""Mood classification: rule-based mood, energy, danceability, valence."""

import numpy as np


# Mood mapping rules
MOOD_RULES = [
    # (condition_fn, mood_label, base_valence)
    # Order matters — first match wins
]


def classify_mood(features: dict) -> dict:
    """Classify mood from extracted features.
    
    Args:
        features: Dict from features.extract_all() or extract_quick()
    
    Returns:
        Dict with mood, energy, danceability, valence, tags
    """
    bpm = features.get('bpm', 100)
    key_mode = features.get('key_mode', 'major')
    rms = features.get('rms_energy', {})
    rms_mean = rms.get('mean', 0.05) if isinstance(rms, dict) else 0.05
    spectral = features.get('spectral', {})
    centroid_mean = spectral.get('spectral_centroid', {}).get('mean', 2000) if isinstance(spectral, dict) else 2000
    hnr = features.get('hnr', {})
    hnr_db = hnr.get('hnr_db', 10) if isinstance(hnr, dict) else 10
    
    # Compute energy score (0-1) from RMS + BPM + spectral
    # Raw RMS alone is misleading for normalized audio (e.g., Suno output)
    # So we blend RMS with BPM-based energy estimate
    rms_energy = _clamp(rms_mean / 0.12, 0, 1)
    bpm_energy = _clamp((bpm - 60) / 100, 0, 1)  # 60=calm, 160=energetic
    centroid_energy = _clamp((centroid_mean - 1000) / 4000, 0, 1)
    # Weighted blend: BPM matters most for perceived energy
    energy = _clamp(0.45 * bpm_energy + 0.30 * rms_energy + 0.25 * centroid_energy, 0, 1)
    
    # Danceability: based on BPM sweetspot (100-130) + beat regularity + energy
    bpm_score = 1.0 - abs(bpm - 115) / 60  # Peak at 115 BPM
    bpm_score = _clamp(bpm_score, 0, 1)
    danceability = _clamp(0.5 * bpm_score + 0.3 * energy + 0.2 * (1.0 if bpm > 90 else 0.4), 0, 1)
    
    # Determine mood
    is_minor = key_mode == 'minor'
    is_major = key_mode == 'major'
    is_bright = centroid_mean > 2500
    is_dark = centroid_mean < 1500
    
    mood = 'Neutral'
    valence = 0.5
    tags = []
    
    # Rule-based classification
    if bpm < 75 and is_minor and energy < 0.35:
        mood = 'Melancholic'
        valence = 0.15
        tags = ['sad', 'slow', 'introspective']
    elif bpm < 80 and is_minor and energy < 0.5:
        mood = 'Somber'
        valence = 0.2
        tags = ['dark', 'emotional', 'heavy']
    elif bpm < 85 and is_major and energy < 0.4:
        mood = 'Tender'
        valence = 0.45
        tags = ['gentle', 'intimate', 'soft']
    elif bpm < 100 and is_minor and energy < 0.5:
        mood = 'Melancholic'
        valence = 0.25
        tags = ['reflective', 'moody']
    elif bpm < 100 and is_minor and is_dark:
        mood = 'Dark'
        valence = 0.15
        tags = ['moody', 'atmospheric', 'brooding']
    elif 80 <= bpm <= 120 and is_major and 0.3 <= energy <= 0.7:
        mood = 'Warm'
        valence = 0.65
        tags = ['nostalgic', 'comforting', 'smooth']
    elif 80 <= bpm <= 110 and is_minor and 0.3 <= energy <= 0.6:
        mood = 'Bittersweet'
        valence = 0.4
        tags = ['nostalgic', 'wistful', 'emotional']
    elif bpm > 120 and energy > 0.6:
        mood = 'Energetic'
        valence = 0.8
        tags = ['upbeat', 'driving', 'powerful']
    elif bpm > 130 and energy > 0.7 and is_major:
        mood = 'Euphoric'
        valence = 0.9
        tags = ['ecstatic', 'peak', 'joyful']
    elif bpm > 100 and energy > 0.5 and is_major:
        mood = 'Uplifting'
        valence = 0.75
        tags = ['positive', 'bright', 'hopeful']
    elif bpm > 100 and energy > 0.5 and is_minor:
        mood = 'Intense'
        valence = 0.45
        tags = ['dramatic', 'powerful', 'driving']
    elif is_dark and energy < 0.3:
        mood = 'Ambient'
        valence = 0.35
        tags = ['spacious', 'ethereal', 'calm']
    elif energy < 0.25:
        mood = 'Calm'
        valence = 0.5
        tags = ['peaceful', 'relaxed', 'serene']
    elif is_bright and energy > 0.5:
        mood = 'Bright'
        valence = 0.7
        tags = ['cheerful', 'crisp', 'lively']
    else:
        mood = 'Neutral'
        valence = 0.5
        tags = ['balanced', 'moderate']
    
    return {
        'mood': mood,
        'energy': round(energy, 2),
        'danceability': round(danceability, 2),
        'valence': round(valence, 2),
        'tags': tags,
    }


def _clamp(value, low, high):
    """Clamp a value between low and high."""
    return max(low, min(high, float(value)))


def get_mood_emoji(mood: str) -> str:
    """Get an emoji representing the mood."""
    mapping = {
        'Melancholic': '😢',
        'Somber': '🌧️',
        'Tender': '💕',
        'Dark': '🌑',
        'Warm': '☀️',
        'Bittersweet': '🍂',
        'Energetic': '⚡',
        'Euphoric': '🎉',
        'Uplifting': '🌈',
        'Intense': '🔥',
        'Ambient': '🌫️',
        'Calm': '🧘',
        'Bright': '✨',
        'Neutral': '😐',
    }
    return mapping.get(mood, '🎵')
