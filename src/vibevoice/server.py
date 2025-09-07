"""FastAPI server for Whisper transcription"""

import uvicorn
import os
import time
from datetime import datetime, timedelta
from fastapi import FastAPI
from pydantic import BaseModel
from faster_whisper import WhisperModel

app = FastAPI()

# Store service start time for uptime calculation
service_start_time = time.time()

model = WhisperModel("large", device="cuda", compute_type="float16")
# Enable in case you want to run on CPU, but it's much slower
#model = WhisperModel("medium", device="cpu", compute_type="int8")

class TranscribeRequest(BaseModel):
    file_path: str

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/status")
def status_check():
    """Return detailed service status information"""
    uptime_seconds = time.time() - service_start_time
    uptime_delta = timedelta(seconds=int(uptime_seconds))
    
    # Format uptime nicely
    if uptime_delta.days > 0:
        uptime_str = f"{uptime_delta.days}d {uptime_delta.seconds//3600}h {(uptime_delta.seconds//60)%60}m"
    elif uptime_delta.seconds >= 3600:
        uptime_str = f"{uptime_delta.seconds//3600}h {(uptime_delta.seconds//60)%60}m {uptime_delta.seconds%60}s"
    elif uptime_delta.seconds >= 60:
        uptime_str = f"{(uptime_delta.seconds//60)}m {uptime_delta.seconds%60}s"
    else:
        uptime_str = f"{uptime_delta.seconds}s"
    
    return {
        "status": "running",
        "uptime": uptime_str,
        "uptime_seconds": int(uptime_seconds),
        "start_time": datetime.fromtimestamp(service_start_time).isoformat(),
        "model": os.getenv('OLLAMA_MODEL', 'gemma3:27b'),
        "keys": {
            "dictation": os.getenv('VOICEKEY', 'ctrl_r'),
            "command": os.getenv('VOICEKEY_CMD', 'scroll_lock'),
            "custom": os.getenv('VOICEKEY_CUSTOM', 'num_lock')
        },
        "screenshot_enabled": os.getenv('INCLUDE_SCREENSHOT', 'true').lower() == 'true',
        "screenshot_max_width": int(os.getenv('SCREENSHOT_MAX_WIDTH', '1024'))
    }

@app.post("/transcribe/")
async def transcribe(request: TranscribeRequest):
    segments, info = model.transcribe(request.file_path)
    text = " ".join([segment.text.strip() for segment in segments])
    return {"text": text}

def run_server():
    uvicorn.run(app, host="0.0.0.0", port=4242)

if __name__ == "__main__":
    run_server()
