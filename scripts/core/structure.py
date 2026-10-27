# -*- coding: utf-8 -*-
"""Song structure detection: segment boundaries and section labeling."""

import numpy as np
import librosa

from scripts.utils.audio import format_time


def detect_segments(y, sr: int, min_segment_sec: float = 8.0) -> list:
    """Detect structural segments using spectral clustering.
    
    Args:
        y: Audio signal
        sr: Sample rate
        min_segment_sec: Minimum segment duration in seconds
    
    Returns:
        List of dicts with 'start', 'end', 'label', 'energy', 'description'
    """
    duration = len(y) / sr
    
    # For very short clips, return a single segment
    if duration < 15:
        energy = _compute_segment_energy(y, sr, 0, duration)
        return [{
            'start': 0.0,
            'end': duration,
            'start_fmt': '0:00',
            'end_fmt': format_time(duration),
            'label': 'Full',
            'energy': energy,
            'description': '',
        }]
    
    try:
        # Compute features for segmentation
        # Use mel spectrogram for better musicality
        S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmax=8000)
        S_db = librosa.power_to_db(S, ref=np.max)
        
        # Compute self-similarity matrix using chroma + MFCC
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        
        # Stack features
        features = np.vstack([
            librosa.util.normalize(chroma, axis=1),
            librosa.util.normalize(mfcc, axis=1),
        ])
        
        # Compute recurrence matrix for repetition detection
        R = librosa.segment.recurrence_matrix(features, mode='affinity', sym=True)
        
        # Use spectral clustering via agglomerative approach
        # Estimate number of segments based on duration
        n_segments = max(3, min(12, int(duration / 20)))
        
        # Novelty-based segmentation
        novelty = librosa.onset.onset_strength(y=y, sr=sr)
        
        # Use agglomerative clustering on the feature matrix
        bound_frames = librosa.segment.agglomerative(features, n_segments)
        bound_times = librosa.frames_to_time(bound_frames, sr=sr)
        
        # Always include 0 and end
        boundaries = [0.0]
        for t in sorted(bound_times):
            if t - boundaries[-1] >= min_segment_sec:
                boundaries.append(float(t))
        if duration - boundaries[-1] > min_segment_sec / 2:
            boundaries.append(float(duration))
        elif boundaries[-1] != duration:
            boundaries[-1] = float(duration)
        
        # Build segments
        segments = []
        for i in range(len(boundaries) - 1):
            start = boundaries[i]
            end = boundaries[i + 1]
            energy = _compute_segment_energy(y, sr, start, end)
            
            segments.append({
                'start': round(start, 2),
                'end': round(end, 2),
                'start_fmt': format_time(start),
                'end_fmt': format_time(end),
                'label': '',  # Will be labeled by _label_segments
                'energy': round(energy, 3),
                'description': '',
            })
        
        # Label segments
        segments = _label_segments(segments, y, sr)
        
        return segments
        
    except Exception as e:
        # Fallback: equal-length segments
        n = max(3, min(8, int(duration / 30)))
        seg_len = duration / n
        segments = []
        for i in range(n):
            start = i * seg_len
            end = min((i + 1) * seg_len, duration)
            energy = _compute_segment_energy(y, sr, start, end)
            segments.append({
                'start': round(start, 2),
                'end': round(end, 2),
                'start_fmt': format_time(start),
                'end_fmt': format_time(end),
                'label': f'Section {i+1}',
                'energy': round(energy, 3),
                'description': '',
            })
        return segments


def _compute_segment_energy(y, sr, start_sec, end_sec) -> float:
    """Compute normalized RMS energy for a segment."""
    start_sample = int(start_sec * sr)
    end_sample = int(end_sec * sr)
    segment = y[start_sample:end_sample]
    
    if len(segment) == 0:
        return 0.0
    
    rms = float(np.sqrt(np.mean(segment ** 2)))
    return rms


def _label_segments(segments: list, y, sr: int) -> list:
    """Label segments as intro/verse/chorus/bridge/outro based on energy + position.
    
    Heuristic approach:
    - First segment with low energy → Intro
    - Last segment with decreasing energy → Outro
    - Highest energy segments → Chorus
    - Medium energy → Verse
    - Between verse and chorus → Pre-chorus
    - Low energy in middle → Bridge
    """
    if not segments:
        return segments
    
    n = len(segments)
    energies = [s['energy'] for s in segments]
    max_energy = max(energies) if energies else 1.0
    min_energy = min(energies) if energies else 0.0
    energy_range = max_energy - min_energy if max_energy > min_energy else 1.0
    
    # Normalize energies to 0-1
    norm_energies = [(e - min_energy) / energy_range for e in energies]
    
    # Compute spectral features per segment for descriptions
    for i, seg in enumerate(segments):
        start_sample = int(seg['start'] * sr)
        end_sample = int(seg['end'] * sr)
        seg_audio = y[start_sample:end_sample]
        
        if len(seg_audio) > 0:
            desc_parts = []
            # Energy descriptor
            ne = norm_energies[i]
            if ne < 0.3:
                desc_parts.append('soft')
            elif ne < 0.6:
                desc_parts.append('moderate')
            else:
                desc_parts.append('high energy')
            
            # Spectral analysis for instrument hints
            try:
                cent = float(np.mean(librosa.feature.spectral_centroid(y=seg_audio, sr=sr)))
                if cent < 1500:
                    desc_parts.append('warm/bass-heavy')
                elif cent < 3000:
                    desc_parts.append('balanced')
                else:
                    desc_parts.append('bright/treble')
            except Exception:
                pass
            
            seg['description'] = ', '.join(desc_parts)
    
    # Label assignment
    if n == 1:
        segments[0]['label'] = 'Full'
        return segments
    
    # Identify chorus candidates: highest energy segments
    energy_threshold = min_energy + 0.65 * energy_range
    chorus_candidates = [i for i, e in enumerate(energies) if e >= energy_threshold]
    
    # Label each segment
    labeled = [False] * n
    
    # First segment: Intro if energy is below median
    median_energy = float(np.median(energies))
    if energies[0] <= median_energy:
        segments[0]['label'] = 'Intro'
        labeled[0] = True
    
    # Last segment: Outro if energy is below median
    if n > 1 and energies[-1] <= median_energy:
        segments[-1]['label'] = 'Outro'
        labeled[-1] = True
    
    # Mark choruses
    for i in chorus_candidates:
        if not labeled[i]:
            segments[i]['label'] = 'Chorus'
            labeled[i] = True
    
    # Label remaining segments
    verse_count = 0
    for i in range(n):
        if labeled[i]:
            continue
        
        ne = norm_energies[i]
        
        # Check if this is right before a chorus → Pre-chorus
        if i + 1 < n and segments[i + 1].get('label') == 'Chorus' and ne > 0.3:
            segments[i]['label'] = 'Pre-Chorus'
            labeled[i] = True
            continue
        
        # Low energy in the middle → Bridge
        if ne < 0.35 and 0 < i < n - 1:
            # Check if there's already a chorus before this
            has_chorus_before = any(segments[j]['label'] == 'Chorus' for j in range(i))
            if has_chorus_before:
                segments[i]['label'] = 'Bridge'
                labeled[i] = True
                continue
        
        # Default: Verse
        verse_count += 1
        segments[i]['label'] = f'Verse {verse_count}' if verse_count > 1 else 'Verse'
        labeled[i] = True
    
    return segments


def get_structure_summary(segments: list) -> str:
    """Generate a compact text summary of the song structure."""
    if not segments:
        return "No structure detected."
    
    lines = []
    for seg in segments:
        desc = f" — {seg['description']}" if seg.get('description') else ''
        lines.append(f"{seg['start_fmt']}-{seg['end_fmt']} [{seg['label']}]{desc}")
    
    return '\n'.join(lines)
