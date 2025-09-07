#!/bin/bash

# Vibevoice Autostart and Status Widget Setup Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "======================================"
echo "Vibevoice Autostart & Widget Setup"
echo "======================================"
echo

# Check system requirements
echo "Checking system requirements..."

# Check for systemd
if ! command -v systemctl &> /dev/null; then
    echo "❌ Error: systemctl not found. This script requires systemd."
    exit 1
fi

# Check for GUI environment
if [ -z "$DISPLAY" ]; then
    echo "❌ Error: No GUI display found. Please run this from a desktop session."
    exit 1
fi

# Check for Python and pyenv
if [ ! -d "$HOME/.pyenv" ]; then
    echo "❌ Error: pyenv not found at ~/.pyenv. Please ensure pyenv is installed."
    exit 1
fi

echo "✓ System requirements met"
echo

# Install systemd service
echo "Installing systemd autostart service..."
"$SCRIPT_DIR/install-service.sh"
echo

# Check for GTK dependencies
echo "Checking GTK dependencies..."
python3 -c "
import sys
try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
    print('✓ Basic GTK3 available')
    
    # Check for AppIndicator3 (optional) - try modern Ayatana first
    appindicator_available = False
    try:
        gi.require_version('AyatanaAppIndicator3', '0.1')
        from gi.repository import AyatanaAppIndicator3
        print('✓ Ayatana AppIndicator3 available (modern system tray support)')
        appindicator_available = True
    except:
        try:
            gi.require_version('AppIndicator3', '0.1')
            from gi.repository import AppIndicator3
            print('✓ Legacy AppIndicator3 available (system tray support)')
            appindicator_available = True
        except:
            pass
    
    if not appindicator_available:
        print('ℹ  No AppIndicator available (will use window mode)')
        print('   For system tray support: sudo apt install gir1.2-ayatanaappindicator3-0.1')
        print('   Or for legacy systems: sudo apt install gir1.2-appindicator3-0.1')
        
except ImportError as e:
    print(f'❌ Missing required GTK dependency: {e}')
    print('Please install required packages:')
    print('  sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0')
    sys.exit(1)
except Exception as e:
    print(f'❌ GTK check failed: {e}')
    sys.exit(1)
"

# Setup status widget autostart
echo
echo "Setting up status widget autostart..."

# Create autostart directory
mkdir -p "$HOME/.config/autostart"

# Copy desktop file and update paths
cp "$PROJECT_DIR/assets/vibevoice-indicator.desktop" "$HOME/.config/autostart/"
sed -i "s|%h/vibevoice|$PROJECT_DIR|g" "$HOME/.config/autostart/vibevoice-indicator.desktop"
echo "✓ Status widget autostart configured"

# Make desktop files available
echo "Installing desktop entries..."
mkdir -p "$HOME/.local/share/applications"
cp "$PROJECT_DIR/assets/vibevoice.desktop" "$HOME/.local/share/applications/"
sed -i "s|%h/vibevoice|$PROJECT_DIR|g" "$HOME/.local/share/applications/vibevoice.desktop"
echo "✓ Desktop entries installed"

# Test the widget
echo
echo "Testing status widget..."
timeout 5s python3 "$PROJECT_DIR/src/vibevoice/status_widget.py" --test 2>/dev/null || {
    echo "❌ Status widget test failed. Please check GTK dependencies."
    exit 1
}
echo "✓ Status widget test successful"

echo
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo
echo "The following has been configured:"
echo "• Vibevoice service will start automatically when you log in"
echo "• Status widget will appear in your system tray/panel"
echo "• Desktop entries are available in applications menu"
echo
echo "Available commands:"
echo "• Start service:       systemctl --user start vibevoice"
echo "• Stop service:        systemctl --user stop vibevoice"
echo "• Service status:      systemctl --user status vibevoice"
echo "• View logs:          journalctl --user -u vibevoice -f"
echo "• Start widget:       python3 src/vibevoice/status_widget.py"
echo
echo "To start everything now:"
echo "1. Start the service:   systemctl --user start vibevoice"
echo "2. Start the widget:    python3 src/vibevoice/status_widget.py &"
echo
echo "Or simply log out and log back in for everything to start automatically!"
echo