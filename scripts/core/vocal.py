# -*- coding: utf-8 -*-
"""Vocal analysis: presence detection, range estimation, quality labels."""

import numpy as np
import librosa

from scripts.utils.audio import hz_to_note


def analyze_vocals(y, sr: int) -> dict:
    """Analyze vocal characteristics from audio.
    
    Uses harmonic/percussive separation to isolate vocal-like content,
    then analyzes spectral features of the harmonic component.
    
    Returns dict with vocal presence, range, quality, and characteristics.
    """
    try:
        # Harmonic/percussive separation
        y_harmonic, y_percussive = librosa.effects.hpss(y)
        
        # Vocal presence: ratio of harmonic to total energy
        harmonic_energy = float(np.sum(y_harmonic ** 2))
        total_energy = float(np.sum(y ** 2))
        vocal_presence = harmonic_energy / (total_energy + 1e-10)
        
        has_vocals = vocal_presence > 0.3
        
        result = {
            'has_vocals': has_vocals,
            'vocal_presence': round(vocal_presence, 3),
            'vocal_range': {'low': 'N/A', 'high': 'N/A', 'low_hz': 0, 'high_hz': 0},
            'quality': [],
            'register': 'unknown',
            'gender_estimate': 'unknown',
        }
        
        if not has_vocals:
            result['quality'] = ['instrumental']
            return result
        
        # Estimate vocal range using pitch detection on harmonic component
        range_info = _estimate_vocal_range(y_harmonic, sr)
        result['vocal_range'] = range_info
        
        # Estimate gender/register from pitch range
        result['gender_estimate'] = _estimate_gender(range_info)
        result['register'] = _estimate_register(range_info)
        
        # Quality analysis
        result['quality'] = _analyze_quality(y_harmonic, sr)
        
        return result
        
    except Exception as e:
        return {
            'has_vocals': False,
            'vocal_presence': 0.0,
            'vocal_range': {'low': 'N/A', 'high': 'N/A', 'low_hz': 0, 'high_hz': 0},
            'quality': ['analysis_failed'],
            'register': 'unknown',
            'gender_estimate': 'unknown',
            'error': str(e),
        }


def _estimate_vocal_range(y_harmonic, sr: int) -> dict:
    """Estimate vocal pitch range using pyin."""
    try:
        # Use pyin for robust pitch tracking
        f0, voiced_flag, voiced_probs = librosa.pyin(
            y_harmonic, fmin=60, fmax=1200, sr=sr
        )
        
        # Filter to voiced segments with reasonable confidence
        voiced_f0 = f0[voiced_flag & ~np.isnan(f0)]
        
        if len(voiced_f0) < 10:
            return {'low': 'N/A', 'high': 'N/A', 'low_hz': 0, 'high_hz': 0}
        
        # Use percentiles to avoid outliers
        low_hz = float(np.percentile(voiced_f0, 5))
        high_hz = float(np.percentile(voiced_f0, 95))
        median_hz = float(np.median(voiced_f0))
        
        return {
            'low': hz_to_note(low_hz),
            'high': hz_to_note(high_hz),
            'low_hz': round(low_hz, 1),
            'high_hz': round(high_hz, 1),
            'median_hz': round(median_hz, 1),
            'median_note': hz_to_note(median_hz),
        }
    except Exception:
        return {'low': 'N/A', 'high': 'N/A', 'low_hz': 0, 'high_hz': 0}


def _estimate_gender(range_info: dict) -> str:
    """Estimate vocal gender from pitch range."""
    median_hz = range_info.get('median_hz', 0)
    if median_hz <= 0:
        return 'unknown'
    
    # Male vocal range: ~85-350 Hz fundamental
    # Female vocal range: ~165-700 Hz fundamental
    if median_hz < 165:
        return 'male'
    elif median_hz < 250:
        return 'male'  # Could be high male or low female
    elif median_hz < 400:
        return 'female'
    else:
        return 'female'


def _estimate_register(range_info: dict) -> str:
    """Estimate vocal register from pitch range."""
    median_hz = range_info.get('median_hz', 0)
    if median_hz <= 0:
        return 'unknown'
    
    if median_hz < 130:
        return 'bass'
    elif median_hz < 200:
        return 'baritone'
    elif median_hz < 280:
        return 'tenor'
    elif median_hz < 370:
        return 'alto'
    elif median_hz < 500:
        return 'mezzo-soprano'
    else:
        return 'soprano'


def _analyze_quality(y_harmonic, sr: int) -> list:
    """Analyze vocal quality based on spectral features.
    
    Returns list of quality descriptors.
    """
    qualities = []
    
    try:
        # Spectral centroid — brightness
        centroid = float(np.mean(librosa.feature.spectral_centroid(y=y_harmonic, sr=sr)))
        
        # Spectral bandwidth — spread
        bandwidth = float(np.mean(librosa.feature.spectral_bandwidth(y=y_harmonic, sr=sr)))
        
        # Spectral flatness — noisiness/breathiness
        flatness = float(np.mean(librosa.feature.spectral_flatness(y=y_harmonic)))
        
        # Zero crossing rate — texture
        zcr = float(np.mean(librosa.feature.zero_crossing_rate(y_harmonic)))
        
        # Classify based on features
        if flatness > 0.1:
            qualities.append('breathy')
        elif flatness < 0.02:
            qualities.append('clear')
        
        if centroid > 3000:
            qualities.append('bright')
        elif centroid < 1500:
            qualities.append('warm')
        
        if bandwidth > 3000:
            qualities.append('rich')
        elif bandwidth < 1500:
            qualities.append('thin')
        
        if zcr > 0.1:
            qualities.append('harsh')
        elif zcr < 0.03:
            qualities.append('smooth')
        
        # Check for muddiness — high low-frequency energy
        spec = np.abs(librosa.stft(y_harmonic))
        low_band = np.mean(spec[:int(spec.shape[0] * 0.1), :])
        total = np.mean(spec)
        if total > 0 and low_band / total > 0.6:
            qualities.append('muddy')
        
        if not qualities:
            qualities.append('balanced')
            
    except Exception:
        qualities.append('unknown')
    
    return qualities


def get_vocal_summary(vocal_data: dict) -> str:
    """Generate a compact vocal summary string."""
    if not vocal_data.get('has_vocals', False):
        return 'Instrumental (no vocals detected)'
    
    parts = []
    
    # Gender + quality
    gender = vocal_data.get('gender_estimate', 'unknown')
    if gender != 'unknown':
        parts.append(gender.capitalize())
    
    quality = vocal_data.get('quality', [])
    if quality:
        parts.extend(quality)
    
    # Range
    vr = vocal_data.get('vocal_range', {})
    low = vr.get('low', 'N/A')
    high = vr.get('high', 'N/A')
    if low != 'N/A' and high != 'N/A':
        parts.append(f"range {low}-{high}")
    
    return ', '.join(parts) if parts else 'Vocals detected'
