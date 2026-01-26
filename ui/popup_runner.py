"""
Popup Runner - Runs popup windows in a separate process
This script is executed via subprocess to avoid tkinter threading issues
"""

import sys
import json
import tkinter as tk
import winsound
import time

def play_sound(sound_type="info"):
    """Play a subtle system sound"""
    try:
        if sound_type == "mode":
            # Subtle ascending beep for mode switch
            winsound.Beep(600, 50)
            winsound.Beep(800, 50)
        elif sound_type == "info":
            winsound.Beep(700, 100)
        elif sound_type == "success":
            winsound.Beep(800, 100)
            winsound.Beep(1000, 100)
        elif sound_type == "error":
            winsound.Beep(400, 200)
    except:
        pass

def show_notification_popup(title: str, message: str, duration: int = 2000):
    """Show a simple notification popup"""
    play_sound("info")
    try:
        root = tk.Tk()
        root.withdraw()
        
        notif = tk.Toplevel(root)
        notif.overrideredirect(True)
        notif.attributes('-topmost', True)
        notif.attributes('-alpha', 0.0)
        
        width = 320
        height = 90
        x = notif.winfo_screenwidth() - width - 20
        y = notif.winfo_screenheight() - height - 60
        notif.geometry(f"{width}x{height}+{x}+{y}")
        
        # GitHub Dark theme colors
        bg_color = "#161b22"
        border_color = "#30363d"
        text_primary = "#f0f6fc"
        text_secondary = "#8b949e"
        
        notif.configure(bg=border_color)
        
        inner = tk.Frame(notif, bg=bg_color, padx=15, pady=10)
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        
        tk.Label(
            inner, text=title, font=("Segoe UI", 11, "bold"),
            fg=text_primary, bg=bg_color
        ).pack(anchor="w")
        
        tk.Label(
            inner, text=message, font=("Segoe UI", 10),
            fg=text_secondary, bg=bg_color
        ).pack(anchor="w", pady=(5, 0))
        
        # Accent bar
        tk.Frame(inner, bg="#1f6feb", height=3).pack(fill="x", side="bottom", pady=(5, 0))

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
    except:
        pass


def show_key_feedback_popup(key: str, pattern: str, action: str, accent_color: str = "#4CAF50"):
    """Show visual feedback overlay"""
    play_sound("success")
    try:
        bg_color = "#1a1a2e"
        text_primary = "#ffffff"
        text_secondary = "#8b949e"
        
        root = tk.Tk()
        root.withdraw()
        
        overlay = tk.Toplevel(root)
        overlay.overrideredirect(True)
        overlay.attributes('-topmost', True)
        overlay.attributes('-alpha', 0.0)
        
        width = 280
        height = 60
        screen_w = overlay.winfo_screenwidth()
        screen_h = overlay.winfo_screenheight()
        x = screen_w - width - 20
        y = screen_h - height - 80
        overlay.geometry(f"{width}x{height}+{x}+{y}")
        
        overlay.configure(bg=bg_color)
        
        main = tk.Frame(overlay, bg=bg_color)
        main.pack(fill="both", expand=True, padx=8, pady=8)
        
        left = tk.Frame(main, bg=bg_color)
        left.pack(side="left", fill="y")
        
        key_badge = tk.Label(
            left, text=f" {key.upper()} ", font=("Consolas", 14, "bold"),
            fg=accent_color, bg="#2d333b", padx=10, pady=4
        )
        key_badge.pack(pady=8)
        
        right = tk.Frame(main, bg=bg_color)
        right.pack(side="left", fill="both", expand=True, padx=(10, 0))
        
        tk.Label(
            right, text=pattern, font=("Segoe UI", 9),
            fg=text_secondary, bg=bg_color, anchor="w"
        ).pack(anchor="w")
        
        tk.Label(
            right, text=action, font=("Segoe UI", 12, "bold"),
            fg=text_primary, bg=bg_color, anchor="w"
        ).pack(anchor="w")
        
        accent_bar = tk.Frame(overlay, bg=accent_color, width=3)
        accent_bar.place(x=0, y=0, relheight=1)
        
        def fade_in(alpha=0.0):
            try:
                if alpha < 0.95:
                    overlay.attributes('-alpha', alpha)
                    overlay.after(15, lambda: fade_in(alpha + 0.15))
                else:
                    overlay.attributes('-alpha', 0.95)
            except:
                pass
        
        def fade_out(alpha=0.95):
            try:
                if alpha > 0.05:
                    overlay.attributes('-alpha', alpha)
                    overlay.after(20, lambda: fade_out(alpha - 0.12))
                else:
                    root.destroy()
            except:
                try:
                    root.destroy()
                except:
                    pass
        
        overlay.after(10, fade_in)
        root.after(1500, fade_out)
        
        root.mainloop()
    except:
        pass


def show_mode_popup(mode_name: str, duration: int = 2000):
    """Show a simple popup when switching modes"""
    play_sound("mode")
    try:
        root = tk.Tk()
        root.withdraw()
        
        # Colors
        bg_color = "#161b22"
        text_color = "#f0f6fc"
        accent_color = "#238636"
        
        # Mode config for colors
        mode_colors = {
            "Development Mode": "#238636",
            "Git Mode": "#f78166",
            "AI Assistant Mode": "#a371f7",
            "Script Mode": "#58a6ff"
        }
        accent_color = mode_colors.get(mode_name, "#238636")
        
        popup = tk.Toplevel(root)
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
        popup.configure(bg="#30363d")
        
        inner = tk.Frame(popup, bg=bg_color)
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        
        tk.Label(inner, text="Switching Mode", font=("Segoe UI", 9), fg="#8b949e", bg=bg_color).pack(pady=(10, 0))
        tk.Label(inner, text=mode_name, font=("Segoe UI", 14, "bold"), fg=text_color, bg=bg_color).pack()
        
        accent_bar = tk.Frame(inner, bg=accent_color, height=3)
        accent_bar.pack(fill="x", side="bottom")
        
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
        root = tk.Tk()
        root.withdraw()
        
        # Colors - GitHub Dark Theme
        bg_dark = "#0d1117"
        bg_card = "#161b22"
        bg_row_alt = "#1c2129"
        text_primary = "#f0f6fc"
        text_secondary = "#8b949e"
        border_color = "#30363d"
        
        # Mode config for colors and icons
        mode_config = {
            "Development Mode": {"color": "#238636", "icon": "🚀", "tips": ["💡 กดค้าง F9 เพื่อเปลี่ยน project path", "⚡ กด F10 สองครั้งเร็วๆ เพื่อเลือก project"]},
            "Git Mode": {"color": "#f78166", "icon": "📦", "tips": ["💡 กดค้าง F9 เพื่อดู git status", "🔄 ใช้ F10 สำหรับ push และ pull"]},
            "AI Assistant Mode": {"color": "#a371f7", "icon": "🤖", "tips": ["💡 พิมพ์คำถามแล้วกด F9 เพื่อถาม AI"]},
            "Script Mode": {"color": "#58a6ff", "icon": "⚙️", "tips": ["💡 รัน script ได้ทันทีด้วย F9"]}
        }
        
        config = mode_config.get(mode_name, {"color": "#238636", "icon": "🎮", "tips": ["💡 กด F11 เพื่อเปลี่ยน Mode"]})
        accent_color = config["color"]
        mode_icon = config["icon"]
        tips = config["tips"]
        
        # UI dimensions
        width = 350 if is_notification else 500
        height = 120 if is_notification else min(600, 150 + (len(guide_lines) * 40) + (len(tips) * 35))
        
        popup = tk.Toplevel(root)
        popup.overrideredirect(True)
        popup.attributes('-topmost', True)
        popup.attributes('-alpha', 0.0)
        
        # Position at bottom-right if notification, center if guide
        screen_w = popup.winfo_screenwidth()
        screen_h = popup.winfo_screenheight()
        
        if is_notification:
            x = screen_w - width - 20
            y = screen_h - height - 60
        else:
            x = (screen_w - width) // 2
            y = (screen_h - height) // 2
            
        popup.geometry(f"{width}x{height}+{x}+{y}")
        popup.configure(bg=border_color)
        
        inner = tk.Frame(popup, bg=bg_dark)
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        
        # Header
        header = tk.Frame(inner, bg=accent_color, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text=f"{mode_icon} {mode_name}", font=("Segoe UI", 14, "bold"), fg="white", bg=accent_color).pack(pady=15)
        
        if not is_notification:
            # Content Area (Shortcuts)
            content = tk.Frame(inner, bg=bg_dark, padx=15, pady=10)
            content.pack(fill="both", expand=True)
            
            for i, item in enumerate(guide_lines):
                row_bg = bg_row_alt if i % 2 == 1 else bg_card
                row = tk.Frame(content, bg=row_bg, height=38)
                row.pack(fill="x", pady=1)
                row.pack_propagate(False)
                
                tk.Label(row, text=f" {item['key']} ", font=("Consolas", 10, "bold"), fg=accent_color, bg="#2d333b").pack(side="left", padx=10)
                tk.Label(row, text=item['pattern'], font=("Segoe UI", 9), fg=text_secondary, bg=row_bg).pack(side="left")
                tk.Label(row, text=item['action'], font=("Segoe UI", 10, "bold"), fg=text_primary, bg=row_bg).pack(side="right", padx=10)
            
            # Tips
            if tips:
                tips_frame = tk.Frame(content, bg=bg_dark, pady=10)
                tips_frame.pack(fill="x")
                for tip in tips:
                    tk.Label(tips_frame, text=tip, font=("Segoe UI", 9), fg=text_primary, bg=bg_dark, anchor="w").pack(fill="x", pady=2)
            
            # Footer
            footer = tk.Frame(inner, bg=bg_card, height=30)
            footer.pack(fill="x", side="bottom")
            tk.Label(footer, text="กด ESC หรือ F12 เพื่อปิด", font=("Segoe UI", 8), fg=text_secondary, bg=bg_card).pack(pady=5)
        else:
            tk.Label(inner, text="กด F12 เพื่อดู guide", font=("Segoe UI", 10), fg=text_secondary, bg=bg_dark).pack(pady=10)
        
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
        with open("popup_error.log", "a") as f:
            f.write(f"Error: {str(e)}\n")

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
