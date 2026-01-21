"""
Keyboard Input Provider - Uses pynput to capture global keyboard events
Works with physical keyboard AND USB HID devices (Arduino, Macro Pad)
"""

import time
import threading
from typing import Callable, Optional, Set
from pynput import keyboard
from inputs.base_input import BaseInputProvider
from core.events.input_event import InputEvent, PressType
from utils.logger import get_logger

logger = get_logger(__name__)

# All possible function keys
ALL_FUNCTION_KEYS = {
    keyboard.Key.f1: "f1", keyboard.Key.f2: "f2", keyboard.Key.f3: "f3",
    keyboard.Key.f4: "f4", keyboard.Key.f5: "f5", keyboard.Key.f6: "f6",
    keyboard.Key.f7: "f7", keyboard.Key.f8: "f8", keyboard.Key.f9: "f9",
    keyboard.Key.f10: "f10", keyboard.Key.f11: "f11", keyboard.Key.f12: "f12",
}

# Default monitored keys
DEFAULT_MONITORED = ["f9", "f10", "f11", "f12"]


class KeyboardInputProvider(BaseInputProvider):
    """
    Keyboard input provider using pynput.
    
    This works with:
    - Physical keyboard
    - USB HID devices (Arduino, macro pads)
    - Any device that sends keyboard events to Windows
    """
    
    source_name = "keyboard"
    
    def __init__(self, event_callback: Callable[[InputEvent], None], config_manager=None):
        super().__init__(event_callback)
        
        self.config_manager = config_manager
        self.listener: Optional[keyboard.Listener] = None
        self.key_press_times: dict = {}
        self._lock = threading.Lock()
        self._monitored_keys = None
    
    @property
    def MONITORED_KEYS(self):
        """Get monitored keys from config or use defaults"""
        if self._monitored_keys is None:
            self._build_monitored_keys()
        return self._monitored_keys
    
    def _build_monitored_keys(self):
        """Build monitored keys dict from config"""
        monitored = DEFAULT_MONITORED
        
        if self.config_manager:
            settings = self.config_manager.get_settings()
            configured = settings.get("monitored_keys", None)
            if configured:
                monitored = configured
        
        self._monitored_keys = {}
        for key_obj, key_str in ALL_FUNCTION_KEYS.items():
            if key_str in monitored:
                self._monitored_keys[key_obj] = key_str
    
    def reload_monitored_keys(self):
        """Reload monitored keys from config"""
        self._monitored_keys = None
        logger.info(f"Reloaded monitored keys: {list(self.MONITORED_KEYS.values())}")
    
    def start(self):
        """Start the keyboard listener"""
        if self.running:
            return
        
        self.running = True
        
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.listener.start()
        
        logger.info("Keyboard input provider started")
        logger.info(f"Monitoring keys: {list(self.MONITORED_KEYS.values())}")
    
    def stop(self):
        """Stop the keyboard listener"""
        self.running = False
        
        if self.listener:
            self.listener.stop()
            self.listener = None
        
        logger.info("Keyboard input provider stopped")
    
    def _on_press(self, key):
        """Handle key press event"""
        with self._lock:
            # Check if this is a monitored key
            if key not in self.MONITORED_KEYS:
                return
            
            # Record press time if not already pressed
            key_name = self.MONITORED_KEYS[key]
            if key_name not in self.key_press_times:
                self.key_press_times[key_name] = time.time()
                logger.debug(f"Key pressed: {key_name}")
    
    def _on_release(self, key):
        """Handle key release event"""
        with self._lock:
            # Check if this is a monitored key
            if key not in self.MONITORED_KEYS:
                return
            
            key_name = self.MONITORED_KEYS[key]
            
            # Calculate press duration
            press_duration_ms = 0
            if key_name in self.key_press_times:
                press_duration_ms = int((time.time() - self.key_press_times[key_name]) * 1000)
                del self.key_press_times[key_name]
            
            # Emit the event
            event = InputEvent(
                key_combination=key_name,
                press_duration_ms=press_duration_ms,
                timestamp=time.time()
            )
            
            logger.info(f"Emitting event: {key_name} (duration: {press_duration_ms}ms)")
            self.emit_event(event)
