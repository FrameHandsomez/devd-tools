"""
Popup Runner - Runs popup windows in a separate process
This script is executed via subprocess to avoid tkinter threading issues
"""

import sys
import json
import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import winsound
import time

def play_sound(sound_type="info"):
    """Play a subtle system sound"""
    try:
        if sound_type == "mode":
            winsound.Beep(600, 50)
            winsound.Beep(800, 50)
        elif sound_type == "info":
            winsound.Beep(700, 100)
        elif sound_type == "success":
            winsound.Beep(800, 100)
            winsound.Beep(1000, 100)
    except:
        pass

def show_notification_popup(title: str, message: str, duration: int = 2000):
    """Show a modern notification popup"""
    play_sound("info")
    try:
        # Use ttkbootstrap's ToastNotification if possible, but we need it blocking?
        # ToastNotification is non-blocking usually. 
        # Let's stick to custom generic window for control but use tb styling.
        
        root = tb.Window(themename="cyborg")
        root.withdraw()
        
        notif = tb.Toplevel(root)
        notif.overrideredirect(True)
        notif.attributes('-topmost', True)
        notif.attributes('-alpha', 0.0)
        
        width = 320
        height = 90
        x = notif.winfo_screenwidth() - width - 20
        y = notif.winfo_screenheight() - height - 60
        notif.geometry(f"{width}x{height}+{x}+{y}")
        
        # Frame with nicer border
        main_frame = tb.Frame(notif, bootstyle="secondary", padding=2)
        main_frame.pack(fill=BOTH, expand=YES)
        
        inner = tb.Frame(main_frame, bootstyle="dark", padding=15)
        inner.pack(fill=BOTH, expand=YES)
        
        tb.Label(
            inner, text=title, font=("Segoe UI", 11, "bold"),
            bootstyle="inverse-dark"
        ).pack(anchor="w")
        
        tb.Label(
            inner, text=message, font=("Segoe UI", 10),
            bootstyle="inverse-dark"
        ).pack(anchor="w", pady=(5, 0))
        
        # Accent bar
        tb.Frame(inner, bootstyle="primary", height=3).pack(fill=X, side=BOTTOM, pady=(5, 0))

        def fade_in(alpha=0.0):
            if alpha < 0.95:
                notif.attributes('-alpha', alpha)
                notif.after(10, lambda: fade_in(alpha + 0.1))
        
        def fade_out(alpha=0.95):
            if alpha > 0.05:
                notif.attributes('-alpha', alpha)
                notif.after(10, lambda: fade_out(alpha - 0.1))
            else:
                root.destroy()
        
        notif.after(0, fade_in)
        root.after(duration, fade_out)
        root.mainloop()
    except Exception as e:
        pass


def show_key_feedback_popup(key: str, pattern: str, action: str, accent_color: str = "#4CAF50"):
    """Show visual feedback overlay"""
    play_sound("success")
    try:
        root = tb.Window(themename="cyborg")
        root.withdraw()
        
        overlay = tb.Toplevel(root)
        overlay.overrideredirect(True)
        overlay.attributes('-topmost', True)
        overlay.attributes('-alpha', 0.0)
        
        width = 300
        height = 70
        screen_w = overlay.winfo_screenwidth()
        screen_h = overlay.winfo_screenheight()
        x = screen_w - width - 20
        y = screen_h - height - 80
        overlay.geometry(f"{width}x{height}+{x}+{y}")
        
        # Modern styling
        main_frame = tb.Frame(overlay, bootstyle="dark", padding=10)
        main_frame.pack(fill=BOTH, expand=YES)
        
        # Key Badge (Left)
        key_frame = tb.Frame(main_frame, bootstyle="secondary", padding=5)
        key_frame.pack(side=LEFT, padx=(0, 10))
        
        tb.Label(
            key_frame, text=f"{key.upper()}", font=("Consolas", 16, "bold"),
            bootstyle="inverse-secondary"
        ).pack()
        
        # Info (Right)
        right = tb.Frame(main_frame)
        right.pack(side=LEFT, fill=BOTH, expand=YES)
        
        tb.Label(
            right, text=pattern, font=("Segoe UI", 8),
            bootstyle="secondary"
        ).pack(anchor="w")
        
        tb.Label(
            right, text=action, font=("Segoe UI", 12, "bold"),
            bootstyle="success"
        ).pack(anchor="w")
        
        def fade_in(alpha=0.0):
            try:
                if alpha < 0.95:
                    overlay.attributes('-alpha', alpha)
                    overlay.after(15, lambda: fade_in(alpha + 0.15))
                else:
                    overlay.attributes('-alpha', 0.95)
            except: pass
        
        def fade_out(alpha=0.95):
            try:
                if alpha > 0.05:
                    overlay.attributes('-alpha', alpha)
                    overlay.after(20, lambda: fade_out(alpha - 0.12))
                else:
                    root.destroy()
            except: root.destroy()
        
        overlay.after(10, fade_in)
        root.after(1500, fade_out)
        
        root.mainloop()
    except:
        pass


def show_mode_popup(mode_name: str, duration: int = 2000):
    """Show a simple popup when switching modes"""
    play_sound("mode")
    try:
        root = tb.Window(themename="cyborg")
        root.withdraw()
        
        # Map modes to bootstyles
        styles = {
            "Development Mode": "success",
            "Git Mode": "danger",
            "AI Assistant Mode": "primary",
            "Script Mode": "info"
        }
        style = styles.get(mode_name, "light")
        
        popup = tb.Toplevel(root)
        popup.overrideredirect(True)
        popup.attributes('-topmost', True)
        popup.attributes('-alpha', 0.0)
        
        width = 300
        height = 80
        screen_w = popup.winfo_screenwidth()
        screen_h = popup.winfo_screenheight()
        x = screen_w - width - 20
        y = screen_h - height - 60
        popup.geometry(f"{width}x{height}+{x}+{y}")
        
        inner = tb.Frame(popup, bootstyle="dark", padding=15)
        inner.pack(fill=BOTH, expand=YES)
        
        tb.Label(inner, text="Switching Mode", font=("Segoe UI", 9), bootstyle="secondary").pack(anchor="w")
        tb.Label(inner, text=mode_name, font=("Segoe UI", 14, "bold"), bootstyle=style).pack(anchor="w")
        
        # Progress bar decoration
        tb.Progressbar(inner, bootstyle=style, value=100).pack(fill=X, pady=(5, 0))
        
        def fade_in(alpha=0.0):
            if alpha < 0.95:
                popup.attributes('-alpha', alpha)
                popup.after(15, lambda: fade_in(alpha + 0.15))
        
        def fade_out(alpha=0.95):
            if alpha > 0.05:
                popup.attributes('-alpha', alpha)
                popup.after(20, lambda: fade_out(alpha - 0.12))
            else:
                root.quit()
        
        popup.after(10, fade_in)
        root.after(duration, fade_out)
        root.mainloop()
    except:
        pass


def show_guide_popup(mode_name: str, guide_lines: list, is_notification: bool = False):
    """Show the full shortcut guide popup in this separate process"""
    try:
        root = tb.Window(themename="cyborg")
        root.withdraw()
        
        # Mode config
        mode_config = {
            "Development Mode": {"style": "success", "icon": "🚀", "tips": ["💡 Hold F9 to change project path", "⚡ Double tap F10 to select project"]},
            "Git Mode": {"style": "danger", "icon": "📦", "tips": ["💡 Hold F9 for git status", "🔄 Use F10 for push/pull"]},
            "AI Assistant Mode": {"style": "primary", "icon": "🤖", "tips": ["💡 Type query and press F9"]},
            "Script Mode": {"style": "info", "icon": "⚙️", "tips": ["💡 Run scripts with F9"]}
        }
        
        config = mode_config.get(mode_name, {"style": "light", "icon": "🎮", "tips": ["💡 Press F11 to switch mode"]})
        style = config["style"]
        icon = config["icon"]
        tips = config["tips"]
        
        # UI dimensions
        width = 380 if is_notification else 550
        # Increased height calculation to prevent footer cut-off
        height = 140 if is_notification else min(680, 200 + (len(guide_lines) * 45) + (len(tips) * 40))
        
        popup = tb.Toplevel(root)
        popup.overrideredirect(True)
        popup.attributes('-topmost', True)
        popup.attributes('-alpha', 0.0)
        
        screen_w = popup.winfo_screenwidth()
        screen_h = popup.winfo_screenheight()
        
        if is_notification:
            x = screen_w - width - 20
            y = screen_h - height - 60
        else:
            x = (screen_w - width) // 2
            y = (screen_h - height) // 2
            
        popup.geometry(f"{width}x{height}+{x}+{y}")
        
        # Main container
        main = tb.Frame(popup, bootstyle="secondary", padding=2) # Border effect
        main.pack(fill=BOTH, expand=YES)
        
        inner = tb.Frame(main, bootstyle="dark")
        inner.pack(fill=BOTH, expand=YES)
        
        # Header
        header = tb.Frame(inner, bootstyle=style, height=60, padding=15)
        header.pack(fill=X)
        header.pack_propagate(False)
        tb.Label(header, text=f"{icon} {mode_name}", font=("Segoe UI", 16, "bold"), bootstyle="inverse-"+style).pack()
        
        if not is_notification:
            # Shortcuts
            content = tb.Frame(inner, padding=20)
            content.pack(fill=BOTH, expand=YES)
            
            for item in guide_lines:
                row = tb.Frame(content, height=40)
                row.pack(fill=X, pady=2)
                row.pack_propagate(False)
                
                # Key
                tb.Label(
                    row, text=f" {item['key']} ", font=("Consolas", 11, "bold"), 
                    bootstyle=f"{style}-inverse"
                ).pack(side=LEFT)
                
                # Pattern
                tb.Label(
                    row, text=f" {item['pattern']}", font=("Segoe UI", 10), 
                    bootstyle="secondary"
                ).pack(side=LEFT, padx=10)
                
                # Action
                tb.Label(
                    row, text=item['action'], font=("Segoe UI", 11, "bold"), 
                    bootstyle="light"
                ).pack(side=RIGHT)
                
                tb.Separator(content).pack(fill=X, pady=2)
            
            # Tips
            if tips:
                tips_frame = tb.Frame(content, padding=(0, 10))
                tips_frame.pack(fill=X, pady=10)
                for tip in tips:
                    tb.Label(tips_frame, text=tip, font=("Segoe UI", 10, "italic"), bootstyle="warning").pack(fill=X)
            
            # Footer - Increased padding for safety
            footer = tb.Frame(inner, padding=10, bootstyle="secondary")
            footer.pack(fill=X, side=BOTTOM)
            
            tb.Label(footer, text="Press ESC or F12 to close", font=("Segoe UI", 9), bootstyle="inverse-secondary").pack(side=LEFT)
            
            def open_settings():
                import subprocess
                import sys
                from pathlib import Path
                
                # Launch settings asynchronously
                is_frozen = getattr(sys, 'frozen', False)
                if is_frozen:
                    subprocess.Popen([sys.executable, "settings"])
                else:
                    settings_script = Path(__file__).parent / "settings_dialog.py"
                    subprocess.Popen([sys.executable, str(settings_script)])
                
                # Close guide
                fade_out()

            tb.Button(footer, text="⚙️ Settings", command=open_settings, bootstyle="light-outline", padding=(10, 2)).pack(side=RIGHT)
        else:
             tb.Label(inner, text="Press F12 to view full guide", font=("Segoe UI", 12), justify="center").pack(expand=YES)
        
        def fade_in(alpha=0.0):
            if alpha < 0.98:
                popup.attributes('-alpha', alpha)
                popup.after(15, lambda: fade_in(alpha + 0.1))
            else:
                popup.attributes('-alpha', 0.98)
        
        def fade_out(alpha=0.98):
            if alpha > 0.05:
                popup.attributes('-alpha', alpha)
                popup.after(20, lambda: fade_out(alpha - 0.1))
            else:
                root.quit()
                root.destroy()
        
        popup.after(10, fade_in)
        popup.bind('<Escape>', lambda e: fade_out())
        popup.bind('<F12>', lambda e: fade_out())
        
        if is_notification:
            root.after(3000, fade_out)
        else:
            root.after(15000, fade_out)
            
        root.mainloop()
    except Exception as e:
        pass

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
    
    popup_type = sys.argv[1]
    
    if popup_type == "notification":
        data = json.loads(sys.argv[2])
        show_notification_popup(
            title=data.get("title", ""),
            message=data.get("message", ""),
            duration=data.get("duration", 2000)
        )
    
    elif popup_type == "key_feedback":
        data = json.loads(sys.argv[2])
        show_key_feedback_popup(
            key=data.get("key", ""),
            pattern=data.get("pattern", ""),
            action=data.get("action", ""),
            accent_color=data.get("accent_color", "#4CAF50")
        )
    
    elif popup_type == "guide":
        data = json.loads(sys.argv[2])
        show_guide_popup(
            mode_name=data.get("mode_name", ""),
            guide_lines=data.get("guide_lines", []),
            is_notification=data.get("is_notification", False)
        )
    
    elif popup_type == "mode":
        data = json.loads(sys.argv[2])
        show_mode_popup(
            mode_name=data.get("mode_name", ""),
            duration=data.get("duration", 2000)
        )
