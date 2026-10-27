# -*- coding: utf-8 -*-
"""Agent-optimized output formatter (~500 tokens for LLM consumption)."""

from scripts.utils.audio import format_time
from scripts.core.mood import get_mood_emoji
from scripts.core.vocal import get_vocal_summary


def format_agent(analysis: dict) -> str:
    """Format analysis optimized for LLM consumption (~500 tokens).
    
    This is the KEY differentiator of E-Ears — a compact, information-dense
    summary that lets an AI agent "understand" the song.
    """
    name = analysis.get('filename', 'Unknown')
    features = analysis.get('features', {})
    mood = analysis.get('mood', {})
    structure = analysis.get('structure', [])
    vocal = analysis.get('vocal', {})
    
    bpm = features.get('bpm', 0)
    key = features.get('key', '?')
    duration = features.get('duration_seconds', 0)
    mood_label = mood.get('mood', 'Unknown')
    emoji = get_mood_emoji(mood_label)
    energy = mood.get('energy', 0)
    danceability = mood.get('danceability', 0)
    valence = mood.get('valence', 0)
    
    lines = []
    lines.append(f"🎵 E-Ears Analysis: {name}")
    lines.append("━" * 30)
    lines.append(f"BPM: {bpm} | Key: {key} | Mood: {mood_label} {emoji}")
    lines.append(f"Energy: {energy}/1.0 | Danceability: {danceability}/1.0 | Valence: {valence}/1.0")
    lines.append(f"Duration: {format_time(duration)}")
    
    # Tags
    tags = mood.get('tags', [])
    if tags:
        lines.append(f"Tags: {', '.join(tags)}")
    
    # Structure
    if structure:
        lines.append(f"\nSTRUCTURE:")
        for seg in structure:
            desc = f" {seg['description']}" if seg.get('description') else ''
            lines.append(f"  {seg['start_fmt']}-{seg['end_fmt']} [{seg['label']}]{desc}")
    
    # Vocals
    lines.append(f"\nVOCAL: {get_vocal_summary(vocal)}")
    
    # Production notes
    production_notes = _generate_production_notes(features, vocal)
    lines.append(f"PRODUCTION: {production_notes}")
    
    # Verdict
    verdict = _generate_verdict(features, mood, vocal, structure)
    lines.append(f"\nVERDICT: {verdict}")
    
    return '\n'.join(lines)


def _generate_production_notes(features: dict, vocal: dict) -> str:
    """Generate brief production notes from features."""
    notes = []
    
    hnr = features.get('hnr', {})
    hnr_db = hnr.get('hnr_db', 0) if isinstance(hnr, dict) else 0
    
    if hnr_db > 15:
        notes.append('clean mix')
    elif hnr_db > 8:
        notes.append('moderate mix')
    else:
        notes.append('raw/noisy mix')
    
    spectral = features.get('spectral', {})
    centroid = spectral.get('spectral_centroid', {}).get('mean', 2000) if isinstance(spectral, dict) else 2000
    
    if centroid < 1500:
        notes.append('warm/dark tone')
    elif centroid > 3500:
        notes.append('bright/airy tone')
    else:
        notes.append('balanced tone')
    
    rms = features.get('rms_energy', {})
    dr = rms.get('dynamic_range_db', 0) if isinstance(rms, dict) else 0
    
    if abs(dr) > 8:
        notes.append('high dynamic range')
    elif abs(dr) < 3:
        notes.append('compressed')
    
    # Bandwidth → reverb estimate
    bw = spectral.get('spectral_bandwidth', {}).get('mean', 2000) if isinstance(spectral, dict) else 2000
    if bw > 3000:
        notes.append('spacious/reverb')
    elif bw < 1200:
        notes.append('dry/intimate')
    
    return ', '.join(notes) if notes else 'standard production'


def _generate_verdict(features: dict, mood: dict, vocal: dict, structure: list) -> str:
    """Generate a brief verdict/summary of the track."""
    parts = []
    
    bpm = features.get('bpm', 100)
    key = features.get('key', '?')
    mood_label = mood.get('mood', 'Unknown')
    energy = mood.get('energy', 0.5)
    
    # Genre/style hint
    if bpm < 85 and energy < 0.4:
        parts.append('Ballad tempo')
    elif 85 <= bpm <= 120:
        parts.append('Mid-tempo')
    elif bpm > 120:
        parts.append('Up-tempo')
    
    # Key mood match
    key_mode = features.get('key_mode', 'major')
    if key_mode == 'minor' and mood_label in ('Melancholic', 'Somber', 'Dark', 'Bittersweet'):
        parts.append('key matches mood well')
    elif key_mode == 'major' and mood_label in ('Warm', 'Uplifting', 'Bright', 'Euphoric'):
        parts.append('key matches mood well')
    
    # Vocal assessment
    if vocal.get('has_vocals'):
        quality = vocal.get('quality', [])
        if 'warm' in quality or 'clear' in quality:
            parts.append('good vocal quality')
        elif 'breathy' in quality:
            parts.append('intimate vocal delivery')
        elif 'harsh' in quality:
            parts.append('vocal may need treatment')
    
    # Structure assessment
    n_sections = len(structure)
    if n_sections >= 5:
        parts.append('well-structured arrangement')
    elif n_sections >= 3:
        parts.append('standard arrangement')
    
    # Dynamic assessment
    rms = features.get('rms_energy', {})
    dr = abs(rms.get('dynamic_range_db', 0)) if isinstance(rms, dict) else 0
    if dr > 6:
        parts.append('good dynamics')
    
    return '. '.join(parts) + '.' if parts else 'Standard track.'
