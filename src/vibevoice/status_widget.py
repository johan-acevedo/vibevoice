#!/usr/bin/env python3
"""GTK status widget/indicator for vibevoice service"""

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GObject, GLib

# Try to import AyatanaAppIndicator3 (modern) or AppIndicator3 (legacy), fallback to basic GTK window if not available
HAS_APPINDICATOR = False
AppIndicator3 = None

# Try modern Ayatana AppIndicator first
try:
    gi.require_version('AyatanaAppIndicator3', '0.1')
    from gi.repository import AyatanaAppIndicator3 as AppIndicator3
    HAS_APPINDICATOR = True
    print("Using Ayatana AppIndicator3 (modern)")
except (ImportError, ValueError):
    # Fallback to legacy AppIndicator3
    try:
        gi.require_version('AppIndicator3', '0.1')
        from gi.repository import AppIndicator3
        HAS_APPINDICATOR = True
        print("Using legacy AppIndicator3")
    except (ImportError, ValueError):
        HAS_APPINDICATOR = False
        print("Warning: No AppIndicator available. Using basic GTK window instead.")
        print("For system tray support, install: sudo apt install gir1.2-ayatanaappindicator3-0.1")
        print("Or for legacy systems: sudo apt install gir1.2-appindicator3-0.1")
import subprocess
import requests
import json
import os
import sys
import threading
import time

class VibevoiceIndicator:
    def __init__(self):
        if HAS_APPINDICATOR:
            self.indicator = AppIndicator3.Indicator.new(
                "vibevoice-indicator",
                "audio-input-microphone-symbolic",  # Default icon
                AppIndicator3.IndicatorCategory.APPLICATION_STATUS
            )
            
            # Set initial status
            self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
            self.indicator.set_title("Vibevoice Status")
            self.use_window = False
        else:
            # Fallback to GTK window
            self.window = Gtk.Window()
            self.window.set_title("Vibevoice Status")
            self.window.set_default_size(300, 200)
            self.window.set_position(Gtk.WindowPosition.CENTER)
            self.window.connect("delete-event", self.on_window_delete)
            self.use_window = True
        
        # Create menu/content
        self.create_menu()
        
        # Start status monitoring
        self.start_monitoring()
        
    def create_menu(self):
        """Create the right-click context menu"""
        menu = Gtk.Menu()
        
        # Status item (non-clickable)
        self.status_item = Gtk.MenuItem(label="Status: Checking...")
        self.status_item.set_sensitive(False)
        menu.append(self.status_item)
        
        # Separator
        separator = Gtk.SeparatorMenuItem()
        menu.append(separator)
        
        # Service controls
        self.start_item = Gtk.MenuItem(label="Start Service")
        self.start_item.connect('activate', self.start_service)
        menu.append(self.start_item)
        
        self.stop_item = Gtk.MenuItem(label="Stop Service")
        self.stop_item.connect('activate', self.stop_service)
        menu.append(self.stop_item)
        
        self.restart_item = Gtk.MenuItem(label="Restart Service")
        self.restart_item.connect('activate', self.restart_service)
        menu.append(self.restart_item)
        
        # Separator
        separator2 = Gtk.SeparatorMenuItem()
        menu.append(separator2)
        
        # Info and logs
        self.info_item = Gtk.MenuItem(label="Service Info")
        self.info_item.connect('activate', self.show_info)
        menu.append(self.info_item)
        
        self.logs_item = Gtk.MenuItem(label="View Logs")
        self.logs_item.connect('activate', self.view_logs)
        menu.append(self.logs_item)
        
        # Separator
        separator3 = Gtk.SeparatorMenuItem()
        menu.append(separator3)
        
        # About
        about_item = Gtk.MenuItem(label="About")
        about_item.connect('activate', self.show_about)
        menu.append(about_item)
        
        # Quit
        quit_item = Gtk.MenuItem(label="Quit Indicator")
        quit_item.connect('activate', self.quit)
        menu.append(quit_item)
        
        menu.show_all()
        
        if self.use_window:
            # For window mode, create a simple interface
            vbox = Gtk.VBox(spacing=10)
            vbox.set_margin_left(10)
            vbox.set_margin_right(10)
            vbox.set_margin_top(10)
            vbox.set_margin_bottom(10)
            
            # Status label
            self.status_label = Gtk.Label("Status: Checking...")
            vbox.pack_start(self.status_label, False, False, 0)
            
            # Buttons
            button_box = Gtk.HBox(spacing=5)
            
            start_btn = Gtk.Button.new_with_label("Start")
            start_btn.connect('clicked', self.start_service)
            button_box.pack_start(start_btn, True, True, 0)
            
            stop_btn = Gtk.Button.new_with_label("Stop") 
            stop_btn.connect('clicked', self.stop_service)
            button_box.pack_start(stop_btn, True, True, 0)
            
            restart_btn = Gtk.Button.new_with_label("Restart")
            restart_btn.connect('clicked', self.restart_service)
            button_box.pack_start(restart_btn, True, True, 0)
            
            vbox.pack_start(button_box, False, False, 0)
            
            # Info button
            info_btn = Gtk.Button.new_with_label("Service Info")
            info_btn.connect('clicked', self.show_info)
            vbox.pack_start(info_btn, False, False, 0)
            
            self.window.add(vbox)
            self.window.show_all()
        else:
            self.indicator.set_menu(menu)
        
    def start_monitoring(self):
        """Start background monitoring of service status"""
        def monitor_loop():
            while True:
                GLib.idle_add(self.update_status)
                time.sleep(5)  # Check every 5 seconds
                
        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()
        
    def update_status(self):
        """Update indicator status and menu based on service state"""
        try:
            # Check if systemd service is running
            result = subprocess.run(['systemctl', '--user', 'is-active', 'vibevoice'], 
                                  capture_output=True, text=True)
            systemd_active = result.stdout.strip() == 'active'
            
            # Check if HTTP server is responding
            http_active = False
            service_info = {}
            try:
                response = requests.get('http://localhost:4242/health', timeout=2)
                if response.status_code == 200:
                    http_active = True
                    # Try to get additional service info
                    try:
                        info_response = requests.get('http://localhost:4242/status', timeout=1)
                        if info_response.status_code == 200:
                            service_info = info_response.json()
                    except:
                        pass
            except requests.RequestException:
                pass
            
            # Update status based on both checks
            if systemd_active and http_active:
                status_text = "Status: Running"
                if service_info:
                    keys_info = f" ({service_info.get('keys', {}).get('dictation', 'ctrl_r')}, {service_info.get('keys', {}).get('command', 'scroll_lock')}, {service_info.get('keys', {}).get('custom', 'num_lock')})"
                    status_text += keys_info
                if not self.use_window:
                    self.indicator.set_icon_full("audio-input-microphone", "Vibevoice Active")
                    self.start_item.set_sensitive(False)
                    self.stop_item.set_sensitive(True)
                    self.restart_item.set_sensitive(True)
            elif systemd_active and not http_active:
                status_text = "Status: Starting..."
                if not self.use_window:
                    self.indicator.set_icon_full("audio-input-microphone-muted", "Vibevoice Starting")
                    self.start_item.set_sensitive(False)
                    self.stop_item.set_sensitive(True)
                    self.restart_item.set_sensitive(True)
            else:
                status_text = "Status: Stopped"
                if not self.use_window:
                    self.indicator.set_icon_full("audio-input-microphone-muted", "Vibevoice Stopped")
                    self.start_item.set_sensitive(True)
                    self.stop_item.set_sensitive(False)
                    self.restart_item.set_sensitive(False)
                
            if self.use_window:
                self.status_label.set_text(status_text)
            else:
                self.status_item.set_label(status_text)
            
        except Exception as e:
            print(f"Error updating status: {e}")
            error_text = "Status: Error"
            if self.use_window:
                self.status_label.set_text(error_text)
            else:
                self.status_item.set_label(error_text)
                self.indicator.set_icon_full("dialog-error", "Vibevoice Error")
            
        return False  # Don't repeat this GLib.idle_add call
        
    def start_service(self, widget):
        """Start the vibevoice service"""
        try:
            subprocess.run(['systemctl', '--user', 'start', 'vibevoice'], check=True)
            self.show_notification("Starting Vibevoice service...")
        except subprocess.CalledProcessError as e:
            self.show_error_dialog(f"Failed to start service: {e}")
            
    def stop_service(self, widget):
        """Stop the vibevoice service"""
        try:
            subprocess.run(['systemctl', '--user', 'stop', 'vibevoice'], check=True)
            self.show_notification("Stopping Vibevoice service...")
        except subprocess.CalledProcessError as e:
            self.show_error_dialog(f"Failed to stop service: {e}")
            
    def restart_service(self, widget):
        """Restart the vibevoice service"""
        try:
            subprocess.run(['systemctl', '--user', 'restart', 'vibevoice'], check=True)
            self.show_notification("Restarting Vibevoice service...")
        except subprocess.CalledProcessError as e:
            self.show_error_dialog(f"Failed to restart service: {e}")
            
    def show_info(self, widget):
        """Show service information dialog"""
        try:
            # Get systemctl status
            result = subprocess.run(['systemctl', '--user', 'status', 'vibevoice'], 
                                  capture_output=True, text=True)
            
            # Try to get service info from HTTP
            service_info = {}
            try:
                response = requests.get('http://localhost:4242/status', timeout=2)
                if response.status_code == 200:
                    service_info = response.json()
            except:
                pass
            
            info_text = "Vibevoice Service Information\n\n"
            info_text += f"Systemd Status:\n{result.stdout}\n"
            
            if service_info:
                info_text += "\nService Details:\n"
                info_text += f"Uptime: {service_info.get('uptime', 'Unknown')}\n"
                info_text += f"Model: {service_info.get('model', 'Unknown')}\n"
                keys = service_info.get('keys', {})
                info_text += f"Dictation Key: {keys.get('dictation', 'ctrl_r')}\n"
                info_text += f"Command Key: {keys.get('command', 'scroll_lock')}\n"
                info_text += f"Custom Key: {keys.get('custom', 'num_lock')}\n"
            
            self.show_info_dialog("Service Information", info_text)
            
        except Exception as e:
            self.show_error_dialog(f"Failed to get service info: {e}")
            
    def view_logs(self, widget):
        """Open logs in terminal"""
        try:
            # Try different terminal emulators
            terminals = ['gnome-terminal', 'xterm', 'konsole', 'xfce4-terminal']
            for terminal in terminals:
                if subprocess.run(['which', terminal], capture_output=True).returncode == 0:
                    subprocess.Popen([terminal, '--', 'journalctl', '--user', '-u', 'vibevoice', '-f'])
                    break
            else:
                self.show_error_dialog("No terminal emulator found. Please run:\njournalctl --user -u vibevoice -f")
        except Exception as e:
            self.show_error_dialog(f"Failed to open logs: {e}")
            
    def show_about(self, widget):
        """Show about dialog"""
        about_text = """Vibevoice Status Indicator

A voice-controlled AI assistant service with:
• Voice dictation (Ctrl+R)
• AI commands with screenshot (Scroll Lock)  
• Custom AI prompts (Num Lock)

This indicator shows service status and provides
easy access to service controls."""
        
        self.show_info_dialog("About Vibevoice", about_text)
        
    def show_notification(self, message):
        """Show desktop notification"""
        try:
            subprocess.run(['notify-send', 'Vibevoice', message])
        except:
            pass  # Notifications not critical
            
    def show_info_dialog(self, title, message):
        """Show information dialog"""
        dialog = Gtk.MessageDialog(
            transient_for=None,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
        
    def show_error_dialog(self, message):
        """Show error dialog"""
        dialog = Gtk.MessageDialog(
            transient_for=None,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Error"
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
        
    def on_window_delete(self, widget, event):
        """Handle window close event"""
        Gtk.main_quit()
        return False
        
    def quit(self, widget):
        """Quit the indicator application"""
        Gtk.main_quit()

def main():
    """Main entry point"""
    # Check if we're in a GUI environment
    if not os.environ.get('DISPLAY'):
        print("Error: No display found. This application requires a GUI environment.")
        sys.exit(1)
        
    # Check for basic GTK (AppIndicator3 is optional)
    try:
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk
    except (ImportError, ValueError) as e:
        print(f"Error: GTK3 not available: {e}")
        print("Please install: sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0")
        sys.exit(1)
    
    # Create and run indicator
    indicator = VibevoiceIndicator()
    
    # Update status immediately
    GLib.idle_add(indicator.update_status)
    
    print("Vibevoice status indicator started")
    
    try:
        Gtk.main()
    except KeyboardInterrupt:
        print("\nShutting down indicator...")
        Gtk.main_quit()

if __name__ == "__main__":
    main()