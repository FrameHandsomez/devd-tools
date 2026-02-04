"""
Dialog utilities using ttkbootstrap
Provides modern input dialogs for features
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from typing import Optional, Tuple
import sys
import os

# Add project root to sys.path if running as script
if __name__ == "__main__":
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    import json

from utils.logger import get_logger

logger = get_logger(__name__)


def _create_root() -> tb.Window:
    """Create a hidden root window for dialogs"""
    # Use 'cyborg' for a cool dark theme
    root = tb.Window(themename="cyborg")
    root.withdraw()
    root.attributes('-topmost', True)
    return root


def ask_yes_no(title: str, message: str) -> bool:
    """Show Yes/No confirmation dialog"""
    root = _create_root()
    try:
        # standard messagebox is stil fine, but we can make a custom one if needed.
        # tb.dialogs.Messagebox is available in newer ttkbootstrap
        try:
            from ttkbootstrap.dialogs import Messagebox
            result = Messagebox.yesno(message, title, parent=root) == 'Yes'
        except ImportError:
            result = messagebox.askyesno(title, message, parent=root)
            
        root.destroy()
        return result
    except Exception as e:
        logger.error(f"Error checking yes/no: {e}")
        if root:
            root.destroy()
        return False


def ask_git_clone_info(default_path: str = "C:\\Projects") -> Optional[Tuple[str, str]]:
    """Ask user for Git URL and clone path."""
    root = _create_root()
    
    try:
        dialog = tb.Toplevel(root)
        dialog.title("Clone Project")
        dialog.geometry("600x220")
        dialog.resizable(False, False)
        dialog.attributes('-topmost', True)
        
        # Center
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 600) // 2
        y = (dialog.winfo_screenheight() - 220) // 2
        dialog.geometry(f"+{x}+{y}")
        
        result = {"git_url": None, "path": None}
        
        main_frame = tb.Frame(dialog, padding=20)
        main_frame.pack(fill=BOTH, expand=YES)
        
        # Git URL
        tb.Label(main_frame, text="Git Repository URL:", font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 5))
        url_entry = tb.Entry(main_frame, width=60, font=("Consolas", 10))
        url_entry.pack(fill=X, pady=(0, 15))
        url_entry.focus_set()
        
        # Clone path
        tb.Label(main_frame, text="Clone to folder:", font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 5))
        
        path_frame = tb.Frame(main_frame)
        path_frame.pack(fill=X)
        
        path_entry = tb.Entry(path_frame, font=("Consolas", 10))
        path_entry.pack(side=LEFT, fill=X, expand=YES)
        path_entry.insert(0, default_path)
        
        def browse_folder():
            folder = filedialog.askdirectory(initialdir=default_path)
            if folder:
                path_entry.delete(0, END)
                path_entry.insert(0, folder)
        
        browse_btn = tb.Button(path_frame, text="Browse", command=browse_folder, bootstyle=OUTLINE)
        browse_btn.pack(side=LEFT, padx=(10, 0))
        
        # Buttons
        btn_frame = tb.Frame(main_frame)
        btn_frame.pack(pady=(20, 0), anchor="e")
        
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
        
        tb.Button(btn_frame, text="Cancel", command=on_cancel, bootstyle="secondary-outline").pack(side=LEFT, padx=(0, 10))
        tb.Button(btn_frame, text="Clone Project", command=on_clone, bootstyle="success").pack(side=LEFT)
        
        dialog.bind('<Return>', lambda e: on_clone())
        dialog.bind('<Escape>', lambda e: on_cancel())
        
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
    root = _create_root()
    try:
        folder = filedialog.askdirectory(title=title)
        return folder if folder else None
    finally:
        root.destroy()


def ask_choice(title: str, message: str, choices: list[str]) -> Optional[int]:
    """Ask user to choose from a list of options."""
    # For single-process dialogs, use root directly
    root = tb.Window(themename="cyborg")
    root.title(title)
    root.geometry("400x350")
    root.resizable(False, False)
    root.attributes('-topmost', True)
    
    # Center
    root.update_idletasks()
    x = (root.winfo_screenwidth() - 400) // 2
    y = (root.winfo_screenheight() - 350) // 2
    root.geometry(f"+{x}+{y}")
    
    try:
        result = {"index": None}
        
        main_frame = tb.Frame(root, padding=20)
        main_frame.pack(fill=BOTH, expand=YES)
        
        tb.Label(main_frame, text=message, font=("Segoe UI", 11)).pack(anchor="w", pady=(0, 10))
        
        if len(choices) <= 8:
            # Button list style
            # Manual scrollable frame using Canvas for compatibility
            canvas = tb.Canvas(main_frame, bd=0, highlightthickness=0)
            scrollbar = tb.Scrollbar(main_frame, command=canvas.yview)
            scroll_frame = tb.Frame(canvas)
            
            scroll_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scroll_frame, anchor="nw", width=360)
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side=LEFT, fill=BOTH, expand=YES)
            scrollbar.pack(side=RIGHT, fill=Y)
            
            # Enable Mouse Wheel Scrolling
            def _on_mousewheel(event):
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            
            for i, choice in enumerate(choices):
                style = "primary-outline" if i == 0 else "secondary-outline"
                if "Delete" in choice or "Remove" in choice or "Discard" in choice:
                    style = "danger-outline"
                elif "Confirm" in choice or "Success" in choice or "Commit" in choice:
                    style = "success-outline"
                
                btn = tb.Button(
                    scroll_frame, 
                    text=choice, 
                    command=lambda idx=i: [result.update({"index": idx}), root.destroy()],
                    bootstyle=style,
                    width=30
                )
                btn.pack(fill=X, pady=2)
                
                # Bind numbers
                if i < 9:
                    root.bind(str(i+1), lambda e, idx=i: [result.update({"index": idx}), root.destroy()])
            
        else:
            # Fallback to Listbox for many items
            list_frame = tb.Frame(main_frame)
            list_frame.pack(fill=BOTH, expand=YES)
            
            scrollbar = tb.Scrollbar(list_frame)
            scrollbar.pack(side=RIGHT, fill=Y)
            
            listbox = tk.Listbox(
                list_frame, font=("Segoe UI", 10),
                bg="#1a1a1a", fg="#ffffff", selectbackground="#238636",
                relief=FLAT, borderwidth=0,
                yscrollcommand=scrollbar.set
            )
            listbox.pack(fill=BOTH, expand=YES)
            scrollbar.config(command=listbox.yview)
            
            for choice in choices:
                listbox.insert(END, choice)
            listbox.select_set(0)
            
            def on_select():
                if listbox.curselection():
                    result["index"] = listbox.curselection()[0]
                root.destroy()
            
            tb.Button(main_frame, text="Select", command=on_select, bootstyle="primary").pack(fill=X, pady=(15, 0))
            
            root.bind('<Return>', lambda e: on_select())
            root.bind('<Double-1>', lambda e: on_select())

        root.bind('<Escape>', lambda e: root.destroy())
        
        # Important: Mainloop for root window interaction
        root.mainloop()
        
        return result["index"]
        
    except Exception as e:
        logger.error(f"Error in choice dialog: {e}")
        import sys
        print(f"Dialog Error: {e}", file=sys.stderr)
        return None
    finally:
        # Unbind global mousewheel to avoid side effects
        try:
             root.unbind_all("<MouseWheel>")
        except:
             pass
             
        # root.destroy() is usually called by the triggers above, but if exception happens:
        try:
            if 'root' in locals() and root.winfo_exists():
                root.destroy()
        except:
            pass


def show_notification(title: str, message: str, duration: int = 3000):
    """Show a simple notification popup."""
    # Create root to hold the process
    root = _create_root()
    try:
        from ttkbootstrap.toast import ToastNotification
        toast = ToastNotification(
            title=title,
            message=message,
            duration=duration,
            bootstyle="dark",
            position=(None, None, 'sw') # bottom-right
        )
        toast.show_toast()
        
        # Keep process alive until toast finishes (duration is in ms)
        # Add a small buffer (1000ms) to ensure fade out completes
        root.after(duration + 1000, root.destroy)
        root.mainloop()
        
    except Exception as e:
        logger.error(f"Notification error: {e}")
        root.destroy()



def show_git_output(title: str, output: str, is_error: bool = False):
    """Show git command output in a dialog"""
    root = _create_root()
    try:
        dialog = tb.Toplevel(root)
        dialog.title(title)
        dialog.geometry("600x400")
        dialog.attributes('-topmost', True)
        
        # Center
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 600) // 2
        y = (dialog.winfo_screenheight() - 400) // 2
        dialog.geometry(f"+{x}+{y}")
        
        container = tb.Frame(dialog, padding=10)
        container.pack(fill=BOTH, expand=YES)
        
        # Header with status
        status_color = "danger" if is_error else "success"
        header_text = "❌ Error" if is_error else "✅ Success"
        if "Status" in title:
            header_text = "📊 Status"
            status_color = "info"
            
        tb.Label(
            container, 
            text=header_text, 
            bootstyle=status_color, 
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", pady=(0, 10))
        
        # Output text area
        text_frame = tb.Frame(container)
        text_frame.pack(fill=BOTH, expand=YES)
        
        output_text = tb.Text(
            text_frame, 
            font=("Consolas", 9), 
            wrap="word", 
            height=15
        )
        scroll = tb.Scrollbar(text_frame, command=output_text.yview)
        
        output_text.configure(yscrollcommand=scroll.set)
        output_text.pack(side=LEFT, fill=BOTH, expand=YES)
        scroll.pack(side=RIGHT, fill=Y)
        
        output_text.insert("1.0", output)
        output_text.configure(state="disabled") # Read-only
        
        # Close button
        btn = tb.Button(
            container, 
            text="Close", 
            command=dialog.destroy, 
            bootstyle="secondary"
        )
        btn.pack(pady=(10, 0), anchor="e")
        
        dialog.bind('<Escape>', lambda e: dialog.destroy())
        dialog.wait_window()
        
    except Exception as e:
        logger.error(f"Error showing git output: {e}")
    finally:
        root.destroy()


def ask_commit_message(title: str = "Git Commit", initial_value: str = "") -> Optional[str]:
    root = _create_root()
    try:
        dialog = tb.Toplevel(root)
        dialog.title(title)
        dialog.geometry("500x200")
        dialog.resizable(False, False)
        dialog.attributes('-topmost', True)
        
        # Center
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 500) // 2
        y = (dialog.winfo_screenheight() - 200) // 2
        dialog.geometry(f"+{x}+{y}")
        
        result = {"message": None}
        
        main_frame = tb.Frame(dialog, padding=20)
        main_frame.pack(fill=BOTH, expand=YES)
        
        tb.Label(main_frame, text="Commit Message:", font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 5))
        
        msg_entry = tb.Entry(main_frame, font=("Consolas", 10))
        msg_entry.pack(fill=X, pady=(0, 15))
        if initial_value:
             msg_entry.insert(0, initial_value)
        msg_entry.focus_set()
        
        btn_frame = tb.Frame(main_frame)
        btn_frame.pack(anchor="e")
        
        def on_commit():
            msg = msg_entry.get().strip()
            if not msg:
                return
            result["message"] = msg
            dialog.destroy()
            
        tb.Button(btn_frame, text="Cancel", command=dialog.destroy, bootstyle="secondary-outline").pack(side=LEFT, padx=(0, 10))
        tb.Button(btn_frame, text="Commit", command=on_commit, bootstyle="success").pack(side=LEFT)
        
        dialog.bind('<Return>', lambda e: on_commit())
        dialog.bind('<Escape>', lambda e: dialog.destroy())
        
        dialog.wait_window()
        return result["message"]
    finally:
        root.destroy()


def ask_project_selection(
    projects: list[dict],
    title: str = "Select Project",
    allow_add: bool = True,
    allow_remove: bool = True
) -> dict | None:
    """Show project selection dialog with modern cards/list"""
    root = _create_root()
    
    try:
        dialog = tb.Toplevel(root)
        dialog.title(title)
        dialog.geometry("500x500")
        dialog.resizable(False, False)
        dialog.attributes('-topmost', True)
        
        # Center
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 500) // 2
        y = (dialog.winfo_screenheight() - 500) // 2
        dialog.geometry(f"+{x}+{y}")
        
        result = {"action": None, "data": None}
        
        # Header
        header = tb.Frame(dialog, bootstyle="primary", padding=15)
        header.pack(fill=X)
        tb.Label(header, text=f"📁 {title}", font=("Segoe UI", 14, "bold"), bootstyle="inverse-primary").pack(side=LEFT)
        
        # Main content
        main_frame = tb.Frame(dialog, padding=15)
        main_frame.pack(fill=BOTH, expand=YES)
        
        if not projects:
            tb.Label(main_frame, text="No projects found.\nAdd one to get started.", justify="center").pack(pady=50)
        else:
            # Scrollable list of project cards
            canvas = tb.Canvas(main_frame, bd=0, highlightthickness=0)
            scrollbar = tb.Scrollbar(main_frame, command=canvas.yview)
            scroll_frame = tb.Frame(canvas)
            
            scroll_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scroll_frame, anchor="nw", width=440)
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side=LEFT, fill=BOTH, expand=YES)
            scrollbar.pack(side=RIGHT, fill=Y)
            
            # Enable Mouse Wheel Scrolling
            def _on_mousewheel(event):
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
                
            # Bind to all children
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            
            # Populate projects
            for i, p in enumerate(projects):
                card = tb.Frame(scroll_frame, padding=10, bootstyle="secondary")
                card.pack(fill=X, pady=2)
                
                # Project Name and Path
                info_frame = tb.Frame(card)
                info_frame.pack(side=LEFT, fill=BOTH, expand=YES)
                
                tb.Label(info_frame, text=p['name'], font=("Segoe UI", 11, "bold")).pack(anchor="w")
                tb.Label(info_frame, text=p['path'], font=("Consolas", 8), bootstyle="secondary").pack(anchor="w")
                
                def select_project(proj=p):
                    result["action"] = "select"
                    result["data"] = proj
                    dialog.destroy()
                
                # Card click
                card.bind("<Button-1>", lambda e, proj=p: select_project(proj))
                info_frame.bind("<Button-1>", lambda e, proj=p: select_project(proj))
                
                # Selection button (Play icon)
                tb.Button(
                    card, 
                    text="▶", 
                    command=lambda proj=p: select_project(proj), 
                    bootstyle="success-link",
                    width=3
                ).pack(side=RIGHT)

                if allow_remove:
                    def remove_project(proj=p):
                        result["action"] = "remove"
                        result["data"] = proj
                        dialog.destroy()
                        
                    tb.Button(
                        card,
                        text="✕",
                        command=lambda proj=p: remove_project(proj),
                        bootstyle="danger-link",
                        width=3
                    ).pack(side=RIGHT)

        # Footer Actions
        footer = tb.Frame(dialog, padding=15)
        footer.pack(fill=X, side=BOTTOM)
        
        tb.Button(footer, text="Cancel", command=dialog.destroy, bootstyle="secondary-outline").pack(side=LEFT)
        
        if allow_add:
            def on_add():
                dialog.destroy()
                folder = filedialog.askdirectory()
                if folder:
                    result["action"] = "add"
                    result["data"] = folder
            
            tb.Button(footer, text="Add New Project", command=on_add, bootstyle="primary").pack(side=RIGHT)
            
        dialog.bind('<Escape>', lambda e: dialog.destroy())
        dialog.wait_window()
        
        if result["action"]:
            return {"action": result["action"], "project" if result["action"] != "add" else "path": result["data"]}
        return None
        
    finally:
        root.destroy()


def process_dialog_command(command, data_str):
    import json
    try:
        data = json.loads(data_str)
        result = None
        
        if command == "ask_choice":
            result = ask_choice(
                title=data.get("title", "Choice"),
                message=data.get("message", "Select option:"),
                choices=data.get("choices", [])
            )
            # Output MUST be just the JSON to stdout
            print(json.dumps({"result": result}))
            
        elif command == "ask_project_selection":
            result = ask_project_selection(
                projects=data.get("projects", []),
                title=data.get("title", "Select Project"),
                allow_add=data.get("allow_add", True),
                allow_remove=data.get("allow_remove", True)
            )
            print(json.dumps({"result": result}))
            
        elif command == "show_notification":
            show_notification(
                title=data.get("title", "Notification"),
                message=data.get("message", ""),
                duration=data.get("duration", 3000)
            )
            
        elif command == "ask_folder_path":
            result = ask_folder_path(
                title=data.get("title", "Select Folder")
            )
            print(json.dumps({"path": result}))
            
        elif command == "ask_commit_message":
            result = ask_commit_message(
                title=data.get("title", "Commit Message"),
                initial_value=data.get("initial_value", "")
            )
            print(json.dumps({"message": result}))
            
        elif command == "ask_yes_no":
            result = ask_yes_no(
                title=data.get("title", "Confirmation"),
                message=data.get("message", "Are you sure?")
            )
            print(json.dumps({"result": result}))
            
        elif command == "show_git_output":
            show_git_output(
                title=data.get("title", "Git Output"),
                output=data.get("output", ""),
                is_error=data.get("is_error", False)
            )
            
    except Exception as e:
        logger.error(f"Process error: {e}")
        # Print to stderr so parent process can capture it
        sys.stderr.write(f"{e}\n")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(1)
        
    process_dialog_command(sys.argv[1], sys.argv[2])


