#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import threading
import sys
import shutil
import os
from pathlib import Path
from io import StringIO

from irish_anki import convert_to_mp3, organize_music_files, generate_anki_cards
from locale_manager import _, get_available_languages, set_language, get_current_language


class DirectoryPickerDialog:
    def __init__(self, parent, title=None, initial_dir=None):
        if title is None:
            title = _("gui.dialog.select_directory")
        self.result = None
        self.current_path = initial_dir or str(Path.home())
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("600x500")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        self.setup_dialog()
        self.refresh_contents()
        
    def setup_dialog(self):
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Current path display
        path_frame = ttk.Frame(main_frame)
        path_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(path_frame, text=_("gui.label.current_directory")).pack(side="left")
        self.path_var = tk.StringVar(value=self.current_path)
        path_entry = ttk.Entry(path_frame, textvariable=self.path_var, state="readonly")
        path_entry.pack(side="left", fill="x", expand=True, padx=(10, 0))
        
        # File/directory list with scrollbar
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Create treeview with scrollbar
        tree_scroll = ttk.Scrollbar(list_frame)
        tree_scroll.pack(side="right", fill="y")
        
        self.tree = ttk.Treeview(list_frame, yscrollcommand=tree_scroll.set, selectmode="extended")
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll.config(command=self.tree.yview)
        
        # Configure treeview columns
        self.tree["columns"] = ("type", "size")
        self.tree.column("#0", width=300, minwidth=200)
        self.tree.column("type", width=80, minwidth=50)
        self.tree.column("size", width=100, minwidth=70)
        
        self.tree.heading("#0", text=_("gui.label.name"), anchor="w")
        self.tree.heading("type", text=_("gui.label.type"), anchor="w")
        self.tree.heading("size", text=_("gui.label.size"), anchor="w")
        
        # Bind double-click to navigate
        self.tree.bind("<Double-1>", self.on_double_click)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x")
        
        ttk.Button(button_frame, text=_("gui.button.up"), command=self.go_up).pack(side="left", padx=(0, 5))
        ttk.Button(button_frame, text=_("gui.button.refresh"), command=self.refresh_contents).pack(side="left", padx=(0, 20))
        
        ttk.Button(button_frame, text=_("gui.button.cancel"), command=self.cancel).pack(side="right")
        ttk.Button(button_frame, text=_("gui.button.choose_directory"), command=self.choose_directory).pack(side="right", padx=(0, 10))
        
    def refresh_contents(self):
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        self.path_var.set(self.current_path)
        
        try:
            # Get directory contents
            items = []
            for item in os.listdir(self.current_path):
                item_path = os.path.join(self.current_path, item)
                if os.path.isdir(item_path):
                    items.append((item, _("gui.file_types.folder"), "", True))
                else:
                    # Show file size
                    try:
                        size = os.path.getsize(item_path)
                        if size < 1024:
                            size_str = f"{size} B"
                        elif size < 1024*1024:
                            size_str = f"{size//1024} KB"
                        else:
                            size_str = f"{size//(1024*1024)} MB"
                    except:
                        size_str = ""
                    
                    # Determine file type
                    ext = os.path.splitext(item)[1].lower()
                    if ext in ['.mp3', '.m4a', '.wav', '.flac', '.aac', '.ogg']:
                        file_type = _("gui.file_types.audio")
                    else:
                        file_type = _("gui.file_types.file")
                    
                    items.append((item, file_type, size_str, False))
            
            # Sort: directories first, then files, both alphabetically
            items.sort(key=lambda x: (not x[3], x[0].lower()))
            
            # Add items to tree
            for name, file_type, size, is_dir in items:
                tags = ("directory",) if is_dir else ("file",)
                self.tree.insert("", "end", text=name, values=(file_type, size), tags=tags)
                
            # Configure tags for different colors
            self.tree.tag_configure("directory", foreground="blue")
            self.tree.tag_configure("file", foreground="black")
                
        except PermissionError:
            self.tree.insert("", "end", text=_("gui.file_types.permission_denied"), values=(_("gui.file_types.error"), ""), tags=("error",))
            self.tree.tag_configure("error", foreground="red")
        except Exception as e:
            self.tree.insert("", "end", text=f"[Error: {e}]", values=(_("gui.file_types.error"), ""), tags=("error",))
            
    def on_double_click(self, event):
        selection = self.tree.selection()
        if not selection:
            return
            
        item = selection[0]
        name = self.tree.item(item, "text")
        tags = self.tree.item(item, "tags")
        
        if "directory" in tags:
            # Navigate into directory
            new_path = os.path.join(self.current_path, name)
            if os.path.isdir(new_path):
                self.current_path = new_path
                self.refresh_contents()
                
    def go_up(self):
        parent = os.path.dirname(self.current_path)
        if parent != self.current_path:  # Not at root
            self.current_path = parent
            self.refresh_contents()
            
    def choose_directory(self):
        self.result = self.current_path
        self.dialog.destroy()
        
    def cancel(self):
        self.result = None
        self.dialog.destroy()
        
    def show(self):
        self.dialog.wait_window()
        return self.result


class ConsoleCapture:
    def __init__(self, callback):
        self.callback = callback
        self.buffer = StringIO()
        
    def write(self, text):
        self.buffer.write(text)
        if self.callback:
            self.callback(text)
        return len(text)
        
    def flush(self):
        pass


class IrishAnkiGUI:
    def __init__(self):
        self.console_capture = None
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
        # Create main window
        self.root = tk.Tk()
        self.root.title(_("gui.title"))
        self.root.geometry("950x850")
        self.root.minsize(800, 700)
        
        # Configure grid weights for resizing
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Variables for form inputs
        self.input_dir = tk.StringVar()
        self.mp3_dir = tk.StringVar(value="mp3_files")
        self.export_dir = tk.StringVar(value="export")
        self.output_file = tk.StringVar(value="irish_music.apkg")
        self.deck_name = tk.StringVar(value="Irish Traditional Music")
        self.randomize_cards = tk.BooleanVar(value=True)
        self.current_language = tk.StringVar(value=get_current_language())
        
        # Card layout customization variables
        self.front_name = tk.BooleanVar(value=False)
        self.front_audio = tk.BooleanVar(value=True)
        self.front_key = tk.BooleanVar(value=False)
        self.front_rhythm = tk.BooleanVar(value=False)
        
        self.back_name = tk.BooleanVar(value=True)
        self.back_audio = tk.BooleanVar(value=False)
        self.back_key = tk.BooleanVar(value=True)
        self.back_rhythm = tk.BooleanVar(value=True)
        
        self.setup_gui()
        
    def change_language(self, *args):
        """Handle language change event"""
        new_language = self.current_language.get()
        if set_language(new_language):
            # Rebuild the interface with new language
            self.rebuild_interface()
    
    def rebuild_interface(self):
        """Rebuild the entire interface with new language strings"""
        # Store current values
        current_values = {
            'input_dir': self.input_dir.get(),
            'mp3_dir': self.mp3_dir.get(),
            'export_dir': self.export_dir.get(),
            'output_file': self.output_file.get(),
            'deck_name': self.deck_name.get(),
            'randomize_cards': self.randomize_cards.get(),
            'front_name': self.front_name.get(),
            'front_audio': self.front_audio.get(),
            'front_key': self.front_key.get(),
            'front_rhythm': self.front_rhythm.get(),
            'back_name': self.back_name.get(),
            'back_audio': self.back_audio.get(),
            'back_key': self.back_key.get(),
            'back_rhythm': self.back_rhythm.get(),
        }
        
        # Clear the main window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Update window title
        self.root.title(_("gui.title"))
        
        # Restore grid configuration
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Rebuild the GUI
        self.setup_gui()
        
        # Restore the values
        self.input_dir.set(current_values['input_dir'])
        self.mp3_dir.set(current_values['mp3_dir'])
        self.export_dir.set(current_values['export_dir'])
        self.output_file.set(current_values['output_file'])
        self.deck_name.set(current_values['deck_name'])
        self.randomize_cards.set(current_values['randomize_cards'])
        self.front_name.set(current_values['front_name'])
        self.front_audio.set(current_values['front_audio'])
        self.front_key.set(current_values['front_key'])
        self.front_rhythm.set(current_values['front_rhythm'])
        self.back_name.set(current_values['back_name'])
        self.back_audio.set(current_values['back_audio'])
        self.back_key.set(current_values['back_key'])
        self.back_rhythm.set(current_values['back_rhythm'])
        
        # Re-bind language change event (since the combobox was recreated)
        # Note: The combobox is now created in create_workflow_section
        self.language_combo.bind('<<ComboboxSelected>>', self.change_language)
        
    def setup_gui(self):
        # Create a canvas and scrollbar for the main content
        canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Main frame inside scrollable area
        main_frame = ttk.Frame(scrollable_frame, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Configure grid weights
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text=_("gui.title"), 
                               font=("", 16, "bold"))
        title_label.grid(row=0, column=0, pady=(0, 10), sticky="w")
        
        # Workflow explanation (collapsed by default)
        self.create_workflow_section(main_frame, row=1)
        
        # Input/Output Configuration
        self.create_io_section(main_frame, row=2)
        
        # Options
        self.create_options_section(main_frame, row=3)
        
        # Card Layout Customization
        self.create_card_layout_section(main_frame, row=4)
        
        # Action Buttons
        self.create_actions_section(main_frame, row=5)
        
        # Status
        self.create_status_section(main_frame, row=6)
        
        # Console output (larger)
        self.create_console_section(main_frame, row=7)
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
    def create_workflow_section(self, parent, row):
        # Container frame
        container = ttk.Frame(parent)
        container.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        container.grid_columnconfigure(0, weight=1)
        
        # Top frame for workflow button and language selector
        top_frame = ttk.Frame(container)
        top_frame.grid(row=0, column=0, sticky="ew")
        top_frame.grid_columnconfigure(0, weight=1)
        
        # Toggle button for collapsible section
        self.workflow_visible = tk.BooleanVar(value=False)  # Collapsed by default
        
        def toggle_workflow():
            if self.workflow_visible.get():
                workflow_content.grid_remove()
                toggle_btn.config(text=_("gui.workflow.title"))
                self.workflow_visible.set(False)
            else:
                workflow_content.grid()
                toggle_btn.config(text=_("gui.workflow.title_collapsed"))
                self.workflow_visible.set(True)
        
        toggle_btn = ttk.Button(top_frame, text=_("gui.workflow.title"), 
                               command=toggle_workflow)
        toggle_btn.grid(row=0, column=0, sticky="w")
        
        # Language selector on the right side
        language_frame = ttk.Frame(top_frame)
        language_frame.grid(row=0, column=1, sticky="e", padx=(20, 0))
        
        ttk.Label(language_frame, text=_("gui.label.language")).grid(row=0, column=0, sticky="w", padx=(0, 5))
        
        # Get available languages and create combobox
        available_langs = get_available_languages()
        language_values = list(available_langs.keys())
        
        self.language_combo = ttk.Combobox(language_frame, textvariable=self.current_language, 
                                          values=language_values, state="readonly", width=12)
        self.language_combo.grid(row=0, column=1, sticky="w")
        self.language_combo.bind('<<ComboboxSelected>>', self.change_language)
        
        # Content frame (hidden by default)
        workflow_content = ttk.LabelFrame(container, text="", padding="10")
        workflow_content.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        workflow_content.grid_columnconfigure(0, weight=1)
        workflow_content.grid_remove()  # Hide by default
        
        workflow_text = _("gui.workflow.description")
        
        workflow_label = ttk.Label(workflow_content, text=workflow_text, justify="left")
        workflow_label.grid(row=0, column=0, sticky="w")
        
    def create_io_section(self, parent, row):
        io_frame = ttk.LabelFrame(parent, text=_("gui.section.directories_files"), padding="10")
        io_frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        io_frame.grid_columnconfigure(1, weight=1)
        
        # Input Directory
        ttk.Label(io_frame, text=_("gui.label.input_directory")).grid(row=0, column=0, sticky="w", pady=2)
        input_frame = ttk.Frame(io_frame)
        input_frame.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        input_frame.grid_columnconfigure(0, weight=1)
        
        input_entry = ttk.Entry(input_frame, textvariable=self.input_dir, width=50)
        input_entry.grid(row=0, column=0, sticky="ew")
        ttk.Button(input_frame, text=_("gui.button.browse"), 
                  command=self.select_input_directory).grid(row=0, column=1, padx=(5, 0))
        
        # MP3 Directory
        ttk.Label(io_frame, text=_("gui.label.mp3_directory")).grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(io_frame, textvariable=self.mp3_dir, width=60).grid(row=1, column=1, sticky="ew", padx=(10, 0))
        
        # Export Directory
        ttk.Label(io_frame, text=_("gui.label.export_directory")).grid(row=2, column=0, sticky="w", pady=2)
        ttk.Entry(io_frame, textvariable=self.export_dir, width=60).grid(row=2, column=1, sticky="ew", padx=(10, 0))
        
        # Output File
        ttk.Label(io_frame, text=_("gui.label.output_file")).grid(row=3, column=0, sticky="w", pady=2)
        output_frame = ttk.Frame(io_frame)
        output_frame.grid(row=3, column=1, sticky="ew", padx=(10, 0))
        output_frame.grid_columnconfigure(0, weight=1)
        
        output_entry = ttk.Entry(output_frame, textvariable=self.output_file, width=50)
        output_entry.grid(row=0, column=0, sticky="ew")
        ttk.Button(output_frame, text=_("gui.button.browse"), 
                  command=self.select_output_file).grid(row=0, column=1, padx=(5, 0))
        
    def create_options_section(self, parent, row):
        options_frame = ttk.LabelFrame(parent, text=_("gui.section.options"), padding="10")
        options_frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        options_frame.grid_columnconfigure(1, weight=1)
        
        # Deck name
        ttk.Label(options_frame, text=_("gui.label.deck_name")).grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(options_frame, textvariable=self.deck_name, width=60).grid(row=0, column=1, sticky="ew", padx=(10, 0))
        
        # Randomize cards checkbox
        ttk.Checkbutton(options_frame, text=_("gui.checkbox.randomize_cards"), 
                       variable=self.randomize_cards).grid(row=1, column=0, columnspan=2, sticky="w", pady=5)
        
    def create_card_layout_section(self, parent, row):
        """Create the card layout customization section"""
        layout_frame = ttk.LabelFrame(parent, text=_("gui.section.card_layout"), padding="10")
        layout_frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        layout_frame.grid_columnconfigure(0, weight=1)
        layout_frame.grid_columnconfigure(1, weight=1)
        
        # Instructions
        instructions = ttk.Label(layout_frame, 
                                text=_("gui.card_layout.instruction"),
                                font=("", 9))
        instructions.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        
        # Front side
        front_frame = ttk.LabelFrame(layout_frame, text=_("gui.section.front_side"), padding="10")
        front_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 5))
        
        ttk.Checkbutton(front_frame, text=_("gui.checkbox.name"), 
                       variable=self.front_name).pack(anchor="w", pady=2)
        ttk.Checkbutton(front_frame, text=_("gui.checkbox.audio"), 
                       variable=self.front_audio).pack(anchor="w", pady=2)
        ttk.Checkbutton(front_frame, text=_("gui.checkbox.key"), 
                       variable=self.front_key).pack(anchor="w", pady=2)
        ttk.Checkbutton(front_frame, text=_("gui.checkbox.rhythm"), 
                       variable=self.front_rhythm).pack(anchor="w", pady=2)
        
        # Back side
        back_frame = ttk.LabelFrame(layout_frame, text=_("gui.section.back_side"), padding="10")
        back_frame.grid(row=1, column=1, sticky="nsew", padx=(5, 0))
        
        ttk.Checkbutton(back_frame, text=_("gui.checkbox.name"), 
                       variable=self.back_name).pack(anchor="w", pady=2)
        ttk.Checkbutton(back_frame, text=_("gui.checkbox.audio"), 
                       variable=self.back_audio).pack(anchor="w", pady=2)
        ttk.Checkbutton(back_frame, text=_("gui.checkbox.key"), 
                       variable=self.back_key).pack(anchor="w", pady=2)
        ttk.Checkbutton(back_frame, text=_("gui.checkbox.rhythm"), 
                       variable=self.back_rhythm).pack(anchor="w", pady=2)
        
        # Validation function to ensure at least one item is selected on front
        def validate_selection():
            if not any([self.front_name.get(), self.front_audio.get(), 
                       self.front_key.get(), self.front_rhythm.get()]):
                # If nothing selected on front, default to audio
                self.front_audio.set(True)
        
        # Bind validation to all checkboxes
        for var in [self.front_name, self.front_audio, self.front_key, self.front_rhythm]:
            var.trace('w', lambda *args: validate_selection())
        
        # Preview text
        preview_label = ttk.Label(layout_frame, 
                                 text=_("gui.card_layout.preview"),
                                 font=("", 8), foreground="gray")
        preview_label.grid(row=2, column=0, columnspan=2, sticky="w", pady=(10, 0))
        
    def create_actions_section(self, parent, row):
        actions_frame = ttk.LabelFrame(parent, text=_("gui.section.actions"), padding="10")
        actions_frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        
        # Individual step buttons
        step_frame = ttk.Frame(actions_frame)
        step_frame.grid(row=0, column=0, sticky="ew")
        
        self.convert_btn = ttk.Button(step_frame, text=_("gui.button.process_audio"), 
                                     command=self.run_convert, width=15)
        self.convert_btn.grid(row=0, column=0, padx=(0, 5))
        
        self.organize_btn = ttk.Button(step_frame, text=_("gui.button.organize_files"), 
                                      command=self.run_organize, width=15)
        self.organize_btn.grid(row=0, column=1, padx=5)
        
        self.generate_btn = ttk.Button(step_frame, text=_("gui.button.generate_cards"), 
                                      command=self.run_generate_cards, width=15)
        self.generate_btn.grid(row=0, column=2, padx=(5, 0))
        
        # Run all button
        self.all_btn = ttk.Button(actions_frame, text=_("gui.button.run_all"), 
                                 command=self.run_all, width=50)
        self.all_btn.grid(row=1, column=0, pady=(10, 0))
        
    def create_status_section(self, parent, row):
        status_frame = ttk.LabelFrame(parent, text=_("gui.section.status"), padding="10")
        status_frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        status_frame.grid_columnconfigure(0, weight=1)
        
        self.status_label = ttk.Label(status_frame, text=_("gui.status.ready"), foreground="gray")
        self.status_label.grid(row=0, column=0, sticky="w")
        
        ttk.Button(status_frame, text=_("gui.button.clear_console"), 
                  command=self.clear_console).grid(row=0, column=1, sticky="e")
        
    def create_console_section(self, parent, row):
        console_frame = ttk.LabelFrame(parent, text=_("gui.section.console_output"), padding="10")
        console_frame.grid(row=row, column=0, sticky="ew", pady=(0, 0))
        console_frame.grid_columnconfigure(0, weight=1)
        
        # Make console much larger and properly scrollable
        self.console = scrolledtext.ScrolledText(
            console_frame, 
            height=20,  # Increased height
            width=100,  # Fixed width to prevent layout issues
            wrap=tk.WORD,
            font=("Consolas", 9)  # Monospace font for better readability
        )
        self.console.grid(row=0, column=0, sticky="ew", pady=(0, 0))
        
        # Initial help text
        self.clear_console()
        
    def log_message(self, message):
        try:
            # Insert message at end
            self.console.insert(tk.END, message)
            # Force scroll to bottom
            self.console.see(tk.END)
            # Ensure the console is always scrolled to show latest content
            self.console.mark_set(tk.INSERT, tk.END)
            self.console.update_idletasks()
            self.root.update_idletasks()
        except Exception:
            print(message, end="")
        
    def clear_console(self):
        self.console.delete(1.0, tk.END)
        help_text = _("gui.console.help_text")
        self.console.insert(tk.END, help_text)
        
    def set_status(self, status):
        self.status_label.config(text=status)
        
    def capture_console_output(self):
        self.console_capture = ConsoleCapture(self.log_message)
        sys.stdout = self.console_capture
        sys.stderr = self.console_capture
        
    def restore_console_output(self):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        
    def select_input_directory(self):
        # Start in user's home directory by default
        initial_dir = str(Path.home())
        if self.input_dir.get() and Path(self.input_dir.get()).exists():
            initial_dir = self.input_dir.get()
        
        # Use our custom directory picker
        dialog = DirectoryPickerDialog(
            self.root, 
            title=_("gui.dialog.select_input_directory"),
            initial_dir=initial_dir
        )
        selected_directory = dialog.show()
        
        if selected_directory:
            self.input_dir.set(selected_directory)
            
    def select_output_file(self):
        filename = filedialog.asksaveasfilename(
            title=_("gui.dialog.save_anki_deck"),
            defaultextension=".apkg",
            filetypes=[("Anki Package", "*.apkg"), ("All Files", "*.*")]
        )
        if filename:
            self.output_file.set(filename)
            
    def validate_and_create_directories(self, input_dir, mp3_dir, export_dir):
        if not input_dir or not Path(input_dir).exists():
            self.log_message(f"❌ Error: Input directory '{input_dir}' does not exist or is not selected\n")
            return False
            
        if mp3_dir and mp3_dir != "dummy":
            mp3_path = Path(mp3_dir)
            if not mp3_path.exists():
                try:
                    mp3_path.mkdir(parents=True, exist_ok=True)
                    self.log_message(f"📁 Created MP3 directory: {mp3_dir}\n")
                except Exception as e:
                    self.log_message(f"❌ Error creating MP3 directory '{mp3_dir}': {e}\n")
                    return False
                    
        if export_dir and export_dir != "dummy":
            export_path = Path(export_dir)
            if not export_path.exists():
                try:
                    export_path.mkdir(parents=True, exist_ok=True)
                    self.log_message(f"📁 Created export directory: {export_dir}\n")
                except Exception as e:
                    self.log_message(f"❌ Error creating export directory '{export_dir}': {e}\n")
                    return False
                    
        return True
        
    def disable_buttons(self):
        self.convert_btn.config(state="disabled")
        self.organize_btn.config(state="disabled")
        self.generate_btn.config(state="disabled")
        self.all_btn.config(state="disabled")
        
    def enable_buttons(self):
        self.convert_btn.config(state="normal")
        self.organize_btn.config(state="normal")
        self.generate_btn.config(state="normal")
        self.all_btn.config(state="normal")
            
    def run_convert(self):
        def convert_task():
            try:
                self.disable_buttons()
                self.set_status("Starting conversion...")
                self.capture_console_output()
                
                input_dir = self.input_dir.get()
                mp3_dir = self.mp3_dir.get()
                
                self.log_message("🎵 PROCESS: Audio files → MP3 format\n")
                self.log_message("=" * 50 + "\n")
                
                if not self.validate_and_create_directories(input_dir, mp3_dir, ""):
                    self.set_status("Validation failed")
                    return
                
                success = convert_to_mp3(input_dir, mp3_dir)
                
                if success:
                    self.set_status("Processing completed!")
                    self.log_message("\n✅ Processing completed successfully!\n")
                    self.log_message(f"📁 MP3 files are now in: {mp3_dir}\n")
                else:
                    self.set_status("Processing failed")
                    self.log_message("\n❌ Processing failed\n")
                    
            except Exception as e:
                self.log_message(f"\n❌ Error during processing: {e}\n")
                self.set_status("Error occurred")
            finally:
                self.restore_console_output()
                self.enable_buttons()
                
        threading.Thread(target=convert_task, daemon=True).start()
        
    def run_organize(self):
        def organize_task():
            try:
                self.disable_buttons()
                self.set_status("Starting organization...")
                self.capture_console_output()
                
                mp3_dir = self.mp3_dir.get()
                export_dir = self.export_dir.get()
                
                self.log_message("🗂️  ORGANIZE: MP3 files → Organized by rhythm/metadata\n")
                self.log_message("=" * 50 + "\n")
                
                if not Path(mp3_dir).exists():
                    self.log_message(f"❌ Error: MP3 directory '{mp3_dir}' does not exist\n")
                    self.log_message("💡 Tip: Run 'Process Audio' first, or check your MP3 directory path\n")
                    self.set_status("Directory not found")
                    return
                
                if not self.validate_and_create_directories(mp3_dir, "", export_dir):
                    self.set_status("Cannot create export directory")
                    return
                    
                success = organize_music_files(mp3_dir, export_dir)
                
                if success:
                    self.set_status("Organization completed!")
                    self.log_message("\n✅ Organization completed successfully!\n")
                    self.log_message(f"📁 Organized files are now in: {export_dir}\n")
                else:
                    self.set_status("Organization failed")
                    self.log_message("\n❌ Organization failed\n")
                    
            except Exception as e:
                self.log_message(f"\n❌ Error during organization: {e}\n")
                self.set_status("Error occurred")
            finally:
                self.restore_console_output()
                self.enable_buttons()
                
        threading.Thread(target=organize_task, daemon=True).start()
        
    def run_generate_cards(self):
        def generate_task():
            try:
                self.disable_buttons()
                self.set_status("Starting card generation...")
                self.capture_console_output()
                
                music_dir = self.export_dir.get()
                output_file = self.output_file.get()
                deck_name = self.deck_name.get()
                randomize = self.randomize_cards.get()
                
                # Collect card layout options
                card_layout = {
                    'front': {
                        'name': self.front_name.get(),
                        'audio': self.front_audio.get(),
                        'key': self.front_key.get(),
                        'rhythm': self.front_rhythm.get()
                    },
                    'back': {
                        'name': self.back_name.get(),
                        'audio': self.back_audio.get(),
                        'key': self.back_key.get(),
                        'rhythm': self.back_rhythm.get()
                    }
                }
                
                self.log_message("🎴 GENERATE: Organized files → Anki deck (.apkg)\n")
                self.log_message("=" * 50 + "\n")
                
                if not Path(music_dir).exists():
                    self.log_message(f"❌ Error: Export directory '{music_dir}' does not exist\n")
                    self.log_message("💡 Tip: Run 'Organize Files' first, or check your export directory path\n")
                    self.set_status("Directory not found")
                    return
                    
                success = generate_anki_cards(music_dir, output_file, deck_name, randomize, card_layout)
                
                if success:
                    self.set_status("Cards generated!")
                    self.log_message("\n✅ Anki cards generated successfully!\n")
                    self.log_message(f"📱 Ready to import: {output_file}\n")
                else:
                    self.set_status("Card generation failed")
                    self.log_message("\n❌ Card generation failed\n")
                    
            except Exception as e:
                self.log_message(f"\n❌ Error during card generation: {e}\n")
                self.set_status("Error occurred")
            finally:
                self.restore_console_output()
                self.enable_buttons()
                
        threading.Thread(target=generate_task, daemon=True).start()
        
    def run_all(self):
        def all_task():
            try:
                self.disable_buttons()
                self.set_status("Starting full process...")
                self.capture_console_output()
                
                input_dir = self.input_dir.get()
                mp3_dir = self.mp3_dir.get()
                export_dir = self.export_dir.get()
                output_file = self.output_file.get()
                deck_name = self.deck_name.get()
                randomize = self.randomize_cards.get()
                
                # Collect card layout options
                card_layout = {
                    'front': {
                        'name': self.front_name.get(),
                        'audio': self.front_audio.get(),
                        'key': self.front_key.get(),
                        'rhythm': self.front_rhythm.get()
                    },
                    'back': {
                        'name': self.back_name.get(),
                        'audio': self.back_audio.get(),
                        'key': self.back_key.get(),
                        'rhythm': self.back_rhythm.get()
                    }
                }
                
                self.log_message("🚀 FULL WORKFLOW: Audio → MP3 → Organized → Anki Deck\n")
                self.log_message("=" * 60 + "\n")
                
                if not self.validate_and_create_directories(input_dir, mp3_dir, export_dir):
                    self.set_status("Validation failed")
                    return
                
                self.log_message("🎵 Step 1: Processing audio files...\n")
                self.set_status("Step 1: Processing audio files...")
                if not convert_to_mp3(input_dir, mp3_dir):
                    self.set_status("Processing failed")
                    self.log_message("❌ Audio processing failed, stopping process\n")
                    return
                
                self.log_message("\n🗂️  Step 2: Organizing music files...\n")
                self.set_status("Step 2: Organizing music files...")
                if not organize_music_files(mp3_dir, export_dir):
                    self.set_status("Organization failed")
                    self.log_message("❌ Organization failed, stopping process\n")
                    return
                
                # Clean up MP3 directory after successful organization
                try:
                    if Path(mp3_dir).exists():
                        shutil.rmtree(mp3_dir)
                        self.log_message(f"🗑️  Cleaned up temporary MP3 directory: {mp3_dir}\n")
                except Exception as e:
                    self.log_message(f"⚠️  Could not remove MP3 directory: {e}\n")
                
                self.log_message("\n🎴 Step 3: Generating Anki .apkg file...\n")
                self.set_status("Step 3: Generating Anki cards...")
                if generate_anki_cards(export_dir, output_file, deck_name, randomize, card_layout):
                    self.set_status("All steps completed!")
                    self.log_message("\n🎉 All steps completed successfully!\n")
                    self.log_message(f"📱 Your Anki deck is ready: {output_file}\n")
                else:
                    self.set_status("Card generation failed")
                    self.log_message("❌ Card generation failed\n")
                    
            except Exception as e:
                self.log_message(f"\n❌ Error during process: {e}\n")
                self.set_status("Error occurred")
            finally:
                self.restore_console_output()
                self.enable_buttons()
                
        threading.Thread(target=all_task, daemon=True).start()
        
    def run(self):
        """Start the GUI application"""
        self.root.mainloop()


def main():
    app = IrishAnkiGUI()
    app.run()


if __name__ == "__main__":
    main() 