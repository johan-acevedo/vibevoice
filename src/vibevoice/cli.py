"""Command-line interface for vibevoice"""

import os
import subprocess
import time
import json
import sounddevice as sd
import numpy as np
import requests
import sys
import base64

SCREENSHOT_AVAILABLE = False
try:
    import pyautogui
    from PIL import Image
    SCREENSHOT_AVAILABLE = True
except ImportError as e:
    print(f"Screenshot functionality not available: {e}")
    print("Install Pillow with: pip install Pillow")

from pynput.keyboard import Controller as KeyboardController, Key, Listener, KeyCode
from scipy.io import wavfile
from dotenv import load_dotenv

from loading_indicator import LoadingIndicator

loading_indicator = LoadingIndicator()

def load_custom_system_prompt():
    """Load custom system prompt from custom_prompt.md file."""
    custom_prompt_path = os.path.join(os.getcwd(), 'custom_prompt.md')
    try:
        if os.path.exists(custom_prompt_path):
            with open(custom_prompt_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    print(f"Loaded custom system prompt from {custom_prompt_path}")
                    return content
    except Exception as e:
        print(f"Error loading custom system prompt: {e}")
    
    # Fall back to default prompt
    default_prompt = """You are a voice-controlled AI assistant. The user is talking to their computer using voice commands.
Your responses will be directly typed into the user's keyboard at their cursor position, so:
1. Be concise and to the point, but friendly and engaging - prefer shorter answers
2. Focus on answering the specific question or request
3. Don't use introductory phrases like "Here's..." or "Based on the screenshot..."
4. Don't include formatting like bullet points, which might look strange when typed
5. Never apologize for limitations or explain what you're doing"""
    print("Using default system prompt (custom_prompt.md not found or empty)")
    return default_prompt

def start_whisper_server():
    server_script = os.path.join(os.path.dirname(__file__), 'server.py')
    process = subprocess.Popen(['python', server_script])
    return process

def wait_for_server(timeout=1800, interval=0.5):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get('http://localhost:4242/health')
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(interval)
    raise TimeoutError("Server failed to start within timeout")

def capture_screenshot():
    """Capture a screenshot, save it, and return the path and base64 data."""
    if not SCREENSHOT_AVAILABLE:
        print("Screenshot functionality not available. Install Pillow with: pip install Pillow")
        return None, None
        
    try:
        screenshot_path = os.path.abspath('screenshot.png')
        print(f"Capturing screenshot to: {screenshot_path}")
        
        screenshot = pyautogui.screenshot()
        
        max_width = int(os.getenv('SCREENSHOT_MAX_WIDTH', '1024'))
        width, height = screenshot.size
        
        if width > max_width:
            ratio = max_width / width
            new_width = max_width
            new_height = int(height * ratio)
            screenshot = screenshot.resize((new_width, new_height))
        
        screenshot.save(screenshot_path)
        
        with open(screenshot_path, "rb") as image_file:
            base64_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        return screenshot_path, base64_data
    except Exception as e:
        print(f"Error capturing screenshot: {e}")
        return None, None

def _process_llm_cmd(keyboard_controller, transcript):
    """Process transcript with Ollama and type the response."""

    try:
        loading_indicator.show(message=f"Processing: {transcript}")
        
        model = os.getenv('OLLAMA_MODEL', 'gemma3:27b')
        include_screenshot = os.getenv('INCLUDE_SCREENSHOT', 'true').lower() == 'true'
        
        screenshot_path, screenshot_base64 = (None, None)
        if include_screenshot and SCREENSHOT_AVAILABLE:
            screenshot_path, screenshot_base64 = capture_screenshot()
        
        user_prompt = transcript.strip()
        
        system_prompt = """You are a voice-controlled AI assistant. The user is talking to their computer using voice commands.
Your responses will be directly typed into the user's keyboard at their cursor position, so:
1. Be concise and to the point, but friendly and engaging - prefer shorter answers
2. Focus on answering the specific question or request
3. Don't use introductory phrases like "Here's..." or "Based on the screenshot..."
4. Don't include formatting like bullet points, which might look strange when typed
5. If you see a screenshot, analyze it and use it to inform your response
6. Never apologize for limitations or explain what you're doing"""
        
        if screenshot_base64:
            url = "http://localhost:11434/api/generate"
            payload = {
                "model": model,
                "prompt": user_prompt,
                "system": system_prompt,
                "stream": True,
                "images": [screenshot_base64]  # Pass base64 data directly without data URI prefix
            }
            print(f"Sending request with screenshot to model: {model}")
        else:
            url = "http://localhost:11434/api/generate"
            payload = {
                "model": model,
                "prompt": user_prompt,
                "system": system_prompt,
                "stream": True
            }
            print(f"Sending text-only request")
        
        response = requests.post(url, json=payload, stream=True)
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                data = line.decode('utf-8')
                if data.startswith('{'):
                    chunk = json.loads(data)
                    if 'response' in chunk:
                        chunk_text = chunk['response']
                        print(f"Debug - received chunk: {repr(chunk_text)}")
                        
                        # Replace smart/curly quotes with standard apostrophes
                        # U+2018 (') and U+2019 (') are both replaced with standard apostrophe (')
                        normalized_text = chunk_text.replace('\u2019', "'").replace('\u2018', "'")
                        
                        # Remove newlines to prevent unwanted line breaks when typing
                        normalized_text = normalized_text.replace('\n', ' ').replace('\r', ' ')
                        
                        keyboard_controller.type(normalized_text)
                        loading_indicator.hide()
        
        return "Successfully processed with Ollama"
    except requests.exceptions.RequestException as e:
        print(f"Error calling Ollama: {e}")
    finally:
        loading_indicator.hide()

def _transcribe_swedish(keyboard_controller, recording_path):
    """Transcribe audio to Swedish with software development context."""
    try:
        loading_indicator.show(message="Transcribing to Swedish...")

        # Get configurable parameters from environment
        swedish_language = os.getenv('SWEDISH_LANGUAGE', 'sv')
        swedish_prompt = os.getenv('SWEDISH_PROMPT',
            'Det här är en intervju om mjukvaruutveckling och SaaS med svenska termer. Å, Ä, Ö ska användas. Termer: API, databas, skalbarhet, deployment, commit, branch, merge, pull request, issue, sprint, backlog, scrum, kanban, devops, CI/CD, docker, kubernetes, microservices, serverless, cloud, azure, aws.')

        # Send transcription request with Swedish language and advanced decoding parameters
        response = requests.post('http://localhost:4242/transcribe/',
                              json={
                                  'file_path': recording_path,
                                  'language': swedish_language,
                                  'task': 'transcribe',
                                  'initial_prompt': swedish_prompt,
                                  'beam_size': 5,
                                  'best_of': 1,
                                  'temperature': 0,
                                  'vad_filter': True,
                                  'vad_parameters': { 'min_silence_duration_ms': 200, 'speech_pad_ms': 120 },
                                  'log_prob_threshold': -1.0
                              })
        response.raise_for_status()
        transcript = response.json()['text']

        if transcript:
            processed_transcript = transcript + " "
            print(f"Swedish: {processed_transcript}")
            keyboard_controller.type(processed_transcript)

        loading_indicator.hide()
        return "Successfully transcribed to Swedish"
    except requests.exceptions.RequestException as e:
        print(f"Error transcribing to Swedish: {e}")
    finally:
        loading_indicator.hide()

def _transcribe_english(keyboard_controller, recording_path):
    """Transcribe audio to English with software development context."""
    try:
        loading_indicator.show(message="Transcribing to English...")

        # Get configurable parameters from environment
        english_language = os.getenv('ENGLISH_LANGUAGE', 'en')
        english_prompt = os.getenv('ENGLISH_PROMPT',
            'This is a technical discussion about software development, SaaS, and startups. Technical terms include programming, APIs, databases, cloud services, scalability, deployment, commit, branch, merge, pull request, issue, sprint, backlog, scrum, kanban, devops, CI/CD, docker, kubernetes, microservices, serverless.')

        # Send transcription request with English language and advanced decoding parameters
        response = requests.post('http://localhost:4242/transcribe/',
                              json={
                                  'file_path': recording_path,
                                  'language': english_language,
                                  'task': 'transcribe',
                                  'initial_prompt': english_prompt,
                                  'beam_size': 5,
                                  'best_of': 1,
                                  'temperature': 0,
                                  'vad_filter': True,
                                  'vad_parameters': { 'min_silence_duration_ms': 200, 'speech_pad_ms': 120 },
                                  'log_prob_threshold': -1.0
                              })
        response.raise_for_status()
        transcript = response.json()['text']

        if transcript:
            processed_transcript = transcript + " "
            print(f"English: {processed_transcript}")
            keyboard_controller.type(processed_transcript)

        loading_indicator.hide()
        return "Successfully transcribed to English"
    except requests.exceptions.RequestException as e:
        print(f"Error transcribing to English: {e}")
    finally:
        loading_indicator.hide()

def main():
    load_dotenv()
    key_label = os.environ.get("VOICEKEY", "ctrl_r")
    cmd_label = os.environ.get("VOICEKEY_CMD", "scroll_lock")
    custom_label = os.environ.get("VOICEKEY_CUSTOM", "num_lock")
    RECORD_KEY = Key[key_label]
    CMD_KEY = Key[cmd_label]
    CUSTOM_KEY = Key[custom_label]
#    CMD_KEY = KeyCode(vk=65027)  # This is how you can use non-standard keys, this is AltGr for me

    # Load custom system prompt at startup
    custom_system_prompt = load_custom_system_prompt()

    recording = False
    audio_data = []
    sample_rate = 16000
    keyboard_controller = KeyboardController()

    def on_press(key):
        nonlocal recording, audio_data
        if (key == RECORD_KEY or key == CMD_KEY or key == CUSTOM_KEY) and not recording:
            recording = True
            audio_data = []
            print("Listening...")

    def on_release(key):
        nonlocal recording, audio_data
        if key == RECORD_KEY or key == CMD_KEY or key == CUSTOM_KEY:
            recording = False
            print("Transcribing...")
            
            try:
                audio_data_np = np.concatenate(audio_data, axis=0)
            except ValueError as e:
                print(e)
                return
            
            recording_path = os.path.abspath('recording.wav')
            audio_data_int16 = (audio_data_np * np.iinfo(np.int16).max).astype(np.int16)
            wavfile.write(recording_path, sample_rate, audio_data_int16)

            try:
                if key == RECORD_KEY:
                    # English transcription with software development context
                    _transcribe_english(keyboard_controller, recording_path)
                elif key == CMD_KEY:
                    # AI command mode (existing functionality)
                    response = requests.post('http://localhost:4242/transcribe/',
                                          json={'file_path': recording_path})
                    response.raise_for_status()
                    transcript = response.json()['text']
                    if transcript:
                        _process_llm_cmd(keyboard_controller, transcript)
                elif key == CUSTOM_KEY:
                    # Swedish transcription with software development context
                    _transcribe_swedish(keyboard_controller, recording_path)
            except requests.exceptions.RequestException as e:
                print(f"Error sending request to local API: {e}")
            except Exception as e:
                print(f"Error processing transcript: {e}")

    def callback(indata, frames, time, status):
        if status:
            print(status)
        if recording:
            audio_data.append(indata.copy())

    server_process = start_whisper_server()
    
    try:
        print(f"Waiting for the server to be ready...")
        wait_for_server()
        print(f"vibevoice is active.")
        print(f"  {key_label}: English transcription (software development context)")
        print(f"  {cmd_label}: AI command mode (with screenshot if enabled)")
        print(f"  {custom_label}: Swedish transcription (software development context)")
        with Listener(on_press=on_press, on_release=on_release) as listener:
            with sd.InputStream(callback=callback, channels=1, samplerate=sample_rate):
                listener.join()
    except TimeoutError as e:
        print(f"Error: {e}")
        server_process.terminate()
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        server_process.terminate()

if __name__ == "__main__":
    main()
