#!/bin/bash

# Vibevoice Autostart and Status Widget Removal Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "======================================"
echo "Vibevoice Autostart & Widget Removal"
echo "======================================"
echo

# Remove systemd service
echo "Removing systemd autostart service..."
"$SCRIPT_DIR/uninstall-service.sh"
echo

# Remove status widget autostart
echo "Removing status widget autostart..."
if [ -f "$HOME/.config/autostart/vibevoice-indicator.desktop" ]; then
    rm "$HOME/.config/autostart/vibevoice-indicator.desktop"
    echo "✓ Status widget autostart removed"
else
    echo "• Status widget autostart was not configured"
fi

# Remove desktop entries
echo "Removing desktop entries..."
if [ -f "$HOME/.local/share/applications/vibevoice.desktop" ]; then
    rm "$HOME/.local/share/applications/vibevoice.desktop"
    echo "✓ Desktop entry removed"
else
    echo "• Desktop entry was not installed"
fi

echo
echo "======================================"
echo "Removal Complete!"
echo "======================================"
echo
echo "Vibevoice autostart and status widget have been removed."
echo "The service files and widget code remain in the project directory."
echo "You can still start the service manually with:"
echo "  export PATH=\"\$HOME/.pyenv/bin:\$PATH\" && eval \"\$(pyenv init -)\" && python src/vibevoice/cli.py"
echo