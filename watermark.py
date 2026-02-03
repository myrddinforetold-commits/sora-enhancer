#!/usr/bin/env python3
"""
Sora Watermark Removal - Detects and removes Sora watermarks using inpainting
"""

import cv2
import numpy as np
from pathlib import Path


def detect_sora_watermark(frame: np.ndarray) -> np.ndarray:
    """
    Detect Sora watermark in frame and return mask.
    Sora watermark is typically in bottom-right corner, white/gray text "Sora"
    """
    h, w = frame.shape[:2]
    
    # Create empty mask
    mask = np.zeros((h, w), dtype=np.uint8)
    
    # Sora watermark is usually in bottom-right quadrant
    # Focus on that region for detection
    roi_y = int(h * 0.85)  # Bottom 15%
    roi_x = int(w * 0.70)  # Right 30%
    roi = frame[roi_y:, roi_x:]
    
    # Convert to grayscale
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    # Detect bright text (watermark is usually white/light gray)
    # Use adaptive thresholding for varying backgrounds
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    
    # Find contours that could be text
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filter contours by size (text-like dimensions)
    for cnt in contours:
        x, y, cw, ch = cv2.boundingRect(cnt)
        area = cv2.contourArea(cnt)
        
        # Filter: reasonable text size, not too small, not too large
        if 100 < area < 10000 and 10 < cw < 300 and 5 < ch < 100:
            # Add padding around detected region
            pad = 5
            x1 = max(0, x - pad) + roi_x
            y1 = max(0, y - pad) + roi_y
            x2 = min(w, x + cw + pad) + roi_x - roi_x
            y2 = min(h, y + ch + pad) + roi_y - roi_y
            
            # Mark in mask with dilation for better coverage
            cv2.rectangle(mask, (x1, y1), (x1 + cw + pad*2, y1 + ch + pad*2), 255, -1)
    
    # Also check for common watermark positions with template matching
    # Add a generous region in bottom-right for safety
    watermark_region = np.zeros((h, w), dtype=np.uint8)
    
    # Common Sora watermark position: bottom-right corner
    # Approximate size: ~80x25 pixels for "Sora" text
    margin_x = int(w * 0.02)
    margin_y = int(h * 0.02)
    wm_w = int(w * 0.08)  # ~8% of width
    wm_h = int(h * 0.04)  # ~4% of height
    
    # Bottom-right corner region
    cv2.rectangle(watermark_region, 
                  (w - margin_x - wm_w, h - margin_y - wm_h),
                  (w - margin_x, h - margin_y),
                  128, -1)
    
    # Combine detected text with common position
    mask = cv2.bitwise_or(mask, watermark_region)
    
    # Dilate mask to ensure full coverage
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    mask = cv2.dilate(mask, kernel, iterations=2)
    
    return mask


def remove_watermark_inpaint(frame: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Remove watermark using inpainting"""
    # Use Telea inpainting algorithm (good for small regions)
    result = cv2.inpaint(frame, mask, inpaintRadius=5, flags=cv2.INPAINT_TELEA)
    return result


def remove_watermark_smart(frame: np.ndarray, mask: np.ndarray, 
                           prev_frame: np.ndarray = None) -> np.ndarray:
    """
    Smart watermark removal using temporal information if available.
    Falls back to inpainting if no previous frame.
    """
    if prev_frame is not None:
        # Use previous frame's clean region to fill current frame
        # This works well for static watermarks on moving backgrounds
        result = frame.copy()
        
        # Blend with previous frame in watermark region
        mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR) / 255.0
        result = (result * (1 - mask_3ch) + prev_frame * mask_3ch).astype(np.uint8)
        
        # Apply slight inpainting to smooth edges
        edge_mask = cv2.Canny(mask, 50, 150)
        edge_mask = cv2.dilate(edge_mask, None, iterations=2)
        result = cv2.inpaint(result, edge_mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
        
        return result
    else:
        return remove_watermark_inpaint(frame, mask)


def process_video_watermark(input_path: str, output_path: str,
                           method: str = 'auto') -> None:
    """
    Remove watermark from entire video.
    
    Methods:
    - 'auto': Auto-detect watermark position
    - 'bottom-right': Assume watermark in bottom-right
    - 'manual': Use provided mask coordinates
    """
    cap = cv2.VideoCapture(input_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"Processing {frame_count} frames for watermark removal...")
    
    # Output writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    prev_clean_frame = None
    
    # Detect watermark from first frame
    ret, first_frame = cap.read()
    if not ret:
        raise ValueError("Could not read video")
    
    # Get watermark mask (assume consistent position)
    watermark_mask = detect_sora_watermark(first_frame)
    
    # Reset video
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    
    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Remove watermark
        clean_frame = remove_watermark_smart(frame, watermark_mask, prev_clean_frame)
        
        out.write(clean_frame)
        prev_clean_frame = clean_frame
        frame_idx += 1
        
        if frame_idx % 30 == 0:
            print(f"  Processed {frame_idx}/{frame_count} frames")
    
    cap.release()
    out.release()
    print(f"Watermark removal complete: {output_path}")


def create_manual_mask(width: int, height: int, 
                       x: int, y: int, w: int, h: int) -> np.ndarray:
    """Create a manual mask for known watermark position"""
    mask = np.zeros((height, width), dtype=np.uint8)
    cv2.rectangle(mask, (x, y), (x + w, y + h), 255, -1)
    
    # Dilate for safety
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.dilate(mask, kernel, iterations=2)
    
    return mask


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Remove Sora watermark from video')
    parser.add_argument('input', help='Input video file')
    parser.add_argument('-o', '--output', help='Output video file')
    
    args = parser.parse_args()
    
    output = args.output or args.input.replace('.', '_nowatermark.')
    process_video_watermark(args.input, output)
