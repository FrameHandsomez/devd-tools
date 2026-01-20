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
        on_exit: Callable
    ):
        self.mode_manager = mode_manager
        self.on_exit = on_exit
        self.icon: Optional[pystray.Icon] = None
        self._running = False
    
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
        """Get color based on current mode"""
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
            MenuItem("Show Status", self._on_show_status),
            MenuItem(
                "Start on Boot", 
                self._on_toggle_auto_start,
                checked=lambda item: is_autostart
            ),
            MenuItem("Reload Config", self._on_reload_config),
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
        """Reload configuration"""
        try:
            self.mode_manager.config_manager.load()
            from ui.dialogs import show_notification
            show_notification(
                title="Config Reloaded",
                message="Configuration has been reloaded",
                duration=2000
            )
        except Exception as e:
            logger.error(f"Error reloading config: {e}")
    
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

