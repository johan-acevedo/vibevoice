# Vibevoice 🎙️

Hi, I'm [Marc Päpper](https://x.com/mpaepper) and I wanted to vibe code like [Karpathy](https://x.com/karpathy/status/1886192184808149383) ;D, so I looked around and found the cool work of [Vlad](https://github.com/vlad-ds/whisper-keyboard). I extended it to run with a local whisper model, so I don't need to pay for OpenAI tokens.
I hope you have fun with it!

## What it does 🚀

![Demo Video](docs/vibevoice-demo-caption.gif)

Simply run `cli.py` and start dictating text anywhere in your system:
1. Hold down right control key (Ctrl_r)
2. Speak your text
3. Release the key
4. Watch as your spoken words are transcribed and automatically typed!

Works in any application or window - your text editor, browser, chat apps, anywhere you can type!

NEW: Enhanced LLM voice modes:

**AI Command Mode:**
1. Hold down the scroll_lock key (I think it's normally not used anymore that's why I chose it)
2. Speak what you want the LLM to do
3. The LLM receives your transcribed text and a screenshot of your current view
4. The LLM answer is typed into your keyboard (streamed)

**Custom AI Prompt Mode (NEW!):**
1. Hold down the Num Lock key
2. Speak your text in any language
3. Uses your custom system prompt from `custom_prompt.md` for specialized processing
4. Perfect for technical transcription, translation, and grammar improvement

Works everywhere on your system with full context awareness

## Installation 🛠️

### Quick Start
```bash
git clone https://github.com/mpaepper/vibevoice.git
cd vibevoice
pip install -r requirements.txt
python src/vibevoice/cli.py
```

### Autostart Setup (Recommended)
For automatic startup and system tray integration:
```bash
# Install autostart service and status widget
./scripts/setup-autostart.sh

# Start everything now (or it will start automatically on next login)
systemctl --user start vibevoice
python3 src/vibevoice/status_widget.py &
```

The project includes several configuration files:
- `custom_prompt.md` - Custom system prompt for specialized AI processing
- `CLAUDE.md` - Detailed setup and configuration guide
- `start_no_screenshot.sh` - Utility script to start without screenshots

## Requirements 📋

### Python Dependencies
- Python 3.13 or higher

### System Requirements
- CUDA-capable GPU (recommended) -> in server.py you can enable cpu use
- CUDA 12.x
- cuBLAS
- cuDNN 9.x
- In case you get this error: `OSError: PortAudio library not found` run `sudo apt install libportaudio2`
- [Ollama](https://ollama.com) for AI command mode (with multimodal models for screenshot support)

### GUI Dependencies (for status widget)
- GTK3: `sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0`
- System tray support (recommended): `sudo apt install gir1.2-ayatanaappindicator3-0.1`
- Legacy system tray (fallback): `sudo apt install gir1.2-appindicator3-0.1`

### System Integration (Linux)
- systemd (for autostart service)
- Desktop environment with system tray/notification area

#### Setting up Ollama
1. Install Ollama by following the instructions at [ollama.com](https://ollama.com)
2. Pull a model that supports both text and images for best results:
   ```bash
   ollama pull gemma3:27b  # Great model which can run on RTX 3090 or similar
   ```
3. Make sure Ollama is running in the background:
   ```bash
   ollama serve
   ```

#### Handling the CUDA requirements

* Make sure that you have CUDA >= 12.4 and cuDNN >= 9.x
* I had some trouble at first with Ubuntu 24.04, so I did the following:

```bash
sudo apt update && sudo apt upgrade
sudo apt autoremove nvidia* --purge
ubuntu-drivers devices
sudo ubuntu-drivers autoinstall
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb && sudo apt update
sudo apt install cuda-toolkit-12-8
```
or alternatively:

``` 
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt update
sudo apt install cudnn9-cuda-12
```

* Then after rebooting, it worked well.

## Usage 💡

1. Start the application:
```bash
python src/vibevoice/cli.py
```

2. Hold down right control key (Ctrl_r) while speaking
3. Release to transcribe
4. Your text appears wherever your cursor is!

### Configuration

You can customize various aspects of VibeVoice with the following environment variables:

#### Keyboard Controls
- `VOICEKEY`: Change the dictation activation key (default: "ctrl_r")
  ```bash
  export VOICEKEY="ctrl"  # Use left control instead
  ```
- `VOICEKEY_CMD`: Set the key for AI command mode (default: "scroll_lock")
  ```bash
  export VOICEKEY_CMD="ctsl"  # Use left control instead of Scroll Lock key
  ```
- `VOICEKEY_CUSTOM`: Set the key for custom AI prompt mode (default: "num_lock")
  ```bash
  export VOICEKEY_CUSTOM="pause"  # Use Pause key instead of Num Lock
  ```

#### AI and Screenshot Features
- `OLLAMA_MODEL`: Specify which Ollama model to use (default: "gemma3:27b")
  ```bash
  export OLLAMA_MODEL="gemma3:4b"  # Use a smaller VLM in case you have less GPU RAM
  ```
- `INCLUDE_SCREENSHOT`: Enable or disable screenshots in AI command mode (default: "true")
  ```bash
  export INCLUDE_SCREENSHOT="false"  # Disable screenshots (but they are local only anyways)
  ```
- `SCREENSHOT_MAX_WIDTH`: Set the maximum width for screenshots (default: "1024")
  ```bash
  export SCREENSHOT_MAX_WIDTH="800"  # Smaller screenshots
  ```

#### Screenshot Dependencies
To use the screenshot functionality:
```bash
sudo apt install gnome-screenshot
```

## Custom System Prompts 🎯

VibeVoice supports custom system prompts for specialized AI processing through the `custom_prompt.md` file.

### Setting Up Custom Prompts

1. Create a `custom_prompt.md` file in the project root directory
2. Write your custom system prompt in this file
3. The prompt will be loaded when the service starts
4. Use the custom key (default: Num Lock) to activate custom prompt mode

### Features

The default custom prompt is configured as a **technical transcription assistant** that:

- **Cleans transcription errors**: Fixes technical terms like "post gray sequel" → "PostgreSQL"
- **Removes fillers**: Eliminates "um", "uh", stutters, and repetitions
- **Translates languages**: Converts any non-English speech to English
- **Improves grammar**: Enhances clarity while preserving original meaning
- **Handles technical jargon**: Accurately interprets coding terms, function names, and APIs
- **Single-line output**: Prevents unwanted line breaks when typing into editors

### Example Custom Prompt Usage

**Input (Swedish):** "Jag vill um konfigurera post gray sequel databasen med redis caching"

**Output:** "I want to configure the PostgreSQL database with Redis caching"

### Customization

Replace the contents of `custom_prompt.md` with your own system prompt for different behaviors:
- Code review assistant
- Writing improvement tool  
- Domain-specific terminology processor
- Language-specific translator

## Usage Modes 💡

VibeVoice supports three modes:

### 1. Dictation Mode
1. Hold down the dictation key (default: right Control)
2. Speak your text
3. Release to transcribe
4. Your text appears wherever your cursor is!

### 2. AI Command Mode
1. Hold down the command key (default: Scroll Lock)
2. Ask a question or give a command
3. Release the key
4. The AI will analyze your request (and current screen if enabled) and type a response

### 3. Custom AI Prompt Mode
1. Hold down the custom key (default: Num Lock)
2. Speak your text in any language
3. Release the key
4. The AI processes your speech using your custom system prompt from `custom_prompt.md`
5. Perfect for technical transcription, translation, grammar improvement, and specialized text processing

## Autostart & Status Widget 🔧

VibeVoice includes systemd service integration and a desktop status widget for seamless system integration:

### Features
- **Automatic startup** when you log in
- **System tray indicator** showing service status
- **Easy service control** via right-click menu or command line
- **Service monitoring** with status updates every 5 seconds
- **Desktop notifications** for service state changes

### Setup
```bash
# Install autostart and status widget
./scripts/setup-autostart.sh

# Manual service control
systemctl --user start vibevoice     # Start service
systemctl --user stop vibevoice      # Stop service
systemctl --user status vibevoice    # Check status
journalctl --user -u vibevoice -f    # View logs

# Launch status widget manually
python3 src/vibevoice/status_widget.py &
```

### Status Widget
The status widget provides:
- **Visual status indicator** (microphone icon in system tray)
- **Service controls** (Start/Stop/Restart via right-click menu)
- **Service information** (uptime, model, key bindings)
- **Log access** (opens terminal with live log viewing)
- **Fallback mode** (window interface if system tray unavailable)

### Removal
```bash
# Remove autostart and status widget
./scripts/remove-autostart.sh
```

## Credits 🙏

- Original inspiration: [whisper-keyboard](https://github.com/vlad-ds/whisper-keyboard) by Vlad
- [Faster Whisper](https://github.com/guillaumekln/faster-whisper) for the optimized Whisper implementation
- Built by [Marc Päpper](https://www.paepper.com)
