"""
Floating Quick Panel - Always on top window for quick actions
"""

import tkinter as tk
from tkinter import ttk
import sys
from utils.logger import get_logger

logger = get_logger(__name__)

class QuickPanel(tk.Toplevel):
    """
    Floating draggable panel that shows actions for current mode
    """
    
    def __init__(self, root, config_manager, command_executor, on_snippets=None):
        super().__init__(root)
        self.config_manager = config_manager
        self.command_executor = command_executor
        self.on_snippets = on_snippets
        
        # Window setup
        self.overrideredirect(True) # No title bar
        self.attributes('-topmost', True) # Always on top
        self.configure(bg="#1a1a2e")
        
        # internal state
        self._drag_data = {"x": 0, "y": 0}
        
        # Load position
        settings = self.config_manager.get_quick_panel_settings()
        self.geometry(f"+{settings.get('x', 100)}+{settings.get('y', 100)}")
        
        if not settings.get("visible", True):
            self.withdraw()
            
        # UI Setup
        self._create_widgets()
        self._bind_events()
        
        # Initial draw
        current_mode = self.config_manager.get_current_mode()
        self.update_mode(current_mode)
        
    def _create_widgets(self):
        """Create static widgets"""
        # Main container with border
        self.container = tk.Frame(self, bg="#1a1a2e", highlightbackground="#4CAF50", highlightthickness=1)
        self.container.pack(fill="both", expand=True)
        
        # Header/Drag handle
        self.header = tk.Frame(self.container, bg="#2a2a4e", height=20, cursor="fleur")
        self.header.pack(fill="x", side="top")
        
        # Valid dragging area
        self.header.bind("<Button-1>", self._start_drag)
        self.header.bind("<B1-Motion>", self._do_drag)
        self.header.bind("<ButtonRelease-1>", self._stop_drag)
        
        # Snippets Button
        if self.on_snippets:
            snip_btn = tk.Button(
                self.header, 
                text="{}", 
                command=self.on_snippets,
                bg="#2a2a4e", 
                fg="#4CAF50",
                bd=0, 
                activebackground="#3d3d5c",
                activeforeground="#81C784",
                font=("Consolas", 10, "bold"),
                width=3
            )
            snip_btn.pack(side="right", padx=2)
        
        # Content area
        self.content = tk.Frame(self.container, bg="#1a1a2e", padx=5, pady=5)
        self.content.pack(fill="both", expand=True)
        
    def _bind_events(self):
        """Bind global events"""
        pass
        
    def _start_drag(self, event):
        """Begin dragging window"""
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y
        
    def _do_drag(self, event):
        """Handle dragging"""
        x = self.runnable_x + event.x - self._drag_data["x"]
        y = self.runnable_y + event.y - self._drag_data["y"]
        self.geometry(f"+{x}+{y}")
        
    @property
    def runnable_x(self):
        return self.winfo_x()
        
    @property
    def runnable_y(self):
        return self.winfo_y()

    def _stop_drag(self, event):
        """End dragging and save position"""
        self.config_manager.set_quick_panel_settings(
            visible=True, # Assume visible if dragged
            x=self.winfo_x(),
            y=self.winfo_y()
        )
        
    def update_mode(self, mode_name: str):
        """Update panel content for new mode"""
        # Clear existing buttons
        for widget in self.content.winfo_children():
            widget.destroy()
            
        # Update header color based on mode (optional visual cue)
        # For now just text
        tk.Label(
            self.content, 
            text=f"[{mode_name}]", 
            font=("Segoe UI", 8, "bold"), 
            fg="#888888", 
            bg="#1a1a2e"
        ).pack(fill="x", pady=(0, 5))
            
        # Get bindings
        bindings = self.config_manager.get_mode_bindings(mode_name)
        
        if not bindings:
             tk.Label(self.content, text="No Actions", fg="#666", bg="#1a1a2e").pack()
             return

        # Create buttons for each binding
        # We'll show the 'short' pattern action by default or just the feature name
        count = 0
        for key, data in bindings.items():
            feature = data.get("feature", "Unknown")
            patterns = data.get("patterns", {})
            
            # Prioritize 'short' pattern for label, otherwise feature name
            label = patterns.get("short", feature)
            
            btn = tk.Button(
                self.content,
                text=f"{key}: {label}",
                font=("Segoe UI", 9),
                bg="#333333",
                fg="white",
                activebackground="#444444",
                activeforeground="white",
                bd=0,
                padx=8,
                pady=4,
                command=lambda k=key, f=feature: self._execute_action(k, f)
            )
            btn.pack(fill="x", pady=2)
            count += 1
            
        # Auto-resize
        self.update_idletasks()
        
    def _execute_action(self, key, feature):
        """Execute the action associated with the key"""
        logger.info(f"Quick Panel: Executing {feature} for key {key}")
        # We need to trigger the command executor
        # Since we don't have the full context (pattern), we might need to assume 'short'
        # Or better, just simulate the key press? 
        # For now, let's try to execute the feature directly if possible, 
        # but CommandExecutor usually takes (feature_name, action, context)
        
        # Let's get the 'short' action for this key to pass to executor
        mode = self.config_manager.get_current_mode()
        bindings = self.config_manager.get_mode_bindings(mode)
        action = bindings.get(key, {}).get("patterns", {}).get("short", "default")
        
        self.command_executor.execute(feature, action)
        
    def toggle_visibility(self):
        """Toggle panel visibility"""
        if self.state() == "withdrawn":
            self.deiconify()
            self.config_manager.set_quick_panel_settings(True, self.winfo_x(), self.winfo_y())
        else:
            self.withdraw()
            self.config_manager.set_quick_panel_settings(False, self.winfo_x(), self.winfo_y())

