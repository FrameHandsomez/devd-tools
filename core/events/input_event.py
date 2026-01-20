"""
Unified InputEvent class - Hardware-agnostic event format
All input providers (keyboard, Arduino, macro pad) produce this same format
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import time


class PressType(Enum):
    """Type of key press detected"""
    SHORT = "short"
    LONG = "long"
    DOUBLE = "double"
    MULTI = "multi"  # 3+ presses
    CHORD = "chord"  # Multiple keys at once (future)
    UNKNOWN = "unknown"


@dataclass
class InputEvent:
    """
    Hardware-agnostic input event.
    All input sources (keyboard, Arduino HID, macro pad) produce this same format.
    """
    
    # The key combination pressed (e.g., "ctrl+alt+1")
    key_combination: str
    
    # Type of press detected
    press_type: PressType = PressType.SHORT
    
    # Timestamp when the event occurred
    timestamp: float = field(default_factory=time.time)
    
    # Source of the input (for logging/debugging)
    source: str = "keyboard"
    
    # Duration of the press in milliseconds (for long press detection)
    press_duration_ms: int = 0
    
    # Number of presses (for multi-press detection)
    press_count: int = 1
    
    # Optional action name from pattern matching
    action: Optional[str] = None
    
    def __str__(self) -> str:
        return (
            f"InputEvent(key={self.key_combination}, "
            f"type={self.press_type.value}, "
            f"source={self.source}, "
            f"count={self.press_count})"
        )


@dataclass
class KeyState:
    """Track the state of a key combination for pattern detection"""
    
    key_combination: str
    press_start: float = 0.0
    press_count: int = 0
    last_press_time: float = 0.0
    is_pressed: bool = False
    
    def reset(self):
        """Reset the state"""
        self.press_start = 0.0
        self.press_count = 0
        self.last_press_time = 0.0
        self.is_pressed = False
