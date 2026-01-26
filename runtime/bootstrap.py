"""
Bootstrap Layer - Initialize and start all components
main.py only calls start() from here
"""

import sys
import threading
import signal
import os
from pathlib import Path

# Windows specific for single instance check
if sys.platform == 'win32':
    import ctypes
    from ctypes import wintypes

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import setup_logger, get_logger
from core.config.config_manager import ConfigManager
from core.modes.mode_manager import ModeManager
from core.events.event_router import EventRouter
from core.commands.command_executor import CommandExecutor
from core.features.feature_registry import FeatureRegistry
from inputs.keyboard_provider import KeyboardInputProvider
from ui.system_tray import SystemTrayUI

logger = get_logger(__name__)

from utils.windows_utils import enable_auto_start, disable_auto_start, is_auto_start_enabled


class MacroEngine:
    """Main application class that orchestrates all components"""
    
    def __init__(self):
        self.running = False
        self.config_manager = None
        self.mode_manager = None
        self.event_router = None
        self.command_executor = None
        self.feature_registry = None
        self.input_provider = None
        self.system_tray = None
    
    def initialize(self):
        """Initialize all components in correct order"""
        logger.info("Initializing Macro Engine...")
        
        # 1. Load configuration
        config_path = PROJECT_ROOT / "config" / "macros.json"
        self.config_manager = ConfigManager(config_path)
        self.config_manager.load()
        logger.info("Configuration loaded")
        
        # 2. Initialize command executor
        self.command_executor = CommandExecutor()
        logger.info("Command executor ready")
        
        # 3. Initialize feature registry
        self.feature_registry = FeatureRegistry(
            config_manager=self.config_manager,
            command_executor=self.command_executor
        )
        self.feature_registry.discover_features()
        logger.info(f"Features loaded: {list(self.feature_registry.features.keys())}")
        
        # 4. Initialize mode manager
        self.mode_manager = ModeManager(
            config_manager=self.config_manager,
            feature_registry=self.feature_registry
        )
        logger.info(f"Mode manager ready, current mode: {self.mode_manager.current_mode}")
        
        # 5. Initialize event router
        self.event_router = EventRouter(
            config_manager=self.config_manager,
            mode_manager=self.mode_manager
        )
        logger.info("Event router ready")
        
        # 6. Initialize input provider
        self.input_provider = KeyboardInputProvider(
            event_callback=self.event_router.route_event,
            config_manager=self.config_manager
        )
        logger.info("Keyboard input provider ready")
        
        # 6.6 Initialize Snippet Manager
        try:
            from core.snippets.snippet_manager import SnippetManager
            snippet_config = PROJECT_ROOT / "config" / "snippets.json"
            self.snippet_manager = SnippetManager(snippet_config)
            logger.info("Snippet Manager initialized")
        except Exception as e:
            logger.warning(f"Snippet Manager failed: {e}")
            self.snippet_manager = None
            
        # Register snippet command
        self.command_executor.register_command("launch_snippets", self.launch_snippet_selector)
            
        # 6.5. Initialize Tkinter Root and Quick Panel
        try:
            import tkinter as tk
            from ui.quick_panel import QuickPanel
            
            # Create hidden root window
            self.root = tk.Tk()
            self.root.withdraw()
            
            self.quick_panel = QuickPanel(
                root=self.root,
                config_manager=self.config_manager,
                command_executor=self.command_executor,
                on_snippets=self.launch_snippet_selector
            )
            # Register QuickPanel as observer
            self.mode_manager.add_observer(self.quick_panel.update_mode)
            logger.info("Quick Panel initialized")
        except Exception as e:
            logger.warning(f"Quick Panel not available: {e}")
            self.root = None
            self.root = None
            self.quick_panel = None
            
        # 7. Initialize system tray (optional UI)
        try:
            self.system_tray = SystemTrayUI(
                mode_manager=self.mode_manager,
                on_exit=self.stop,
                quick_panel=self.quick_panel, # Pass quick panel to tray
                on_snippets=self.launch_snippet_selector
            )
            # Register SystemTray as observer
            self.mode_manager.add_observer(lambda mode: self.system_tray.update_icon())
            logger.info("System tray ready")
        except Exception as e:
            logger.warning(f"System tray not available: {e}")
            self.system_tray = None
        
        # 8. Sync auto-start with config
        auto_start_setting = self.config_manager.get_settings().get("auto_start", False)
        if auto_start_setting and not is_auto_start_enabled():
            enable_auto_start()
        elif not auto_start_setting and is_auto_start_enabled():
            disable_auto_start()
        
        logger.info("Macro Engine initialized successfully!")

    def launch_snippet_selector(self):
        """Launch the snippet selector UI"""
        if not self.snippet_manager or not self.root:
            logger.warning("Snippet manager or UI root not available")
            return
            
        from ui.snippet_selector import SnippetSelector
        import pyperclip
        import time 
        
        # Use existing keyboard provider if possible to inject, 
        # but KeyboardInputProvider is for listening.
        # We need a controller. pynput.keyboard.Controller or similar.
        # Let's verify what inputs/keyboard_provider.py uses.
        # It likely uses pynput.
        
        def on_snippet_selected(snippet, variables=None):
            insert_snippet(snippet, variables)

        def insert_snippet(snippet, variables=None):
            # Process content
            content = self.snippet_manager.process_snippet(snippet, variables)
            if not content:
                return
                
            logger.info(f"Inserting snippet: {snippet['trigger']}")
            
            # Method 1: Type it out (slow for long text)
            # Method 2: Paste from clipboard (faster, reliable)
            
            try:
                # Save old clipboard
                old_clip = pyperclip.paste()
                
                # Set new content
                pyperclip.copy(content)
                
                # Simulate Ctrl+V
                # We need a way to press keys. 
                # Since we don't have a reliable cross-platform keyboard controller exposed yet,
                # let's try pynput directly or import it if verified.
                from pynput.keyboard import Controller, Key
                keyboard = Controller()
                
                # Focus back to previous window (the selector is already closed/closing)
                # But we might need a small delay
                time.sleep(0.1) 
                
                with keyboard.pressed(Key.ctrl):
                    keyboard.press('v')
                    keyboard.release('v')
                    
                # Restore clipboard (delayed to allow paste to happen)
                def restore():
                    time.sleep(0.5) 
                    pyperclip.copy(old_clip)
                
                threading.Thread(target=restore).start()
                
            except Exception as e:
                logger.error(f"Failed to insert snippet: {e}")

        # Launch UI on main thread (or ensure root is thread safe? Tkinter isn't)
        # Since this is called from where?
        # If called from a hotkey (background thread), we must use root.after
        
        self.root.after(0, lambda: SnippetSelector(self.root, self.snippet_manager, on_snippet_selected))
    
    def start(self):
        """Start the engine"""
        self.running = True
        logger.info("Starting Macro Engine...")
        
        # Start statistics session
        try:
            from utils.statistics import get_tracker
            get_tracker().start_session()
        except Exception:
            pass
        
        # Start input listener
        self.input_provider.start()
        
        # Start system tray in a separate thread because it blocks
        if self.system_tray:
            import threading
            tray_thread = threading.Thread(target=self.system_tray.run, daemon=True)
            tray_thread.start()
        else:
            logger.info("Running in headless mode (no system tray)")

        # Run tkinter mainloop if UI exists
        if self.root:
            logger.info("Starting UI loop")
            self.root.mainloop()
        else:
             # Fallback for headless
            try:
                signal.pause()
            except AttributeError:
                import time
                while self.running:
                    time.sleep(1)
    
    def stop(self):
        """Stop the engine gracefully"""
        logger.info("Stopping Macro Engine...")
        self.running = False
        
        if self.input_provider:
            self.input_provider.stop()
            
        if self.quick_panel:
            try:
                self.quick_panel.destroy()
            except:
                pass
        
        if self.root:
            try:
                self.root.quit()
            except:
                pass
        
        if self.system_tray:
            self.system_tray.stop()

        
        logger.info("Macro Engine stopped")


# Global engine instance
_engine = None


def start():
    """Entry point called by main.py"""
    # Check if this is a popup request (from subprocess)
    if len(sys.argv) >= 3:
        popup_type = sys.argv[1]
        if popup_type in ["mode", "guide"]:
            try:
                import json
                from ui.popup_runner import show_mode_popup, show_guide_popup
                data = json.loads(sys.argv[2])
                if popup_type == "mode":
                    show_mode_popup(data["mode_name"])
                elif popup_type == "guide":
                    show_guide_popup(data["mode_name"], data["guide_lines"], data.get("is_notification", False))
                sys.exit(0)
            except Exception:
                # Fallback to normal start if error or not a popup request
                pass

    # Single instance check (Windows)
    if sys.platform == 'win32':
        mutex_name = "Global\\JRDev_MacroEngine_Mutex"
        kernel32 = ctypes.windll.kernel32
        mutex = kernel32.CreateMutexW(None, False, mutex_name)
        last_error = kernel32.GetLastError()
        
        if last_error == 183: # ERROR_ALREADY_EXISTS
            print("Another instance of JR-Dev is already running.")
            sys.exit(0)

    global _engine
    
    setup_logger()
    logger.info("=" * 50)
    logger.info("Developer Macro Engine v2.0")
    logger.info("=" * 50)
    
    try:
        _engine = MacroEngine()
        _engine.initialize()
        _engine.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        if _engine:
            _engine.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise


def stop():
    """Stop the engine from external call"""
    global _engine
    if _engine:
        _engine.stop()
