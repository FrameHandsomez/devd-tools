"""
Bootstrap Layer - Initialize and start all components
main.py only calls start() from here
"""

import sys
import signal
from pathlib import Path

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
        
        # 7. Initialize system tray (optional UI)
        try:
            self.system_tray = SystemTrayUI(
                mode_manager=self.mode_manager,
                on_exit=self.stop
            )
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
        
        # Start system tray (this blocks on Windows)
        if self.system_tray:
            self.system_tray.run()  # Blocking call
        else:
            # If no tray, just wait for keyboard interrupt
            logger.info("Running in headless mode (no system tray)")
            try:
                signal.pause()
            except AttributeError:
                # Windows doesn't have signal.pause
                import time
                while self.running:
                    time.sleep(1)
    
    def stop(self):
        """Stop the engine gracefully"""
        logger.info("Stopping Macro Engine...")
        self.running = False
        
        if self.input_provider:
            self.input_provider.stop()
        
        if self.system_tray:
            self.system_tray.stop()
        
        logger.info("Macro Engine stopped")


# Global engine instance
_engine = None


def start():
    """Entry point called by main.py"""
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
