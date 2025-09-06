#!/bin/bash

# Start Vibevoice with 12b quantized model and no screenshot
export OLLAMA_MODEL="gemma3:12b-it-qat"
export INCLUDE_SCREENSHOT="false"
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init -)"

python src/vibevoice/cli.py