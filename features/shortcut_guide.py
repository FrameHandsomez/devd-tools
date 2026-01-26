"""
Shortcut Guide Feature - Show current mode's key bindings

Actions:
- show_guide: Display a popup with all keybindings for current mode
"""

import tkinter as tk
from typing import Optional
from core.features.base_feature import BaseFeature, FeatureResult, FeatureStatus
from core.events.input_event import InputEvent, PressType
from utils.logger import get_logger

logger = get_logger(__name__)


class ShortcutGuideFeature(BaseFeature):
    """
    Feature: Keyboard Shortcut Guide
    
    - F12: Show current mode's key bindings in a popup
    """
    
    name = "shortcut_guide"
    description = "Show keyboard shortcuts for current mode"
    supported_patterns = [PressType.SHORT]
    
    # Track active window for singleton behavior
    _active_root = None
    _active_popup = None
    
    def execute(self, event: InputEvent, action: str) -> FeatureResult:
        """Execute the shortcut guide display"""
        logger.info(f"ShortcutGuideFeature executing action: {action}")
        
        # Any action will trigger show_guide for now
        return self._show_guide()
    
    def _get_mode_manager(self):
        """Get mode manager from bootstrap"""
        from runtime.bootstrap import _engine
        if _engine and _engine.mode_manager:
            return _engine.mode_manager
        return None
    
    def _show_guide(self) -> FeatureResult:
        """Show the shortcut guide popup using a separate process for stability"""
        
        mode_manager = self._get_mode_manager()
        if not mode_manager:
            logger.error("ShortcutGuide: Mode manager not available")
            return FeatureResult(status=FeatureStatus.ERROR, message="Mode manager not available")
        
        current_mode = mode_manager.current_mode
        mode_name = mode_manager.get_mode_name()
        bindings = self.config_manager.get_mode_bindings(current_mode)
        
        logger.info(f"ShortcutGuide: Preparing guide for {mode_name} (mode: {current_mode})")
        
        # Build guide content
        guide_lines = []
        for key, binding in bindings.items():
            feature_name = binding.get("feature", "?")
            patterns = binding.get("patterns", {})
            for pattern, action in patterns.items():
                pattern_display = {
                    "short": "กดสั้น", 
                    "long": "กดค้าง", 
                    "double": "กด 2 ครั้ง",
                    "multi_3": "กด 3 ครั้ง"
                }.get(pattern, str(pattern))
                guide_lines.append({
                    "key": str(key).upper(),
                    "pattern": pattern_display,
                    "action": str(action),
                    "feature": str(feature_name)
                })
        
        # Launch popup in a separate process to avoid main process crash
        import subprocess
        import sys
        import json
        from pathlib import Path
        
        # Get path to popup_runner.py relative to this file
        popup_runner = Path(__file__).parent.parent / "ui" / "popup_runner.py"
        
        data = json.dumps({
            "mode_name": mode_name,
            "guide_lines": guide_lines,
            "is_notification": False
        })
        
        try:
            is_frozen = getattr(sys, 'frozen', False)
            if is_frozen:
                # In frozen mode (PyInstaller), run the executable itself with arguments
                # The bootstrap.py will intercept these arguments
                cmd = [sys.executable, "guide", data]
            else:
                # In development mode, run the script directly
                cmd = [sys.executable, str(popup_runner), "guide", data]

            logger.info(f"ShortcutGuide: Launching process {cmd}")
            subprocess.Popen(
                cmd,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return FeatureResult(status=FeatureStatus.SUCCESS, message=f"Guide launched for {mode_name}")
        except Exception as e:
            logger.error(f"Error launching guide process: {e}")
            return FeatureResult(status=FeatureStatus.ERROR, message=str(e))

    @classmethod
    def show_mode_change_notification(cls, mode_name: str):
        """Show a quick notification using separate process"""
        import subprocess
        import sys
        import json
        from pathlib import Path
        
        popup_runner = Path(__file__).parent.parent / "ui" / "popup_runner.py"
        data = json.dumps({
            "mode_name": mode_name,
            "duration": 2000
        })
        
        try:
            is_frozen = getattr(sys, 'frozen', False)
            if is_frozen:
                cmd = [sys.executable, "mode", data]
            else:
                cmd = [sys.executable, str(popup_runner), "mode", data]

            subprocess.Popen(
                cmd,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        except Exception as e:
            logger.error(f"Error launching notification process: {e}")

    
    @classmethod
    def close_existing_guide(cls):
        """Deprecated: UI handled by separate process"""
        pass

    def _create_guide_popup(self, mode_name: str, guide_lines: list, is_notification: bool = False):
        """Deprecated: UI now handled by popup_runner.py for stability"""
        pass
    
    def _close_popup(self, popup, root, canvas=None):
        """Deprecated: UI now handled by popup_runner.py for stability"""
        pass

