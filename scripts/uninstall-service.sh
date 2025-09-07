#!/bin/bash

# Vibevoice Service Uninstallation Script

set -e

USER_SYSTEMD_DIR="$HOME/.config/systemd/user"
SERVICE_NAME="vibevoice.service"
SERVICE_PATH="$USER_SYSTEMD_DIR/$SERVICE_NAME"

echo "Uninstalling Vibevoice autostart service..."

# Stop the service if running
if systemctl --user is-active --quiet "$SERVICE_NAME"; then
    systemctl --user stop "$SERVICE_NAME"
    echo "✓ Service stopped"
fi

# Disable the service
if systemctl --user is-enabled --quiet "$SERVICE_NAME"; then
    systemctl --user disable "$SERVICE_NAME"
    echo "✓ Service disabled"
fi

# Remove service file
if [ -f "$SERVICE_PATH" ]; then
    rm "$SERVICE_PATH"
    echo "✓ Service file removed"
fi

# Reload systemd daemon
systemctl --user daemon-reload
echo "✓ Systemd daemon reloaded"

echo ""
echo "Uninstallation complete! The service will no longer start automatically."