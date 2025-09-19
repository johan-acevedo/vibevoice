"""FastAPI server for Whisper transcription"""

import uvicorn
import os
import time
from datetime import datetime, timedelta
from fastapi import FastAPI
from pydantic import BaseModel
from faster_whisper import WhisperModel
from typing import Dict, Tuple

app = FastAPI()

# Store service start time for uptime calculation
service_start_time = time.time()

# Attempt GPU first; on failure, fall back to CPU.
# Sizes and compute types can be tuned via environment variables.
WHISPER_SIZE_GPU = os.getenv("WHISPER_SIZE_GPU", "Systran/faster-distil-whisper-large-v3")
WHISPER_COMPUTE_GPU = os.getenv("WHISPER_COMPUTE_GPU", "float16")
WHISPER_SIZE_CPU = os.getenv("WHISPER_SIZE_CPU", "Systran/faster-distil-whisper-large-v3")
WHISPER_COMPUTE_CPU = os.getenv("WHISPER_COMPUTE_CPU", "int8")

# Swedish-specific model override (falls back to GPU/CPU defaults if unset).
WHISPER_MODEL_SWEDISH = os.getenv("WHISPER_MODEL_SWEDISH", "KBLab/kb-whisper-large")

model_cache: Dict[Tuple[str, str, str], WhisperModel] = {}


def load_model(model_name: str, device: str, compute_type: str) -> WhisperModel:
    """Load (or reuse) a Whisper model for the requested configuration."""
    cache_key = (model_name, device, compute_type)
    if cache_key in model_cache:
        return model_cache[cache_key]

    print(f"Loading Whisper model '{model_name}' on {device} (compute={compute_type})")
    model_instance = WhisperModel(model_name, device=device, compute_type=compute_type)
    model_cache[cache_key] = model_instance
    return model_instance


whisper_backend = None
whisper_model_size = None
whisper_compute_type = None
primary_model = None
language_model_runtime: Dict[str, Dict[str, str]] = {}

try:
    primary_model = load_model(WHISPER_SIZE_GPU, device="cuda", compute_type=WHISPER_COMPUTE_GPU)
    whisper_backend = "cuda"
    whisper_model_size = WHISPER_SIZE_GPU
    whisper_compute_type = WHISPER_COMPUTE_GPU
except Exception as e:
    # Log and fall back to CPU so the app remains usable after suspend
    print(
        f"Failed to initialize Whisper on CUDA ({e}). Falling back to CPU: "
        f"size={WHISPER_SIZE_CPU}, compute_type={WHISPER_COMPUTE_CPU}"
    )
    primary_model = load_model(WHISPER_SIZE_CPU, device="cpu", compute_type=WHISPER_COMPUTE_CPU)
    whisper_backend = "cpu"
    whisper_model_size = WHISPER_SIZE_CPU
    whisper_compute_type = WHISPER_COMPUTE_CPU

language_model_runtime["default"] = {
    "backend": whisper_backend,
    "size": whisper_model_size,
    "compute_type": whisper_compute_type,
}


def get_model_for_language(language: str | None) -> WhisperModel:
    """Return a Whisper model suited for the requested language."""
    if language and language.lower().startswith("sv"):
        runtime_override = language_model_runtime.get("sv")
        if runtime_override:
            backend = runtime_override.get("backend", whisper_backend or "cuda")
            compute = runtime_override.get("compute_type", whisper_compute_type or WHISPER_COMPUTE_CPU)
            return load_model(
                runtime_override.get("size", WHISPER_MODEL_SWEDISH),
                device=backend,
                compute_type=compute,
            )

        # Prefer the currently active backend (GPU if available), fall back to CPU otherwise.
        preferred_device = whisper_backend or "cuda"
        preferred_compute = whisper_compute_type if whisper_backend != "cpu" else WHISPER_COMPUTE_CPU

        try:
            swedish_model = load_model(
                WHISPER_MODEL_SWEDISH,
                device=preferred_device,
                compute_type=preferred_compute,
            )
            language_model_runtime["sv"] = {
                "backend": preferred_device,
                "size": WHISPER_MODEL_SWEDISH,
                "compute_type": preferred_compute,
            }
            return swedish_model
        except Exception as e:
            print(
                f"Failed to load Swedish model on {preferred_device} ({preferred_compute}): {e}. "
                "Retrying on CPU."
            )
            swedish_model_cpu = load_model(
                WHISPER_MODEL_SWEDISH,
                device="cpu",
                compute_type=WHISPER_COMPUTE_CPU,
            )
            language_model_runtime["sv"] = {
                "backend": "cpu",
                "size": WHISPER_MODEL_SWEDISH,
                "compute_type": WHISPER_COMPUTE_CPU,
            }
            return swedish_model_cpu

    return primary_model

class TranscribeRequest(BaseModel):
    file_path: str
    language: str = None  # Optional: force specific language ("en", "sv", etc.)
    task: str = "transcribe"  # "transcribe" or "translate"
    initial_prompt: str = None  # Context prompt for better transcription
    beam_size: int = 5  # Beam search size for better accuracy
    best_of: int = 1  # Number of candidates to consider
    temperature: float = 0  # Sampling temperature (0 = greedy, higher = more random)
    vad_filter: bool = True  # Voice activity detection filter
    log_prob_threshold: float = -1.0  # Filter out low-confidence segments

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
        "whisper": {
            "backend": whisper_backend,
            "size": whisper_model_size,
            "compute_type": whisper_compute_type,
        },
        "language_models": language_model_runtime,
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
    # Prepare transcription parameters with advanced decoding settings
    transcribe_kwargs = {
        "audio": request.file_path,
        "beam_size": request.beam_size,
        "best_of": request.best_of,
        "temperature": request.temperature,
        "vad_filter": request.vad_filter,
        "log_prob_threshold": request.log_prob_threshold,
    }

    # Add optional parameters if provided
    if request.language:
        transcribe_kwargs["language"] = request.language
    if request.task:
        transcribe_kwargs["task"] = request.task
    if request.initial_prompt:
        transcribe_kwargs["initial_prompt"] = request.initial_prompt

    # Try transcription with temperature fallback for robustness
    temperatures_to_try = [request.temperature, 0.2, 0.4] if request.temperature == 0 else [request.temperature]

    model_instance = get_model_for_language(request.language)

    for temp in temperatures_to_try:
        try:
            transcribe_kwargs["temperature"] = temp
            segments, info = model_instance.transcribe(**transcribe_kwargs)

            # Filter segments by log probability if threshold is set
            if request.log_prob_threshold is not None:
                filtered_segments = []
                for segment in segments:
                    avg_logprob = getattr(segment, 'avg_logprob', None)
                    if avg_logprob is None or avg_logprob > request.log_prob_threshold:
                        filtered_segments.append(segment)

                # Fall back to the unfiltered segments if we filtered everything out.
                if filtered_segments:
                    segments = filtered_segments
                else:
                    print(
                        "All segments were filtered out by log_prob_threshold; "
                        "returning unfiltered transcription instead."
                    )

            text = " ".join([segment.text.strip() for segment in segments])

            # If we got text with the first temperature, return it
            if text.strip() and temp == request.temperature:
                return {"text": text}

            # If we got text with fallback temperature, log it and return
            if text.strip():
                print(f"Used fallback temperature {temp} for transcription")
                return {"text": text}

        except Exception as e:
            print(f"Transcription failed with temperature {temp}: {e}")
            continue

    # If all temperatures failed, return empty text
    return {"text": ""}

def run_server():
    uvicorn.run(app, host="0.0.0.0", port=4242)

if __name__ == "__main__":
    run_server()
