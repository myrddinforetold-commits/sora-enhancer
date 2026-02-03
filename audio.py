#!/usr/bin/env python3
"""
Audio Enhancement - Noise reduction, clarity improvement, normalization
"""

import subprocess
import os
from pathlib import Path


def enhance_audio(input_path: str, output_path: str,
                  noise_reduction: float = 0.3,
                  normalize: bool = True,
                  clarity: bool = True,
                  bass_boost: float = 0,
                  treble_boost: float = 0) -> None:
    """
    Enhance audio using FFmpeg filters.
    
    Args:
        input_path: Input video/audio file
        output_path: Output file
        noise_reduction: Amount of noise reduction (0-1)
        normalize: Normalize audio levels
        clarity: Apply clarity enhancement (high-pass filter + compression)
        bass_boost: Bass boost in dB (0 = none)
        treble_boost: Treble boost in dB (0 = none)
    """
    
    filters = []
    
    # High-pass filter to remove rumble
    if clarity:
        filters.append("highpass=f=80")
    
    # Noise reduction using FFmpeg's anlmdn filter
    if noise_reduction > 0:
        # anlmdn: Non-local means denoising
        strength = noise_reduction * 0.01  # Scale to reasonable range
        filters.append(f"anlmdn=s={strength}")
        
        # Also add a subtle gate to remove very quiet noise
        filters.append("agate=threshold=0.01:ratio=2:attack=20:release=250")
    
    # EQ adjustments
    if bass_boost != 0 or treble_boost != 0:
        eq_parts = []
        if bass_boost != 0:
            eq_parts.append(f"bass=g={bass_boost}")
        if treble_boost != 0:
            eq_parts.append(f"treble=g={treble_boost}")
        filters.extend(eq_parts)
    
    # Clarity enhancement: gentle compression + presence boost
    if clarity:
        # Boost presence frequencies (2-5kHz) for clarity
        filters.append("equalizer=f=3500:t=q:w=1:g=2")
        # Gentle compression for consistency
        filters.append("acompressor=threshold=-20dB:ratio=3:attack=5:release=100")
    
    # Normalize audio levels
    if normalize:
        filters.append("loudnorm=I=-16:TP=-1.5:LRA=11")
    
    # Build filter chain
    filter_chain = ",".join(filters) if filters else "anull"
    
    # Run FFmpeg
    cmd = [
        'ffmpeg', '-y',
        '-i', input_path,
        '-af', filter_chain,
        '-c:v', 'copy',  # Copy video stream unchanged
        output_path
    ]
    
    print(f"Enhancing audio with filters: {filter_chain}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {result.stderr}")
    
    print(f"Audio enhancement complete: {output_path}")


def extract_audio(video_path: str, audio_path: str) -> None:
    """Extract audio from video file"""
    cmd = [
        'ffmpeg', '-y',
        '-i', video_path,
        '-vn',  # No video
        '-acodec', 'pcm_s16le',
        '-ar', '44100',
        '-ac', '2',
        audio_path
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def merge_audio_video(video_path: str, audio_path: str, output_path: str) -> None:
    """Merge enhanced audio with video"""
    cmd = [
        'ffmpeg', '-y',
        '-i', video_path,
        '-i', audio_path,
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-map', '0:v:0',
        '-map', '1:a:0',
        '-shortest',
        output_path
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def enhance_video_audio(input_path: str, output_path: str,
                        preset: str = 'balanced') -> None:
    """
    Enhance audio in a video file.
    
    Presets:
    - 'balanced': General enhancement
    - 'voice': Optimized for speech/voiceover
    - 'music': Optimized for music
    - 'podcast': Clear voice with noise reduction
    """
    
    presets = {
        'balanced': {
            'noise_reduction': 0.3,
            'normalize': True,
            'clarity': True,
            'bass_boost': 0,
            'treble_boost': 0
        },
        'voice': {
            'noise_reduction': 0.5,
            'normalize': True,
            'clarity': True,
            'bass_boost': -2,
            'treble_boost': 3
        },
        'music': {
            'noise_reduction': 0.1,
            'normalize': True,
            'clarity': False,
            'bass_boost': 2,
            'treble_boost': 1
        },
        'podcast': {
            'noise_reduction': 0.6,
            'normalize': True,
            'clarity': True,
            'bass_boost': 1,
            'treble_boost': 2
        }
    }
    
    settings = presets.get(preset, presets['balanced'])
    enhance_audio(input_path, output_path, **settings)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhance audio in video')
    parser.add_argument('input', help='Input video file')
    parser.add_argument('-o', '--output', help='Output video file')
    parser.add_argument('--preset', choices=['balanced', 'voice', 'music', 'podcast'],
                       default='balanced', help='Audio enhancement preset')
    
    args = parser.parse_args()
    
    output = args.output or args.input.replace('.', '_enhanced_audio.')
    enhance_video_audio(args.input, output, preset=args.preset)
