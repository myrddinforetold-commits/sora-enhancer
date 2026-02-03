#!/usr/bin/env python3
"""
Video Enhancer - AI-powered video upscaling and enhancement
"""

import argparse
import cv2
import numpy as np
import os
import subprocess
import tempfile
from pathlib import Path
from tqdm import tqdm

# Check for GPU (lazy load torch) - AI is optional
DEVICE = 'cpu'
AI_AVAILABLE = False

def get_device():
    global DEVICE, AI_AVAILABLE
    try:
        import torch
        AI_AVAILABLE = True
        if torch.backends.mps.is_available():
            DEVICE = 'mps'
        elif torch.cuda.is_available():
            DEVICE = 'cuda'
    except ImportError:
        AI_AVAILABLE = False
    return DEVICE


def extract_frames(video_path: str, output_dir: str) -> tuple[int, float, tuple[int, int]]:
    """Extract frames from video, return (frame_count, fps, resolution)"""
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"Input: {width}x{height} @ {fps}fps, {frame_count} frames")
    
    os.makedirs(output_dir, exist_ok=True)
    
    for i in tqdm(range(frame_count), desc="Extracting frames"):
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imwrite(os.path.join(output_dir, f"frame_{i:06d}.png"), frame)
    
    cap.release()
    return frame_count, fps, (width, height)


def enhance_frame(frame: np.ndarray, scale: int = 2, sharpen: float = 0.5, 
                  brightness: float = 1.0, contrast: float = 1.0, 
                  saturation: float = 1.0) -> np.ndarray:
    """Apply enhancements to a single frame"""
    
    # Simple upscaling with INTER_LANCZOS4 (fast, decent quality)
    if scale > 1:
        h, w = frame.shape[:2]
        frame = cv2.resize(frame, (w * scale, h * scale), interpolation=cv2.INTER_LANCZOS4)
    
    # Sharpening
    if sharpen > 0:
        kernel = np.array([[-1, -1, -1],
                          [-1, 9 + sharpen * 2, -1],
                          [-1, -1, -1]])
        frame = cv2.filter2D(frame, -1, kernel * (sharpen * 0.3))
        frame = np.clip(frame, 0, 255).astype(np.uint8)
    
    # Brightness and contrast
    if brightness != 1.0 or contrast != 1.0:
        frame = cv2.convertScaleAbs(frame, alpha=contrast, beta=(brightness - 1) * 50)
    
    # Saturation
    if saturation != 1.0:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] *= saturation
        hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)
        frame = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    
    return frame


def enhance_frame_ai(frame: np.ndarray, upsampler) -> np.ndarray:
    """Enhance frame using Real-ESRGAN"""
    output, _ = upsampler.enhance(frame, outscale=2)
    return output


def process_frames(input_dir: str, output_dir: str, use_ai: bool = False,
                   scale: int = 2, sharpen: float = 0.5, brightness: float = 1.0,
                   contrast: float = 1.0, saturation: float = 1.0):
    """Process all frames with enhancement"""
    
    os.makedirs(output_dir, exist_ok=True)
    frames = sorted([f for f in os.listdir(input_dir) if f.endswith('.png')])
    
    upsampler = None
    if use_ai and AI_AVAILABLE:
        try:
            from realesrgan import RealESRGANer
            from basicsr.archs.rrdbnet_arch import RRDBNet
            
            model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, 
                           num_block=23, num_grow_ch=32, scale=4)
            
            model_path = os.path.expanduser('~/.cache/realesrgan/RealESRGAN_x4plus.pth')
            
            # Download model if not exists
            if not os.path.exists(model_path):
                os.makedirs(os.path.dirname(model_path), exist_ok=True)
                print("Downloading Real-ESRGAN model...")
                import urllib.request
                url = 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth'
                urllib.request.urlretrieve(url, model_path)
            
            upsampler = RealESRGANer(
                scale=4,
                model_path=model_path,
                model=model,
                tile=400,
                tile_pad=10,
                pre_pad=0,
                half=False,
                device=get_device()
            )
            print("AI enhancement enabled (Real-ESRGAN)")
        except Exception as e:
            print(f"AI enhancement not available: {e}")
            print("Falling back to standard enhancement")
            use_ai = False
    
    for frame_file in tqdm(frames, desc="Enhancing frames"):
        frame_path = os.path.join(input_dir, frame_file)
        frame = cv2.imread(frame_path)
        
        if use_ai and upsampler:
            enhanced = enhance_frame_ai(frame, upsampler)
            # Apply additional tweaks after AI upscaling
            enhanced = enhance_frame(enhanced, scale=1, sharpen=sharpen * 0.3,
                                    brightness=brightness, contrast=contrast,
                                    saturation=saturation)
        else:
            enhanced = enhance_frame(frame, scale=scale, sharpen=sharpen,
                                    brightness=brightness, contrast=contrast,
                                    saturation=saturation)
        
        output_path = os.path.join(output_dir, frame_file)
        cv2.imwrite(output_path, enhanced)


def frames_to_video(frames_dir: str, output_path: str, fps: float, 
                    audio_source: str = None):
    """Combine frames back into video with optional audio"""
    
    frames = sorted([f for f in os.listdir(frames_dir) if f.endswith('.png')])
    if not frames:
        raise ValueError("No frames found")
    
    first_frame = cv2.imread(os.path.join(frames_dir, frames[0]))
    h, w = first_frame.shape[:2]
    
    # Use ffmpeg for better compression
    frame_pattern = os.path.join(frames_dir, 'frame_%06d.png')
    
    cmd = [
        'ffmpeg', '-y',
        '-framerate', str(fps),
        '-i', frame_pattern,
        '-c:v', 'libx264',
        '-preset', 'slow',
        '-crf', '18',
        '-pix_fmt', 'yuv420p',
    ]
    
    if audio_source:
        cmd.extend(['-i', audio_source, '-c:a', 'aac', '-b:a', '192k', '-shortest'])
    
    cmd.append(output_path)
    
    print(f"Encoding video: {w}x{h} @ {fps}fps")
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"Output saved: {output_path}")


def enhance_video(input_path: str, output_path: str, 
                  use_ai: bool = True,
                  scale: int = 2,
                  sharpen: float = 0.5,
                  brightness: float = 1.0,
                  contrast: float = 1.0,
                  saturation: float = 1.1,
                  preset: str = None):
    """Main function to enhance a video"""
    
    # Presets
    presets = {
        'cinematic': {'sharpen': 0.3, 'contrast': 1.1, 'saturation': 0.95, 'brightness': 0.98},
        'vivid': {'sharpen': 0.6, 'contrast': 1.15, 'saturation': 1.3, 'brightness': 1.02},
        'clean': {'sharpen': 0.2, 'contrast': 1.0, 'saturation': 1.0, 'brightness': 1.0},
        'hdr': {'sharpen': 0.5, 'contrast': 1.2, 'saturation': 1.2, 'brightness': 1.05},
    }
    
    if preset and preset in presets:
        p = presets[preset]
        sharpen = p.get('sharpen', sharpen)
        contrast = p.get('contrast', contrast)
        saturation = p.get('saturation', saturation)
        brightness = p.get('brightness', brightness)
        print(f"Using preset: {preset}")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        frames_in = os.path.join(tmpdir, 'frames_in')
        frames_out = os.path.join(tmpdir, 'frames_out')
        
        # Extract frames
        frame_count, fps, (w, h) = extract_frames(input_path, frames_in)
        
        # Process frames
        process_frames(frames_in, frames_out, use_ai=use_ai, scale=scale,
                      sharpen=sharpen, brightness=brightness, 
                      contrast=contrast, saturation=saturation)
        
        # Rebuild video with original audio
        frames_to_video(frames_out, output_path, fps, audio_source=input_path)
    
    print("✅ Enhancement complete!")


def main():
    parser = argparse.ArgumentParser(description='AI Video Enhancer')
    parser.add_argument('input', help='Input video file')
    parser.add_argument('-o', '--output', help='Output video file')
    parser.add_argument('--ai', action='store_true', default=True,
                       help='Use AI upscaling (Real-ESRGAN)')
    parser.add_argument('--no-ai', action='store_true',
                       help='Disable AI upscaling (faster)')
    parser.add_argument('--scale', type=int, default=2, 
                       help='Upscale factor (default: 2)')
    parser.add_argument('--sharpen', type=float, default=0.5,
                       help='Sharpening amount 0-1 (default: 0.5)')
    parser.add_argument('--brightness', type=float, default=1.0,
                       help='Brightness multiplier (default: 1.0)')
    parser.add_argument('--contrast', type=float, default=1.0,
                       help='Contrast multiplier (default: 1.0)')
    parser.add_argument('--saturation', type=float, default=1.1,
                       help='Saturation multiplier (default: 1.1)')
    parser.add_argument('--preset', choices=['cinematic', 'vivid', 'clean', 'hdr'],
                       help='Use a preset configuration')
    
    args = parser.parse_args()
    
    input_path = args.input
    if not os.path.exists(input_path):
        print(f"Error: Input file not found: {input_path}")
        return 1
    
    output_path = args.output
    if not output_path:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_enhanced.mp4"
    
    use_ai = args.ai and not args.no_ai
    
    enhance_video(
        input_path, output_path,
        use_ai=use_ai,
        scale=args.scale,
        sharpen=args.sharpen,
        brightness=args.brightness,
        contrast=args.contrast,
        saturation=args.saturation,
        preset=args.preset
    )
    
    return 0


if __name__ == '__main__':
    exit(main())
