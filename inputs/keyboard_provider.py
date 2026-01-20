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


class KeyboardInputProvider(BaseInputProvider):
    """
    Keyboard input provider using pynput.
    
    This works with:
    - Physical keyboard
    - USB HID devices (Arduino, macro pads)
    - Any device that sends keyboard events to Windows
    """
    
    source_name = "keyboard"
    
    # Single keys we're listening for: F9, F10, F11
    MONITORED_KEYS = {
        keyboard.Key.f9: "f9",
        keyboard.Key.f10: "f10",
        keyboard.Key.f11: "f11",
    }
    
    def __init__(self, event_callback: Callable[[InputEvent], None]):
        super().__init__(event_callback)
        
        self.listener: Optional[keyboard.Listener] = None
        self.key_press_times: dict = {}
        self._lock = threading.Lock()
    
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
