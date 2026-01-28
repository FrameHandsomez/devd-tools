import tkinter as tk
from tkinter import ttk, messagebox
import json
import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.config.config_manager import ConfigManager

class SettingsWindow:
    def __init__(self):
        self.config_path = PROJECT_ROOT / "config" / "macros.json"
        self.config_manager = ConfigManager(self.config_path)
        self.config_manager.load()
        
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

    def _add_binding(self):
        messagebox.showinfo("Coming Soon", "Feature to add new bindings will be implemented next!")

    def _delete_binding(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Item", "Please select a binding to delete.")
            return
            
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this binding?"):
            self.tree.delete(selected)
            # Note: This only deletes from UI, need to implement logic to update config object
            
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
