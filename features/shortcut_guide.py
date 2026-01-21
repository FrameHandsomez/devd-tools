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
    
    def execute(self, event: InputEvent, action: str) -> FeatureResult:
        """Execute the shortcut guide display"""
        
        if action == "show":
            return self._show_guide()
        else:
            return self._show_guide()  # Default action
    
    def _get_mode_manager(self):
        """Get mode manager from bootstrap"""
        from runtime.bootstrap import _engine
        if _engine and _engine.mode_manager:
            return _engine.mode_manager
        return None
    
    def _show_guide(self) -> FeatureResult:
        """Show the shortcut guide popup"""
        
        mode_manager = self._get_mode_manager()
        
        if not mode_manager:
            return FeatureResult(
                status=FeatureStatus.ERROR,
                message="Mode manager not available"
            )
        
        current_mode = mode_manager.current_mode
        mode_name = mode_manager.get_mode_name()
        bindings = self.config_manager.get_mode_bindings(current_mode)
        
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
                }.get(pattern, pattern)
                
                guide_lines.append({
                    "key": key.upper(),
                    "pattern": pattern_display,
                    "action": action,
                    "feature": feature_name
                })
        
        # Show in popup
        import threading
        def show_popup():
            self._create_guide_popup(mode_name, guide_lines)
        
        threading.Thread(target=show_popup, daemon=True).start()
        
        logger.info(f"Shortcut guide shown for mode: {current_mode}")
        
        return FeatureResult(
            status=FeatureStatus.SUCCESS,
            message=f"Guide shown for {mode_name}"
        )
    
    def _create_guide_popup(self, mode_name: str, guide_lines: list):
        """Create and show the guide popup window"""
        
        root = tk.Tk()
        root.withdraw()
        
        # Create popup window
        popup = tk.Toplevel(root)
        popup.title(f"🎮 Shortcut Guide - {mode_name}")
        popup.attributes('-topmost', True)
        popup.configure(bg="#1a1a2e")
        
        # Calculate size based on content
        width = 450
        height = min(100 + len(guide_lines) * 35, 500)
        
        # Center on screen
        x = (popup.winfo_screenwidth() - width) // 2
        y = (popup.winfo_screenheight() - height) // 2
        popup.geometry(f"{width}x{height}+{x}+{y}")
        
        # Mode colors
        mode_colors = {
            "Development Mode": "#4CAF50",
            "Git Mode": "#FF9800",
            "AI Assistant Mode": "#9C27B0",
            "Script Mode": "#2196F3"
        }
        accent_color = mode_colors.get(mode_name, "#4CAF50")
        
        # Header
        header = tk.Frame(popup, bg=accent_color, height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text=f"🎮 {mode_name}",
            font=("Segoe UI", 14, "bold"),
            fg="white",
            bg=accent_color
        ).pack(pady=12)
        
        # Content frame with scrollbar
        content_frame = tk.Frame(popup, bg="#1a1a2e")
        content_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        if not guide_lines:
            tk.Label(
                content_frame,
                text="ไม่มี shortcuts ใน mode นี้",
                font=("Segoe UI", 11),
                fg="#888888",
                bg="#1a1a2e"
            ).pack(pady=20)
        else:
            for item in guide_lines:
                row = tk.Frame(content_frame, bg="#1a1a2e")
                row.pack(fill="x", pady=3)
                
                # Key badge
                key_label = tk.Label(
                    row,
                    text=f" {item['key']} ",
                    font=("Consolas", 11, "bold"),
                    fg="white",
                    bg="#333355",
                    padx=8,
                    pady=2
                )
                key_label.pack(side="left")
                
                # Pattern
                pattern_label = tk.Label(
                    row,
                    text=f"({item['pattern']})",
                    font=("Segoe UI", 9),
                    fg="#888888",
                    bg="#1a1a2e"
                )
                pattern_label.pack(side="left", padx=5)
                
                # Action
                action_label = tk.Label(
                    row,
                    text=item['action'],
                    font=("Segoe UI", 10),
                    fg=accent_color,
                    bg="#1a1a2e"
                )
                action_label.pack(side="right")
        
        # Footer hint
        footer = tk.Label(
            popup,
            text="กด F11 เพื่อเปลี่ยน Mode  |  กด Escape เพื่อปิด",
            font=("Segoe UI", 9),
            fg="#666666",
            bg="#1a1a2e"
        )
        footer.pack(pady=8)
        
        # Close on Escape or click outside
        popup.bind('<Escape>', lambda e: self._close_popup(popup, root))
        popup.bind('<FocusOut>', lambda e: self._close_popup(popup, root))
        
        # Auto-close after 10 seconds
        popup.after(10000, lambda: self._close_popup(popup, root))
        
        root.mainloop()
    
    def _close_popup(self, popup, root):
        """Safely close popup"""
        try:
            popup.destroy()
            root.destroy()
        except:
            pass
