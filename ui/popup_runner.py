"""
Popup Runner - Runs popup windows in a separate process
This script is executed via subprocess to avoid tkinter threading issues
"""

import sys
import json
import tkinter as tk


def show_notification_popup(title: str, message: str, duration: int = 2000):
    """Show a simple notification popup"""
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        notif = tk.Toplevel(root)
        notif.overrideredirect(True)
        notif.attributes('-topmost', True)
        
        width = 300
        height = 80
        x = notif.winfo_screenwidth() - width - 20
        y = notif.winfo_screenheight() - height - 60
        notif.geometry(f"{width}x{height}+{x}+{y}")
        
        notif.configure(bg="#333333")
        
        frame = tk.Frame(notif, bg="#333333", padx=15, pady=10)
        frame.pack(fill="both", expand=True)
        
        tk.Label(
            frame, text=title, font=("Segoe UI", 11, "bold"),
            fg="white", bg="#333333"
        ).pack(anchor="w")
        
        tk.Label(
            frame, text=message, font=("Segoe UI", 10),
            fg="#CCCCCC", bg="#333333"
        ).pack(anchor="w", pady=(5, 0))
        
        def close():
            root.quit()
            root.destroy()
        
        root.after(duration, close)
        root.mainloop()
    except:
        pass


def show_key_feedback_popup(key: str, pattern: str, action: str, accent_color: str = "#4CAF50"):
    """Show visual feedback overlay"""
    try:
        bg_color = "#1a1a2e"
        text_primary = "#ffffff"
        text_secondary = "#8b949e"
        
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
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
                    root.quit()
                    root.destroy()
            except:
                try:
                    root.quit()
                    root.destroy()
                except:
                    pass
        
        overlay.after(10, fade_in)
        root.after(1500, fade_out)
        
        root.mainloop()
    except:
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
