#!/usr/bin/env python3
"""
Sora Video Enhancer - Complete Web App
- Watermark removal
- Video enhancement
- Audio enhancement
"""

import os
import uuid
import asyncio
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
import aiofiles

app = FastAPI(title="Sora Video Enhancer")

UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

jobs = {}


@app.get("/", response_class=HTMLResponse)
async def home():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Sora Video Enhancer - Remove Watermark & Enhance Quality</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="Remove Sora watermarks and enhance video quality with AI. Free online tool.">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
            min-height: 100vh;
            color: #fff;
        }
        .container { max-width: 700px; margin: 0 auto; padding: 40px 20px; }
        
        header { text-align: center; margin-bottom: 40px; }
        h1 { 
            font-size: 2.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        .tagline { color: #888; font-size: 1.1rem; }
        
        .features {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin: 30px 0;
        }
        .feature {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 20px 15px;
            text-align: center;
        }
        .feature-icon { font-size: 2rem; margin-bottom: 10px; }
        .feature-title { font-weight: 600; margin-bottom: 5px; }
        .feature-desc { font-size: 0.85rem; color: #888; }
        
        .card {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 20px;
        }
        
        .upload-area {
            border: 2px dashed rgba(255,255,255,0.2);
            border-radius: 12px;
            padding: 50px 30px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }
        .upload-area:hover { border-color: #667eea; background: rgba(102,126,234,0.05); }
        .upload-area.dragover { border-color: #764ba2; background: rgba(118,75,162,0.1); }
        .upload-area.has-file { border-color: #22c55e; background: rgba(34,197,94,0.05); }
        
        input[type="file"] { display: none; }
        
        .upload-icon { font-size: 3rem; margin-bottom: 15px; opacity: 0.5; }
        .upload-text { color: #888; margin-bottom: 10px; }
        .upload-btn {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 28px;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .upload-btn:hover { transform: translateY(-2px); box-shadow: 0 10px 30px rgba(102,126,234,0.3); }
        
        .file-name { 
            margin-top: 15px; 
            padding: 10px 15px;
            background: rgba(34,197,94,0.1);
            border-radius: 8px;
            color: #22c55e;
            display: none;
        }
        .file-name.show { display: block; }
        
        .options { margin: 25px 0; }
        .option-group { margin-bottom: 20px; }
        .option-label { 
            display: block; 
            margin-bottom: 8px; 
            font-weight: 500;
            color: #ccc;
        }
        
        .toggle-group { display: flex; gap: 10px; flex-wrap: wrap; }
        .toggle {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 10px 16px;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .toggle:hover { background: rgba(255,255,255,0.08); }
        .toggle.active { 
            background: rgba(102,126,234,0.2); 
            border-color: #667eea;
        }
        .toggle input { display: none; }
        .toggle-check {
            width: 18px;
            height: 18px;
            border: 2px solid #555;
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }
        .toggle.active .toggle-check { 
            background: #667eea; 
            border-color: #667eea;
        }
        .toggle.active .toggle-check::after {
            content: '✓';
            color: white;
            font-size: 12px;
        }
        
        select {
            width: 100%;
            padding: 12px 15px;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 8px;
            color: #fff;
            font-size: 1rem;
            cursor: pointer;
        }
        select option { background: #1a1a2e; }
        
        .submit-btn {
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 12px;
            color: white;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            margin-top: 10px;
        }
        .submit-btn:hover { transform: translateY(-2px); box-shadow: 0 15px 40px rgba(102,126,234,0.4); }
        .submit-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        
        .status {
            margin-top: 25px;
            padding: 25px;
            border-radius: 12px;
            display: none;
        }
        .status.show { display: block; }
        .status.processing { background: rgba(102,126,234,0.1); border: 1px solid rgba(102,126,234,0.3); }
        .status.complete { background: rgba(34,197,94,0.1); border: 1px solid rgba(34,197,94,0.3); }
        .status.error { background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3); }
        
        .status-header { display: flex; align-items: center; gap: 10px; margin-bottom: 15px; }
        .status-icon { font-size: 1.5rem; }
        .status-title { font-weight: 600; font-size: 1.1rem; }
        
        .progress-bar {
            height: 6px;
            background: rgba(255,255,255,0.1);
            border-radius: 3px;
            overflow: hidden;
            margin-top: 15px;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            width: 0%;
            transition: width 0.5s ease;
        }
        
        .download-btn {
            display: inline-block;
            background: #22c55e;
            color: white;
            padding: 14px 28px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            margin-top: 15px;
            transition: all 0.2s;
        }
        .download-btn:hover { background: #16a34a; transform: translateY(-2px); }
        
        footer {
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid rgba(255,255,255,0.1);
            color: #666;
            font-size: 0.9rem;
        }
        footer a { color: #888; }
        
        @media (max-width: 600px) {
            .features { grid-template-columns: 1fr; }
            h1 { font-size: 1.8rem; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>✨ Sora Video Enhancer</h1>
            <p class="tagline">Remove watermarks & enhance quality instantly</p>
        </header>
        
        <div class="features">
            <div class="feature">
                <div class="feature-icon">🚫</div>
                <div class="feature-title">Remove Watermark</div>
                <div class="feature-desc">AI-powered Sora watermark removal</div>
            </div>
            <div class="feature">
                <div class="feature-icon">🎬</div>
                <div class="feature-title">Enhance Video</div>
                <div class="feature-desc">Upscale, sharpen & color grade</div>
            </div>
            <div class="feature">
                <div class="feature-icon">🔊</div>
                <div class="feature-title">Enhance Audio</div>
                <div class="feature-desc">Noise reduction & clarity</div>
            </div>
        </div>
        
        <form id="uploadForm" class="card">
            <div class="upload-area" id="dropZone">
                <div class="upload-icon">🎥</div>
                <p class="upload-text">Drag & drop your Sora video here</p>
                <label class="upload-btn">
                    Choose File
                    <input type="file" id="videoFile" accept="video/*">
                </label>
                <div class="file-name" id="fileName"></div>
            </div>
            
            <div class="options">
                <div class="option-group">
                    <label class="option-label">Enhancement Options</label>
                    <div class="toggle-group">
                        <label class="toggle active" id="toggleWatermark">
                            <input type="checkbox" name="remove_watermark" checked>
                            <span class="toggle-check"></span>
                            <span>Remove Watermark</span>
                        </label>
                        <label class="toggle active" id="toggleVideo">
                            <input type="checkbox" name="enhance_video" checked>
                            <span class="toggle-check"></span>
                            <span>Enhance Video</span>
                        </label>
                        <label class="toggle active" id="toggleAudio">
                            <input type="checkbox" name="enhance_audio" checked>
                            <span class="toggle-check"></span>
                            <span>Enhance Audio</span>
                        </label>
                    </div>
                </div>
                
                <div class="option-group">
                    <label class="option-label">Video Style</label>
                    <select id="videoPreset">
                        <option value="cinematic">🎬 Cinematic - Film-like color grading</option>
                        <option value="vivid">🌈 Vivid - Vibrant & punchy colors</option>
                        <option value="clean">✨ Clean - Natural enhancement</option>
                        <option value="hdr">☀️ HDR - High dynamic range look</option>
                    </select>
                </div>
                
                <div class="option-group">
                    <label class="option-label">Audio Style</label>
                    <select id="audioPreset">
                        <option value="balanced">⚖️ Balanced - General enhancement</option>
                        <option value="voice">🎙️ Voice - Optimized for speech</option>
                        <option value="music">🎵 Music - Optimized for music</option>
                        <option value="podcast">🎧 Podcast - Clear voice + noise reduction</option>
                    </select>
                </div>
            </div>
            
            <button type="submit" class="submit-btn" id="submitBtn">
                🚀 Enhance Video
            </button>
        </form>
        
        <div class="status" id="status">
            <div class="status-header">
                <span class="status-icon" id="statusIcon">⏳</span>
                <span class="status-title" id="statusTitle">Processing...</span>
            </div>
            <p id="statusText">Your video is being enhanced. This may take a few minutes.</p>
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            <div id="downloadArea"></div>
        </div>
        
        <footer>
            <p>Free • No signup • Processed locally</p>
        </footer>
    </div>
    
    <script>
        const form = document.getElementById('uploadForm');
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('videoFile');
        const fileNameEl = document.getElementById('fileName');
        const status = document.getElementById('status');
        const statusIcon = document.getElementById('statusIcon');
        const statusTitle = document.getElementById('statusTitle');
        const statusText = document.getElementById('statusText');
        const progressFill = document.getElementById('progressFill');
        const downloadArea = document.getElementById('downloadArea');
        const submitBtn = document.getElementById('submitBtn');
        
        // Toggle buttons
        document.querySelectorAll('.toggle').forEach(toggle => {
            toggle.addEventListener('click', () => {
                toggle.classList.toggle('active');
                toggle.querySelector('input').checked = toggle.classList.contains('active');
            });
        });
        
        // Drag and drop
        ['dragenter', 'dragover'].forEach(e => {
            dropZone.addEventListener(e, (ev) => { ev.preventDefault(); dropZone.classList.add('dragover'); });
        });
        ['dragleave', 'drop'].forEach(e => {
            dropZone.addEventListener(e, (ev) => { ev.preventDefault(); dropZone.classList.remove('dragover'); });
        });
        dropZone.addEventListener('drop', (e) => {
            fileInput.files = e.dataTransfer.files;
            updateFileName();
        });
        fileInput.addEventListener('change', updateFileName);
        
        function updateFileName() {
            if (fileInput.files[0]) {
                fileNameEl.textContent = '📁 ' + fileInput.files[0].name;
                fileNameEl.classList.add('show');
                dropZone.classList.add('has-file');
            }
        }
        
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            if (!fileInput.files[0]) {
                alert('Please select a video file');
                return;
            }
            
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            formData.append('remove_watermark', document.querySelector('[name="remove_watermark"]').checked);
            formData.append('enhance_video', document.querySelector('[name="enhance_video"]').checked);
            formData.append('enhance_audio', document.querySelector('[name="enhance_audio"]').checked);
            formData.append('video_preset', document.getElementById('videoPreset').value);
            formData.append('audio_preset', document.getElementById('audioPreset').value);
            
            submitBtn.disabled = true;
            status.className = 'status show processing';
            statusIcon.textContent = '⏳';
            statusTitle.textContent = 'Processing...';
            statusText.textContent = 'Uploading your video...';
            progressFill.style.width = '5%';
            downloadArea.innerHTML = '';
            
            try {
                const res = await fetch('/enhance', { method: 'POST', body: formData });
                if (!res.ok) throw new Error('Upload failed');
                
                const { job_id } = await res.json();
                progressFill.style.width = '15%';
                statusText.textContent = 'Processing your video. This may take a few minutes...';
                
                while (true) {
                    await new Promise(r => setTimeout(r, 2000));
                    const pollRes = await fetch(`/status/${job_id}`);
                    const job = await pollRes.json();
                    
                    if (job.status === 'complete') {
                        status.className = 'status show complete';
                        statusIcon.textContent = '✅';
                        statusTitle.textContent = 'Enhancement Complete!';
                        statusText.textContent = 'Your video has been enhanced and is ready to download.';
                        progressFill.style.width = '100%';
                        downloadArea.innerHTML = `<a href="/download/${job_id}" class="download-btn">⬇️ Download Enhanced Video</a>`;
                        break;
                    } else if (job.status === 'error') {
                        throw new Error(job.error || 'Processing failed');
                    } else {
                        progressFill.style.width = `${15 + (job.progress || 0) * 0.8}%`;
                        if (job.step) statusText.textContent = job.step;
                    }
                }
            } catch (err) {
                status.className = 'status show error';
                statusIcon.textContent = '❌';
                statusTitle.textContent = 'Error';
                statusText.textContent = err.message;
            } finally {
                submitBtn.disabled = false;
            }
        });
    </script>
</body>
</html>
"""


@app.post("/enhance")
async def start_enhance(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    remove_watermark: bool = Form(True),
    enhance_video: bool = Form(True),
    enhance_audio: bool = Form(True),
    video_preset: str = Form("cinematic"),
    audio_preset: str = Form("balanced")
):
    job_id = str(uuid.uuid4())
    
    input_path = UPLOAD_DIR / f"{job_id}_{file.filename}"
    async with aiofiles.open(input_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    output_path = OUTPUT_DIR / f"{job_id}_enhanced.mp4"
    
    jobs[job_id] = {
        "status": "processing",
        "progress": 0,
        "step": "Starting...",
        "input": str(input_path),
        "output": str(output_path)
    }
    
    background_tasks.add_task(
        run_processing, job_id, str(input_path), str(output_path),
        remove_watermark, enhance_video, enhance_audio,
        video_preset, audio_preset
    )
    
    return {"job_id": job_id}


def run_processing(job_id: str, input_path: str, output_path: str,
                   remove_watermark: bool, enhance_video_flag: bool, 
                   enhance_audio_flag: bool,
                   video_preset: str, audio_preset: str):
    try:
        from process import process_complete
        
        jobs[job_id]["step"] = "Processing video..."
        jobs[job_id]["progress"] = 10
        
        process_complete(
            input_path, output_path,
            remove_watermark=remove_watermark,
            enhance_video_quality=enhance_video_flag,
            enhance_audio_quality=enhance_audio_flag,
            video_preset=video_preset,
            audio_preset=audio_preset,
            use_ai=False
        )
        
        jobs[job_id]["status"] = "complete"
        jobs[job_id]["progress"] = 100
        
    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)
    finally:
        try:
            os.remove(input_path)
        except:
            pass


@app.get("/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]


@app.get("/download/{job_id}")
async def download(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    if job["status"] != "complete":
        raise HTTPException(status_code=400, detail="Job not complete")
    
    return FileResponse(
        job["output"],
        media_type="video/mp4",
        filename="enhanced_video.mp4"
    )


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
