# -*- coding: utf-8 -*-
"""Feature extraction: BPM, key, tempo, spectral features, MFCC, etc."""

import numpy as np
import librosa


# Krumhansl-Kessler key profiles
MAJOR_PROFILE = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MINOR_PROFILE = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

KEY_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def detect_bpm(y, sr: int) -> dict:
    """Detect BPM/tempo using librosa beat tracker.
    
    Returns dict with 'bpm' (float) and 'beat_frames' (array).
    """
    try:
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        # librosa >= 0.10 returns array; extract scalar
        bpm = float(np.atleast_1d(tempo)[0])
        beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()
        
        # Fix double-tempo detection: if BPM > 140, likely doubled
        # Most music is 60-160 BPM; ballads are 60-90
        if bpm > 140:
            bpm_half = bpm / 2
            # Prefer half-tempo if it falls in common range
            if 55 <= bpm_half <= 120:
                bpm = bpm_half
        
        return {
            'bpm': round(bpm, 1),
            'beat_count': len(beat_frames),
            'beat_times': beat_times,
        }
    except Exception:
        return {'bpm': 0.0, 'beat_count': 0, 'beat_times': []}


def detect_key(y, sr: int) -> dict:
    """Detect musical key using chroma features + Krumhansl-Kessler profiles.
    
    Returns dict with 'key', 'mode' (major/minor), 'confidence'.
    """
    try:
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        chroma_mean = np.mean(chroma, axis=1)
        
        # Normalize
        chroma_norm = chroma_mean / (np.linalg.norm(chroma_mean) + 1e-8)
        
        best_corr = -1
        best_key = 0
        best_mode = 'major'
        
        for shift in range(12):
            # Rotate profiles to test each key
            major_shifted = np.roll(MAJOR_PROFILE, shift)
            minor_shifted = np.roll(MINOR_PROFILE, shift)
            
            major_norm = major_shifted / (np.linalg.norm(major_shifted) + 1e-8)
            minor_norm = minor_shifted / (np.linalg.norm(minor_shifted) + 1e-8)
            
            corr_major = float(np.corrcoef(chroma_norm, major_norm)[0, 1])
            corr_minor = float(np.corrcoef(chroma_norm, minor_norm)[0, 1])
            
            if corr_major > best_corr:
                best_corr = corr_major
                best_key = shift
                best_mode = 'major'
            if corr_minor > best_corr:
                best_corr = corr_minor
                best_key = shift
                best_mode = 'minor'
        
        key_name = KEY_NAMES[best_key]
        mode_suffix = 'm' if best_mode == 'minor' else ''
        
        return {
            'key': f"{key_name}{mode_suffix}",
            'root': key_name,
            'mode': best_mode,
            'confidence': round(best_corr, 3),
        }
    except Exception:
        return {'key': 'Unknown', 'root': 'C', 'mode': 'major', 'confidence': 0.0}


def estimate_time_signature(beat_times: list) -> dict:
    """Estimate time signature from beat intervals.
    
    Heuristic: analyze beat interval patterns for groupings of 3 or 4.
    """
    if len(beat_times) < 4:
        return {'time_signature': '4/4', 'confidence': 0.0}
    
    try:
        intervals = np.diff(beat_times)
        if len(intervals) < 3:
            return {'time_signature': '4/4', 'confidence': 0.5}
        
        median_interval = float(np.median(intervals))
        
        # Check for waltz (3/4) — look for repeating pattern of 3
        # Most pop/rock is 4/4, waltz has characteristic swing
        # Simple heuristic: if beat strength follows 3-pattern
        variance = float(np.std(intervals) / (median_interval + 1e-8))
        
        if variance < 0.15:
            # Very regular beats — likely 4/4
            return {'time_signature': '4/4', 'confidence': round(1.0 - variance, 2)}
        elif variance < 0.3:
            return {'time_signature': '4/4', 'confidence': round(0.7 - variance, 2)}
        else:
            # Irregular — might be 3/4 or 6/8
            return {'time_signature': '3/4', 'confidence': round(0.5, 2)}
    except Exception:
        return {'time_signature': '4/4', 'confidence': 0.0}


def extract_spectral_features(y, sr: int) -> dict:
    """Extract spectral features: centroid, bandwidth, rolloff, contrast, ZCR."""
    try:
        spec_cent = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        spec_bw = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
        spec_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        
        # Spectral contrast (7 bands)
        try:
            spec_contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
            contrast_mean = np.mean(spec_contrast, axis=1).tolist()
        except Exception:
            contrast_mean = []
        
        return {
            'spectral_centroid': {
                'mean': round(float(np.mean(spec_cent)), 1),
                'std': round(float(np.std(spec_cent)), 1),
            },
            'spectral_bandwidth': {
                'mean': round(float(np.mean(spec_bw)), 1),
                'std': round(float(np.std(spec_bw)), 1),
            },
            'spectral_rolloff': {
                'mean': round(float(np.mean(spec_rolloff)), 1),
            },
            'spectral_contrast': [round(c, 2) for c in contrast_mean],
            'zero_crossing_rate': {
                'mean': round(float(np.mean(zcr)), 5),
                'std': round(float(np.std(zcr)), 5),
            },
        }
    except Exception:
        return {
            'spectral_centroid': {'mean': 0.0, 'std': 0.0},
            'spectral_bandwidth': {'mean': 0.0, 'std': 0.0},
            'spectral_rolloff': {'mean': 0.0},
            'spectral_contrast': [],
            'zero_crossing_rate': {'mean': 0.0, 'std': 0.0},
        }


def extract_mfcc(y, sr: int, n_mfcc: int = 13) -> dict:
    """Extract MFCC coefficients."""
    try:
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
        mfcc_mean = np.mean(mfcc, axis=1).tolist()
        mfcc_std = np.std(mfcc, axis=1).tolist()
        return {
            'coefficients': [round(m, 2) for m in mfcc_mean],
            'std': [round(s, 2) for s in mfcc_std],
        }
    except Exception:
        return {'coefficients': [], 'std': []}


def extract_rms_energy(y) -> dict:
    """Extract RMS energy envelope."""
    try:
        rms = librosa.feature.rms(y=y)[0]
        return {
            'mean': round(float(np.mean(rms)), 4),
            'std': round(float(np.std(rms)), 4),
            'max': round(float(np.max(rms)), 4),
            'min': round(float(np.min(rms)), 4),
            'dynamic_range_db': round(float(20 * np.log10((np.max(rms) + 1e-10) / (np.mean(rms) + 1e-10))), 1),
        }
    except Exception:
        return {'mean': 0.0, 'std': 0.0, 'max': 0.0, 'min': 0.0, 'dynamic_range_db': 0.0}


def extract_harmonic_noise_ratio(y, sr: int) -> dict:
    """Estimate Harmonic-to-Noise Ratio."""
    try:
        y_harmonic, y_percussive = librosa.effects.hpss(y)
        
        harmonic_energy = float(np.sum(y_harmonic ** 2))
        noise_energy = float(np.sum(y_percussive ** 2))
        
        if noise_energy > 0:
            hnr = 10 * np.log10(harmonic_energy / (noise_energy + 1e-10))
        else:
            hnr = 60.0  # Very clean signal
        
        return {
            'hnr_db': round(float(hnr), 1),
            'harmonic_ratio': round(harmonic_energy / (harmonic_energy + noise_energy + 1e-10), 3),
        }
    except Exception:
        return {'hnr_db': 0.0, 'harmonic_ratio': 0.5}


def extract_all(y, sr: int) -> dict:
    """Run all feature extraction and return combined results."""
    bpm_data = detect_bpm(y, sr)
    key_data = detect_key(y, sr)
    time_sig = estimate_time_signature(bpm_data.get('beat_times', []))
    spectral = extract_spectral_features(y, sr)
    mfcc = extract_mfcc(y, sr)
    rms = extract_rms_energy(y)
    hnr = extract_harmonic_noise_ratio(y, sr)
    
    duration = len(y) / sr
    
    return {
        'duration_seconds': round(duration, 1),
        'sample_rate': sr,
        'bpm': bpm_data['bpm'],
        'beat_count': bpm_data['beat_count'],
        'key': key_data['key'],
        'key_root': key_data['root'],
        'key_mode': key_data['mode'],
        'key_confidence': key_data['confidence'],
        'time_signature': time_sig['time_signature'],
        'spectral': spectral,
        'mfcc': mfcc,
        'rms_energy': rms,
        'hnr': hnr,
        'beat_times': bpm_data['beat_times'],
    }


def extract_quick(y, sr: int) -> dict:
    """Quick extraction: BPM + key only (fast)."""
    bpm_data = detect_bpm(y, sr)
    key_data = detect_key(y, sr)
    rms = extract_rms_energy(y)
    duration = len(y) / sr
    
    return {
        'duration_seconds': round(duration, 1),
        'bpm': bpm_data['bpm'],
        'key': key_data['key'],
        'key_mode': key_data['mode'],
        'key_confidence': key_data['confidence'],
        'rms_energy': rms,
    }
