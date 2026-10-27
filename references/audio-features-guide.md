# Audio Features Guide

Reference cho agent hiểu ý nghĩa từng feature trong E-Ears output.

## Core Features

### BPM (Beats Per Minute)
- Tốc độ nhịp bài hát
- 60-80: Ballad, slow
- 80-120: Mid-tempo, pop
- 120-140: Dance, upbeat
- 140+: Fast, EDM, punk

### Key (Tông giọng)
- Major: sáng, vui, tích cực (C, D, E, F, G, A, B)
- Minor: buồn, sâu, u tối (Cm, Dm, Em, Fm, Gm, Am, Bm)
- Confidence > 0.8: đáng tin
- Confidence < 0.5: không chắc chắn

### Time Signature
- 4/4: Phổ biến nhất (pop, rock, EDM)
- 3/4: Waltz, ballad
- 6/8: Compound time

## Spectral Features

### Spectral Centroid (Hz)
- "Trung tâm trọng lực" của tần số
- Thấp (< 1500): Warm, bass-heavy, dark
- Trung bình (1500-3000): Balanced
- Cao (> 3000): Bright, treble, airy

### Spectral Bandwidth (Hz)
- Độ rộng tần số
- Hẹp (< 1500): Dry, intimate
- Rộng (> 3000): Spacious, reverb-heavy

### Spectral Rolloff (Hz)
- Tần số mà 85% năng lượng nằm dưới
- Cho biết âm thanh có nhiều treble hay không

### Zero Crossing Rate (ZCR)
- Tần suất tín hiệu đổi dấu
- Cao: Noisy, harsh, percussive
- Thấp: Smooth, tonal

## Energy Features

### RMS Energy
- Biên độ trung bình (loudness)
- 0.01-0.03: Rất nhẹ (whispered)
- 0.03-0.08: Nhẹ (acoustic ballad)
- 0.08-0.15: Trung bình (pop)
- 0.15+: Mạnh (rock, EDM)
- ⚠️ Suno normalize cao nên RMS không phản ánh "cảm giác" năng lượng

### Dynamic Range (dB)
- Chênh lệch giữa loud nhất và trung bình
- < 3 dB: Compressed (EDM, modern pop)
- 3-8 dB: Normal
- > 8 dB: Dynamic (classical, jazz, ballad)

### HNR (Harmonic-to-Noise Ratio, dB)
- Tỉ lệ harmonic vs noise
- > 15 dB: Clean mix
- 8-15 dB: Moderate
- < 8 dB: Noisy/raw

## MFCC (Mel-Frequency Cepstral Coefficients)
- 13 hệ số mô tả "texture" âm thanh
- Dùng cho machine learning, fingerprinting
- Coefficient 1: Overall energy shape
- Coefficient 2-13: Spectral detail

## Vocal Features

### Vocal Presence (0-1)
- Tỉ lệ harmonic content
- > 0.3: Có vocal
- < 0.3: Instrumental

### Vocal Range
- Low note - High note (e.g., B1-D#4)
- Male: typically C2-C5
- Female: typically C3-C6

### Register
- Bass: < 130 Hz median
- Baritone: 130-200 Hz
- Tenor: 200-280 Hz
- Alto: 280-370 Hz
- Mezzo-soprano: 370-500 Hz
- Soprano: > 500 Hz

### Vocal Quality
- **breathy**: High spectral flatness (air in voice)
- **clear**: Low flatness (focused tone)
- **warm**: Low spectral centroid
- **bright**: High centroid
- **harsh**: High zero crossing rate
- **smooth**: Low ZCR
- **muddy**: Excess low-frequency energy
- **rich**: Wide bandwidth
- **thin**: Narrow bandwidth
