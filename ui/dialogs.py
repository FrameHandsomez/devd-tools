"""
Dialog utilities using tkinter
Provides input dialogs for features
"""

import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from typing import Optional, Tuple
from utils.logger import get_logger

logger = get_logger(__name__)


def _create_root() -> tk.Tk:
    """Create a hidden root window for dialogs"""
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    return root


def ask_yes_no(title: str, message: str) -> bool:
    """Show Yes/No confirmation dialog"""
    root = _create_root()
    try:
        result = messagebox.askyesno(title, message, parent=root)
        root.destroy()
        return result
    except Exception as e:
        logger.error(f"Error checking yes/no: {e}")
        if root:
            root.destroy()
        return False


def ask_git_clone_info(default_path: str = "C:\\Projects") -> Optional[Tuple[str, str]]:
    """
    Ask user for Git URL and clone path.
    
    Returns:
        Tuple of (git_url, clone_path) or None if cancelled
    """
    root = _create_root()
    
    try:
        # Create custom dialog
        dialog = tk.Toplevel(root)
        dialog.title("Clone Project")
        dialog.geometry("500x180")
        dialog.resizable(False, False)
        dialog.attributes('-topmost', True)
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 500) // 2
        y = (dialog.winfo_screenheight() - 180) // 2
        dialog.geometry(f"+{x}+{y}")
        
        result = {"git_url": None, "path": None}
        
        # Git URL
        tk.Label(dialog, text="Git Repository URL:", font=("Segoe UI", 10)).pack(anchor="w", padx=20, pady=(15, 5))
        url_entry = tk.Entry(dialog, width=60, font=("Consolas", 10))
        url_entry.pack(padx=20)
        url_entry.focus_set()
        
        # Clone path
        tk.Label(dialog, text="Clone to folder:", font=("Segoe UI", 10)).pack(anchor="w", padx=20, pady=(10, 5))
        
        path_frame = tk.Frame(dialog)
        path_frame.pack(padx=20, fill="x")
        
        path_entry = tk.Entry(path_frame, width=50, font=("Consolas", 10))
        path_entry.pack(side="left")
        path_entry.insert(0, default_path)
        
        def browse_folder():
            folder = filedialog.askdirectory(initialdir=default_path)
            if folder:
                path_entry.delete(0, tk.END)
                path_entry.insert(0, folder)
        
        browse_btn = tk.Button(path_frame, text="Browse...", command=browse_folder)
        browse_btn.pack(side="left", padx=5)
        
        # Buttons
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=15)
        
        def on_clone():
            url = url_entry.get().strip()
            path = path_entry.get().strip()
            
            if not url:
                messagebox.showerror("Error", "Please enter a Git URL")
                return
            
            result["git_url"] = url
            result["path"] = path
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        clone_btn = tk.Button(btn_frame, text="Clone", command=on_clone, width=10, bg="#4CAF50", fg="white")
        clone_btn.pack(side="left", padx=5)
        
        cancel_btn = tk.Button(btn_frame, text="Cancel", command=on_cancel, width=10)
        cancel_btn.pack(side="left", padx=5)
        
        # Handle Enter key
        dialog.bind('<Return>', lambda e: on_clone())
        dialog.bind('<Escape>', lambda e: on_cancel())
        
        # Wait for dialog to close
        dialog.wait_window()
        
        if result["git_url"]:
            return (result["git_url"], result["path"])
        return None
        
    except Exception as e:
        logger.error(f"Error in clone dialog: {e}")
        return None
    finally:
        root.destroy()


def ask_folder_path(title: str = "Select Folder") -> Optional[str]:
    """
    Ask user to select a folder.
    
    Returns:
        Selected folder path or None if cancelled
    """
    root = _create_root()
    
    try:
        folder = filedialog.askdirectory(title=title)
        return folder if folder else None
    finally:
        root.destroy()


def ask_choice(title: str, message: str, choices: list[str]) -> Optional[int]:
    """
    Ask user to choose from a list of options.
    
    Returns:
        Index of selected choice or None if cancelled
    """
    root = _create_root()
    
    try:
        dialog = tk.Toplevel(root)
        dialog.title(title)
        dialog.geometry("350x300")
        dialog.resizable(False, False)
        dialog.attributes('-topmost', True)
        
        # Center
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 350) // 2
        y = (dialog.winfo_screenheight() - 300) // 2
        dialog.geometry(f"+{x}+{y}")
        
        result = {"index": None}
        
        tk.Label(dialog, text=message, font=("Segoe UI", 10)).pack(pady=10)
        
        listbox = tk.Listbox(dialog, font=("Segoe UI", 10), height=8, width=40)
        listbox.pack(padx=20, pady=5)
        
        for choice in choices:
            listbox.insert(tk.END, choice)
        
        listbox.select_set(0)
        
        def on_select():
            selection = listbox.curselection()
            if selection:
                result["index"] = selection[0]
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Select", command=on_select, width=10).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Cancel", command=on_cancel, width=10).pack(side="left", padx=5)
        
        dialog.bind('<Return>', lambda e: on_select())
        dialog.bind('<Escape>', lambda e: on_cancel())
        dialog.bind('<Double-1>', lambda e: on_select())
        
        dialog.wait_window()
        
        return result["index"]
        
    except Exception as e:
        logger.error(f"Error in choice dialog: {e}")
        return None
    finally:
        root.destroy()


def show_notification(title: str, message: str, duration: int = 3000):
    """
    Show a simple notification popup.
    
    Args:
        title: Notification title
        message: Notification message
        duration: Duration in milliseconds before auto-close
    """
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        # Create notification window
        notif = tk.Toplevel(root)
        notif.overrideredirect(True)
        notif.attributes('-topmost', True)
        
        # Position at bottom-right
        width = 300
        height = 80
        x = notif.winfo_screenwidth() - width - 20
        y = notif.winfo_screenheight() - height - 60
        notif.geometry(f"{width}x{height}+{x}+{y}")
        
        # Style
        notif.configure(bg="#333333")
        
        frame = tk.Frame(notif, bg="#333333", padx=15, pady=10)
        frame.pack(fill="both", expand=True)
        
        tk.Label(
            frame, 
            text=title, 
            font=("Segoe UI", 11, "bold"),
            fg="white",
            bg="#333333"
        ).pack(anchor="w")
        
        tk.Label(
            frame,
            text=message,
            font=("Segoe UI", 10),
            fg="#CCCCCC",
            bg="#333333"
        ).pack(anchor="w", pady=(5, 0))
        
        # Safe close function
        def safe_close():
            try:
                root.quit()
                root.destroy()
            except:
                pass
        
        # Auto-close
        root.after(duration, safe_close)
        
        # Keep the notification visible
        root.mainloop()
        
    except Exception as e:
        logger.error(f"Error showing notification: {e}")


def show_mode_switch_notification(
    mode_name: str, 
    guide_lines: list[dict],
    accent_color: str = "#4CAF50",
    duration: int = 5000
):
    """
    Show a premium mode switch notification with shortcut guide.
    
    Args:
        mode_name: Name of the new mode
        guide_lines: List of dicts with 'key', 'pattern', 'action' keys
        accent_color: Color for the mode header
        duration: Duration in milliseconds before auto-close
    """
    root = _create_root()
    
    try:
        # Colors
        bg_dark = "#0d1117"
        bg_card = "#161b22"
        bg_row_alt = "#1c2129"
        text_primary = "#f0f6fc"
        text_secondary = "#8b949e"
        border_color = "#30363d"
        
        # Calculate dimensions
        num_items = min(len(guide_lines), 6)
        row_height = 36
        header_height = 50
        footer_height = 45
        padding = 16
        height = header_height + (num_items * row_height) + footer_height + padding
        width = 420
        
        # Create notification window
        notif = tk.Toplevel(root)
        notif.overrideredirect(True)
        notif.attributes('-topmost', True)
        notif.attributes('-alpha', 0.0)  # Start invisible for fade in
        
        # Position at bottom-right
        screen_w = notif.winfo_screenwidth()
        screen_h = notif.winfo_screenheight()
        x = screen_w - width - 24
        y = screen_h - height - 70
        notif.geometry(f"{width}x{height}+{x}+{y}")
        
        # Main container with border effect
        notif.configure(bg=border_color)
        
        # Inner container (simulates border)
        inner = tk.Frame(notif, bg=bg_dark)
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        
        # Header with gradient effect
        header = tk.Frame(inner, bg=accent_color, height=header_height)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        # Mode icon and name
        header_content = tk.Frame(header, bg=accent_color)
        header_content.pack(expand=True)
        
        tk.Label(
            header_content,
            text=f"🎯 {mode_name}",
            font=("Segoe UI", 13, "bold"),
            fg="white",
            bg=accent_color
        ).pack(pady=12)
        
        # Content area
        content = tk.Frame(inner, bg=bg_dark)
        content.pack(fill="both", expand=True, padx=12, pady=8)
        
        # Table header
        table_header = tk.Frame(content, bg=bg_dark)
        table_header.pack(fill="x", pady=(0, 6))
        
        tk.Label(
            table_header,
            text="SHORTCUT",
            font=("Segoe UI", 8, "bold"),
            fg=text_secondary,
            bg=bg_dark
        ).pack(side="left")
        
        tk.Label(
            table_header,
            text="ACTION",
            font=("Segoe UI", 8, "bold"),
            fg=text_secondary,
            bg=bg_dark
        ).pack(side="right")
        
        # Show shortcuts in styled rows
        for i, item in enumerate(guide_lines[:6]):
            row_bg = bg_row_alt if i % 2 == 1 else bg_card
            
            row = tk.Frame(content, bg=row_bg, height=row_height)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)
            
            row_inner = tk.Frame(row, bg=row_bg)
            row_inner.pack(fill="both", expand=True, padx=8)
            
            # Left side: Key + Pattern
            left = tk.Frame(row_inner, bg=row_bg)
            left.pack(side="left", fill="y")
            
            # Key badge with modern style
            key_badge = tk.Label(
                left,
                text=f" {item['key']} ",
                font=("Consolas", 10, "bold"),
                fg=accent_color,
                bg="#2d333b",
                padx=6,
                pady=2
            )
            key_badge.pack(side="left", pady=6)
            
            # Pattern in subtle style
            pattern_label = tk.Label(
                left,
                text=f" {item['pattern']}",
                font=("Segoe UI", 9),
                fg=text_secondary,
                bg=row_bg
            )
            pattern_label.pack(side="left", padx=6, pady=6)
            
            # Right side: Action
            action_label = tk.Label(
                row_inner,
                text=item['action'],
                font=("Segoe UI", 10),
                fg=text_primary,
                bg=row_bg
            )
            action_label.pack(side="right", pady=6)
        
        # Footer with F12 hint
        footer = tk.Frame(inner, bg=bg_dark, height=footer_height)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)
        
        # Separator line
        separator = tk.Frame(footer, bg=border_color, height=1)
        separator.pack(fill="x")
        
        # Footer content
        footer_content = tk.Frame(footer, bg=bg_dark)
        footer_content.pack(expand=True)
        
        hint_frame = tk.Frame(footer_content, bg=bg_dark)
        hint_frame.pack(pady=10)
        
        tk.Label(
            hint_frame,
            text="💡 กด ",
            font=("Segoe UI", 9),
            fg=text_secondary,
            bg=bg_dark
        ).pack(side="left")
        
        tk.Label(
            hint_frame,
            text=" F12 ",
            font=("Consolas", 9, "bold"),
            fg=accent_color,
            bg="#2d333b",
            padx=4
        ).pack(side="left")
        
        tk.Label(
            hint_frame,
            text=" เพื่อดู guide แบบละเอียด",
            font=("Segoe UI", 9),
            fg=text_secondary,
            bg=bg_dark
        ).pack(side="left")
        
        # Fade in animation
        def fade_in(alpha=0.0):
            try:
                if alpha < 0.95:
                    notif.attributes('-alpha', alpha)
                    notif.after(20, lambda: fade_in(alpha + 0.1))
                else:
                    notif.attributes('-alpha', 0.95)
            except:
                pass
        
        # Safe close function
        def safe_close():
            try:
                root.quit()
                root.destroy()
            except:
                pass
        
        # Fade out animation
        def fade_out(alpha=0.95):
            try:
                if alpha > 0.05:
                    notif.attributes('-alpha', alpha)
                    notif.after(25, lambda: fade_out(alpha - 0.1))
                else:
                    safe_close()
            except:
                safe_close()
        
        # Start fade in
        notif.after(10, fade_in)
        
        # Schedule fade out before close
        root.after(duration - 300, fade_out)
        
        # Click to close
        def close_on_click(e):
            fade_out()
        
        notif.bind('<Button-1>', close_on_click)
        
        root.mainloop()
        
    except Exception as e:
        logger.error(f"Error showing mode switch notification: {e}")


def ask_commit_message(title: str = "Git Commit") -> Optional[str]:
    """
    Ask user for a commit message.
    
    Returns:
        Commit message or None if cancelled
    """
    root = _create_root()
    
    try:
        dialog = tk.Toplevel(root)
        dialog.title(title)
        dialog.geometry("450x150")
        dialog.resizable(False, False)
        dialog.attributes('-topmost', True)
        
        # Center
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 450) // 2
        y = (dialog.winfo_screenheight() - 150) // 2
        dialog.geometry(f"+{x}+{y}")
        
        result = {"message": None}
        
        tk.Label(dialog, text="Enter commit message:", font=("Segoe UI", 10)).pack(anchor="w", padx=20, pady=(15, 5))
        
        msg_entry = tk.Entry(dialog, width=55, font=("Consolas", 10))
        msg_entry.pack(padx=20)
        msg_entry.focus_set()
        
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=15)
        
        def on_commit():
            msg = msg_entry.get().strip()
            if not msg:
                messagebox.showerror("Error", "Please enter a commit message")
                return
            result["message"] = msg
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        tk.Button(btn_frame, text="Commit", command=on_commit, width=10, bg="#4CAF50", fg="white").pack(side="left", padx=5)
        tk.Button(btn_frame, text="Cancel", command=on_cancel, width=10).pack(side="left", padx=5)
        
        dialog.bind('<Return>', lambda e: on_commit())
        dialog.bind('<Escape>', lambda e: on_cancel())
        
        dialog.wait_window()
        
        return result["message"]
        
    except Exception as e:
        logger.error(f"Error in commit message dialog: {e}")
        return None
    finally:
        root.destroy()


def show_git_output(title: str, output: str, is_error: bool = False):
    """
    Show git command output in a scrollable dialog.
    
    Args:
        title: Dialog title
        output: Text output to display
        is_error: Whether this is an error output (red text)
    """
    root = _create_root()
    
    try:
        dialog = tk.Toplevel(root)
        dialog.title(title)
        dialog.geometry("600x400")
        dialog.resizable(True, True)
        dialog.attributes('-topmost', True)
        
        # Center
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 600) // 2
        y = (dialog.winfo_screenheight() - 400) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Title label
        title_color = "#ff6b6b" if is_error else "#4CAF50"
        tk.Label(dialog, text=title, font=("Segoe UI", 12, "bold"), fg=title_color).pack(pady=(10, 5))
        
        # Scrollable text widget
        text_frame = tk.Frame(dialog)
        text_frame.pack(fill="both", expand=True, padx=15, pady=5)
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")
        
        text_widget = tk.Text(
            text_frame,
            wrap="word",
            font=("Consolas", 10),
            bg="#1e1e1e",
            fg="#d4d4d4",
            yscrollcommand=scrollbar.set,
            padx=10,
            pady=10
        )
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=text_widget.yview)
        
        text_widget.insert("1.0", output)
        text_widget.config(state="disabled")  # Read-only
        
        # Close button
        tk.Button(dialog, text="Close", command=dialog.destroy, width=10).pack(pady=10)
        
        dialog.bind('<Escape>', lambda e: dialog.destroy())
        dialog.bind('<Return>', lambda e: dialog.destroy())
        
        dialog.wait_window()
        
    except Exception as e:
        logger.error(f"Error showing git output: {e}")
    finally:
        root.destroy()


def ask_project_selection(
    projects: list[dict],
    title: str = "Select Project",
    allow_add: bool = True,
    allow_remove: bool = True
) -> dict | None:
    """
    Show project selection dialog with list of saved projects.
    
    Args:
        projects: List of project dicts with 'name' and 'path' keys
        title: Dialog title
        allow_add: Show "Add New" button
        allow_remove: Show "Remove" button
    
    Returns:
        Dict with action and data:
        - {"action": "select", "project": {...}}
        - {"action": "add", "path": "..."}
        - {"action": "remove", "project": {...}}
        - None if cancelled
    """
    root = _create_root()
    
    try:
        dialog = tk.Toplevel(root)
        dialog.title(title)
        dialog.geometry("450x380")
        dialog.resizable(False, False)
        dialog.attributes('-topmost', True)
        dialog.configure(bg="#1a1a2e")
        
        # Center
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 450) // 2
        y = (dialog.winfo_screenheight() - 380) // 2
        dialog.geometry(f"+{x}+{y}")
        
        result = {"action": None, "data": None}
        
        # Header
        header = tk.Frame(dialog, bg="#4CAF50", height=45)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text=f"📁 {title}",
            font=("Segoe UI", 12, "bold"),
            fg="white",
            bg="#4CAF50"
        ).pack(pady=10)
        
        # Project list
        list_frame = tk.Frame(dialog, bg="#1a1a2e")
        list_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        if not projects:
            tk.Label(
                list_frame,
                text="ยังไม่มี project\nกด 'Add New' เพื่อเพิ่ม",
                font=("Segoe UI", 11),
                fg="#888888",
                bg="#1a1a2e",
                justify="center"
            ).pack(pady=40)
            listbox = None
        else:
            # Scrollbar
            scrollbar = tk.Scrollbar(list_frame)
            scrollbar.pack(side="right", fill="y")
            
            listbox = tk.Listbox(
                list_frame,
                font=("Segoe UI", 10),
                bg="#2a2a4e",
                fg="white",
                selectbackground="#4CAF50",
                selectforeground="white",
                height=10,
                yscrollcommand=scrollbar.set
            )
            listbox.pack(fill="both", expand=True)
            scrollbar.config(command=listbox.yview)
            
            for p in projects:
                listbox.insert(tk.END, f"  {p['name']}  ({p['path']})")
            
            if projects:
                listbox.select_set(0)
        
        # Buttons
        btn_frame = tk.Frame(dialog, bg="#1a1a2e")
        btn_frame.pack(pady=10)
        
        def on_select():
            if listbox and listbox.curselection():
                idx = listbox.curselection()[0]
                result["action"] = "select"
                result["data"] = projects[idx]
            dialog.destroy()
        
        def on_add():
            dialog.destroy()
            folder = filedialog.askdirectory(title="Select project folder")
            if folder:
                result["action"] = "add"
                result["data"] = folder
        
        def on_remove():
            if listbox and listbox.curselection():
                idx = listbox.curselection()[0]
                result["action"] = "remove"
                result["data"] = projects[idx]
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        # Select button
        if projects:
            tk.Button(
                btn_frame, text="▶ Run", command=on_select,
                width=10, bg="#4CAF50", fg="white", font=("Segoe UI", 10)
            ).pack(side="left", padx=5)
        
        # Add button
        if allow_add:
            tk.Button(
                btn_frame, text="➕ Add", command=on_add,
                width=10, bg="#2196F3", fg="white", font=("Segoe UI", 10)
            ).pack(side="left", padx=5)
        
        # Remove button
        if allow_remove and projects:
            tk.Button(
                btn_frame, text="🗑️ Remove", command=on_remove,
                width=10, bg="#ff6b6b", fg="white", font=("Segoe UI", 10)
            ).pack(side="left", padx=5)
        
        # Cancel button
        tk.Button(
            btn_frame, text="Cancel", command=on_cancel,
            width=10, font=("Segoe UI", 10)
        ).pack(side="left", padx=5)
        
        # Bindings
        dialog.bind('<Return>', lambda e: on_select())
        dialog.bind('<Escape>', lambda e: on_cancel())
        if listbox:
            listbox.bind('<Double-1>', lambda e: on_select())
        
        dialog.wait_window()
        
        if result["action"]:
            return {"action": result["action"], "project" if result["action"] != "add" else "path": result["data"]}
        return None
        
    except Exception as e:
        logger.error(f"Error in project selection dialog: {e}")
        return None
    finally:
        root.destroy()

