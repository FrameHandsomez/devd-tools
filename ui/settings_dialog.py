"""
Settings Dialog for Developer Macro Engine
"""
import sys
import os
import json
import tkinter as tk
from tkinter import messagebox, filedialog
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.logger import get_logger
from core.config.config_manager import ConfigManager

logger = get_logger(__name__)

class SettingsDialog:
    def __init__(self, root, config_path: Path):
        self.root = root
        self.root.title("⚙️ Settings")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.load()
        
        # UI Variables
        self.var_commit_lang = tk.StringVar(value=self._get_setting("preferences.default_commit_language", "en"))
        self.var_clone_path = tk.StringVar(value=self._get_setting("preferences.default_clone_path", "C:\\Projects"))
        
        self.create_ui()
        self.center_window()
        
        # Force window to front
        self.root.deiconify()
        self.root.lift()
        self.root.attributes('-topmost',True)
        self.root.after_idle(self.root.attributes,'-topmost',False)
        self.root.focus_force()
        
    def _get_setting(self, path: str, default=None):
        """Helper to get nested setting"""
        keys = path.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, {})
            else:
                return default
                
        if value == {}: return default
        return value

    def create_ui(self):
        # Notebook (Tabs)
        self.notebook = tb.Notebook(self.root)
        self.notebook.pack(fill=BOTH, expand=YES, padx=10, pady=10)
        
        # Tabs
        self.tab_projects = tb.Frame(self.notebook, padding=10)
        self.tab_bindings = tb.Frame(self.notebook, padding=10)
        self.tab_prefs = tb.Frame(self.notebook, padding=10)
        self.tab_about = tb.Frame(self.notebook, padding=10)
        
        self.notebook.add(self.tab_projects, text="📂 Projects")
        self.notebook.add(self.tab_bindings, text="⌨️ Key Bindings")
        self.notebook.add(self.tab_prefs, text="⚙️ Preferences")
        self.notebook.add(self.tab_about, text="ℹ️ About")
        
        self._build_projects_tab()
        self._build_bindings_tab()
        self._build_prefs_tab()
        self._build_about_tab()
        
        # Bottom Buttons
        btn_frame = tb.Frame(self.root, padding=10)
        btn_frame.pack(fill=X, side=BOTTOM)
        
        tb.Button(btn_frame, text="Close", bootstyle="secondary-outline", command=self.root.destroy).pack(side=RIGHT, padx=5)
        tb.Button(btn_frame, text="Save & Restart", bootstyle="success", command=self.save_and_close).pack(side=RIGHT, padx=5)

    def _build_projects_tab(self):
        # Project Lists
        lbl = tb.Label(self.tab_projects, text="Manage Docker/Git Projects", font=("Segoe UI", 10, "bold"))
        lbl.pack(anchor="w", pady=(0, 10))
        
        # Container for lists
        list_container = tb.Frame(self.tab_projects)
        list_container.pack(fill=BOTH, expand=YES)
        
        # Left: Docker Projects
        f_docker = tb.Labelframe(list_container, text="Docker Projects", padding=5)
        f_docker.pack(side=LEFT, fill=BOTH, expand=YES, padx=(0, 5))
        
        self.lb_docker = tk.Listbox(f_docker, bg="#2d2d2d", fg="white", borderwidth=0, highlightthickness=0)
        self.lb_docker.pack(fill=BOTH, expand=YES)
        
        # Right: Git Projects
        f_git = tb.Labelframe(list_container, text="Git Projects", padding=5)
        f_git.pack(side=LEFT, fill=BOTH, expand=YES, padx=(5, 0))
        
        self.lb_git = tk.Listbox(f_git, bg="#2d2d2d", fg="white", borderwidth=0, highlightthickness=0)
        self.lb_git.pack(fill=BOTH, expand=YES)
        
        # Populate
        self._refresh_lists()
        
        # Remove buttons
        btn_container = tb.Frame(self.tab_projects, padding=(0, 10))
        btn_container.pack(fill=X)
        
        tb.Button(btn_container, text="🗑️ Remove Selected Docker", 
                 command=lambda: self._remove_project("docker"), 
                 bootstyle="danger-outline", width=25).pack(side=LEFT, padx=5)
                 
        tb.Button(btn_container, text="🗑️ Remove Selected Git", 
                 command=lambda: self._remove_project("git"), 
                 bootstyle="danger-outline", width=25).pack(side=RIGHT, padx=5)

    def _refresh_lists(self):
        self.lb_docker.delete(0, END)
        self.lb_git.delete(0, END)
        
        # Helper to get projects list safely
        def get_list(key):
            return self.config.get("saved_paths", {}).get(f"{key}_list", [])
            
        for p in get_list("docker"):
            self.lb_docker.insert(END, f"{p.get('name')} ({p.get('path')})")
            
        for p in get_list("git_project"):
            self.lb_git.insert(END, f"{p.get('name')} ({p.get('path')})")

    def _remove_project(self, ptype):
        listbox = self.lb_docker if ptype == "docker" else self.lb_git
        config_key = "docker" if ptype == "docker" else "git_project"
        
        sel = listbox.curselection()
        if not sel:
            return
            
        idx = sel[0]
        projects = self.config.get("saved_paths", {}).get(f"{config_key}_list", [])
        
        if idx < len(projects):
            proj = projects[idx]
            if messagebox.askyesno("Confirm", f"Remove project '{proj.get('name')}'?"):
                del projects[idx]
                # Update config directly
                if "saved_paths" not in self.config: self.config["saved_paths"] = {}
                self.config["saved_paths"][f"{config_key}_list"] = projects
                self._refresh_lists()

    def _build_bindings_tab(self):
        # Layout: Left side Mode list, Right side Bindings table
        paned = tb.Panedwindow(self.tab_bindings, orient=HORIZONTAL)
        paned.pack(fill=BOTH, expand=YES)
        
        # Left Panel (Modes)
        f_left = tb.Frame(paned, padding=(0, 0, 5, 0))
        paned.add(f_left, weight=1)
        
        tb.Label(f_left, text="MODES", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        self.lb_modes = tk.Listbox(f_left, bg="#2d2d2d", fg="white", borderwidth=0, highlightthickness=0)
        self.lb_modes.pack(fill=BOTH, expand=YES)
        self.lb_modes.bind('<<ListboxSelect>>', self._on_mode_select)
        
        # Right Panel (Table)
        f_right = tb.Frame(paned, padding=(5, 0, 0, 0))
        paned.add(f_right, weight=3)
        
        tb.Label(f_right, text="KEY BINDINGS", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        # Treeview for bindings
        columns = ("key", "pattern", "feature", "action")
        self.tv_bindings = tb.Treeview(
            f_right, 
            columns=columns, 
            show="headings",
            bootstyle="dark"
        )
        
        self.tv_bindings.heading("key", text="Key")
        self.tv_bindings.column("key", width=60, anchor="center")
        
        self.tv_bindings.heading("pattern", text="Pattern")
        self.tv_bindings.column("pattern", width=80, anchor="center")
        
        self.tv_bindings.heading("feature", text="Feature")
        self.tv_bindings.column("feature", width=120)
        
        self.tv_bindings.heading("action", text="Action")
        self.tv_bindings.column("action", width=120)
        
        # Scrollbar
        scrollbar = tb.Scrollbar(f_right, orient=VERTICAL, command=self.tv_bindings.yview)
        self.tv_bindings.configure(yscrollcommand=scrollbar.set)
        
        self.tv_bindings.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # Populate Modes
        self._refresh_modes()

    def _refresh_modes(self):
        self.lb_modes.delete(0, END)
        modes = self.config.get("modes", {}).keys()
        for m in modes:
            self.lb_modes.insert(END, m)
            
        if self.lb_modes.size() > 0:
            self.lb_modes.selection_set(0)
            self._on_mode_select(None)

    def _on_mode_select(self, event):
        selection = self.lb_modes.curselection()
        if not selection:
            return
            
        mode = self.lb_modes.get(selection[0])
        bindings = self.config.get("modes", {}).get(mode, {}).get("bindings", {})
        
        # Clear table
        for item in self.tv_bindings.get_children():
            self.tv_bindings.delete(item)
            
        # Populate table
        for key, data in bindings.items():
            feature = data.get("feature", "?")
            patterns = data.get("patterns", {})
            
            for pat, action in patterns.items():
                self.tv_bindings.insert("", END, values=(key, pat, feature, action))

    def _build_prefs_tab(self):
        # AI Settings
        group_ai = tb.Labelframe(self.tab_prefs, text="AI Automation", padding=10)
        group_ai.pack(fill=X, pady=10)
        
        tb.Label(group_ai, text="Default Commit Language:").pack(anchor="w")
        
        combo_lang = tb.Combobox(group_ai, textvariable=self.var_commit_lang, 
                               values=["en", "th"], state="readonly")
        combo_lang.pack(fill=X, pady=5)
        
        # General Settings
        group_gen = tb.Labelframe(self.tab_prefs, text="General", padding=10)
        group_gen.pack(fill=X, pady=10)
        
        tb.Label(group_gen, text="Default Clone Path:").pack(anchor="w")
        
        frame_path = tb.Frame(group_gen)
        frame_path.pack(fill=X, pady=5)
        
        tb.Entry(frame_path, textvariable=self.var_clone_path).pack(side=LEFT, fill=X, expand=YES)
        tb.Button(frame_path, text="Browse", command=self._browse_path, bootstyle="outline").pack(side=LEFT, padx=5)

    def _browse_path(self):
        path = filedialog.askdirectory()
        if path:
            self.var_clone_path.set(path)

    def _build_about_tab(self):
        from core.constants import APP_NAME, APP_VERSION, REPO_OWNER
        
        tb.Label(self.tab_about, text="Developer Macro Engine", font=("Segoe UI", 20, "bold")).pack(pady=20)
        tb.Label(self.tab_about, text=f"Version {APP_VERSION} ({APP_NAME})", font=("Segoe UI", 12)).pack()
        tb.Label(self.tab_about, text=f"© 2026 {REPO_OWNER}", font=("Segoe UI", 10), foreground="gray").pack(pady=20)
        
        info = "Features:\n- AI Auto-Commit\n- Smart Terminal\n- Docker Manager\n- Git Workflow"
        tb.Label(self.tab_about, text=info, justify="center").pack(pady=(0, 20))
        
        tb.Button(self.tab_about, text="🔄 Check for Updates", 
                 command=self._check_updates, bootstyle="info-outline").pack()

    def _check_updates(self):
        import threading
        def check():
            from utils.updater import get_updater
            updater = get_updater()
            
            self.root.after(0, lambda: messagebox.showinfo("Checking", "Checking for updates..."))
            
            has_update, msg, ver = updater.check_for_updates()
            
            if has_update:
                if messagebox.askyesno("Update Available", f"{msg}\n\nUpdate now?"):
                    success, u_msg = updater.apply_update()
                    if success:
                        messagebox.showinfo("Success", "Updated! Please restart.")
                    else:
                        messagebox.showerror("Failed", u_msg)
            else:
                messagebox.showinfo("Up to Date", f"{msg} ({ver})")
        
        threading.Thread(target=check, daemon=True).start()

    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def save_and_close(self):
        # Save Preferences
        if "preferences" not in self.config:
            self.config["preferences"] = {}
            
        self.config["preferences"]["default_commit_language"] = self.var_commit_lang.get()
        self.config["preferences"]["default_clone_path"] = self.var_clone_path.get()
        
        # ConfigManager deals with saving
        # We manually update the internal dict of config_manager and call save
        self.config_manager._config = self.config
        if self.config_manager.save():
            messagebox.showinfo("Saved", "Settings saved successfully!")
            self.root.destroy()
        else:
            messagebox.showerror("Error", "Failed to save settings.")

def main():
    try:
        root = tb.Window(themename="cyborg")
    except:
        import tkinter as tk
        root = tk.Tk()
        
    # Find config path
    current_dir = Path(__file__).parent.parent
    config_path = current_dir / "config" / "macros.json"
    
    app = SettingsDialog(root, config_path)
    root.mainloop()

if __name__ == "__main__":
    main()
