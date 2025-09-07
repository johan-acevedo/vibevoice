# Claude Code Setup Guide for Vibevoice

## Quick Start

To run the vibevoice service:

```bash
export PATH="$HOME/.pyenv/bin:$PATH" && eval "$(pyenv init -)" && python src/vibevoice/cli.py
```

## Environment Setup

### Python Environment
- **Python Version**: 3.13.0 (managed by pyenv)
- **Location**: `~/.pyenv/versions/3.13.0/`
- **Activation**: Run `export PATH="$HOME/.pyenv/bin:$PATH" && eval "$(pyenv init -)"` before any Python commands

### Dependencies
All dependencies are installed and up-to-date in the pyenv environment. If you need to reinstall:

```bash
export PATH="$HOME/.pyenv/bin:$PATH" && eval "$(pyenv init -)" && pip install -r requirements.txt
```

## System Requirements Status

✅ **Python 3.13.0** - Available via pyenv  
✅ **CUDA 12.x** - Driver Version: 575.64.03, CUDA Version: 12.9  
✅ **GPU** - NVIDIA GeForce RTX 4070 (16GB VRAM)  
✅ **Ollama** - Running with gemma3:12b-it-qat model  
✅ **gnome-screenshot** - Available at `/usr/bin/gnome-screenshot`  
✅ **All Python dependencies** - Installed and working  

## Usage

### Dictation Mode
1. Hold down right Control key (Ctrl_r)
2. Speak your text
3. Release the key
4. Text appears where cursor is located

### AI Command Mode  
1. Hold down Scroll Lock key
2. Speak your command/question
3. Release the key
4. AI analyzes request + screenshot and types response

### Custom AI Prompt Mode
1. Hold down Num Lock key
2. Speak your command/question
3. Release the key
4. AI processes request with your custom system prompt (text-only, no screenshot)

## Service Details

- **Server runs on**: http://localhost:4242
- **Health check**: The service automatically starts a health check endpoint
- **GPU Memory**: Currently using ~894MB/16GB (plenty of headroom)

## Configuration Options

Environment variables you can set:
- `VOICEKEY`: Change dictation key (default: "ctrl_r")
- `VOICEKEY_CMD`: Change AI command key (default: "scroll_lock") 
- `VOICEKEY_CUSTOM`: Change custom AI prompt key (default: "num_lock")
- `OLLAMA_MODEL`: Change Ollama model (default: "gemma3:27b", currently using "gemma3:12b-it-qat")
- `INCLUDE_SCREENSHOT`: Enable/disable screenshots (default: "true")
- `SCREENSHOT_MAX_WIDTH`: Screenshot width (default: "1024")

### Custom System Prompt

To use custom AI prompts:
1. Create a file named `custom_prompt.md` in the project root directory
2. Write your custom system prompt in this file
3. The prompt will be loaded when the service starts
4. Use the Num Lock key to trigger custom prompt mode

If `custom_prompt.md` doesn't exist or is empty, the system will fall back to a default prompt similar to the regular AI mode but without screenshot functionality.

## Autostart & Status Widget

The vibevoice service can be configured to start automatically and show a desktop status widget:

### Installation
```bash
./scripts/setup-autostart.sh
```

### System Tray Support
For system tray indicator (recommended):
```bash
sudo apt install gir1.2-ayatanaappindicator3-0.1
```

Or for legacy systems:
```bash
sudo apt install gir1.2-appindicator3-0.1
```

### Manual Control
```bash
# Service control
systemctl --user start vibevoice
systemctl --user stop vibevoice
systemctl --user status vibevoice
journalctl --user -u vibevoice -f

# Status widget
python3 src/vibevoice/status_widget.py &
```

### Removal
```bash
./scripts/remove-autostart.sh
```

## Troubleshooting

### If pyenv isn't working:
```bash
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
```

### If Ollama isn't responding:
```bash
ollama serve
```

### Check GPU memory:
```bash
nvidia-smi
```

### Verify Ollama models:
```bash
ollama list
```

## Testing Commands

```bash
# Test Python environment
export PATH="$HOME/.pyenv/bin:$PATH" && eval "$(pyenv init -)" && python --version

# Test Ollama
curl -s http://localhost:11434/api/tags

# Test service (will start server)
export PATH="$HOME/.pyenv/bin:$PATH" && eval "$(pyenv init -)" && python src/vibevoice/cli.py
```