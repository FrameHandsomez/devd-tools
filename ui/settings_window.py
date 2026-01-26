import tkinter as tk
from tkinter import ttk, messagebox
import json
import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.config.config_manager import ConfigManager

class BindingDialog:
    def __init__(self, parent, modes, current_mode, features, binding_data=None):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Edit Binding" if binding_data else "Add Binding")
        self.dialog.geometry("400x500")
        self.dialog.configure(bg="#0d1117")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.modes = modes
        self.features = features
        self.binding_data = binding_data # (key, pattern, feature, action)
        
        self._setup_ui(current_mode)

    def _setup_ui(self, current_mode):
        frame = tk.Frame(self.dialog, bg="#0d1117", padx=20, pady=20)
        frame.pack(fill="both", expand=True)
        
        # Style for Combobox
        style = ttk.Style()
        style.configure("TCombobox", fieldbackground="#161b22", background="#21262d", foreground="#f0f6fc")
        
        # Mode
        tk.Label(frame, text="Mode", font=("Segoe UI", 9, "bold"), fg="#8b949e", bg="#0d1117").pack(anchor="w")
        self.mode_var = tk.StringVar(value=current_mode)
        mode_cb = ttk.Combobox(frame, textvariable=self.mode_var, values=self.modes, state="readonly")
        mode_cb.pack(fill="x", pady=(5, 15))
        
        # Key
        tk.Label(frame, text="Key (e.g., f8, f10)", font=("Segoe UI", 9, "bold"), fg="#8b949e", bg="#0d1117").pack(anchor="w")
        self.key_var = tk.StringVar(value=self.binding_data[0].lower() if self.binding_data else "")
        entry_key = tk.Entry(frame, textvariable=self.key_var, bg="#161b22", fg="#f0f6fc", 
                             insertbackground="white", bd=0, font=("Segoe UI", 10))
        entry_key.pack(fill="x", pady=(5, 15), ipady=8)
        
        # Pattern
        tk.Label(frame, text="Press Pattern", font=("Segoe UI", 9, "bold"), fg="#8b949e", bg="#0d1117").pack(anchor="w")
        self.pattern_var = tk.StringVar(value=self.binding_data[1] if self.binding_data else "short")
        patterns = ["short", "long", "multi_2", "multi_3"]
        pattern_cb = ttk.Combobox(frame, textvariable=self.pattern_var, values=patterns, state="readonly")
        pattern_cb.pack(fill="x", pady=(5, 15))
        
        # Feature
        tk.Label(frame, text="Feature", font=("Segoe UI", 9, "bold"), fg="#8b949e", bg="#0d1117").pack(anchor="w")
        self.feature_var = tk.StringVar(value=self.binding_data[2] if self.binding_data else "")
        feature_cb = ttk.Combobox(frame, textvariable=self.feature_var, values=self.features, state="readonly")
        feature_cb.pack(fill="x", pady=(5, 15))
        
        # Action
        tk.Label(frame, text="Action", font=("Segoe UI", 9, "bold"), fg="#8b949e", bg="#0d1117").pack(anchor="w")
        self.action_var = tk.StringVar(value=self.binding_data[3] if self.binding_data else "")
        entry_action = tk.Entry(frame, textvariable=self.action_var, bg="#161b22", fg="#f0f6fc", 
                                insertbackground="white", bd=0, font=("Segoe UI", 10))
        entry_action.pack(fill="x", pady=(5, 15), ipady=8)
        
        # Buttons
        btn_frame = tk.Frame(frame, bg="#0d1117")
        btn_frame.pack(fill="x", side="bottom", pady=10)
        
        tk.Button(btn_frame, text="Cancel", command=self.dialog.destroy,
                  bg="#30363d", fg="#f0f6fc", bd=0, padx=20, pady=8, font=("Segoe UI", 9, "bold")).pack(side="right")
        
        tk.Button(btn_frame, text="Save Binding", command=self._save,
                  bg="#238636", fg="white", bd=0, padx=20, pady=8, font=("Segoe UI", 9, "bold")).pack(side="right", padx=10)

    def _save(self):
        mode = self.mode_var.get()
        key = self.key_var.get().lower()
        pattern = self.pattern_var.get()
        feature = self.feature_var.get()
        action = self.action_var.get()
        
        if not key or not feature or not action:
            messagebox.showwarning("Missing Info", "Please fill in all fields.")
            return
            
        self.result = (mode, key, pattern, feature, action)
        self.dialog.destroy()

class SettingsWindow:
    def __init__(self):
        self.config_path = PROJECT_ROOT / "config" / "macros.json"
        self.config_manager = ConfigManager(self.config_path)
        self.config_manager.load()
        
        # Discover features for the dropdown
        self.features = self._discover_features()
        
        self.root = tk.Tk()
        self.root.title("JR-Dev Settings")
        self.root.geometry("900x600")
        self.root.configure(bg="#0d1117")
        
        # Set Icon
        try:
            icon_path = PROJECT_ROOT / "assets" / "icon.ico"
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except:
            pass
        
        # Styles
        self._setup_styles()
        self._setup_ui()
        self._load_data()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Treeview Style
        style.configure("Treeview", 
                        background="#161b22", 
                        foreground="#f0f6fc", 
                        fieldbackground="#161b22",
                        borderwidth=0,
                        rowheight=30)
        style.configure("Treeview.Heading",
                        background="#21262d",
                        foreground="#f0f6fc",
                        relief="flat")
        style.map("Treeview", background=[('selected', '#1f6feb')])
        
        # Scrollbar
        style.configure("Vertical.TScrollbar",
                        background="#30363d",
                        troughcolor="#0d1117",
                        bordercolor="#30363d",
                        arrowcolor="#f0f6fc")

    def _setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#161b22", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(header, text="⚙️ Settings", font=("Segoe UI", 16, "bold"), 
                 fg="#f0f6fc", bg="#161b22").pack(side="left", padx=20)

        # Main Content
        main_frame = tk.Frame(self.root, bg="#0d1117")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Left Panel: Mode Selection
        left_panel = tk.Frame(main_frame, bg="#0d1117", width=220)
        left_panel.pack(side="left", fill="y", padx=(0, 20))
        
        tk.Label(left_panel, text="MODES", font=("Segoe UI", 10, "bold"), 
                 fg="#8b949e", bg="#0d1117").pack(anchor="w", pady=(0, 10))
        
        self.mode_listbox = tk.Listbox(
            left_panel, 
            bg="#161b22", 
            fg="#f0f6fc", 
            selectbackground="#1f6feb", 
            selectforeground="white",
            bd=0,
            highlightthickness=0,
            font=("Segoe UI", 10),
            activestyle="none"
        )
        self.mode_listbox.pack(fill="both", expand=True)
        self.mode_listbox.bind('<<ListboxSelect>>', self._on_mode_select)
        
        # Right Panel: Bindings Table
        right_panel = tk.Frame(main_frame, bg="#0d1117")
        right_panel.pack(side="right", fill="both", expand=True)
        
        # Toolbar
        toolbar = tk.Frame(right_panel, bg="#0d1117")
        toolbar.pack(fill="x", pady=(0, 10))
        
        tk.Label(toolbar, text="KEY BINDINGS", font=("Segoe UI", 10, "bold"), 
                 fg="#8b949e", bg="#0d1117").pack(side="left")
                 
        # Table
        table_frame = tk.Frame(right_panel, bg="#161b22")
        table_frame.pack(fill="both", expand=True)
        
        columns = ("Key", "Pattern", "Feature", "Action")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        
        self.tree.heading("Key", text="Key")
        self.tree.column("Key", width=80, anchor="center")
        
        self.tree.heading("Pattern", text="Press Pattern")
        self.tree.column("Pattern", width=100, anchor="center")
        
        self.tree.heading("Feature", text="Feature")
        self.tree.column("Feature", width=150)
        
        self.tree.heading("Action", text="Action")
        self.tree.column("Action", width=200)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Double click to edit
        self.tree.bind("<Double-1>", lambda e: self._edit_binding())
        
        # Action Buttons
        btn_frame = tk.Frame(right_panel, bg="#0d1117")
        btn_frame.pack(fill="x", pady=15)
        
        self.btn_add = tk.Button(btn_frame, text="+ Add Binding", command=self._add_binding,
                  bg="#238636", fg="white", bd=0, padx=15, pady=5, font=("Segoe UI", 9, "bold"))
        self.btn_add.pack(side="left")
        
        self.btn_del = tk.Button(btn_frame, text="🗑️ Delete", command=self._delete_binding,
                  bg="#da3633", fg="white", bd=0, padx=15, pady=5, font=("Segoe UI", 9, "bold"))
        self.btn_del.pack(side="left", padx=10)
        
        self.btn_save = tk.Button(btn_frame, text="💾 Save Changes", command=self._save_changes,
                  bg="#1f6feb", fg="white", bd=0, padx=15, pady=5, font=("Segoe UI", 9, "bold"))
        self.btn_save.pack(side="right")

    def _load_data(self):
        self.mode_listbox.delete(0, tk.END)
        modes = self.config_manager.get_modes()
        for mode in modes:
            self.mode_listbox.insert(tk.END, mode)
        
        if modes:
            self.mode_listbox.selection_set(0)
            self._on_mode_select(None)

    def _on_mode_select(self, event):
        selection = self.mode_listbox.curselection()
        if not selection: return
        
        mode_name = self.mode_listbox.get(selection[0])
        bindings = self.config_manager.get_mode_bindings(mode_name)
        
        # Clear table
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Populate table
        for key, data in bindings.items():
            feature = data.get("feature", "Unknown")
            patterns = data.get("patterns", {})
            
            for pattern, action in patterns.items():
                self.tree.insert("", tk.END, values=(key.upper(), pattern, feature, action))

    def _discover_features(self):
        """Quickly scan features folder to get list of available features"""
        features = []
        try:
            features_path = PROJECT_ROOT / "core" / "features"
            # Hardcoded core features + scan
            features = ["snippet_tool", "clone_project", "frontend_runner", "mode_switcher", 
                        "shortcut_guide", "git_status", "git_commit", "ai_assistant"]
            
            # Simple file scan to find others
            if features_path.exists():
                for f in features_path.glob("*.py"):
                    if f.name.startswith("_") or f.name == "base_feature.py": continue
                    name = f.stem
                    if name not in features:
                        features.append(name)
        except:
            pass
        return sorted(features)

    def _add_binding(self):
        selection = self.mode_listbox.curselection()
        current_mode = self.mode_listbox.get(selection[0]) if selection else "DEV"
        modes = list(self.config_manager.get_modes().keys())
        
        dialog = BindingDialog(self.root, modes, current_mode, self.features)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            mode, key, pattern, feature, action = dialog.result
            
            # Get existing patterns for this key if any
            bindings = self.config_manager.get_mode_bindings(mode)
            existing_patterns = {}
            
            if key in bindings:
                # If feature matches, keep existing patterns
                if bindings[key]["feature"] == feature:
                    existing_patterns = bindings[key]["patterns"]
                else:
                    # Feature changed, warn user? Or just overwrite?
                    # For now, we overwrite patterns if feature changes
                    pass
            
            existing_patterns[pattern] = action
            
            if self.config_manager.update_binding(mode, key, feature, existing_patterns):
                self._load_data()
                # Select the mode we just edited
                try:
                    idx = list(self.mode_listbox.get(0, tk.END)).index(mode)
                    self.mode_listbox.selection_clear(0, tk.END)
                    self.mode_listbox.selection_set(idx)
                    self._on_mode_select(None)
                except:
                    pass

    def _edit_binding(self):
        selected = self.tree.selection()
        if not selected: return
        
        values = self.tree.item(selected[0])['values']
        # values = (Key, Pattern, Feature, Action)
        
        selection = self.mode_listbox.curselection()
        current_mode = self.mode_listbox.get(selection[0]) if selection else "DEV"
        modes = list(self.config_manager.get_modes().keys())
        
        dialog = BindingDialog(self.root, modes, current_mode, self.features, binding_data=values)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            mode, key, pattern, feature, action = dialog.result
            
            # If key/pattern changed, we might need to delete the old one
            old_key = values[0].lower()
            old_pattern = values[1]
            
            if old_key != key or old_pattern != pattern or current_mode != mode:
                self.config_manager.delete_binding(current_mode, old_key, old_pattern)
            
            # Now add/update new one
            bindings = self.config_manager.get_mode_bindings(mode)
            existing_patterns = {}
            if key in bindings and bindings[key]["feature"] == feature:
                existing_patterns = bindings[key]["patterns"]
            
            existing_patterns[pattern] = action
            
            if self.config_manager.update_binding(mode, key, feature, existing_patterns):
                self._load_data()
                # Select the mode
                try:
                    idx = list(self.mode_listbox.get(0, tk.END)).index(mode)
                    self.mode_listbox.selection_clear(0, tk.END)
                    self.mode_listbox.selection_set(idx)
                    self._on_mode_select(None)
                except:
                    pass

    def _delete_binding(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Item", "Please select a binding to delete.")
            return
            
        values = self.tree.item(selected[0])['values']
        key = values[0].lower()
        pattern = values[1]
        
        selection = self.mode_listbox.curselection()
        if not selection: return
        mode = self.mode_listbox.get(selection[0])

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {key.upper()} ({pattern})?"):
            if self.config_manager.delete_binding(mode, key, pattern):
                self.tree.delete(selected)
                messagebox.showinfo("Deleted", "Binding removed successfully.")
            else:
                messagebox.showerror("Error", "Failed to delete binding.")
            
    def _save_changes(self):
        # In a real implementation, we would sync UI state back to config object here
        if self.config_manager.save():
            messagebox.showinfo("Saved", "Configuration saved successfully!\nPlease restart the application for changes to take effect.")
        else:
            messagebox.showerror("Error", "Failed to save configuration.")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = SettingsWindow()
    app.run()
