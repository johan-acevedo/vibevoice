#!/bin/bash

# Vibevoice Service Installation Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SERVICE_FILE="$PROJECT_DIR/systemd/vibevoice.service"
USER_SYSTEMD_DIR="$HOME/.config/systemd/user"
SERVICE_NAME="vibevoice.service"

echo "Installing Vibevoice autostart service..."

# Create systemd user directory if it doesn't exist
mkdir -p "$USER_SYSTEMD_DIR"

# Copy service file
cp "$SERVICE_FILE" "$USER_SYSTEMD_DIR/$SERVICE_NAME"
echo "✓ Service file installed to $USER_SYSTEMD_DIR/$SERVICE_NAME"

# Update the service file with the correct path
sed -i "s|%h/vibevoice|$PROJECT_DIR|g" "$USER_SYSTEMD_DIR/$SERVICE_NAME"
echo "✓ Service file updated with project path: $PROJECT_DIR"

# Reload systemd daemon
systemctl --user daemon-reload
echo "✓ Systemd daemon reloaded"

# Enable the service
systemctl --user enable "$SERVICE_NAME"
echo "✓ Service enabled for autostart"

echo ""
echo "Installation complete! You can now:"
echo "  Start service:    systemctl --user start vibevoice"
echo "  Stop service:     systemctl --user stop vibevoice"  
echo "  Service status:   systemctl --user status vibevoice"
echo "  View logs:        journalctl --user -u vibevoice -f"
echo ""
echo "The service will automatically start when you log in."
echo "To start it now, run: systemctl --user start vibevoice"