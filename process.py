#!/usr/bin/env python3
"""
Complete Video Processing Pipeline
- Watermark removal
- Video enhancement (upscaling, color, sharpness)
- Audio enhancement
"""

import argparse
import os
import tempfile
import subprocess
from pathlib import Path

from watermark import process_video_watermark
from enhance import enhance_video
from audio import enhance_video_audio


def process_complete(input_path: str, output_path: str,
                     remove_watermark: bool = True,
                     enhance_video_quality: bool = True,
                     enhance_audio_quality: bool = True,
                     video_preset: str = 'cinematic',
                     audio_preset: str = 'balanced',
                     use_ai: bool = False) -> dict:
    """
    Complete processing pipeline.
    
    Returns dict with processing stats.
    """
    
    stats = {
        'input': input_path,
        'output': output_path,
        'steps': []
    }
    
    current_file = input_path
    
    with tempfile.TemporaryDirectory() as tmpdir:
        step_num = 0
        
        # Step 1: Remove watermark
        if remove_watermark:
            step_num += 1
            print(f"\n[Step {step_num}] Removing watermark...")
            watermark_output = os.path.join(tmpdir, f"step{step_num}_nowatermark.mp4")
            
            try:
                process_video_watermark(current_file, watermark_output)
                current_file = watermark_output
                stats['steps'].append('watermark_removal')
            except Exception as e:
                print(f"  Warning: Watermark removal failed: {e}")
        
        # Step 2: Enhance video
        if enhance_video_quality:
            step_num += 1
            print(f"\n[Step {step_num}] Enhancing video quality...")
            video_output = os.path.join(tmpdir, f"step{step_num}_enhanced.mp4")
            
            try:
                enhance_video(
                    current_file, video_output,
                    use_ai=use_ai,
                    preset=video_preset
                )
                current_file = video_output
                stats['steps'].append('video_enhancement')
            except Exception as e:
                print(f"  Warning: Video enhancement failed: {e}")
        
        # Step 3: Enhance audio
        if enhance_audio_quality:
            step_num += 1
            print(f"\n[Step {step_num}] Enhancing audio...")
            audio_output = os.path.join(tmpdir, f"step{step_num}_audio.mp4")
            
            try:
                enhance_video_audio(current_file, audio_output, preset=audio_preset)
                current_file = audio_output
                stats['steps'].append('audio_enhancement')
            except Exception as e:
                print(f"  Warning: Audio enhancement failed: {e}")
        
        # Final: Copy to output location with proper encoding
        print(f"\n[Final] Encoding output...")
        cmd = [
            'ffmpeg', '-y',
            '-i', current_file,
            '-c:v', 'libx264',
            '-preset', 'slow',
            '-crf', '18',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-movflags', '+faststart',
            output_path
        ]
        subprocess.run(cmd, check=True, capture_output=True)
    
    print(f"\n✅ Processing complete!")
    print(f"   Output: {output_path}")
    print(f"   Steps: {', '.join(stats['steps'])}")
    
    return stats


def main():
    parser = argparse.ArgumentParser(
        description='Complete video enhancement: watermark removal + video + audio'
    )
    parser.add_argument('input', help='Input video file')
    parser.add_argument('-o', '--output', help='Output video file')
    
    # Feature toggles
    parser.add_argument('--no-watermark', action='store_true',
                       help='Skip watermark removal')
    parser.add_argument('--no-video', action='store_true',
                       help='Skip video enhancement')
    parser.add_argument('--no-audio', action='store_true',
                       help='Skip audio enhancement')
    
    # Presets
    parser.add_argument('--video-preset', 
                       choices=['cinematic', 'vivid', 'clean', 'hdr'],
                       default='cinematic',
                       help='Video enhancement preset')
    parser.add_argument('--audio-preset',
                       choices=['balanced', 'voice', 'music', 'podcast'],
                       default='balanced',
                       help='Audio enhancement preset')
    
    # AI option
    parser.add_argument('--ai', action='store_true',
                       help='Use AI upscaling (slower, better quality)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        return 1
    
    output = args.output
    if not output:
        base, ext = os.path.splitext(args.input)
        output = f"{base}_processed.mp4"
    
    process_complete(
        args.input, output,
        remove_watermark=not args.no_watermark,
        enhance_video_quality=not args.no_video,
        enhance_audio_quality=not args.no_audio,
        video_preset=args.video_preset,
        audio_preset=args.audio_preset,
        use_ai=args.ai
    )
    
    return 0


if __name__ == '__main__':
    exit(main())
