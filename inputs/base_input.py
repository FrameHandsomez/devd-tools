"""
Base Input Provider - Abstract class for all input sources
All input sources produce the same InputEvent format
"""

from abc import ABC, abstractmethod
from typing import Callable
from core.events.input_event import InputEvent


class BaseInputProvider(ABC):
    """
    Abstract base class for input providers.
    
    All input sources (keyboard, Arduino, macro pad) must:
    1. Inherit from this class
    2. Produce InputEvent objects
    3. Call the event_callback when an event occurs
    """
    
    # Source name for logging
    source_name: str = "base"
    
    def __init__(self, event_callback: Callable[[InputEvent], None]):
        """
        Initialize the input provider.
        
        Args:
            event_callback: Function to call when an input event occurs
        """
        self.event_callback = event_callback
        self.running = False
    
    @abstractmethod
    def start(self):
        """Start listening for input events"""
        pass
    
    @abstractmethod
    def stop(self):
        """Stop listening for input events"""
        pass
    
    def emit_event(self, event: InputEvent):
        """Emit an event to the callback"""
        event.source = self.source_name
        if self.event_callback:
            self.event_callback(event)
