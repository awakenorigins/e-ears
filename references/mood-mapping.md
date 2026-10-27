# Mood Mapping Guide

How E-Ears maps audio features to mood labels.

## Feature → Mood Matrix

| Mood | BPM | Key | Energy | Spectral | Tags |
|---|---|---|---|---|---|
| Melancholic | < 100 | Minor | < 0.35 | Any | sad, slow, introspective |
| Somber | < 80 | Minor | < 0.5 | Any | dark, emotional, heavy |
| Tender | < 85 | Major | < 0.4 | Any | gentle, intimate, soft |
| Dark | < 100 | Minor | < 0.5 | Dark (< 1500) | moody, atmospheric, brooding |
| Warm | 80-120 | Major | 0.3-0.7 | Any | nostalgic, comforting, smooth |
| Bittersweet | 80-110 | Minor | 0.3-0.6 | Any | nostalgic, wistful, emotional |
| Energetic | > 120 | Any | > 0.6 | Any | upbeat, driving, powerful |
| Euphoric | > 130 | Major | > 0.7 | Any | ecstatic, peak, joyful |
| Uplifting | > 100 | Major | > 0.5 | Any | positive, bright, hopeful |
| Intense | > 100 | Minor | > 0.5 | Any | dramatic, powerful, driving |
| Ambient | Any | Any | < 0.3 | Dark | spacious, ethereal, calm |
| Calm | Any | Any | < 0.25 | Any | peaceful, relaxed, serene |
| Bright | Any | Any | > 0.5 | Bright (> 2500) | cheerful, crisp, lively |
| Neutral | Any | Any | Any | Any | balanced, moderate |

## Energy Calculation

E-Ears v1.0 blends 3 signals for perceived energy:
- 45% BPM-based (normalized: 60=0, 160=1)
- 30% RMS amplitude
- 25% Spectral centroid

This avoids the "Suno normalization problem" where all tracks have high RMS regardless of perceived energy.

## Valence Scale

- 0.0-0.2: Very negative (melancholic, somber)
- 0.2-0.4: Negative (dark, bittersweet)
- 0.4-0.6: Neutral (tender, calm)
- 0.6-0.8: Positive (warm, uplifting, bright)
- 0.8-1.0: Very positive (euphoric, energetic)

## Danceability

Blended from:
- 50% BPM sweetspot (peak at 115 BPM)
- 30% Energy
- 20% Tempo threshold (> 90 BPM bonus)
