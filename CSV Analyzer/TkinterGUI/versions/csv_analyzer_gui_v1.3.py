"""
CSV Analyzer

A user-friendly, multi-tool CSV analysis application with a GUI (Tkinter).
Features:
- Column Length Checker: Find rows with column values exceeding a length threshold.
- Find Duplicates: Identify duplicate values in a specified column.
- Find Extra Delimiters: Detect rows with more columns than expected and pinpoint extra delimiter positions.
- Handles huge files (multi-GB) efficiently using streaming and threading.
- Export results to CSV.
- Customizable delimiter and header options.
- Designed for both script and PyInstaller executable use.

Logging:
- Logs key actions and errors to csv_analyzer.log in the application directory.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import csv
import sys
import logging

# Setup logging
if getattr(sys, 'frozen', False):
    app_dir = os.path.dirname(sys.executable)
else:
    app_dir = os.path.dirname(os.path.abspath(__file__))
log_path = os.path.join(app_dir, "csv_analyzer.log")
logging.basicConfig(
    filename=log_path,
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)
logging.info("Application started")

class CSVAnalyzerApp:
    """
    Main application class for the CSV Analyzer GUI.
    Provides a tabbed interface for column length checking, duplicate finding, and extra delimiter detection.
    Handles large files efficiently and supports exporting results.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("CSV Analyzer")
        
        # Set window icon
        try:
            # Handle PyInstaller's temporary directory
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                application_path = sys._MEIPASS
            else:
                # Running as script
                application_path = os.path.dirname(os.path.abspath(__file__))
            
            icon_path = os.path.join(application_path, "magni.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
            else:
                # Fallback: try to find the icon in the current working directory
                icon_path = "magni.ico"
                if os.path.exists(icon_path):
                    self.root.iconbitmap(icon_path)
        except Exception as e:
            logging.warning(f"Could not load icon: {e}")
        
        self.filename = None
        self.delimiter = tk.StringVar(value=',')
        self.has_header = tk.BooleanVar(value=False)
        self.ignore_first_row = tk.BooleanVar(value=True)
        self.processing_thread = None
        self.cancel_flag = False  # Flag to signal cancellation
        self.length_results = []  # Store all matches for export
        self.length_max_display = 1000  # Max rows to display in Treeview
        self.dup_results = []  # Store all duplicate matches for export
        self.dup_max_display = 1000
        self.extra_results = []  # Store all extra delimiter matches for export
        self.extra_max_display = 1000
        self.progress_popup = None

        # Set minimum window size
        self.root.minsize(1000, 600)

        # --- Menu Bar ---
        menubar = tk.Menu(self.root)
        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="About", command=self.show_about_dialog)
        menubar.add_cascade(label="Help", menu=helpmenu)
        self.root.config(menu=menubar)

        # --- Styles ---
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", font=("Segoe UI", 11, "bold"), padding=6)
        style.configure("TLabel", font=("Segoe UI", 11))
        style.configure("Treeview.Heading", font=("Segoe UI", 12, "bold"), background="#e3eafc", foreground="#1a237e")
        style.configure("Treeview", font=("Consolas", 10), rowheight=24)
        style.configure("TLabelframe.Label", font=("Segoe UI", 12, "bold"))

        # --- Shared Controls ---
        shared_frame = ttk.Frame(self.root, padding="10 10 0 10")
        shared_frame.pack(fill="x")
        self.file_label = ttk.Label(shared_frame, text="No file selected", style="TLabel")
        self.file_label.grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.browse_btn = ttk.Button(shared_frame, text="📂 Browse...", command=self.browse_file, width=15)
        self.browse_btn.grid(row=0, column=1, sticky="w", padx=(0, 10))
        self.clear_btn = ttk.Button(shared_frame, text="Clear", command=self.clear_all, width=10)
        self.clear_btn.grid(row=0, column=2, sticky="w", padx=(0, 10))
        ttk.Label(shared_frame, text="Delimiter:", style="TLabel").grid(row=0, column=3, sticky="e", padx=5)
        self.delimiter_label = ttk.Label(shared_frame, text="Auto-detecting...", style="TLabel")
        self.delimiter_label.grid(row=0, column=4, sticky="w", padx=5)
        self.header_check = ttk.Checkbutton(shared_frame, text="File has header", variable=self.has_header)
        self.header_check.grid(row=0, column=5, sticky="w", padx=10)
        self.ignore_first_check = ttk.Checkbutton(shared_frame, text="Ignore first row", variable=self.ignore_first_row)
        self.ignore_first_check.grid(row=0, column=6, sticky="w", padx=10)
        self.analyze_btn = ttk.Button(shared_frame, text="Analyze File", command=self.analyze_file_structure, width=12)
        self.analyze_btn.grid(row=0, column=7, sticky="w", padx=10)

        # --- Tabs ---
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Column Length Checker Tab ---
        self.tab_length = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_length, text="Column Length Checker")
        self._init_length_tab()

        # --- Find Duplicates Tab ---
        self.tab_duplicates = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_duplicates, text="Find Duplicates")
        self._init_duplicates_tab()

        # --- Find Extra Delimiters Tab ---
        self.tab_extra = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_extra, text="Find Extra Delimiters")
        self._init_extra_tab()

        # --- Status Bar ---
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w", padding="5 2 5 2", style="TLabel")
        self.status_bar.pack(fill="x", side="bottom")

    def show_about_dialog(self):
        """Show the About dialog with app information and GitHub link."""
        import webbrowser
        about = tk.Toplevel(self.root)
        about.title("About CSV Analyzer")
        about.resizable(False, False)
        about.grab_set()
        
        # Set icon for about dialog
        try:
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                application_path = sys._MEIPASS
            else:
                # Running as script
                application_path = os.path.dirname(os.path.abspath(__file__))
            
            icon_path = os.path.join(application_path, "magni.ico")
            if os.path.exists(icon_path):
                about.iconbitmap(icon_path)
            else:
                # Fallback: try to find the icon in the current working directory
                icon_path = "magni.ico"
                if os.path.exists(icon_path):
                    about.iconbitmap(icon_path)
        except Exception as e:
            logging.warning(f"Could not load icon for about dialog: {e}")
        tk.Label(about, text="CSV Analyzer", font=("Segoe UI", 14, "bold")).pack(pady=(10, 0))
        tk.Label(about, text="Version 1.3", font=("Segoe UI", 10)).pack()
        tk.Label(about, text="A user-friendly, multi-tool CSV analysis application.\n"
                             "- Column Length Checker\n"
                             "- Find Duplicates\n"
                             "- Find Extra Delimiters\n",
                 justify="left").pack(padx=20, pady=(10, 0))
        tk.Label(about, text="Developed by Xenofon Psychis - Filis.", font=("Segoe UI", 10, "italic")).pack(pady=(5, 0))
        tk.Label(about, text="Contact: [p.xenophon@gmail.com]", font=("Segoe UI", 10)).pack(pady=(0, 10))

        def open_github(event=None):
            webbrowser.open("https://github.com/psycxeno/XenophonPsychisFilis/tree/main/CSV%20Analyzer")

        link = tk.Label(about, text="View README on GitHub", fg="blue", cursor="hand2", font=("Segoe UI", 10, "underline"))
        link.pack(pady=(0, 10))
        link.bind("<Button-1>", open_github)

    def get_delimiter(self):
        """Convert delimiter input to actual character (e.g., '\\t' -> tab)"""
        delim = self.delimiter.get()
        if delim == '\\t':
            return '\t'
        elif delim == '\\n':
            return '\n'
        elif delim == '\\r':
            return '\r'
        elif delim == '\\':  # Backslash delimiter
            return '\\'
        elif delim == '\t':  # Already a tab character from dropdown
            return '\t'
        elif delim == '\n':  # Already a newline character from dropdown
            return '\n'
        elif delim == '\r':  # Already a carriage return character from dropdown
            return '\r'
        else:
            return delim

    def auto_detect_delimiter(self):
        """Auto-detect the delimiter by testing different delimiters on the file."""
        if not self.filename:
            return None
            
        try:
            delimiters = [',', '\t', ';', '|', '\\']
            results = {}
            
            for delim in delimiters:
                with open(self.filename, 'r', encoding='utf-8', errors='ignore') as f:
                    try:
                        # Handle backslash delimiter specially
                        if delim == '\\':
                            # For backslash, we need to read the file as text and split manually
                            f.seek(0)
                            lines = []
                            for i, line in enumerate(f):
                                if i < 20:  # Sample more lines to find actual data
                                    lines.append(line.strip())
                                else:
                                    break
                            
                            if lines:
                                # Find the first line that looks like actual data (has multiple columns)
                                data_lines = []
                                for line in lines:
                                    if line:
                                        parts = line.split('\\')
                                        if len(parts) > 3:  # Assume actual data has more than 3 columns
                                            data_lines.append(parts)
                                        if len(data_lines) >= 5:  # Get 5 data lines
                                            break
                                
                                if data_lines:
                                    col_counts = [len(row) for row in data_lines]
                                    avg_cols = sum(col_counts) / len(col_counts) if col_counts else 0
                                    consistency = len(set(col_counts)) == 1 if col_counts else False
                                    
                                    # Only consider delimiters that give reasonable column counts (>1)
                                    if avg_cols > 1:
                                        results[delim] = (avg_cols, consistency, max(col_counts))
                        else:
                            # Use CSV reader for other delimiters
                            reader = csv.reader(f, delimiter=delim)
                            # Read more rows to find actual data structure
                            rows = []
                            for i, row in enumerate(reader):
                                if i < 20:  # Sample more rows to find actual data
                                    rows.append(row)
                                else:
                                    break
                            
                            if rows:
                                # Find rows that look like actual data (have multiple columns)
                                data_rows = []
                                for row in rows:
                                    if row and len(row) > 3:  # Assume actual data has more than 3 columns
                                        data_rows.append(row)
                                    if len(data_rows) >= 5:  # Get 5 data rows
                                        break
                                
                                if data_rows:
                                    # Calculate average columns and consistency
                                    col_counts = [len(row) for row in data_rows]
                                    avg_cols = sum(col_counts) / len(col_counts)
                                    consistency = len(set(col_counts)) == 1  # All rows have same column count
                                    
                                    # Only consider delimiters that give reasonable column counts (>1)
                                    if avg_cols > 1:
                                        results[delim] = (avg_cols, consistency, max(col_counts))
                            
                    except StopIteration:
                        continue
                    except Exception as e:
                        logging.error(f"Error processing delimiter {delim}: {e}")
                        continue
            
            if not results:
                return None
            
            # Find the best delimiter (prefer highest column count, then consistency)
            best_delim = None
            best_score = (0, False, 0)
            
            for delim, (avg_cols, consistent, max_cols) in results.items():
                if consistent and avg_cols > best_score[0]:
                    best_delim = delim
                    best_score = (avg_cols, consistent, max_cols)
                elif not best_delim and avg_cols > best_score[0]:
                    # If no consistent delimiter found, take the one with most columns
                    best_delim = delim
                    best_score = (avg_cols, consistent, max_cols)
            
            # If still no good delimiter found, use the one with most columns
            if best_delim is None:
                best_delim = max(results, key=lambda k: results[k][0])
            
            return best_delim
            
        except Exception as e:
            logging.error(f"Auto-delimiter detection failed: {e}")
            return None

    def analyze_file_structure(self):
        """Analyze the file structure to help determine the correct delimiter."""
        if not self.filename:
            messagebox.showerror("Error", "Please select a CSV file first.")
            return
            
        try:
            # Use the same auto-detection logic as browse_file
            best_delim = self.auto_detect_delimiter()
            
            if not best_delim:
                messagebox.showwarning("File Analysis", "Could not determine the delimiter. Please try manual selection.")
                logging.warning("File structure analysis could not determine delimiter")
                return
            
            # Count rows and determine column count
            row_count = 0
            column_count = 0
            
            with open(self.filename, 'r', encoding='utf-8', errors='ignore') as f:
                if best_delim == '\\':
                    # For backslash, count lines manually
                    for line in f:
                        if line.strip():  # Skip empty lines
                            parts = line.strip().split('\\')
                            if len(parts) > 3:  # Only count lines that look like actual data
                                row_count += 1
                                if row_count == 1:  # First data line determines column count
                                    column_count = len(parts)
                else:
                    # Use CSV reader for other delimiters
                    reader = csv.reader(f, delimiter=best_delim)
                    for row in reader:
                        if row and len(row) > 3:  # Only count rows that look like actual data
                            row_count += 1
                            if row_count == 1:  # First data row determines column count
                                column_count = len(row)
            
            # Update the delimiter if we found a good one
            if best_delim:
                self.delimiter.set(best_delim)
                delim_name = {'\t': 'Tab', ',': 'Comma', ';': 'Semicolon', '|': 'Pipe', '\\': 'Backslash'}[best_delim]
                #self.delimiter_label.config(text=f"Detected: {delim_name}")
                self.delimiter_label.config(text=f"{delim_name}")
                
                # Show results
                message = f"File Analysis Results:\n\n"
                message += f"1. Delimiter: {delim_name}\n"
                message += f"2. Number of columns: {column_count}\n"
                message += f"3. Number of rows: {row_count}\n"
                
                messagebox.showinfo("File Analysis", message)
                logging.info(f"File structure analysis completed. Delimiter: {best_delim}, Columns: {column_count}, Rows: {row_count}")
            else:
                messagebox.showwarning("File Analysis", "Could not determine the delimiter. Please try manual selection.")
                logging.warning("File structure analysis could not determine delimiter")
                
        except Exception as e:
            messagebox.showerror("Analysis Error", f"Error analyzing file structure: {e}")
            logging.error(f"File structure analysis failed: {e}")

    def browse_file(self):
        """Open file dialog to select a CSV file."""
        filetypes = [("All files", "*.*"), ("CSV files", "*.csv")]
        filename = filedialog.askopenfilename(title="Select file to analyze", filetypes=filetypes)
        if filename:
            self.filename = filename
            self.file_label.config(text=os.path.basename(filename))
            
            # Auto-detect delimiter
            detected_delim = self.auto_detect_delimiter()
            if detected_delim:
                self.delimiter.set(detected_delim)
                delim_name = {'\t': 'Tab', ',': 'Comma', ';': 'Semicolon', '|': 'Pipe', '\\': 'Backslash'}[detected_delim]
                #self.delimiter_label.config(text=f"Detected: {delim_name}")
                self.delimiter_label.config(text=f"{delim_name}")
                #self.set_status(f"File loaded: {os.path.basename(filename)} (Detected: {delim_name})")
                self.set_status(f"File loaded: {os.path.basename(filename)} (Delimiter: {delim_name})")
                logging.info(f"Auto-detected delimiter: {detected_delim} ({delim_name})")
                
                # Show file loaded popup
                messagebox.showinfo("File Loaded", 
                    f"File loaded successfully!\n\n"
                    f"File: {os.path.basename(filename)}\n"
                    f"Detected delimiter: {delim_name}\n\n"
                    f"You can now use any of the analysis tools.")
            else:
                self.delimiter_label.config(text="Unknown")
                self.set_status(f"File loaded: {os.path.basename(filename)} (Delimiter unknown)")
                logging.warning("Could not auto-detect delimiter")
                
                # Show warning popup
                messagebox.showwarning("File Loaded", 
                    f"File loaded but delimiter could not be detected.\n\n"
                    f"File: {os.path.basename(filename)}\n"
                    f"Delimiter: Unknown\n\n"
                    f"Please use 'Analyze File' to determine the correct delimiter.")
            
            logging.info(f"User selected file: {os.path.basename(filename)}")
        else:
            self.set_status("No file selected.")
            logging.warning("User cancelled file selection.")

    def clear_all(self):
        """Clear all results and reset the application state."""
        self.filename = None
        self.file_label.config(text="No file selected")
        self.delimiter_label.config(text="Auto-detecting...")
        self.set_status("Ready")
        logging.info("User cleared all results and status.")
        # Clear all tabs' results and status
        self.length_tree.delete(*self.length_tree.get_children())
        self.length_status.config(text="")
        self.length_export_btn.config(state="disabled")
        self.dup_tree.delete(*self.dup_tree.get_children())
        self.dup_status.config(text="")
        self.dup_export_btn.config(state="disabled")
        self.extra_tree.delete(*self.extra_tree.get_children())
        self.extra_status.config(text="")
        self.extra_export_btn.config(state="disabled")
        
        # Show clear confirmation popup
        messagebox.showinfo("Cleared", 
            "All results and file selection have been cleared.\n\n"
            "The application is ready for a new analysis.")

    def set_status(self, msg):
        """Update the status bar message."""
        self.status_var.set(msg)
        self.status_bar.update_idletasks()
        logging.info(f"Status updated: {msg}")

    # --- Progress Popup ---
    def show_progress_popup(self, message="Processing... Please wait."):
        """Show a modal progress popup during long operations."""
        self.progress_popup = tk.Toplevel(self.root)
        self.progress_popup.title("Processing")
        self.progress_popup.geometry("300x150")  # Increased height for cancel button
        self.progress_popup.resizable(False, False)
        self.progress_popup.transient(self.root)
        self.progress_popup.grab_set()
        
        # Set icon for progress popup
        try:
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                application_path = sys._MEIPASS
            else:
                # Running as script
                application_path = os.path.dirname(os.path.abspath(__file__))
            
            icon_path = os.path.join(application_path, "magni.ico")
            if os.path.exists(icon_path):
                self.progress_popup.iconbitmap(icon_path)
            else:
                # Fallback: try to find the icon in the current working directory
                icon_path = "magni.ico"
                if os.path.exists(icon_path):
                    self.progress_popup.iconbitmap(icon_path)
        except Exception as e:
            logging.warning(f"Could not load icon for progress popup: {e}")
        
        # Center the popup
        self.progress_popup.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
        
        ttk.Label(self.progress_popup, text=message, font=("Segoe UI", 11)).pack(pady=15)
        pb = ttk.Progressbar(self.progress_popup, mode='indeterminate')
        pb.pack(pady=10, padx=20, fill="x")
        pb.start(10)
        
        # Add cancel button
        self.cancel_button = ttk.Button(self.progress_popup, text="Cancel", command=self.cancel_operation, width=10)
        self.cancel_button.pack(pady=10)
        
        self.progress_popup.protocol("WM_DELETE_WINDOW", lambda: None)  # Disable close
        logging.info(f"Progress popup shown: {message}")
    
    def cancel_operation(self):
        """Cancel the current processing operation."""
        self.cancel_flag = True
        if self.progress_popup:
            self.progress_popup.destroy()
            self.progress_popup = None
        logging.info("User cancelled processing operation")
        messagebox.showinfo("Cancelled", "Processing has been cancelled by the user.")

    def close_progress_popup(self):
        """Close the progress popup."""
        if self.progress_popup:
            self.progress_popup.destroy()
            self.progress_popup = None
            logging.info("Progress popup closed.")

    # --- Tab Initializers ---
    def _init_length_tab(self):
        """Initialize the Column Length Checker tab."""
        # Controls frame
        controls_frame = ttk.Frame(self.tab_length, padding="10")
        controls_frame.pack(fill="x")
        
        ttk.Label(controls_frame, text="Column (name or index):", style="TLabel").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.length_col_entry = ttk.Entry(controls_frame, width=20)
        self.length_col_entry.grid(row=0, column=1, sticky="w", padx=(0, 10))
        
        ttk.Label(controls_frame, text="Length threshold:", style="TLabel").grid(row=0, column=2, sticky="w", padx=(0, 5))
        self.length_thresh_entry = ttk.Entry(controls_frame, width=10)
        self.length_thresh_entry.insert(0, "25")
        self.length_thresh_entry.grid(row=0, column=3, sticky="w", padx=(0, 10))
        
        ttk.Button(controls_frame, text="Check", command=self.run_length_check, width=10).grid(row=0, column=4, padx=(0, 10))
        self.length_export_btn = ttk.Button(controls_frame, text="Export Results", command=self.export_length_results, width=12, state="disabled")
        self.length_export_btn.grid(row=0, column=5)
        
        # Status label
        self.length_status = ttk.Label(controls_frame, text="", style="TLabel")
        self.length_status.grid(row=1, column=0, columnspan=6, sticky="w", pady=(5, 0))
        
        # Results tree
        tree_frame = ttk.Frame(self.tab_length)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.length_tree = ttk.Treeview(tree_frame, columns=("row", "column", "value"), show="headings", height=15)
        self.length_tree.heading("row", text="Row")
        self.length_tree.heading("column", text="Column")
        self.length_tree.heading("value", text="Value")
        self.length_tree.column("row", width=80)
        self.length_tree.column("column", width=150)
        self.length_tree.column("value", width=400)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.length_tree.yview)
        self.length_tree.configure(yscrollcommand=scrollbar.set)
        
        self.length_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _init_duplicates_tab(self):
        """Initialize the Find Duplicates tab."""
        # Controls frame
        controls_frame = ttk.Frame(self.tab_duplicates, padding="10")
        controls_frame.pack(fill="x")
        
        ttk.Label(controls_frame, text="Column (name or index):", style="TLabel").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.dup_col_entry = ttk.Entry(controls_frame, width=20)
        self.dup_col_entry.grid(row=0, column=1, sticky="w", padx=(0, 10))
        
        ttk.Button(controls_frame, text="Check", command=self.run_dup_check, width=10).grid(row=0, column=2, padx=(0, 10))
        self.dup_export_btn = ttk.Button(controls_frame, text="Export Results", command=self.export_dup_results, width=12, state="disabled")
        self.dup_export_btn.grid(row=0, column=3)
        
        # Status label
        self.dup_status = ttk.Label(controls_frame, text="", style="TLabel")
        self.dup_status.grid(row=1, column=0, columnspan=4, sticky="w", pady=(5, 0))
        
        # Results tree
        tree_frame = ttk.Frame(self.tab_duplicates)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.dup_tree = ttk.Treeview(tree_frame, columns=("row", "column", "value"), show="headings", height=15)
        self.dup_tree.heading("row", text="Row")
        self.dup_tree.heading("column", text="Column")
        self.dup_tree.heading("value", text="Value")
        self.dup_tree.column("row", width=80)
        self.dup_tree.column("column", width=150)
        self.dup_tree.column("value", width=400)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.dup_tree.yview)
        self.dup_tree.configure(yscrollcommand=scrollbar.set)
        
        self.dup_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _init_extra_tab(self):
        """Initialize the Find Extra Delimiters tab."""
        # Controls frame
        controls_frame = ttk.Frame(self.tab_extra, padding="10")
        controls_frame.pack(fill="x")
        
        ttk.Button(controls_frame, text="Check", command=self.run_extra_check, width=10).grid(row=0, column=0, padx=(0, 10))
        self.extra_export_btn = ttk.Button(controls_frame, text="Export Results", command=self.export_extra_results, width=12, state="disabled")
        self.extra_export_btn.grid(row=0, column=1)
        
        # Status label
        self.extra_status = ttk.Label(controls_frame, text="", style="TLabel")
        self.extra_status.grid(row=1, column=0, columnspan=2, sticky="w", pady=(5, 0))
        
        # Results tree
        tree_frame = ttk.Frame(self.tab_extra)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.extra_tree = ttk.Treeview(tree_frame, columns=("row", "extra_cols", "row_data"), show="headings", height=15)
        self.extra_tree.heading("row", text="Row")
        self.extra_tree.heading("extra_cols", text="Extra Columns")
        self.extra_tree.heading("row_data", text="Row Data")
        self.extra_tree.column("row", width=80)
        self.extra_tree.column("extra_cols", width=150)
        self.extra_tree.column("row_data", width=400)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.extra_tree.yview)
        self.extra_tree.configure(yscrollcommand=scrollbar.set)
        
        self.extra_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    # --- Column Length Checker Logic ---
    def run_length_check(self):
        """Start the column length check process."""
        if not self.filename:
            messagebox.showerror("Error", "Please select a CSV file.")
            logging.warning("User attempted to run length check without a file.")
            return
        col = self.length_col_entry.get().strip()
        if not col:
            messagebox.showerror("Error", "Please specify a column name or index.")
            logging.warning("User attempted to run length check with empty column name.")
            return
        try:
            threshold = int(self.length_thresh_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Length threshold must be an integer.")
            logging.warning(f"User entered invalid length threshold: {self.length_thresh_entry.get()}")
            return
        self.length_tree.delete(*self.length_tree.get_children())
        self.length_results = []
        self.show_progress_popup()
        logging.info(f"User initiated length check for column '{col}' with threshold {threshold}.")
        # Start background thread
        t = threading.Thread(target=self._length_check_worker, args=(col, threshold), daemon=True)
        t.start()

    def _length_check_worker(self, col, threshold):
        """Background worker for column length checking."""
        # Reset cancel flag at start
        self.cancel_flag = False
        
        try:
            delim = self.get_delimiter()
            matches = 0
            with open(self.filename, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.reader(f, delimiter=delim)
                row_num = 0
                col_idx = None
                header = None
                
                for row in reader:
                    # Check for cancellation
                    if self.cancel_flag:
                        self._update_length_status("Processing cancelled by user.")
                        logging.info("Length check cancelled by user")
                        return
                    
                    if not row:
                        continue  # skip empty rows
                    row_num += 1
                    
                    if row_num == 1 and self.has_header.get():
                        header = row
                        # Find column index
                        if col.isdigit():
                            col_idx = int(col)
                        else:
                            try:
                                col_idx = header.index(col)
                            except ValueError:
                                self._update_length_status(f"Column '{col}' not found in header and is not a valid index.")
                                self._close_progress_popup_safe()
                                logging.warning(f"Column '{col}' not found in header and is not a valid index.")
                                return
                        if col_idx < 0 or col_idx >= len(header):
                            self._update_length_status(f"Column index {col_idx} out of range.")
                            self._close_progress_popup_safe()
                            logging.warning(f"Column index {col_idx} out of range.")
                            return
                        continue
                    
                    # Handle "Ignore first row" option (after header processing)
                    if self.ignore_first_row.get() and row_num == 1:
                        continue  # skip the first row if ignore_first_row is checked
                    
                    if col_idx is None:
                        if not self.has_header.get():
                            # For files without headers, column must be an integer index
                            if not col.isdigit():
                                self._update_length_status("For files without headers, column must be an integer index (starting from 0).")
                                self._close_progress_popup_safe()
                                logging.warning("User attempted to run length check without header for a file without headers.")
                                return
                            col_idx = int(col)
                        if col_idx < 0 or col_idx >= len(row):
                            self._update_length_status(f"Column index {col_idx} out of range.")
                            self._close_progress_popup_safe()
                            logging.warning(f"Column index {col_idx} out of range.")
                            return
                    
                    if col_idx is None or col_idx >= len(row):
                        continue
                    
                    value = row[col_idx]
                    if len(value) > threshold:
                        col_name = header[col_idx] if header else f"Column {col_idx}"
                        self._insert_length_result(row_num, col_name, value)
                        self.length_results.append([row_num, col_name, value])
                        matches += 1
                        
                        if matches % 100 == 0:
                            self._update_length_status(f"Found {matches} matches so far...")
                
                # Check for cancellation before showing results
                if self.cancel_flag:
                    self._update_length_status("Processing cancelled by user.")
                    logging.info("Length check cancelled by user")
                    return
                
                if matches > 0:
                    self._update_length_status(f"Found {matches} rows with values longer than {threshold} characters.")
                    self.length_export_btn.config(state="normal")
                    # Show completion popup
                    messagebox.showinfo("Length Check Complete", 
                        f"Analysis completed successfully!\n\n"
                        f"Found {matches} values exceeding {threshold} characters in column '{col}'.\n\n"
                        f"Results are displayed in the table and can be exported to CSV.")
                else:
                    self._update_length_status(f"No rows found with values longer than {threshold} characters.")
                    self.length_export_btn.config(state="disabled")
                    # Show completion popup
                    messagebox.showinfo("Length Check Complete", 
                        f"Analysis completed successfully!\n\n"
                        f"No values found exceeding {threshold} characters in column '{col}'.\n\n"
                        f"The file appears to have consistent column lengths.")
                logging.info(f"Length check for column '{col}' with threshold {threshold} completed. Found {matches} matches.")
        except Exception as e:
            self._update_length_status(f"Error: {e}")
            logging.error(f"Error during length check worker: {e}")
            messagebox.showerror("Length Check Error", 
                f"An error occurred during the length check:\n\n{str(e)}\n\n"
                f"Please check your file format and try again.")
        self._close_progress_popup_safe()

    def _insert_length_result(self, row_num, col_name, value):
        """Insert a length check result into the treeview."""
        self.root.after(0, lambda: self.length_tree.insert("", "end", values=(row_num, col_name, value)))

    def _update_length_status(self, msg):
        """Update the length checker status label."""
        def update():
            self.length_status.config(text=msg)
        self.root.after(0, update)
        logging.info(f"Length status updated: {msg}")

    def _close_progress_popup_safe(self):
        """Safely close the progress popup from a worker thread."""
        self.root.after(0, self.close_progress_popup)
        logging.info("Progress popup closed safely.")

    def export_length_results(self):
        """Export length check results to CSV."""
        if not self.length_results:
            messagebox.showinfo("Export Results", "There are no results to export.")
            logging.warning("User attempted to export length results, but none were found.")
            return
        file = filedialog.asksaveasfilename(
            title="Export Length Results",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not file:
            logging.warning("User cancelled length results export.")
            return
        try:
            with open(file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Row", "Column", "Value"])
                for row in self.length_results:
                    writer.writerow(row)
            self.set_status(f"Results exported to {os.path.basename(file)}")
            logging.info(f"Length results exported to {os.path.basename(file)}")
            messagebox.showinfo("Export Successful", 
                f"Length check results exported successfully!\n\n"
                f"File: {os.path.basename(file)}\n"
                f"Records exported: {len(self.length_results)}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export results: {e}")
            self.set_status("Export failed.")
            logging.error(f"Failed to export length results: {e}")

    # --- Find Duplicates Logic ---
    def run_dup_check(self):
        """Start the duplicate check process."""
        if not self.filename:
            messagebox.showerror("Error", "Please select a CSV file.")
            logging.warning("User attempted to run duplicate check without a file.")
            return
        col = self.dup_col_entry.get().strip()
        if not col:
            messagebox.showerror("Error", "Please specify a column name or index.")
            logging.warning("User attempted to run duplicate check with empty column name.")
            return
        self.dup_tree.delete(*self.dup_tree.get_children())
        self.dup_results = []
        self.show_progress_popup()
        logging.info(f"User initiated duplicate check for column '{col}'.")
        t = threading.Thread(target=self._dup_check_worker, args=(col,), daemon=True)
        t.start()

    def _dup_check_worker(self, col):
        """Background worker for duplicate checking."""
        # Reset cancel flag at start
        self.cancel_flag = False
        
        try:
            delim = self.get_delimiter()
            matches = 0
            seen_values = {}
            duplicate_rows = []
            
            with open(self.filename, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.reader(f, delimiter=delim)
                row_num = 0
                col_idx = None
                header = None
                
                for row in reader:
                    # Check for cancellation
                    if self.cancel_flag:
                        self._update_dup_status("Processing cancelled by user.")
                        logging.info("Duplicate check cancelled by user")
                        return
                    
                    if not row:
                        continue  # skip empty rows
                    row_num += 1
                    
                    if row_num == 1 and self.has_header.get():
                        header = row
                        # Find column index
                        if col.isdigit():
                            col_idx = int(col)
                        else:
                            try:
                                col_idx = header.index(col)
                            except ValueError:
                                self._update_dup_status(f"Column '{col}' not found in header and is not a valid index.")
                                self._close_progress_popup_safe()
                                logging.warning(f"Column '{col}' not found in header and is not a valid index.")
                                return
                        if col_idx < 0 or col_idx >= len(header):
                            self._update_dup_status(f"Column index {col_idx} out of range.")
                            self._close_progress_popup_safe()
                            logging.warning(f"Column index {col_idx} out of range.")
                            return
                        continue
                    
                    # Handle "Ignore first row" option (after header processing)
                    if self.ignore_first_row.get() and row_num == 1:
                        continue  # skip the first row if ignore_first_row is checked
                    
                    if col_idx is None:
                        if not self.has_header.get():
                            # For files without headers, column must be an integer index
                            if not col.isdigit():
                                self._update_dup_status("For files without headers, column must be an integer index (starting from 0).")
                                self._close_progress_popup_safe()
                                logging.warning("User attempted to run duplicate check without header for a file without headers.")
                                return
                            col_idx = int(col)
                        if col_idx < 0 or col_idx >= len(row):
                            self._update_dup_status(f"Column index {col_idx} out of range.")
                            self._close_progress_popup_safe()
                            logging.warning(f"Column index {col_idx} out of range.")
                            return
                    
                    if col_idx is None or col_idx >= len(row):
                        continue
                    
                    value = row[col_idx]
                    if value in seen_values:
                        # This is a duplicate
                        col_name = header[col_idx] if header else f"Column {col_idx}"
                        self._insert_dup_result(row_num, col_name, value)
                        self.dup_results.append([row_num, col_name, value])
                        duplicate_rows.append(row_num)
                        matches += 1
                        
                        if matches % 100 == 0:
                            self._update_dup_status(f"Found {matches} duplicates so far...")
                    else:
                        seen_values[value] = row_num
                
                # Check for cancellation before showing results
                if self.cancel_flag:
                    self._update_dup_status("Processing cancelled by user.")
                    logging.info("Duplicate check cancelled by user")
                    return
                
                if matches > 0:
                    self._update_dup_status(f"Found {matches} duplicate values in column '{col}'.")
                    self.dup_export_btn.config(state="normal")
                    # Show completion popup
                    messagebox.showinfo("Duplicate Check Complete", 
                        f"Analysis completed successfully!\n\n"
                        f"Found {matches} duplicate values in column '{col}'.\n\n"
                        f"Results are displayed in the table and can be exported to CSV.")
                else:
                    self._update_dup_status(f"No duplicates found in column '{col}'.")
                    self.dup_export_btn.config(state="disabled")
                    # Show completion popup
                    messagebox.showinfo("Duplicate Check Complete", 
                        f"Analysis completed successfully!\n\n"
                        f"No duplicate values found in column '{col}'.\n\n"
                        f"The file appears to have unique values in this column.")
                logging.info(f"Duplicate check for column '{col}' completed. Found {matches} duplicates.")
        except Exception as e:
            self._update_dup_status(f"Error: {e}")
            logging.error(f"Error during duplicate check worker: {e}")
            messagebox.showerror("Duplicate Check Error", 
                f"An error occurred during the duplicate check:\n\n{str(e)}\n\n"
                f"Please check your file format and try again.")
        self._close_progress_popup_safe()

    def _insert_dup_result(self, row_num, col_name, value):
        """Insert a duplicate result into the treeview."""
        self.root.after(0, lambda: self.dup_tree.insert("", "end", values=(row_num, col_name, value)))

    def _update_dup_status(self, msg):
        """Update the duplicate checker status label."""
        def update():
            self.dup_status.config(text=msg)
        self.root.after(0, update)
        logging.info(f"Duplicate status updated: {msg}")

    def export_dup_results(self):
        """Export duplicate check results to CSV."""
        if not self.dup_results:
            messagebox.showinfo("Export Results", "There are no results to export.")
            logging.warning("User attempted to export duplicate results, but none were found.")
            return
        file = filedialog.asksaveasfilename(
            title="Export Duplicate Results",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not file:
            logging.warning("User cancelled duplicate results export.")
            return
        try:
            with open(file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Row", "Column", "Value"])
                for row in self.dup_results:
                    writer.writerow(row)
            self.set_status(f"Results exported to {os.path.basename(file)}")
            logging.info(f"Duplicate results exported to {os.path.basename(file)}")
            messagebox.showinfo("Export Successful", 
                f"Duplicate check results exported successfully!\n\n"
                f"File: {os.path.basename(file)}\n"
                f"Records exported: {len(self.dup_results)}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export results: {e}")
            self.set_status("Export failed.")
            logging.error(f"Failed to export duplicate results: {e}")

    # --- Find Extra Delimiters Logic ---
    def run_extra_check(self):
        """Start the extra delimiters check process."""
        if not self.filename:
            messagebox.showerror("Error", "Please select a CSV file.")
            logging.warning("User attempted to run extra delimiter check without a file.")
            return
        self.extra_tree.delete(*self.extra_tree.get_children())
        self.extra_results = []
        self.show_progress_popup()
        logging.info("User initiated extra delimiter check.")
        t = threading.Thread(target=self._extra_check_worker, daemon=True)
        t.start()

    def _extra_check_worker(self):
        """Background worker for extra delimiters checking."""
        # Reset cancel flag at start
        self.cancel_flag = False
        
        try:
            delim = self.get_delimiter()
            matches = 0
            expected_cols = None
            
            with open(self.filename, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.reader(f, delimiter=delim)
                row_num = 0
                
                for row in reader:
                    # Check for cancellation
                    if self.cancel_flag:
                        self._update_extra_status("Processing cancelled by user.")
                        logging.info("Extra delimiter check cancelled by user")
                        return
                    
                    if not row:
                        continue  # skip empty rows
                    row_num += 1
                    
                    # Skip metadata lines (lines with few columns that don't look like actual data)
                    if len(row) <= 3:
                        continue
                    
                    # Find the first actual data row to establish expected column count
                    if expected_cols is None:
                        expected_cols = len(row)
                        if self.has_header.get():
                            continue  # skip header row
                        # If no header, this is the baseline row
                    
                    # Handle "Ignore first row" option (after establishing baseline)
                    if self.ignore_first_row.get() and row_num == 1:
                        continue  # skip the first row if ignore_first_row is checked
                    
                    if len(row) > expected_cols:
                        # Find the extra columns
                        extra_cols = []
                        for i in range(expected_cols, len(row)):
                            extra_cols.append(i + 1)  # 1-based indexing
                        
                        row_data = " | ".join(row)
                        self._insert_extra_result(row_num, extra_cols, row_data)
                        self.extra_results.append([row_num, extra_cols, row_data])
                        matches += 1
                        
                        if matches % 100 == 0:
                            self._update_extra_status(f"Found {matches} problematic rows so far...")
                
                # Check for cancellation before showing results
                if self.cancel_flag:
                    self._update_extra_status("Processing cancelled by user.")
                    logging.info("Extra delimiter check cancelled by user")
                    return
                
                if matches > 0:
                    self._update_extra_status(f"Found {matches} rows with extra delimiters.")
                    self.extra_export_btn.config(state="normal")
                    # Show completion popup
                    messagebox.showinfo("Extra Delimiters Check Complete", 
                        f"Analysis completed successfully!\n\n"
                        f"Found {matches} rows with extra delimiters.\n\n"
                        f"These rows have more columns than expected and may need attention.\n"
                        f"Results are displayed in the table and can be exported to CSV.")
                else:
                    self._update_extra_status("No rows with extra delimiters found.")
                    self.extra_export_btn.config(state="disabled")
                    # Show completion popup
                    messagebox.showinfo("Extra Delimiters Check Complete", 
                        f"Analysis completed successfully!\n\n"
                        f"No rows with extra delimiters found.\n\n"
                        f"The file appears to have consistent column structure.")
                logging.info(f"Extra delimiter check completed. Found {matches} problematic rows.")
        except Exception as e:
            self._update_extra_status(f"Error: {e}")
            logging.error(f"Error during extra delimiter check worker: {e}")
            messagebox.showerror("Extra Delimiters Check Error", 
                f"An error occurred during the extra delimiters check:\n\n{str(e)}\n\n"
                f"Please check your file format and try again.")
        self._close_progress_popup_safe()

    def _insert_extra_result(self, row_num, extra_cols, row_data):
        """Insert an extra delimiter result into the treeview."""
        extra_cols_str = ", ".join(map(str, extra_cols))
        self.root.after(0, lambda: self.extra_tree.insert("", "end", values=(row_num, extra_cols_str, row_data)))

    def _update_extra_status(self, msg):
        """Update the extra delimiters status label."""
        def update():
            self.extra_status.config(text=msg)
        self.root.after(0, update)
        logging.info(f"Extra delimiter status updated: {msg}")

    def export_extra_results(self):
        """Export extra delimiter results to CSV."""
        if not self.extra_results:
            messagebox.showinfo("Export Results", "There are no results to export.")
            logging.warning("User attempted to export extra delimiter results, but none were found.")
            return
        file = filedialog.asksaveasfilename(
            title="Export Extra Delimiter Results",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not file:
            logging.warning("User cancelled extra delimiter results export.")
            return
        try:
            with open(file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Row", "Extra Columns", "Row Data"])
                for row in self.extra_results:
                    writer.writerow(row)
            self.set_status(f"Results exported to {os.path.basename(file)}")
            logging.info(f"Extra delimiter results exported to {os.path.basename(file)}")
            messagebox.showinfo("Export Successful", 
                f"Extra delimiters check results exported successfully!\n\n"
                f"File: {os.path.basename(file)}\n"
                f"Records exported: {len(self.extra_results)}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export results: {e}")
            self.set_status("Export failed.")
            logging.error(f"Failed to export extra delimiter results: {e}")

    def _not_implemented(self):
        """Placeholder for unimplemented features."""
        messagebox.showinfo("Not Implemented", "This functionality will be implemented in the next steps.")
        logging.warning("User attempted to run a not implemented functionality.")

if __name__ == "__main__":
    root = tk.Tk()
    app = CSVAnalyzerApp(root)
    root.mainloop() 