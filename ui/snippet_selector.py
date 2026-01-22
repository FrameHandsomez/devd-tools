"""
Snippet Selector UI - Searchable list execution
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
from typing import Callable, Optional
from core.snippets.snippet_manager import SnippetManager
from utils.logger import get_logger

logger = get_logger(__name__)

class SnippetSelector(tk.Toplevel):
    def __init__(self, root, snippet_manager: SnippetManager, on_select: Callable):
        super().__init__(root)
        self.snippet_manager = snippet_manager
        self.on_select = on_select
        
        self.title("Snippet Manager")
        self.geometry("800x600") # Wider for preview
        
        # Remove standard window decorations for custom styling
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg="#1e1e1e")
        
        # Internal state
        self._drag_data = {"x": 0, "y": 0}
        self.current_matches = []
        self.selected_snippet = None
        
        # Layout Containers
        self._create_header()
        
        self.main_container = tk.Frame(self, bg="#1e1e1e")
        self.main_container.pack(fill="both", expand=True, padx=2, pady=2)
        
        self._create_search_view()
        self._create_input_view()
        self._create_footer()
        
        # Start in search view
        self.show_search_view()
        
        # Bindings
        self.bind("<Escape>", self._on_escape)
        self.bind("<FocusOut>", self._on_focus_out)
        
        # Center on screen
        self._center_window()

    def _create_header(self):
        """Create custom header"""
        header_frame = tk.Frame(self, bg="#2d2d2d", height=40)
        header_frame.pack(fill="x", side="top")
        
        # Icon/Title
        title_label = tk.Label(
            header_frame, 
            text="⚡ Snippet Manager", 
            bg="#2d2d2d", 
            fg="#e0e0e0",
            font=("Segoe UI", 11, "bold")
        )
        title_label.pack(side="left", padx=15, pady=8)
        
        # Close Button
        close_btn = tk.Button(
            header_frame,
            text="✕",
            bg="#2d2d2d",
            fg="#aaaaaa",
            activebackground="#c42b1c",
            activeforeground="white",
            bd=0,
            font=("Segoe UI", 10),
            command=self.close,
            width=4,
            cursor="hand2"
        )
        close_btn.pack(side="right", fill="y")
        
        # Dragging support
        for widget in (header_frame, title_label):
            widget.bind("<Button-1>", self._start_drag)
            widget.bind("<B1-Motion>", self._do_drag)

    def _create_search_view(self):
        """Create the split view for search and preview"""
        self.search_view = tk.Frame(self.main_container, bg="#1e1e1e")
        
        # 1. Search Bar (Top)
        search_frame = tk.Frame(self.search_view, bg="#1e1e1e", pady=10, padx=10)
        search_frame.pack(fill="x")
        
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            search_frame, 
            textvariable=self.search_var,
            font=("Segoe UI", 12),
            bg="#252526",
            fg="white",
            relief="flat",
            insertbackground="white",
            bd=5
        )
        self.search_entry.pack(fill="x", ipady=4)
        self.search_entry.bind("<KeyRelease>", self._on_search)
        self.search_entry.bind("<Down>", lambda e: self.result_list.focus_set())
        self.search_entry.bind("<Return>", lambda e: self._on_confirm())

        # 2. Content Area (Split Pane)
        content_frame = tk.Frame(self.search_view, bg="#1e1e1e", padx=10)
        content_frame.pack(fill="both", expand=True)
        
        # Left: List
        left_pane = tk.Frame(content_frame, bg="#1e1e1e", width=300)
        left_pane.pack(side="left", fill="both", expand=False)
        left_pane.pack_propagate(False) # Fixed width
        
        self.result_list = tk.Listbox(
            left_pane,
            font=("Consolas", 10),
            bg="#252526",
            fg="#d4d4d4",
            selectbackground="#094771",
            selectforeground="white",
            relief="flat",
            highlightthickness=0,
            activestyle="none",
            bd=0
        )
        self.result_list.pack(fill="both", expand=True, side="left")
        
        list_scroll = ttk.Scrollbar(left_pane, orient="vertical", command=self.result_list.yview)
        list_scroll.pack(side="right", fill="y")
        self.result_list.config(yscrollcommand=list_scroll.set)
        
        self.result_list.bind("<<ListboxSelect>>", self._update_preview)
        self.result_list.bind("<Return>", self._on_confirm)
        self.result_list.bind("<Double-Button-1>", self._on_confirm)

        # Separator inside content frame
        ttk.Separator(content_frame, orient="vertical").pack(side="left", fill="y", padx=5)

        # Right: Preview
        right_pane = tk.Frame(content_frame, bg="#1e1e1e")
        right_pane.pack(side="left", fill="both", expand=True)
        
        # Preview Header
        tk.Label(right_pane, text="Preview", bg="#1e1e1e", fg="#569cd6", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 5))
        
        self.preview_text = tk.Text(
            right_pane,
            font=("Consolas", 10),
            bg="#1e1e1e",
            fg="#d4d4d4",
            relief="flat",
            highlightthickness=0,
            state="disabled",
            wrap="word",
            padx=10,
            pady=10
        )
        self.preview_text.pack(fill="both", expand=True)

    def _create_input_view(self):
        """Create view for entering variables"""
        self.input_view = tk.Frame(self.main_container, bg="#1e1e1e", padx=40, pady=20)
        
        tk.Label(
            self.input_view, 
            text="Enter Variables", 
            bg="#1e1e1e", 
            fg="#569cd6", 
            font=("Segoe UI", 14, "bold")
        ).pack(anchor="w", pady=(0, 20))
        
        self.input_fields_frame = tk.Frame(self.input_view, bg="#1e1e1e")
        self.input_fields_frame.pack(fill="both", expand=True)
        
        # Confirm Button Frame
        btn_frame = tk.Frame(self.input_view, bg="#1e1e1e", pady=20)
        btn_frame.pack(fill="x", side="bottom")
        
        tk.Button(
            btn_frame,
            text="Insert Snippet (Enter)",
            bg="#094771",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=20,
            pady=8,
            command=self._submit_variables
        ).pack(side="right")
        
        tk.Button(
            btn_frame,
            text="Back (Esc)",
            bg="#333333",
            fg="white",
            font=("Segoe UI", 10),
            relief="flat",
            padx=15,
            pady=8,
            command=self.show_search_view
        ).pack(side="right", padx=10)

    def _create_footer(self):
        self.footer_label = tk.Label(
            self,
            text="  ENTER: Select  |  ESC: Close",
            bg="#2d2d2d",
            fg="#888888",
            font=("Segoe UI", 9),
            height=2,
            anchor="w"
        )
        self.footer_label.pack(fill="x", side="bottom")

    def show_search_view(self):
        self.input_view.pack_forget()
        self.search_view.pack(fill="both", expand=True)
        self.search_entry.focus_set()
        self.search_entry.select_range(0, tk.END)
        self.footer_label.config(text="  ENTER: Select  |  ESC: Close  |  ⬆/⬇: Navigate")

    def show_input_view(self, variables):
        self.search_view.pack_forget()
        self.input_view.pack(fill="both", expand=True)
        
        # Clear old inputs
        for widget in self.input_fields_frame.winfo_children():
            widget.destroy()
            
        self.variable_entries = {}
        for var in variables:
            frame = tk.Frame(self.input_fields_frame, bg="#1e1e1e", pady=10)
            frame.pack(fill="x")
            
            tk.Label(
                frame, 
                text=var.replace("_", " ").title(), 
                bg="#1e1e1e", 
                fg="#cccccc",
                font=("Segoe UI", 10)
            ).pack(anchor="w")
            
            entry = tk.Entry(
                frame, 
                bg="#252526", 
                fg="white", 
                insertbackground="white", 
                relief="flat",
                font=("Segoe UI", 11),
                bd=5
            )
            entry.pack(fill="x", ipady=3)
            self.variable_entries[var] = entry
            
            # Submitting on Enter inside inputs
            entry.bind("<Return>", lambda e: self._submit_variables())
            entry.bind("<Escape>", lambda e: self.show_search_view())

        # Focus first entry
        if variables:
            self.variable_entries[variables[0]].focus_set()
            
        self.footer_label.config(text="  ENTER: Insert  |  ESC: Back")

    def _on_confirm(self, event=None):
        selection = self.result_list.curselection()
        if not selection:
            return
            
        index = selection[0]
        if index < len(self.current_matches):
            snippet = self.current_matches[index]
            self.selected_snippet = snippet
            
            # Check variables
            required_vars = self.snippet_manager.get_required_variables(snippet)
            if required_vars:
                self.show_input_view(required_vars)
            else:
                self._finalize_selection(snippet)

    def _submit_variables(self):
        variables = {}
        for var, entry in self.variable_entries.items():
            variables[var] = entry.get()
        self._finalize_selection(self.selected_snippet, variables)

    def _finalize_selection(self, snippet, variables=None):
        # We need to construct the result with variables
        # Since on_select expects just the snippet, we might need to modify the protocol 
        # or pass variables along. 
        # Actually, bootstrap.py's on_select calls VariableDialog. 
        # We should change the protocol: process execution HERE or pass verified result?
        # Better: process it via manager here and pass FINAL TEXT or 
        # pass (snippet, variables) tuple to on_select.
        
        # Let's check how SnippetManager processes it.
        # Ideally, we return the snippet and the variables to the caller.
        
        self.close()
        self.after(100, lambda: self.on_select(snippet, variables))

    def _update_preview(self, event):
        selection = self.result_list.curselection()
        if not selection:
            return
            
        index = selection[0]
        if index < len(self.current_matches):
            content = self.current_matches[index].get("content", "")
            self.preview_text.config(state="normal")
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(tk.END, content)
            self._highlight_syntax(content)
            self.preview_text.config(state="disabled")

    def _highlight_syntax(self, content):
        # Basic highlighting (mock)
        self.preview_text.tag_remove("placeholder", "1.0", tk.END)
        
        # Highlight placeholders {{...}}
        import re
        for match in re.finditer(r"\{\{.*?\}\}", content):
            start = f"1.0 + {match.start()} chars"
            end = f"1.0 + {match.end()} chars"
            self.preview_text.tag_add("placeholder", start, end)
            
        self.preview_text.tag_config("placeholder", foreground="#4ec9b0")

    def _populate_list(self, filter_text=""):
        self.result_list.delete(0, tk.END)
        self.current_matches = self.snippet_manager.get_snippets(filter_text)
        
        for s in self.current_matches:
            self.result_list.insert(tk.END, f" {s['trigger']:<12} {s['description']}")
            
        if self.current_matches:
            self.result_list.selection_set(0)
            self._update_preview(None)
            
    def _on_search(self, event):
        if event.keysym in ("Up", "Down", "Return", "Escape"):
            return
        self._populate_list(self.search_var.get())

    def _on_escape(self, event):
        if self.input_view.winfo_viewable():
            self.show_search_view()
        else:
            self.close()

    def _on_focus_out(self, event):
        self.after(200, self._check_focus)
        
    def _check_focus(self):
        try:
            if self.focus_displayof() is None:
                # self.close() 
                pass
        except KeyError:
            pass

    def _start_drag(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _do_drag(self, event):
        x = self.winfo_x() + event.x - self._drag_data["x"]
        y = self.winfo_y() + event.y - self._drag_data["y"]
        self.geometry(f"+{x}+{y}")

    def _center_window(self):
        self.update_idletasks()
        w, h = 800, 600
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def close(self, event=None):
        self.destroy()
