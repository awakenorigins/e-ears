# -*- coding: utf-8 -*-
"""Track comparison: side-by-side analysis of 2+ audio files."""

import os
from .features import extract_all
from .mood import classify_mood
from .vocal import analyze_vocals, get_vocal_summary
from scripts.utils.audio import load_audio


def compare_tracks(file_paths: list) -> dict:
    """Compare 2+ audio tracks side-by-side.
    
    Args:
        file_paths: List of paths to audio files
    
    Returns:
        Dict with per-track analysis and comparison delta
    """
    tracks = []
    
    for path in file_paths:
        y, sr = load_audio(path)
        features = extract_all(y, sr)
        mood = classify_mood(features)
        vocal = analyze_vocals(y, sr)
        
        name = os.path.splitext(os.path.basename(path))[0]
        
        tracks.append({
            'name': name,
            'path': path,
            'bpm': features['bpm'],
            'key': features['key'],
            'key_mode': features['key_mode'],
            'duration': features['duration_seconds'],
            'energy': mood['energy'],
            'danceability': mood['danceability'],
            'valence': mood['valence'],
            'mood': mood['mood'],
            'vocal_summary': get_vocal_summary(vocal),
            'has_vocals': vocal.get('has_vocals', False),
            'rms_mean': features['rms_energy']['mean'],
            'spectral_centroid': features['spectral']['spectral_centroid']['mean'],
            'hnr_db': features['hnr']['hnr_db'],
            'dynamic_range_db': features['rms_energy']['dynamic_range_db'],
        })
    
    # Compute deltas between tracks
    deltas = _compute_deltas(tracks)
    
    # Generate recommendation
    recommendation = _generate_recommendation(tracks)
    
    return {
        'track_count': len(tracks),
        'tracks': tracks,
        'deltas': deltas,
        'recommendation': recommendation,
    }


def _compute_deltas(tracks: list) -> dict:
    """Compute differences between tracks."""
    if len(tracks) < 2:
        return {}
    
    metrics = ['bpm', 'energy', 'danceability', 'valence', 'rms_mean', 'spectral_centroid', 'hnr_db']
    deltas = {}
    
    for metric in metrics:
        values = [t.get(metric, 0) for t in tracks]
        deltas[metric] = {
            'min': round(min(values), 2),
            'max': round(max(values), 2),
            'range': round(max(values) - min(values), 2),
            'values': {t['name']: round(t.get(metric, 0), 2) for t in tracks},
        }
    
    # Key comparison
    keys = [t['key'] for t in tracks]
    deltas['key'] = {
        'values': {t['name']: t['key'] for t in tracks},
        'same_key': len(set(keys)) == 1,
    }
    
    return deltas


def _generate_recommendation(tracks: list) -> dict:
    """Generate a recommendation for which track is "better" based on metrics.
    
    Scoring:
    - Higher HNR → cleaner mix
    - Higher dynamic range → more expressive
    - Balanced energy → neither too quiet nor too loud
    - Higher vocal presence (if applicable) → better vocal capture
    """
    if len(tracks) < 2:
        return {'winner': tracks[0]['name'] if tracks else 'N/A', 'reason': 'Only one track'}
    
    scores = {}
    reasons = {}
    
    for t in tracks:
        score = 0
        track_reasons = []
        
        # HNR: higher is cleaner
        hnr = t.get('hnr_db', 0)
        hnr_score = min(hnr / 20, 1.0)
        score += hnr_score * 30
        
        # Dynamic range: more is better (up to a point)
        dr = abs(t.get('dynamic_range_db', 0))
        dr_score = min(dr / 10, 1.0)
        score += dr_score * 20
        
        # Energy balance: prefer 0.3-0.7
        energy = t.get('energy', 0.5)
        energy_balance = 1.0 - abs(energy - 0.5) * 2
        score += energy_balance * 15
        
        # Spectral centroid: prefer 1500-3500 (balanced)
        cent = t.get('spectral_centroid', 2000)
        cent_score = 1.0 - abs(cent - 2500) / 3000
        cent_score = max(0, min(1, cent_score))
        score += cent_score * 15
        
        # Loudness: prefer moderate RMS
        rms = t.get('rms_mean', 0.05)
        rms_score = 1.0 - abs(rms - 0.06) / 0.06
        rms_score = max(0, min(1, rms_score))
        score += rms_score * 20
        
        # Build reason
        if hnr > 15:
            track_reasons.append('clean mix')
        if dr > 5:
            track_reasons.append('good dynamics')
        if 0.3 < energy < 0.7:
            track_reasons.append('balanced energy')
        
        scores[t['name']] = round(score, 1)
        reasons[t['name']] = track_reasons
    
    # Find winner
    winner = max(scores, key=scores.get)
    
    return {
        'winner': winner,
        'scores': scores,
        'reasons': reasons.get(winner, []),
        'reason_text': f"{winner} scores highest due to: {', '.join(reasons.get(winner, ['overall balance']))}",
    }


def format_comparison_text(result: dict) -> str:
    """Format comparison result as human-readable text."""
    lines = []
    lines.append("=" * 60)
    lines.append("🎵 E-Ears Track Comparison")
    lines.append("=" * 60)
    
    for t in result['tracks']:
        lines.append(f"\n📀 {t['name']}")
        lines.append(f"   BPM: {t['bpm']} | Key: {t['key']} | Mood: {t['mood']}")
        lines.append(f"   Energy: {t['energy']} | Dance: {t['danceability']} | Valence: {t['valence']}")
        lines.append(f"   Vocal: {t['vocal_summary']}")
        lines.append(f"   HNR: {t['hnr_db']}dB | Dynamic Range: {t['dynamic_range_db']}dB")
    
    lines.append(f"\n{'─' * 60}")
    lines.append("📊 COMPARISON DELTAS:")
    deltas = result.get('deltas', {})
    for metric, data in deltas.items():
        if metric == 'key':
            same = "✅ Same" if data.get('same_key') else "❌ Different"
            vals = ', '.join(f"{k}: {v}" for k, v in data['values'].items())
            lines.append(f"   Key: {same} ({vals})")
        else:
            lines.append(f"   {metric}: range={data['range']} ({', '.join(f'{k}: {v}' for k, v in data['values'].items())})")
    
    rec = result.get('recommendation', {})
    lines.append(f"\n🏆 RECOMMENDATION: {rec.get('reason_text', 'N/A')}")
    
    return '\n'.join(lines)
