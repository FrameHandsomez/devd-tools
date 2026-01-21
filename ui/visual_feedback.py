"""
Visual Feedback Overlay - Show key press feedback
Shows a small popup at bottom-right when keys are pressed
Uses subprocess to avoid tkinter threading issues
"""

import subprocess
import sys
import json
import os
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)

# Get the path to popup_runner.py
_POPUP_RUNNER = Path(__file__).parent / "popup_runner.py"


def show_key_feedback(key: str, pattern: str, action: str, accent_color: str = "#4CAF50"):
    """
    Show a visual feedback overlay when a key is pressed.
    Uses subprocess to avoid tkinter threading issues.
    
    Args:
        key: The key that was pressed (e.g., "F9")
        pattern: The press pattern (e.g., "กดสั้น", "กดค้าง")
        action: The action being executed (e.g., "clone", "commit")
        accent_color: Color accent for the overlay
    """
    try:
        data = json.dumps({
            "key": key,
            "pattern": pattern,
            "action": action,
            "accent_color": accent_color
        })
        
        # Run popup in subprocess
        subprocess.Popen(
            [sys.executable, str(_POPUP_RUNNER), "key_feedback", data],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
    except Exception as e:
        logger.debug(f"Could not show key feedback: {e}")
