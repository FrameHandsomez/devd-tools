"""
System Tray UI - Background service indicator with menu
"""

import threading
from typing import Callable, Optional, TYPE_CHECKING
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem, Menu
from utils.logger import get_logger

if TYPE_CHECKING:
    from core.modes.mode_manager import ModeManager

logger = get_logger(__name__)


class SystemTrayUI:
    """
    System tray icon for the Macro Engine.
    
    Shows:
    - Current mode indicator
    - Menu with options: Show Status, Settings, Exit
    """
    
    def __init__(
        self,
        mode_manager: "ModeManager",
        on_exit: Callable,
        quick_panel = None,
        on_snippets: Callable = None
    ):
        self.mode_manager = mode_manager
        self.on_exit = on_exit
        self.quick_panel = quick_panel
        self.on_snippets = on_snippets
        self.icon: Optional[pystray.Icon] = None
        self._running = False
        
        # Set root for QuickPanel if passed
        if self.quick_panel:
            # We need to make sure QuickPanel is linked or we just manage its visibility
            pass

    def _on_toggle_quick_panel(self, icon, item):
        """Toggle Quick Panel visibility"""
        if self.quick_panel:
            self.quick_panel.toggle_visibility()
            # Refresh menu to update checkmark
            self.icon.menu = self._create_menu()
            
    def _on_launch_snippets(self, icon, item):
        """Launch Snippet Selector"""
        if self.on_snippets:
            self.on_snippets()
    
    def _create_icon_image(self, color: str = "#00FF00") -> Image.Image:
        """Create a simple icon image with the given color"""
        size = 64
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Draw a rounded square
        margin = 4
        draw.rounded_rectangle(
            [margin, margin, size - margin, size - margin],
            radius=8,
            fill=color
        )
        
        # Draw "M" for Macro
        draw.text(
            (size // 2 - 12, size // 2 - 15),
            "M",
            fill="white",
            font=None  # Uses default font
        )
        
        return image
    
    def _get_mode_color(self) -> str:
        """Get color based on current mode or custom setting"""
        # Check for custom color in settings
        settings = self.mode_manager.config_manager.get_settings()
        custom_color = settings.get("tray_icon_color")
        
        if custom_color and custom_color != "auto":
            return custom_color
        
        # Default mode-based colors
        mode_colors = {
            "DEV": "#4CAF50",    # Green
            "GIT": "#FF9800",    # Orange
            "AI": "#9C27B0",     # Purple
            "SCRIPT": "#2196F3"  # Blue
        }
        return mode_colors.get(self.mode_manager.current_mode, "#4CAF50")
    
    
    def _create_menu(self) -> Menu:
        """Create the system tray menu"""
        from utils.windows_utils import is_auto_start_enabled
        
        # Status of auto-start for checkbox
        is_autostart = is_auto_start_enabled()
        
        return Menu(
            MenuItem(
                f"Mode: {self.mode_manager.get_mode_name()}",
                lambda: None,
                enabled=False
            ),
            Menu.SEPARATOR,
            MenuItem(
                "Toggle Quick Panel",
                self._on_toggle_quick_panel,
                checked=lambda item: self.quick_panel.winfo_viewable() if self.quick_panel else False
            ),
            MenuItem(
                "Snippets...",
                self._on_launch_snippets
            ),
            MenuItem("Show Status", self._on_show_status),
            MenuItem("⚙️ Settings", self._on_show_settings),
            MenuItem(
                "Start on Boot", 
                self._on_toggle_auto_start,
                checked=lambda item: is_autostart
            ),
            MenuItem("Reload Config", self._on_reload_config),
            MenuItem("🔄 Check for Updates", self._on_check_updates),
            Menu.SEPARATOR,
            MenuItem("Exit", self._on_exit)
        )
    
    def _on_toggle_auto_start(self, icon, item):
        """Toggle auto-start setting"""
        from utils.windows_utils import enable_auto_start, disable_auto_start, is_auto_start_enabled
        
        current_state = is_auto_start_enabled()
        new_state = not current_state
        
        success = False
        if new_state:
            success = enable_auto_start()
            msg = "Application will now start on boot"
        else:
            success = disable_auto_start()
            msg = "Auto-start disabled"
            
        if success:
            # Update config file
            settings = self.mode_manager.config_manager.get_settings()
            settings["auto_start"] = new_state
            self.mode_manager.config_manager.save_settings(settings)
            
            # Show notification
            from ui.dialogs import show_notification
            show_notification(
                title="Settings Updated",
                message=msg,
                duration=2000
            )
            
            # Refresh menu
            self.icon.menu = self._create_menu()
    

    def _on_check_updates(self, icon=None, item=None):
        """Check for updates from GitHub (Thread-Safe via Subprocess)"""
        import threading
        
        def check():
            from utils.updater import get_updater
            from ui.dialogs import show_notification, ask_yes_no
            import subprocess
            import sys
            import json
            from pathlib import Path
            
            # Helper to run dialog commands safely from background thread
            def run_dialog_cmd(action, **kwargs):
                try:
                    data = json.dumps(kwargs)
                    is_frozen = getattr(sys, 'frozen', False)
                    
                    if is_frozen:
                        # Frozen: devd-tools.exe dialog <action> <json>
                        cmd = [sys.executable, "dialog", action, data]
                    else:
                        # Script: python ui/dialogs.py <action> <json>
                        dialog_script = Path(__file__).parent / "dialogs.py"
                        cmd = [sys.executable, str(dialog_script), action, data]
                        
                    creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                    result = subprocess.run(cmd, capture_output=True, text=True, creationflags=creation_flags)
                    
                    if result.returncode != 0:
                        logger.error(f"Dialog command failed: {result.stderr}")
                    return result
                except Exception as e:
                    logger.error(f"Failed to run dialog command: {e}")
                    return None

            # 1. Notify Checking
            run_dialog_cmd("show_notification", title="🔄 Checking...", message="Looking for updates...", duration=2000)
            
            try:
                updater = get_updater()
                has_update, message, ver = updater.check_for_updates()
            except Exception as e:
                logger.error(f"Update check exception: {e}")
                has_update, message, ver = False, f"Check failed: {e}", "0.0.0"
            
            if has_update:
                # 2. Ask to Update
                res = run_dialog_cmd("ask_yes_no", title="🔄 Update Available", message=f"{message}\n\nDownload and install now?")
                
                is_yes = False
                if res and res.stdout:
                    try:
                        output_json = json.loads(res.stdout.strip())
                        is_yes = output_json.get("result", False)
                    except Exception as json_err:
                        logger.error(f"JSON parse error: {json_err}, Output: {res.stdout}")

                if is_yes:
                    success, pull_msg = updater.apply_update()
                    if success:
                         run_dialog_cmd("show_notification", title="✅ Updated!", message="Please restart the application.", duration=5000)
                    else:
                         run_dialog_cmd("show_notification", title="❌ Update Failed", message=pull_msg, duration=5000)
            else:
                 run_dialog_cmd("show_notification", title="✅ Up to Date", message=f"{message}", duration=3000)
        
        threading.Thread(target=check, daemon=True).start()
    
    def _on_show_settings(self):
        """Show settings window in a separate process"""
        import subprocess
        import sys
        from pathlib import Path
        
        # Path to settings_dialog.py
        settings_script = Path(__file__).parent / "settings_dialog.py"
        
        try:
            is_frozen = getattr(sys, 'frozen', False)
            if is_frozen:
                # In frozen mode (PyInstaller), run the executable itself with 'settings' argument
                cmd = [sys.executable, "settings"]
            else:
                # In development mode, run the script directly
                cmd = [sys.executable, str(settings_script)]

            logger.info(f"SystemTray: Launching settings window {cmd}")
            subprocess.Popen(
                cmd,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        except Exception as e:
            logger.error(f"Error launching settings window: {e}")
    
    def _on_show_status(self):
        """Show current status"""
        from ui.dialogs import show_notification
        
        mode = self.mode_manager.get_mode_name()
        show_notification(
            title="Macro Engine Status",
            message=f"Mode: {mode}\nListening for key events...",
            duration=3000
        )
    
    def _on_reload_config(self):
        """Reload configuration and update all components"""
        try:
            # Reload config file
            self.mode_manager.config_manager.load()
            
            # Update mode manager with new modes
            new_modes = list(self.mode_manager.config_manager.get_modes().keys())
            self.mode_manager.modes = new_modes
            
            # Update event router settings
            from runtime.bootstrap import _engine
            if _engine and _engine.event_router:
                settings = self.mode_manager.config_manager.get_settings()
                _engine.event_router.long_press_ms = settings.get("long_press_ms", 800)
                _engine.event_router.multi_press_window_ms = settings.get("multi_press_window_ms", 500)
                _engine.event_router.multi_press_count = settings.get("multi_press_count", 3)
            
            # Update tray icon
            self.update_icon()
            
            from ui.dialogs import show_notification
            show_notification(
                title="✅ Config Reloaded",
                message="All settings have been updated",
                duration=2000
            )
            
            logger.info("Configuration hot-reloaded successfully")
            
        except Exception as e:
            logger.error(f"Error reloading config: {e}")
            from ui.dialogs import show_notification
            show_notification(
                title="❌ Reload Failed",
                message=str(e)[:100],
                duration=3000
            )
    
    def _on_exit(self):
        """Handle exit menu item"""
        logger.info("Exit requested from tray menu")
        self.stop()
        if self.on_exit:
            self.on_exit()
    
    def run(self):
        """Run the system tray icon (blocking)"""
        self._running = True
        
        try:
            self.icon = pystray.Icon(
                name="MacroEngine",
                icon=self._create_icon_image(self._get_mode_color()),
                title=f"Macro Engine - {self.mode_manager.get_mode_name()}",
                menu=self._create_menu()
            )
            
            logger.info("System tray icon started")
            self.icon.run()
            
        except Exception as e:
            logger.error(f"Error running system tray: {e}")
            raise
    
    def stop(self):
        """Stop the system tray icon"""
        self._running = False
        if self.icon:
            self.icon.stop()
            logger.info("System tray icon stopped")
    
    def update_icon(self):
        """Update the icon to reflect current mode"""
        if self.icon:
            self.icon.icon = self._create_icon_image(self._get_mode_color())
            self.icon.title = f"Macro Engine - {self.mode_manager.get_mode_name()}"
            self.icon.menu = self._create_menu()

