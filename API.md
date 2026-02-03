# Sora Video Enhancer API

Base URL: `http://localhost:8000` (dev) / `https://api.yoursite.com` (prod)

## Endpoints

### POST /enhance
Upload and process a video.

**Request:** `multipart/form-data`
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| file | File | required | Video file (mp4, mov, webm) |
| remove_watermark | bool | true | Remove Sora watermark |
| enhance_video | bool | true | Apply video enhancement |
| enhance_audio | bool | true | Apply audio enhancement |
| video_preset | string | "cinematic" | cinematic/vivid/clean/hdr |
| audio_preset | string | "balanced" | balanced/voice/music/podcast |

**Response:**
```json
{
  "job_id": "uuid-string"
}
```

### GET /status/{job_id}
Check processing status.

**Response:**
```json
{
  "status": "processing|complete|error",
  "progress": 0-100,
  "step": "Current step description",
  "error": "Error message if status=error"
}
```

### GET /download/{job_id}
Download the enhanced video (only when status=complete).

**Response:** Video file (video/mp4)

## Video Presets
- `cinematic` - Film-like color grading, subtle contrast
- `vivid` - Vibrant saturated colors
- `clean` - Natural, minimal processing  
- `hdr` - High dynamic range look

## Audio Presets
- `balanced` - General enhancement
- `voice` - Optimized for speech
- `music` - Optimized for music
- `podcast` - Voice clarity + noise reduction

## Example Flow
```javascript
// 1. Upload
const formData = new FormData();
formData.append('file', videoFile);
formData.append('remove_watermark', true);
formData.append('video_preset', 'cinematic');

const { job_id } = await fetch('/enhance', {
  method: 'POST',
  body: formData
}).then(r => r.json());

// 2. Poll status
let status;
do {
  await sleep(2000);
  status = await fetch(`/status/${job_id}`).then(r => r.json());
} while (status.status === 'processing');

// 3. Download
if (status.status === 'complete') {
  window.location = `/download/${job_id}`;
}
```
