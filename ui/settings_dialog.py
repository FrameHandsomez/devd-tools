"""
Settings UI - Advanced settings dialog for Macro Engine
With tabs: General, Key Bindings, Projects
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Callable, Optional
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)


class SettingsDialog:
    """
    Advanced settings dialog with tabs:
    - General: Timing, behavior, paths
    - Key Bindings: Edit hotkeys per mode
    - Projects: Manage saved projects
    """
    
    def __init__(self, config_manager, on_save: Optional[Callable] = None):
        self.config_manager = config_manager
        self.on_save = on_save
        self.settings = config_manager.get_settings().copy()
        self.result = None
        self.bindings_changed = False
    
    def show(self) -> bool:
        """Show the settings dialog. Returns True if settings were saved."""
        
        self.root = tk.Tk()
        self.root.withdraw()
        
        self.dialog = tk.Toplevel(self.root)
        self.dialog.title("⚙️ Macro Engine Settings")
        self.dialog.geometry("580x550")
        self.dialog.resizable(False, False)
        self.dialog.attributes('-topmost', True)
        self.dialog.configure(bg="#1a1a2e")
        
        # Center on screen
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() - 580) // 2
        y = (self.dialog.winfo_screenheight() - 550) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        self._create_widgets()
        
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.dialog.bind('<Escape>', lambda e: self._on_cancel())
        
        self.root.mainloop()
        
        return self.result == "saved"
    
    def _create_widgets(self):
        """Create all dialog widgets"""
        
        # Header
        header = tk.Frame(self.dialog, bg="#4CAF50", height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="⚙️ Settings",
            font=("Segoe UI", 14, "bold"),
            fg="white",
            bg="#4CAF50"
        ).pack(pady=12)
        
        # Style for tabs
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background='#1a1a2e', borderwidth=0)
        style.configure('TNotebook.Tab', background='#2a2a4e', foreground='white', padding=[12, 6], font=('Segoe UI', 9))
        style.map('TNotebook.Tab', background=[('selected', '#4CAF50')], foreground=[('selected', 'white')])
        
        # Notebook (tabs)
        self.notebook = ttk.Notebook(self.dialog)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create tabs
        self._create_general_tab()
        self._create_keybindings_tab()
        self._create_projects_tab()
        self._create_theme_tab()
        self._create_stats_tab()
        self._create_backup_tab()
        self._create_about_tab()
        
        # Buttons
        btn_frame = tk.Frame(self.dialog, bg="#1a1a2e")
        btn_frame.pack(pady=10)
        
        tk.Button(
            btn_frame,
            text="💾 Save All",
            command=self._on_save,
            font=("Segoe UI", 10, "bold"),
            bg="#4CAF50",
            fg="white",
            width=12
        ).pack(side="left", padx=10)
        
        tk.Button(
            btn_frame,
            text="Cancel",
            command=self._on_cancel,
            font=("Segoe UI", 10),
            width=10
        ).pack(side="left", padx=5)
    
    # ==================== General Tab ====================
    
    def _create_general_tab(self):
        """Create General settings tab"""
        tab = tk.Frame(self.notebook, bg="#1a1a2e")
        self.notebook.add(tab, text="⚙️ General")
        
        content = tk.Frame(tab, bg="#1a1a2e", padx=20, pady=10)
        content.pack(fill="both", expand=True)
        
        # Timing section
        self._create_section_header(content, "⏱️ Timing")
        
        timing_frame = tk.Frame(content, bg="#1a1a2e")
        timing_frame.pack(fill="x", pady=(0, 10))
        
        self._create_slider(timing_frame, "Long Press (ms):", "long_press_ms", 400, 1500, 0)
        self._create_slider(timing_frame, "Multi-Press Window (ms):", "multi_press_window_ms", 200, 1000, 1)
        self._create_slider(timing_frame, "Multi-Press Count:", "multi_press_count", 2, 5, 2)
        
        # Behavior section
        self._create_section_header(content, "🔔 Behavior")
        
        behavior_frame = tk.Frame(content, bg="#1a1a2e")
        behavior_frame.pack(fill="x", pady=(0, 10))
        
        self.notif_var = tk.BooleanVar(value=self.settings.get("notification_enabled", True))
        self._create_toggle(behavior_frame, "Show Notifications", self.notif_var, 0)
        
        self.autostart_var = tk.BooleanVar(value=self.settings.get("auto_start", False))
        self._create_toggle(behavior_frame, "Start on Boot", self.autostart_var, 1)
        
        # Active Keys section
        self._create_section_header(content, "⌨️ Active Keys")
        
        keys_frame = tk.Frame(content, bg="#1a1a2e")
        keys_frame.pack(fill="x", pady=(0, 10))
        
        # Load current active keys (default F9-F12)
        current_keys = self.settings.get("monitored_keys", ["f9", "f10", "f11", "f12"])
        self.key_vars = {}
        
        # Grid of checkboxes for F1-F12
        for i in range(1, 13):
            key = f"f{i}"
            row = (i-1) // 6
            col = (i-1) % 6
            
            var = tk.BooleanVar(value=key in current_keys)
            self.key_vars[key] = var
            
            cb = tk.Checkbutton(
                keys_frame,
                text=key.upper(),
                variable=var,
                font=("Segoe UI", 9),
                bg="#1a1a2e",
                fg="white",
                selectcolor="#4CAF50",
                activebackground="#1a1a2e",
                activeforeground="white"
            )
            cb.grid(row=row, column=col, padx=5, pady=5, sticky="w")
        
        # Paths section
        self._create_section_header(content, "📁 Paths")
        
        paths_frame = tk.Frame(content, bg="#1a1a2e")
        paths_frame.pack(fill="x")
        
        tk.Label(paths_frame, text="Default Clone Path:", font=("Segoe UI", 10), fg="white", bg="#1a1a2e").grid(row=0, column=0, sticky="w", pady=5)
        
        self.clone_path_var = tk.StringVar(value=self.settings.get("default_clone_path", "C:\\Projects"))
        tk.Entry(paths_frame, textvariable=self.clone_path_var, font=("Consolas", 10), width=28, bg="#2a2a4e", fg="white", insertbackground="white").grid(row=0, column=1, padx=10)
        tk.Button(paths_frame, text="📁", command=self._browse_clone_path, font=("Segoe UI", 9), width=3).grid(row=0, column=2)
    
    # ==================== Key Bindings Tab ====================
    
    def _create_keybindings_tab(self):
        """Create Key Bindings editor tab"""
        tab = tk.Frame(self.notebook, bg="#1a1a2e")
        self.notebook.add(tab, text="⌨️ Key Bindings")
        
        content = tk.Frame(tab, bg="#1a1a2e", padx=15, pady=10)
        content.pack(fill="both", expand=True)
        
        # Mode selector
        mode_frame = tk.Frame(content, bg="#1a1a2e")
        mode_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(mode_frame, text="Mode:", font=("Segoe UI", 10), fg="white", bg="#1a1a2e").pack(side="left")
        
        self.modes = list(self.config_manager.get_modes().keys())
        self.mode_var = tk.StringVar(value=self.modes[0] if self.modes else "DEV")
        
        mode_combo = ttk.Combobox(mode_frame, textvariable=self.mode_var, values=self.modes, state="readonly", width=20)
        mode_combo.pack(side="left", padx=10)
        mode_combo.bind('<<ComboboxSelected>>', lambda e: self._refresh_bindings_list())
        
        # Bindings list
        self._create_section_header(content, "📋 Bindings for this Mode")
        
        list_frame = tk.Frame(content, bg="#1a1a2e")
        list_frame.pack(fill="both", expand=True, pady=5)
        
        # Treeview for bindings
        columns = ("Key", "Pattern", "Feature", "Action")
        self.bindings_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=8)
        
        for col in columns:
            self.bindings_tree.heading(col, text=col)
            self.bindings_tree.column(col, width=100)
        
        self.bindings_tree.column("Key", width=60)
        self.bindings_tree.column("Pattern", width=80)
        self.bindings_tree.column("Feature", width=150)
        self.bindings_tree.column("Action", width=120)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.bindings_tree.yview)
        self.bindings_tree.configure(yscrollcommand=scrollbar.set)
        
        self.bindings_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Buttons for bindings
        btn_frame = tk.Frame(content, bg="#1a1a2e")
        btn_frame.pack(fill="x", pady=10)
        
        tk.Button(btn_frame, text="✏️ Edit", command=self._edit_binding, font=("Segoe UI", 9), width=10).pack(side="left", padx=5)
        tk.Button(btn_frame, text="➕ Add", command=self._add_binding, font=("Segoe UI", 9), width=10).pack(side="left", padx=5)
        tk.Button(btn_frame, text="🗑️ Delete", command=self._delete_binding, font=("Segoe UI", 9), width=10).pack(side="left", padx=5)
        
        # Load initial bindings
        self._refresh_bindings_list()
    
    def _refresh_bindings_list(self):
        """Refresh the bindings list for selected mode"""
        # Clear existing items
        for item in self.bindings_tree.get_children():
            self.bindings_tree.delete(item)
        
        mode = self.mode_var.get()
        bindings = self.config_manager.get_mode_bindings(mode)
        
        for key, binding in bindings.items():
            feature = binding.get("feature", "")
            patterns = binding.get("patterns", {})
            
            for pattern, action in patterns.items():
                self.bindings_tree.insert("", "end", values=(key.upper(), pattern, feature, action))
    
    def _edit_binding(self):
        """Edit selected binding"""
        selection = self.bindings_tree.selection()
        if not selection:
            messagebox.showwarning("Select Binding", "Please select a binding to edit")
            return
        
        item = self.bindings_tree.item(selection[0])
        values = item['values']
        
        self._show_binding_editor(
            mode=self.mode_var.get(),
            key=values[0].lower(),
            pattern=values[1],
            feature=values[2],
            action=values[3],
            is_edit=True
        )
    
    def _add_binding(self):
        """Add new binding"""
        self._show_binding_editor(
            mode=self.mode_var.get(),
            key="",
            pattern="short",
            feature="",
            action="",
            is_edit=False
        )
    
    def _delete_binding(self):
        """Delete selected binding"""
        selection = self.bindings_tree.selection()
        if not selection:
            messagebox.showwarning("Select Binding", "Please select a binding to delete")
            return
        
        if not messagebox.askyesno("Delete Binding", "Are you sure you want to delete this binding?"):
            return
        
        item = self.bindings_tree.item(selection[0])
        values = item['values']
        key = values[0].lower()
        pattern = values[1]
        mode = self.mode_var.get()
        
        # Remove from config
        modes = self.config_manager.get_modes()
        if mode in modes and "bindings" in modes[mode]:
            if key in modes[mode]["bindings"]:
                patterns = modes[mode]["bindings"][key].get("patterns", {})
                if pattern in patterns:
                    del patterns[pattern]
                    if not patterns:
                        del modes[mode]["bindings"][key]
                    self.config_manager.save()
                    self.bindings_changed = True
        
        self._refresh_bindings_list()
    
    def _show_binding_editor(self, mode: str, key: str, pattern: str, feature: str, action: str, is_edit: bool):
        """Show binding editor dialog"""
        editor = tk.Toplevel(self.dialog)
        editor.title("Edit Binding" if is_edit else "Add Binding")
        editor.geometry("400x280")
        editor.configure(bg="#1a1a2e")
        editor.attributes('-topmost', True)
        editor.transient(self.dialog)
        editor.grab_set()
        
        # Center
        editor.update_idletasks()
        x = self.dialog.winfo_x() + 90
        y = self.dialog.winfo_y() + 100
        editor.geometry(f"+{x}+{y}")
        
        content = tk.Frame(editor, bg="#1a1a2e", padx=20, pady=15)
        content.pack(fill="both", expand=True)
        
        # Key
        tk.Label(content, text="Key:", font=("Segoe UI", 10), fg="white", bg="#1a1a2e").grid(row=0, column=0, sticky="w", pady=5)
        key_var = tk.StringVar(value=key)
        key_combo = ttk.Combobox(content, textvariable=key_var, values=["f9", "f10", "f11", "f12"], width=20)
        key_combo.grid(row=0, column=1, pady=5)
        
        # Pattern
        tk.Label(content, text="Pattern:", font=("Segoe UI", 10), fg="white", bg="#1a1a2e").grid(row=1, column=0, sticky="w", pady=5)
        pattern_var = tk.StringVar(value=pattern)
        pattern_combo = ttk.Combobox(content, textvariable=pattern_var, values=["short", "long", "double", "multi_3"], width=20)
        pattern_combo.grid(row=1, column=1, pady=5)
        
        # Feature
        tk.Label(content, text="Feature:", font=("Segoe UI", 10), fg="white", bg="#1a1a2e").grid(row=2, column=0, sticky="w", pady=5)
        features = ["clone_project", "frontend_runner", "mode_switcher", "shortcut_guide", "git_status", "git_commit", "ai_assistant"]
        feature_var = tk.StringVar(value=feature)
        feature_combo = ttk.Combobox(content, textvariable=feature_var, values=features, width=20)
        feature_combo.grid(row=2, column=1, pady=5)
        
        # Action
        tk.Label(content, text="Action:", font=("Segoe UI", 10), fg="white", bg="#1a1a2e").grid(row=3, column=0, sticky="w", pady=5)
        action_var = tk.StringVar(value=action)
        action_entry = tk.Entry(content, textvariable=action_var, font=("Consolas", 10), width=22, bg="#2a2a4e", fg="white", insertbackground="white")
        action_entry.grid(row=3, column=1, pady=5)
        
        # Buttons
        btn_frame = tk.Frame(content, bg="#1a1a2e")
        btn_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        def on_save():
            new_key = key_var.get().lower()
            new_pattern = pattern_var.get()
            new_feature = feature_var.get()
            new_action = action_var.get()
            
            if not all([new_key, new_pattern, new_feature, new_action]):
                messagebox.showerror("Error", "Please fill all fields")
                return
            
            # Update config
            modes = self.config_manager.get_modes()
            if mode not in modes:
                modes[mode] = {"name": mode, "bindings": {}}
            if "bindings" not in modes[mode]:
                modes[mode]["bindings"] = {}
            
            if new_key not in modes[mode]["bindings"]:
                modes[mode]["bindings"][new_key] = {"feature": new_feature, "patterns": {}}
            
            modes[mode]["bindings"][new_key]["feature"] = new_feature
            modes[mode]["bindings"][new_key]["patterns"][new_pattern] = new_action
            
            self.config_manager.save()
            self.bindings_changed = True
            
            editor.destroy()
            self._refresh_bindings_list()
        
        tk.Button(btn_frame, text="💾 Save", command=on_save, font=("Segoe UI", 10), bg="#4CAF50", fg="white", width=10).pack(side="left", padx=10)
        tk.Button(btn_frame, text="Cancel", command=editor.destroy, font=("Segoe UI", 10), width=10).pack(side="left")
    
    # ==================== Projects Tab ====================
    
    def _create_projects_tab(self):
        """Create Projects manager tab"""
        tab = tk.Frame(self.notebook, bg="#1a1a2e")
        self.notebook.add(tab, text="📁 Projects")
        
        content = tk.Frame(tab, bg="#1a1a2e", padx=15, pady=10)
        content.pack(fill="both", expand=True)
        
        self._create_section_header(content, "📁 Saved Frontend Projects")
        
        # Projects list
        list_frame = tk.Frame(content, bg="#1a1a2e")
        list_frame.pack(fill="both", expand=True, pady=5)
        
        columns = ("Name", "Path")
        self.projects_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        
        self.projects_tree.heading("Name", text="Name")
        self.projects_tree.heading("Path", text="Path")
        self.projects_tree.column("Name", width=150)
        self.projects_tree.column("Path", width=350)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.projects_tree.yview)
        self.projects_tree.configure(yscrollcommand=scrollbar.set)
        
        self.projects_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Buttons
        btn_frame = tk.Frame(content, bg="#1a1a2e")
        btn_frame.pack(fill="x", pady=10)
        
        tk.Button(btn_frame, text="➕ Add Project", command=self._add_project, font=("Segoe UI", 9), width=12).pack(side="left", padx=5)
        tk.Button(btn_frame, text="🗑️ Remove", command=self._remove_project, font=("Segoe UI", 9), width=10).pack(side="left", padx=5)
        tk.Button(btn_frame, text="🔄 Refresh", command=self._refresh_projects_list, font=("Segoe UI", 9), width=10).pack(side="left", padx=5)
        
        # Load projects
        self._refresh_projects_list()
    
    def _refresh_projects_list(self):
        """Refresh the projects list"""
        for item in self.projects_tree.get_children():
            self.projects_tree.delete(item)
        
        projects = self.config_manager.get_projects("frontend_project")
        
        for p in projects:
            self.projects_tree.insert("", "end", values=(p.get("name", ""), p.get("path", "")))
    
    def _add_project(self):
        """Add a new project"""
        folder = filedialog.askdirectory(title="Select Project Folder")
        
        if folder:
            self.config_manager.add_project("frontend_project", folder)
            self._refresh_projects_list()
    
    def _remove_project(self):
        """Remove selected project"""
        selection = self.projects_tree.selection()
        if not selection:
            messagebox.showwarning("Select Project", "Please select a project to remove")
            return
        
        if not messagebox.askyesno("Remove Project", "Remove this project from the list?"):
            return
        
        item = self.projects_tree.item(selection[0])
        path = item['values'][1]
        
        self.config_manager.remove_project("frontend_project", path)
        self._refresh_projects_list()
    
    # ==================== Helper Methods ====================
    
    def _create_section_header(self, parent, text: str):
        """Create a styled section header"""
        frame = tk.Frame(parent, bg="#1a1a2e")
        frame.pack(fill="x", pady=(10, 5))
        
        tk.Label(frame, text=text, font=("Segoe UI", 11, "bold"), fg="#4CAF50", bg="#1a1a2e").pack(anchor="w")
        
        sep = tk.Frame(frame, bg="#333355", height=1)
        sep.pack(fill="x", pady=(5, 0))
    
    def _create_slider(self, parent, label: str, key: str, min_val: int, max_val: int, row: int):
        """Create a labeled slider"""
        tk.Label(parent, text=label, font=("Segoe UI", 10), fg="white", bg="#1a1a2e").grid(row=row, column=0, sticky="w", pady=5)
        
        value_var = tk.IntVar(value=self.settings.get(key, min_val))
        
        slider = ttk.Scale(parent, from_=min_val, to=max_val, variable=value_var, orient="horizontal", length=150)
        slider.grid(row=row, column=1, padx=10, pady=5)
        
        value_label = tk.Label(parent, text=str(value_var.get()), font=("Consolas", 10), fg="#4CAF50", bg="#1a1a2e", width=5)
        value_label.grid(row=row, column=2, pady=5)
        
        def on_change(*args):
            val = int(value_var.get())
            value_label.config(text=str(val))
            self.settings[key] = val
        
        value_var.trace_add("write", on_change)
        setattr(self, f"{key}_var", value_var)
    
    def _create_toggle(self, parent, label: str, var: tk.BooleanVar, row: int):
        """Create a toggle checkbox"""
        cb = tk.Checkbutton(parent, text=label, variable=var, font=("Segoe UI", 10), fg="white", bg="#1a1a2e", selectcolor="#2a2a4e", activebackground="#1a1a2e", activeforeground="white")
        cb.grid(row=row, column=0, sticky="w", pady=5)
    
    def _browse_clone_path(self):
        """Browse for clone path"""
        folder = filedialog.askdirectory(title="Select Default Clone Path", initialdir=self.clone_path_var.get())
        if folder:
            self.clone_path_var.set(folder)
    
    # ==================== Theme Tab ====================
    
    def _create_theme_tab(self):
        """Create Theme settings tab"""
        tab = tk.Frame(self.notebook, bg="#1a1a2e")
        self.notebook.add(tab, text="🎨 Theme")
        
        content = tk.Frame(tab, bg="#1a1a2e", padx=20, pady=15)
        content.pack(fill="both", expand=True)
        
        self._create_section_header(content, "🎨 Tray Icon Color")
        
        # Color options
        colors = [
            ("#4CAF50", "Green (DEV)", "DEV"),
            ("#FF9800", "Orange (GIT)", "GIT"),
            ("#9C27B0", "Purple (AI)", "AI"),
            ("#2196F3", "Blue (SCRIPT)", "SCRIPT"),
            ("#E91E63", "Pink", "custom"),
            ("#00BCD4", "Cyan", "custom2"),
            ("#FF5722", "Red", "custom3"),
            ("#607D8B", "Gray", "custom4"),
        ]
        
        # Get current color
        current_color = self.settings.get("tray_icon_color", "#4CAF50")
        self.icon_color_var = tk.StringVar(value=current_color)
        
        color_frame = tk.Frame(content, bg="#1a1a2e")
        color_frame.pack(fill="x", pady=10)
        
        tk.Label(
            color_frame,
            text="Select icon color:",
            font=("Segoe UI", 10),
            fg="white",
            bg="#1a1a2e"
        ).pack(anchor="w", pady=(0, 10))
        
        # Color buttons grid
        btn_grid = tk.Frame(color_frame, bg="#1a1a2e")
        btn_grid.pack(fill="x")
        
        self.color_buttons = {}
        for i, (color, name, _) in enumerate(colors):
            row = i // 4
            col = i % 4
            
            btn = tk.Button(
                btn_grid,
                bg=color,
                width=4,
                height=2,
                relief="solid",
                bd=2,
                command=lambda c=color: self._select_color(c)
            )
            btn.grid(row=row, column=col, padx=5, pady=5)
            self.color_buttons[color] = btn
            
            # Label
            tk.Label(
                btn_grid,
                text=name.split()[0],
                font=("Segoe UI", 8),
                fg="#888888",
                bg="#1a1a2e"
            ).grid(row=row+2, column=col)
        
        # Preview
        preview_frame = tk.Frame(content, bg="#1a1a2e")
        preview_frame.pack(fill="x", pady=20)
        
        tk.Label(
            preview_frame,
            text="Preview:",
            font=("Segoe UI", 10),
            fg="white",
            bg="#1a1a2e"
        ).pack(side="left")
        
        self.color_preview = tk.Label(
            preview_frame,
            text="  ●  ",
            font=("Segoe UI", 24),
            fg=current_color,
            bg="#1a1a2e"
        )
        self.color_preview.pack(side="left", padx=10)
        
        # Note
        tk.Label(
            content,
            text="หมายเหตุ: สี icon จะเปลี่ยนหลังรีสตาร์ทโปรแกรม",
            font=("Segoe UI", 9),
            fg="#888888",
            bg="#1a1a2e"
        ).pack(anchor="w", pady=10)
    
    def _select_color(self, color: str):
        """Select a color for tray icon"""
        self.icon_color_var.set(color)
        self.color_preview.config(fg=color)
        self.settings["tray_icon_color"] = color
        
        # Update button borders
        for c, btn in self.color_buttons.items():
            if c == color:
                btn.config(relief="sunken", bd=3)
            else:
                btn.config(relief="solid", bd=2)
    
    # ==================== Statistics Tab ====================
    
    def _create_stats_tab(self):
        """Create Statistics dashboard tab"""
        tab = tk.Frame(self.notebook, bg="#1a1a2e")
        self.notebook.add(tab, text="📊 Stats")
        
        content = tk.Frame(tab, bg="#1a1a2e", padx=20, pady=15)
        content.pack(fill="both", expand=True)
        
        self._create_section_header(content, "📊 Usage Statistics")
        
        # Get stats
        try:
            from utils.statistics import get_tracker
            stats = get_tracker().get_summary()
        except Exception:
            stats = {
                "total_actions": 0,
                "total_commits": 0,
                "total_sessions": 0,
                "total_hours": 0,
                "streak_days": 0,
                "favorite_mode": "N/A",
                "favorite_feature": "N/A"
            }
        
        # Stats grid
        stats_frame = tk.Frame(content, bg="#2a2a4e", padx=20, pady=15)
        stats_frame.pack(fill="x", pady=10)
        
        stat_items = [
            ("🎯 Total Actions:", str(stats["total_actions"])),
            ("📝 Total Commits:", str(stats["total_commits"])),
            ("🔄 Sessions:", str(stats["total_sessions"])),
            ("⏱️ Total Hours:", f"{stats['total_hours']}h"),
            ("🔥 Streak:", f"{stats['streak_days']} days"),
            ("❤️ Favorite Mode:", stats["favorite_mode"]),
            ("⭐ Most Used:", stats["favorite_feature"]),
        ]
        
        for i, (label, value) in enumerate(stat_items):
            row = i // 2
            col = i % 2
            
            item_frame = tk.Frame(stats_frame, bg="#2a2a4e")
            item_frame.grid(row=row, column=col, sticky="w", padx=20, pady=8)
            
            tk.Label(
                item_frame,
                text=label,
                font=("Segoe UI", 10),
                fg="#888888",
                bg="#2a2a4e"
            ).pack(side="left")
            
            tk.Label(
                item_frame,
                text=value,
                font=("Consolas", 11, "bold"),
                fg="#4CAF50",
                bg="#2a2a4e"
            ).pack(side="left", padx=5)
        
        # Buttons
        btn_frame = tk.Frame(content, bg="#1a1a2e")
        btn_frame.pack(fill="x", pady=15)
        
        def refresh_stats():
            # Close and reopen settings
            self.dialog.destroy()
            self.root.destroy()
            show_settings_dialog(self.config_manager, self.on_save)
        
        tk.Button(
            btn_frame,
            text="🔄 Refresh",
            command=refresh_stats,
            font=("Segoe UI", 9),
            width=12
        ).pack(side="left", padx=5)
        
        def reset_stats():
            if messagebox.askyesno("Reset Stats", "Reset all statistics?"):
                try:
                    from utils.statistics import get_tracker
                    get_tracker().reset_stats()
                    messagebox.showinfo("Done", "Statistics reset!")
                except Exception as e:
                    messagebox.showerror("Error", str(e))
        
        tk.Button(
            btn_frame,
            text="🗑️ Reset Stats",
            command=reset_stats,
            font=("Segoe UI", 9),
            bg="#ff6b6b",
            fg="white",
            width=12
        ).pack(side="left", padx=5)
    
    # ==================== Backup Tab ====================
    
    def _create_backup_tab(self):
        """Create Backup/Export tab"""
        tab = tk.Frame(self.notebook, bg="#1a1a2e")
        self.notebook.add(tab, text="📤 Backup")
        
        content = tk.Frame(tab, bg="#1a1a2e", padx=20, pady=15)
        content.pack(fill="both", expand=True)
        
        # Export section
        self._create_section_header(content, "📤 Export Settings")
        
        export_frame = tk.Frame(content, bg="#1a1a2e")
        export_frame.pack(fill="x", pady=10)
        
        tk.Label(
            export_frame,
            text="Export all settings to a backup file:",
            font=("Segoe UI", 10),
            fg="white",
            bg="#1a1a2e"
        ).pack(anchor="w", pady=5)
        
        tk.Button(
            export_frame,
            text="📤 Export to File...",
            command=self._export_config,
            font=("Segoe UI", 10),
            bg="#2196F3",
            fg="white",
            width=20
        ).pack(anchor="w", pady=5)
        
        # Import section
        self._create_section_header(content, "📥 Import Settings")
        
        import_frame = tk.Frame(content, bg="#1a1a2e")
        import_frame.pack(fill="x", pady=10)
        
        tk.Label(
            import_frame,
            text="Restore settings from a backup file:",
            font=("Segoe UI", 10),
            fg="white",
            bg="#1a1a2e"
        ).pack(anchor="w", pady=5)
        
        tk.Button(
            import_frame,
            text="📥 Import from File...",
            command=self._import_config,
            font=("Segoe UI", 10),
            bg="#FF9800",
            fg="white",
            width=20
        ).pack(anchor="w", pady=5)
        
        # Reset section
        self._create_section_header(content, "🔄 Reset")
        
        reset_frame = tk.Frame(content, bg="#1a1a2e")
        reset_frame.pack(fill="x", pady=10)
        
        tk.Label(
            reset_frame,
            text="Reset all settings to defaults:",
            font=("Segoe UI", 10),
            fg="white",
            bg="#1a1a2e"
        ).pack(anchor="w", pady=5)
        
        tk.Button(
            reset_frame,
            text="🔄 Reset to Defaults",
            command=self._reset_to_defaults,
            font=("Segoe UI", 10),
            bg="#ff6b6b",
            fg="white",
            width=20
        ).pack(anchor="w", pady=5)
    
    def _export_config(self):
        """Export config to file"""
        import json
        from datetime import datetime
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"macro_engine_backup_{timestamp}.json"
        
        filepath = filedialog.asksaveasfilename(
            title="Export Settings",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile=default_name
        )
        
        if filepath:
            try:
                # Get full config
                config_data = {
                    "version": "2.0",
                    "exported_at": datetime.now().isoformat(),
                    "modes": self.config_manager.get_modes(),
                    "settings": self.settings,
                    "saved_paths": self.config_manager.get("saved_paths", {})
                }
                
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("Export Success", f"Settings exported to:\n{filepath}")
                logger.info(f"Config exported to: {filepath}")
                
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export: {e}")
                logger.error(f"Export error: {e}")
    
    def _import_config(self):
        """Import config from file"""
        import json
        
        filepath = filedialog.askopenfilename(
            title="Import Settings",
            filetypes=[("JSON files", "*.json")]
        )
        
        if filepath:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    imported = json.load(f)
                
                # Validate
                if "settings" not in imported and "modes" not in imported:
                    messagebox.showerror("Invalid File", "This doesn't look like a valid backup file.")
                    return
                
                if not messagebox.askyesno("Confirm Import", 
                    "This will replace all current settings.\nAre you sure?"):
                    return
                
                # Apply imported settings
                if "settings" in imported:
                    self.settings = imported["settings"]
                    self.config_manager.save_settings(self.settings)
                
                if "modes" in imported:
                    current_config = self.config_manager._config
                    current_config["modes"] = imported["modes"]
                    self.config_manager.save()
                
                if "saved_paths" in imported:
                    current_config = self.config_manager._config
                    current_config["saved_paths"] = imported["saved_paths"]
                    self.config_manager.save()
                
                messagebox.showinfo("Import Success", 
                    "Settings imported successfully!\nPlease restart the application.")
                logger.info(f"Config imported from: {filepath}")
                
            except Exception as e:
                messagebox.showerror("Import Error", f"Failed to import: {e}")
                logger.error(f"Import error: {e}")
    
    def _reset_to_defaults(self):
        """Reset all settings to defaults"""
        if not messagebox.askyesno("Confirm Reset", 
            "This will reset ALL settings to defaults.\nAre you sure?"):
            return
        
        # Reset settings
        self.settings = {
            "long_press_ms": 800,
            "multi_press_window_ms": 500,
            "multi_press_count": 3,
            "default_clone_path": "C:\\Projects",
            "notification_enabled": True,
            "auto_start": False,
            "tray_icon_color": "#4CAF50"
        }
        
        # Update UI
        self.long_press_ms_var.set(800)
        self.multi_press_window_ms_var.set(500)
        self.multi_press_count_var.set(3)
        self.notif_var.set(True)
        self.autostart_var.set(False)
        self.clone_path_var.set("C:\\Projects")
        
        messagebox.showinfo("Reset Complete", "Settings reset to defaults.")
    
    # ==================== About Tab ====================
    
    def _create_about_tab(self):
        """Create About tab"""
        tab = tk.Frame(self.notebook, bg="#1a1a2e")
        self.notebook.add(tab, text="ℹ️ About")
        
        content = tk.Frame(tab, bg="#1a1a2e", padx=20, pady=15)
        content.pack(fill="both", expand=True)
        
        # Logo/Title
        title_frame = tk.Frame(content, bg="#1a1a2e")
        title_frame.pack(pady=20)
        
        tk.Label(
            title_frame,
            text="🎮",
            font=("Segoe UI", 48),
            fg="white",
            bg="#1a1a2e"
        ).pack()
        
        tk.Label(
            title_frame,
            text="Macro Engine",
            font=("Segoe UI", 18, "bold"),
            fg="white",
            bg="#1a1a2e"
        ).pack()
        
        tk.Label(
            title_frame,
            text="Developer Productivity Tool",
            font=("Segoe UI", 10),
            fg="#888888",
            bg="#1a1a2e"
        ).pack()
        
        # Version info
        info_frame = tk.Frame(content, bg="#2a2a4e", padx=20, pady=15)
        info_frame.pack(fill="x", pady=15)
        
        info_items = [
            ("Version:", "2.0.0"),
            ("Python:", "3.11+"),
            ("Platform:", "Windows"),
            ("License:", "MIT"),
        ]
        
        for i, (label, value) in enumerate(info_items):
            row = tk.Frame(info_frame, bg="#2a2a4e")
            row.pack(fill="x", pady=2)
            
            tk.Label(
                row,
                text=label,
                font=("Segoe UI", 10),
                fg="#888888",
                bg="#2a2a4e",
                width=12,
                anchor="w"
            ).pack(side="left")
            
            tk.Label(
                row,
                text=value,
                font=("Consolas", 10),
                fg="#4CAF50",
                bg="#2a2a4e"
            ).pack(side="left")
        
        # Credits
        tk.Label(
            content,
            text="Made with ❤️ by Framex",
            font=("Segoe UI", 10),
            fg="#888888",
            bg="#1a1a2e"
        ).pack(pady=15)
        
        # GitHub link (display only)
        tk.Label(
            content,
            text="github.com/FrameHandsomez/jr-dev",
            font=("Segoe UI", 9),
            fg="#4CAF50",
            bg="#1a1a2e",
            cursor="hand2"
        ).pack()
    
    # ==================== Save/Cancel ====================
    
    def _on_save(self):
        """Save all settings"""
        # Update settings
        self.settings["notification_enabled"] = self.notif_var.get()
        self.settings["auto_start"] = self.autostart_var.get()
        self.settings["default_clone_path"] = self.clone_path_var.get()
        
        # Save monitored keys
        if hasattr(self, 'key_vars'):
            monitored = [k for k, v in self.key_vars.items() if v.get()]
            self.settings["monitored_keys"] = monitored
        
        # Save icon color if set
        if hasattr(self, 'icon_color_var'):
            self.settings["tray_icon_color"] = self.icon_color_var.get()
        
        # Handle auto-start
        try:
            from utils.windows_utils import enable_auto_start, disable_auto_start
            if self.autostart_var.get():
                enable_auto_start()
            else:
                disable_auto_start()
        except Exception as e:
            logger.warning(f"Could not update auto-start: {e}")
        
        # Save to config
        self.config_manager.save_settings(self.settings)
        
        self.result = "saved"
        
        if self.on_save:
            self.on_save(self.settings)
        
        self.dialog.destroy()
        self.root.destroy()
        
        logger.info("Settings saved")
    
    def _on_cancel(self):
        """Cancel without saving"""
        self.result = "cancelled"
        self.dialog.destroy()
        self.root.destroy()


def show_settings_dialog(config_manager, on_save: Optional[Callable] = None) -> bool:
    """Show the settings dialog."""
    dialog = SettingsDialog(config_manager, on_save)
    return dialog.show()

