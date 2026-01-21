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
        
        # Show in popup using threading (subprocess is too complex for this UI)
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
        """Create and show the premium guide popup window"""
        
        root = tk.Tk()
        root.withdraw()
        
        # Colors - GitHub Dark Theme
        bg_dark = "#0d1117"
        bg_card = "#161b22"
        bg_row_alt = "#1c2129"
        text_primary = "#f0f6fc"
        text_secondary = "#8b949e"
        border_color = "#30363d"
        
        # Mode colors and tips
        mode_config = {
            "Development Mode": {
                "color": "#238636",
                "icon": "🚀",
                "tips": [
                    "💡 กดค้าง F9 เพื่อเปลี่ยน project path",
                    "⚡ กด F10 สองครั้งเร็วๆ เพื่อเลือก project",
                    "🎯 กด F10 ค้างไว้ 3 วินาที เพื่อ reset path"
                ]
            },
            "Git Mode": {
                "color": "#f78166",
                "icon": "📦",
                "tips": [
                    "💡 กดค้าง F9 เพื่อดู git status แบบละเอียด",
                    "⚡ Commit ด่วนด้วย F9 กดสั้น",
                    "🔄 ใช้ F10 สำหรับ push และ pull"
                ]
            },
            "AI Assistant Mode": {
                "color": "#a371f7",
                "icon": "🤖",
                "tips": [
                    "💡 พิมพ์คำถามแล้วกด F9 เพื่อถาม AI",
                    "⚡ กดค้าง F9 เพื่อเปิด AI chat",
                    "🧠 AI จะช่วยเขียนโค้ดให้อัตโนมัติ"
                ]
            },
            "Script Mode": {
                "color": "#58a6ff",
                "icon": "⚙️",
                "tips": [
                    "💡 รัน script ได้ทันทีด้วย F9",
                    "⚡ กด F10 เพื่อเลือก script ที่ต้องการ",
                    "📁 Scripts อยู่ในโฟลเดอร์ scripts/"
                ]
            }
        }
        
        config = mode_config.get(mode_name, {
            "color": "#238636",
            "icon": "🎮",
            "tips": ["💡 กด F11 เพื่อเปลี่ยน Mode"]
        })
        accent_color = config["color"]
        mode_icon = config["icon"]
        tips = config["tips"]
        
        # Calculate size
        num_shortcuts = len(guide_lines)
        num_tips = len(tips)
        row_height = 38
        tip_height = 28
        header_height = 60
        section_header_height = 35
        footer_height = 50
        padding = 30
        
        content_height = (num_shortcuts * row_height) + (num_tips * tip_height) + (section_header_height * 2)
        height = min(header_height + content_height + footer_height + padding, 600)
        width = 500
        
        # Create popup window
        popup = tk.Toplevel(root)
        popup.title(f"Shortcut Guide - {mode_name}")
        popup.overrideredirect(True)  # Remove window decorations
        popup.attributes('-topmost', True)
        popup.attributes('-alpha', 0.0)  # Start invisible for fade in
        
        # Center on screen
        screen_w = popup.winfo_screenwidth()
        screen_h = popup.winfo_screenheight()
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        popup.geometry(f"{width}x{height}+{x}+{y}")
        
        # Main container with border
        popup.configure(bg=border_color)
        
        # Inner container
        inner = tk.Frame(popup, bg=bg_dark)
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        
        # Header
        header = tk.Frame(inner, bg=accent_color, height=header_height)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        header_content = tk.Frame(header, bg=accent_color)
        header_content.pack(expand=True)
        
        tk.Label(
            header_content,
            text=f"{mode_icon} {mode_name}",
            font=("Segoe UI", 15, "bold"),
            fg="white",
            bg=accent_color
        ).pack(pady=16)
        
        # Scrollable content area
        content_outer = tk.Frame(inner, bg=bg_dark)
        content_outer.pack(fill="both", expand=True)
        
        # Canvas for scrolling
        canvas = tk.Canvas(content_outer, bg=bg_dark, highlightthickness=0)
        scrollbar = tk.Scrollbar(content_outer, orient="vertical", command=canvas.yview)
        
        content = tk.Frame(canvas, bg=bg_dark)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        canvas_frame = canvas.create_window((0, 0), window=content, anchor="nw")
        
        def configure_scroll(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(canvas_frame, width=canvas.winfo_width())
        
        content.bind("<Configure>", configure_scroll)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_frame, width=e.width))
        
        # Mouse wheel scroll
        def on_mousewheel(e):
            canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        # === SHORTCUTS SECTION ===
        section1 = tk.Frame(content, bg=bg_dark)
        section1.pack(fill="x", padx=16, pady=(12, 6))
        
        tk.Label(
            section1,
            text="⌨️  KEYBOARD SHORTCUTS",
            font=("Segoe UI", 10, "bold"),
            fg=text_secondary,
            bg=bg_dark
        ).pack(anchor="w")
        
        # Shortcuts table
        shortcuts_frame = tk.Frame(content, bg=bg_dark)
        shortcuts_frame.pack(fill="x", padx=16, pady=(0, 12))
        
        if not guide_lines:
            tk.Label(
                shortcuts_frame,
                text="ไม่มี shortcuts ใน mode นี้",
                font=("Segoe UI", 10),
                fg=text_secondary,
                bg=bg_dark
            ).pack(pady=12)
        else:
            for i, item in enumerate(guide_lines):
                row_bg = bg_row_alt if i % 2 == 1 else bg_card
                
                row = tk.Frame(shortcuts_frame, bg=row_bg, height=row_height)
                row.pack(fill="x", pady=1)
                row.pack_propagate(False)
                
                row_inner = tk.Frame(row, bg=row_bg)
                row_inner.pack(fill="both", expand=True, padx=12)
                
                # Left: Key + Pattern
                left = tk.Frame(row_inner, bg=row_bg)
                left.pack(side="left", fill="y")
                
                key_badge = tk.Label(
                    left,
                    text=f" {item['key']} ",
                    font=("Consolas", 11, "bold"),
                    fg=accent_color,
                    bg="#2d333b",
                    padx=8,
                    pady=2
                )
                key_badge.pack(side="left", pady=8)
                
                pattern_label = tk.Label(
                    left,
                    text=f" {item['pattern']}",
                    font=("Segoe UI", 9),
                    fg=text_secondary,
                    bg=row_bg
                )
                pattern_label.pack(side="left", padx=8, pady=8)
                
                # Right: Action
                action_label = tk.Label(
                    row_inner,
                    text=item['action'],
                    font=("Segoe UI", 10, "bold"),
                    fg=text_primary,
                    bg=row_bg
                )
                action_label.pack(side="right", pady=8)
        
        # === TIPS SECTION ===
        section2 = tk.Frame(content, bg=bg_dark)
        section2.pack(fill="x", padx=16, pady=(8, 6))
        
        tk.Label(
            section2,
            text="✨  TIPS & TRICKS",
            font=("Segoe UI", 10, "bold"),
            fg=text_secondary,
            bg=bg_dark
        ).pack(anchor="w")
        
        # Tips list
        tips_frame = tk.Frame(content, bg=bg_dark)
        tips_frame.pack(fill="x", padx=16, pady=(0, 12))
        
        for tip in tips:
            tip_row = tk.Frame(tips_frame, bg=bg_card, height=tip_height + 8)
            tip_row.pack(fill="x", pady=2)
            tip_row.pack_propagate(False)
            
            tk.Label(
                tip_row,
                text=tip,
                font=("Segoe UI", 10),
                fg=text_primary,
                bg=bg_card,
                anchor="w"
            ).pack(side="left", padx=12, pady=8)
        
        # === FOOTER ===
        footer = tk.Frame(inner, bg=bg_dark, height=footer_height)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)
        
        # Separator
        separator = tk.Frame(footer, bg=border_color, height=1)
        separator.pack(fill="x")
        
        footer_content = tk.Frame(footer, bg=bg_dark)
        footer_content.pack(expand=True)
        
        hint_frame = tk.Frame(footer_content, bg=bg_dark)
        hint_frame.pack(pady=12)
        
        # Footer hints
        tk.Label(
            hint_frame,
            text="กด ",
            font=("Segoe UI", 9),
            fg=text_secondary,
            bg=bg_dark
        ).pack(side="left")
        
        tk.Label(
            hint_frame,
            text=" F11 ",
            font=("Consolas", 9, "bold"),
            fg=accent_color,
            bg="#2d333b",
            padx=4
        ).pack(side="left")
        
        tk.Label(
            hint_frame,
            text=" เปลี่ยน Mode  •  กด ",
            font=("Segoe UI", 9),
            fg=text_secondary,
            bg=bg_dark
        ).pack(side="left")
        
        tk.Label(
            hint_frame,
            text=" ESC ",
            font=("Consolas", 9, "bold"),
            fg="#f85149",
            bg="#2d333b",
            padx=4
        ).pack(side="left")
        
        tk.Label(
            hint_frame,
            text=" ปิด",
            font=("Segoe UI", 9),
            fg=text_secondary,
            bg=bg_dark
        ).pack(side="left")
        
        # Fade in animation
        def fade_in(alpha=0.0):
            try:
                if alpha < 0.98:
                    popup.attributes('-alpha', alpha)
                    popup.after(15, lambda: fade_in(alpha + 0.08))
                else:
                    popup.attributes('-alpha', 0.98)
            except:
                pass
        
        # Fade out animation
        def fade_out(alpha=0.98):
            try:
                if alpha > 0.05:
                    popup.attributes('-alpha', alpha)
                    popup.after(20, lambda: fade_out(alpha - 0.1))
                else:
                    self._close_popup(popup, root, canvas)
            except:
                self._close_popup(popup, root, canvas)
        
        # Start fade in
        popup.after(10, fade_in)
        
        # Keyboard bindings
        popup.bind('<Escape>', lambda e: fade_out())
        popup.bind('<F12>', lambda e: fade_out())  # Close on F12 press again
        
        # Click outside to close
        popup.bind('<FocusOut>', lambda e: fade_out())
        
        # Auto-close after 15 seconds
        root.after(15000, fade_out)
        
        # Focus the popup
        popup.focus_force()
        
        root.mainloop()
    
    def _close_popup(self, popup, root, canvas=None):
        """Safely close popup"""
        try:
            if canvas:
                canvas.unbind_all("<MouseWheel>")
            root.quit()
            root.destroy()
        except:
            pass

