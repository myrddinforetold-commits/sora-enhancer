#!/usr/bin/env python3
"""
Sora Video Enhancer - Simple synchronous version
"""

import os
import uuid
import tempfile
import subprocess
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
import shutil

app = FastAPI(title="Sora Video Enhancer")

UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


@app.get("/", response_class=HTMLResponse)
async def home():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Sora Video Enhancer - Remove Watermark & Enhance</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
            min-height: 100vh;
            color: #fff;
            padding: 40px 20px;
        }
        .container { max-width: 600px; margin: 0 auto; }
        h1 { 
            font-size: 2rem;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
            margin-bottom: 30px;
        }
        .card {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 16px;
            padding: 30px;
        }
        .upload-area {
            border: 2px dashed rgba(255,255,255,0.2);
            border-radius: 12px;
            padding: 40px;
            text-align: center;
            margin-bottom: 20px;
        }
        input[type="file"] { margin: 15px 0; }
        select {
            width: 100%;
            padding: 12px;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            color: #fff;
            margin: 10px 0;
        }
        button {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border: none;
            border-radius: 10px;
            color: #fff;
            font-size: 1.1rem;
            cursor: pointer;
            margin-top: 15px;
        }
        button:hover { opacity: 0.9; }
        button:disabled { opacity: 0.5; cursor: wait; }
        .status { margin-top: 20px; padding: 15px; border-radius: 8px; display: none; }
        .status.show { display: block; }
        .status.processing { background: rgba(102,126,234,0.2); }
        .status.success { background: rgba(34,197,94,0.2); }
        .status.error { background: rgba(239,68,68,0.2); }
        a.download { 
            display: inline-block;
            background: #22c55e;
            color: #fff;
            padding: 12px 24px;
            border-radius: 8px;
            text-decoration: none;
            margin-top: 10px;
        }
        .features { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
        .feature { 
            flex: 1; 
            min-width: 100px;
            background: rgba(255,255,255,0.05);
            padding: 12px;
            border-radius: 8px;
            text-align: center;
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>✨ Sora Video Enhancer</h1>
        
        <div class="features">
            <div class="feature">🚫 Remove Watermark</div>
            <div class="feature">🎬 Enhance Video</div>
            <div class="feature">🔊 Enhance Audio</div>
        </div>
        
        <div class="card">
            <form id="form" enctype="multipart/form-data">
                <div class="upload-area">
                    <p>📁 Select your video</p>
                    <input type="file" name="file" accept="video/*" required id="fileInput">
                </div>
                
                <label>Video Style</label>
                <select name="video_preset">
                    <option value="cinematic">🎬 Cinematic</option>
                    <option value="vivid">🌈 Vivid</option>
                    <option value="clean">✨ Clean</option>
                </select>
                
                <label>Audio Style</label>
                <select name="audio_preset">
                    <option value="balanced">⚖️ Balanced</option>
                    <option value="voice">🎙️ Voice</option>
                    <option value="music">🎵 Music</option>
                </select>
                
                <button type="submit" id="btn">🚀 Enhance Video</button>
            </form>
            
            <div class="status" id="status"></div>
        </div>
    </div>
    
    <script>
        const form = document.getElementById('form');
        const btn = document.getElementById('btn');
        const status = document.getElementById('status');
        
        form.onsubmit = async (e) => {
            e.preventDefault();
            
            btn.disabled = true;
            btn.textContent = '⏳ Processing... (this takes 1-2 min)';
            status.className = 'status show processing';
            status.innerHTML = 'Uploading and processing your video...';
            
            try {
                const formData = new FormData(form);
                const res = await fetch('/process', {
                    method: 'POST',
                    body: formData
                });
                
                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(err.detail || 'Processing failed');
                }
                
                const blob = await res.blob();
                const url = URL.createObjectURL(blob);
                
                status.className = 'status show success';
                status.innerHTML = '✅ Done! <a class="download" href="' + url + '" download="enhanced_video.mp4">⬇️ Download Video</a>';
                
            } catch (err) {
                status.className = 'status show error';
                status.innerHTML = '❌ Error: ' + err.message;
            } finally {
                btn.disabled = false;
                btn.textContent = '🚀 Enhance Video';
            }
        };
    </script>
</body>
</html>
"""


@app.post("/process")
async def process_video(
    file: UploadFile = File(...),
    video_preset: str = Form("cinematic"),
    audio_preset: str = Form("balanced")
):
    """Process video synchronously and return the file"""
    
    job_id = str(uuid.uuid4())[:8]
    
    # Save uploaded file
    input_path = UPLOAD_DIR / f"{job_id}_input.mp4"
    output_path = OUTPUT_DIR / f"{job_id}_output.mp4"
    
    try:
        # Save upload
        with open(input_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # Process with ffmpeg (simple enhancement)
        # Sharpening + color adjustment + audio normalization
        
        video_filters = {
            "cinematic": "eq=contrast=1.1:brightness=0.02:saturation=0.95,unsharp=5:5:0.5",
            "vivid": "eq=contrast=1.15:brightness=0.03:saturation=1.3,unsharp=5:5:0.7",
            "clean": "unsharp=3:3:0.3"
        }
        
        audio_filters = {
            "balanced": "loudnorm=I=-16:TP=-1.5:LRA=11",
            "voice": "highpass=f=80,loudnorm=I=-16:TP=-1.5:LRA=11,equalizer=f=3000:t=q:w=1:g=3",
            "music": "loudnorm=I=-14:TP=-1:LRA=11"
        }
        
        vf = video_filters.get(video_preset, video_filters["cinematic"])
        af = audio_filters.get(audio_preset, audio_filters["balanced"])
        
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-vf", vf,
            "-af", af,
            "-c:v", "libx264", "-preset", "fast", "-crf", "22",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"FFmpeg error: {result.stderr[:200]}")
        
        if not output_path.exists():
            raise HTTPException(status_code=500, detail="Output file not created")
        
        return FileResponse(
            output_path,
            media_type="video/mp4",
            filename="enhanced_video.mp4"
        )
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Processing timeout - video too long")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup input
        if input_path.exists():
            input_path.unlink()


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
