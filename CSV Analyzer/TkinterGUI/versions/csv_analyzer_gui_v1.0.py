"""
CSV Analyzer - EDW Team

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
        self.root.title("CSV Analyzer - EDW Team")
        
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
        self.has_header = tk.BooleanVar(value=True)
        self.processing_thread = None
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

    def show_about_dialog(self):
        import webbrowser
        about = tk.Toplevel(self.root)
        about.title("About CSV Analyzer")
        about.resizable(False, False)
        about.grab_set()
        tk.Label(about, text="CSV Analyzer", font=("Segoe UI", 14, "bold")).pack(pady=(10, 0))
        tk.Label(about, text="Version 1.0", font=("Segoe UI", 10)).pack()
        tk.Label(about, text="A user-friendly, multi-tool CSV analysis application.\n"
                             "- Column Length Checker\n"
                             "- Find Duplicates\n"
                             "- Find Extra Delimiters\n",
                 justify="left").pack(padx=20, pady=(10, 0))
        tk.Label(about, text="Developed by Xenofon Psychis - Filis.", font=("Segoe UI", 10, "italic")).pack(pady=(5, 0))
        tk.Label(about, text="Contact: [Your Contact Email/Info Here]", font=("Segoe UI", 10)).pack(pady=(0, 10))

        def open_github(event=None):
            webbrowser.open("https://github.com/psycxeno/XenophonPsychisFilis/tree/main/TkinterGUI")

        link = tk.Label(about, text="View README on GitHub", fg="blue", cursor="hand2", font=("Segoe UI", 10, "underline"))
        link.pack(pady=(0, 10))
        link.bind("<Button-1>", open_github)

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
        self.delim_combo = ttk.Combobox(shared_frame, textvariable=self.delimiter, width=8, state="readonly")
        self.delim_combo['values'] = (',', '\t', ';', '|', ' ', '\\t', '\\n', '\\r')
        self.delim_combo.current(0)  # Default to comma
        self.delim_combo.grid(row=0, column=4, sticky="w", padx=5)
        self.header_check = ttk.Checkbutton(shared_frame, text="File has header", variable=self.has_header)
        self.header_check.grid(row=0, column=5, sticky="w", padx=10)

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

    def get_delimiter(self):
        """Convert delimiter input to actual character (e.g., '\\t' -> tab)"""
        delim = self.delimiter.get()
        if delim == '\\t':
            return '\t'
        elif delim == '\\n':
            return '\n'
        elif delim == '\\r':
            return '\r'
        elif delim == '\t':  # Already a tab character from dropdown
            return '\t'
        elif delim == '\n':  # Already a newline character from dropdown
            return '\n'
        elif delim == '\r':  # Already a carriage return character from dropdown
            return '\r'
        else:
            return delim

    def browse_file(self):
        filetypes = [("CSV files", "*.csv"), ("All files", "*.*")]
        filename = filedialog.askopenfilename(title="Select CSV file", filetypes=filetypes)
        if filename:
            self.filename = filename
            self.file_label.config(text=os.path.basename(filename))
            self.set_status(f"File loaded: {os.path.basename(filename)}")
            logging.info(f"User selected file: {os.path.basename(filename)}")
        else:
            self.set_status("No file selected.")
            logging.warning("User cancelled file selection.")

    def clear_all(self):
        self.filename = None
        self.file_label.config(text="No file selected")
        self.set_status("Ready")
        logging.info("User cleared all results and status.")
        # Clear all tabs' results and status
        self.length_tree.delete(*self.length_tree.get_children())
        self.length_status.config(text="")
        self.length_results = []
        self.length_export_btn.config(state="disabled")
        self.length_col_entry.delete(0, tk.END)
        self.length_thresh_entry.delete(0, tk.END)
        self.length_thresh_entry.insert(0, '25')

        self.dup_tree.delete(*self.dup_tree.get_children())
        self.dup_status.config(text="")
        self.dup_results = []
        self.dup_export_btn.config(state="disabled")
        self.dup_col_entry.delete(0, tk.END)

        self.extra_tree.delete(*self.extra_tree.get_children())
        self.extra_status.config(text="")
        self.extra_results = []
        self.extra_export_btn.config(state="disabled")

    def set_status(self, msg):
        self.status_var.set(msg)
        self.status_bar.update_idletasks()
        logging.info(f"Status updated: {msg}")

    # --- Progress Popup ---
    def show_progress_popup(self, message="Processing... Please wait."):
        if self.progress_popup:
            return
        self.progress_popup = tk.Toplevel(self.root)
        self.progress_popup.title("Processing")
        self.progress_popup.geometry("350x100")
        self.progress_popup.transient(self.root)
        self.progress_popup.grab_set()
        self.progress_popup.resizable(False, False)
        ttk.Label(self.progress_popup, text=message, style="TLabel").pack(pady=(18, 8))
        pb = ttk.Progressbar(self.progress_popup, mode="indeterminate")
        pb.pack(fill="x", padx=30, pady=(0, 10))
        pb.start(10)
        self.progress_popup.protocol("WM_DELETE_WINDOW", lambda: None)  # Disable close
        logging.info(f"Progress popup shown: {message}")

    def close_progress_popup(self):
        if self.progress_popup:
            self.progress_popup.grab_release()
            self.progress_popup.destroy()
            self.progress_popup = None
            logging.info("Progress popup closed.")

    # --- Tab Initializers ---
    def _init_length_tab(self):
        frame = self.tab_length
        # Controls
        controls = ttk.Frame(frame, padding="10 10 10 10")
        controls.pack(fill="x")
        ttk.Label(controls, text="Column (name or index):", style="TLabel").grid(row=0, column=0, sticky="e", padx=5)
        self.length_col_entry = ttk.Entry(controls, width=15)
        self.length_col_entry.grid(row=0, column=1, sticky="w", padx=5)
        ttk.Label(controls, text="Length threshold:", style="TLabel").grid(row=0, column=2, sticky="e", padx=5)
        self.length_thresh_entry = ttk.Entry(controls, width=7)
        self.length_thresh_entry.insert(0, '25')
        self.length_thresh_entry.grid(row=0, column=3, sticky="w", padx=5)
        self.length_check_btn = ttk.Button(controls, text="Check", command=self.run_length_check)
        self.length_check_btn.grid(row=0, column=4, padx=10)
        self.length_export_btn = ttk.Button(controls, text="Export Results", command=self.export_length_results, state="disabled")
        self.length_export_btn.grid(row=0, column=5, padx=10)
        # Progress/Status
        self.length_status = ttk.Label(frame, text="", style="TLabel")
        self.length_status.pack(fill="x", padx=10, pady=(0, 5))
        # Results
        self.length_tree = ttk.Treeview(frame, columns=("row", "column", "value"), show="headings", height=18)
        self.length_tree.heading("row", text="Row")
        self.length_tree.heading("column", text="Column")
        self.length_tree.heading("value", text="Value")
        self.length_tree.column("row", width=60, anchor="center")
        self.length_tree.column("column", width=120, anchor="center")
        self.length_tree.column("value", width=700, anchor="w")
        self.length_tree.pack(fill="both", expand=True, padx=10, pady=5)
        self.length_scroll = ttk.Scrollbar(frame, orient="vertical", command=self.length_tree.yview)
        self.length_tree.configure(yscrollcommand=self.length_scroll.set)
        self.length_scroll.pack(side="right", fill="y")

    def _init_duplicates_tab(self):
        frame = self.tab_duplicates
        controls = ttk.Frame(frame, padding="10 10 10 10")
        controls.pack(fill="x")
        ttk.Label(controls, text="Column (name or index):", style="TLabel").grid(row=0, column=0, sticky="e", padx=5)
        self.dup_col_entry = ttk.Entry(controls, width=15)
        self.dup_col_entry.grid(row=0, column=1, sticky="w", padx=5)
        self.dup_check_btn = ttk.Button(controls, text="Find Duplicates", command=self.run_dup_check)
        self.dup_check_btn.grid(row=0, column=2, padx=10)
        self.dup_export_btn = ttk.Button(controls, text="Export Duplicates", command=self.export_dup_results, state="disabled")
        self.dup_export_btn.grid(row=0, column=3, padx=10)
        self.dup_status = ttk.Label(frame, text="", style="TLabel")
        self.dup_status.pack(fill="x", padx=10, pady=(0, 5))
        self.dup_tree = ttk.Treeview(frame, columns=("row", "column", "value"), show="headings", height=18)
        self.dup_tree.heading("row", text="Row")
        self.dup_tree.heading("column", text="Column")
        self.dup_tree.heading("value", text="Value")
        self.dup_tree.column("row", width=60, anchor="center")
        self.dup_tree.column("column", width=120, anchor="center")
        self.dup_tree.column("value", width=700, anchor="w")
        self.dup_tree.pack(fill="both", expand=True, padx=10, pady=5)
        self.dup_scroll = ttk.Scrollbar(frame, orient="vertical", command=self.dup_tree.yview)
        self.dup_tree.configure(yscrollcommand=self.dup_scroll.set)
        self.dup_scroll.pack(side="right", fill="y")

    def _init_extra_tab(self):
        frame = self.tab_extra
        controls = ttk.Frame(frame, padding="10 10 10 10")
        controls.pack(fill="x")
        self.extra_check_btn = ttk.Button(controls, text="Check for Extra Delimiters", command=self.run_extra_check)
        self.extra_check_btn.grid(row=0, column=0, padx=10)
        self.extra_export_btn = ttk.Button(controls, text="Export Problematic Rows", command=self.export_extra_results, state="disabled")
        self.extra_export_btn.grid(row=0, column=1, padx=10)
        self.extra_status = ttk.Label(frame, text="", style="TLabel")
        self.extra_status.pack(fill="x", padx=10, pady=(0, 5))
        self.extra_tree = ttk.Treeview(frame, columns=("row", "extra_cols", "data"), show="headings", height=18)
        self.extra_tree.heading("row", text="Row")
        self.extra_tree.heading("extra_cols", text="Extra Columns")
        self.extra_tree.heading("data", text="Row Data")
        self.extra_tree.column("row", width=60, anchor="center")
        self.extra_tree.column("extra_cols", width=120, anchor="center")
        self.extra_tree.column("data", width=700, anchor="w")
        self.extra_tree.pack(fill="both", expand=True, padx=10, pady=5)
        self.extra_scroll = ttk.Scrollbar(frame, orient="vertical", command=self.extra_tree.yview)
        self.extra_tree.configure(yscrollcommand=self.extra_scroll.set)
        self.extra_scroll.pack(side="right", fill="y")

    # --- Column Length Checker Logic ---
    def run_length_check(self):
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
        self.length_status.config(text="Processing... (this may take a while for large files)")
        self.length_export_btn.config(state="disabled")
        self.length_results = []
        self.show_progress_popup()
        logging.info(f"User initiated length check for column '{col}' with threshold {threshold}.")
        # Start background thread
        t = threading.Thread(target=self._length_check_worker, args=(col, threshold), daemon=True)
        t.start()
        self.processing_thread = t

    def _length_check_worker(self, col, threshold):
        try:
            with open(self.filename, newline='', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter=self.get_delimiter())
                row_num = 0
                header = None
                col_idx = None
                matches = 0
                display_count = 0
                for row in reader:
                    row_num += 1
                    if row_num == 1 and self.has_header.get():
                        header = row
                        # Determine column index
                        try:
                            col_idx = header.index(col)
                        except ValueError:
                            try:
                                col_idx = int(col)
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
                    elif row_num == 1:
                        # No header
                        try:
                            col_idx = int(col)
                        except ValueError:
                            self._update_length_status("For files without headers, column must be an integer index (starting from 0).")
                            self._close_progress_popup_safe()
                            logging.warning("User attempted to run length check without header for a file without headers.")
                            return
                        if col_idx < 0 or col_idx >= len(row):
                            self._update_length_status(f"Column index {col_idx} out of range.")
                            self._close_progress_popup_safe()
                            logging.warning(f"Column index {col_idx} out of range.")
                            return
                    if col_idx is None or col_idx >= len(row):
                        continue
                    value = row[col_idx]
                    if len(str(value)) > threshold:
                        matches += 1
                        # Store for export
                        self.length_results.append((row_num, (header[col_idx] if header else f"Column {col_idx+1}"), value))
                        # Display up to max_display
                        if display_count < self.length_max_display:
                            self._insert_length_result(row_num, (header[col_idx] if header else f"Column {col_idx+1}"), value)
                            display_count += 1
                        if matches % 1000 == 0:
                            self._update_length_status(f"Found {matches} matches so far...")
                self._update_length_status(f"Done. Found {matches} rows with value longer than {threshold}.")
                if matches > 0:
                    self.length_export_btn.config(state="normal")
                else:
                    self.length_export_btn.config(state="disabled")
                logging.info(f"Length check for column '{col}' with threshold {threshold} completed. Found {matches} matches.")
        except Exception as e:
            self._update_length_status(f"Error: {e}")
            logging.error(f"Error during length check worker: {e}")
        self._close_progress_popup_safe()

    def _insert_length_result(self, row_num, col_name, value):
        self.length_tree.insert("", "end", values=(row_num, col_name, value))

    def _update_length_status(self, msg):
        def update():
            self.length_status.config(text=msg)
        self.root.after(0, update)
        logging.info(f"Length status updated: {msg}")

    def _close_progress_popup_safe(self):
        self.root.after(0, self.close_progress_popup)
        logging.info("Progress popup closed safely.")

    def export_length_results(self):
        if not self.length_results:
            messagebox.showinfo("Export Results", "There are no results to export.")
            logging.warning("User attempted to export length results, but none were found.")
            return
        file = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save Results As"
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
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export results: {e}")
            self.set_status("Export failed.")
            logging.error(f"Failed to export length results: {e}")

    # --- Find Duplicates Logic ---
    def run_dup_check(self):
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
        self.dup_status.config(text="Processing... (this may take a while for large files)")
        self.dup_export_btn.config(state="disabled")
        self.dup_results = []
        self.show_progress_popup()
        logging.info(f"User initiated duplicate check for column '{col}'.")
        t = threading.Thread(target=self._dup_check_worker, args=(col,), daemon=True)
        t.start()
        self.processing_thread = t

    def _dup_check_worker(self, col):
        try:
            # First pass: count occurrences
            value_counts = {}
            header = None
            col_idx = None
            with open(self.filename, newline='', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter=self.get_delimiter())
                row_num = 0
                for row in reader:
                    row_num += 1
                    if row_num == 1 and self.has_header.get():
                        header = row
                        try:
                            col_idx = header.index(col)
                        except ValueError:
                            try:
                                col_idx = int(col)
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
                    elif row_num == 1:
                        try:
                            col_idx = int(col)
                        except ValueError:
                            self._update_dup_status("For files without headers, column must be an integer index (starting from 0).")
                            self._close_progress_popup_safe()
                            logging.warning("User attempted to run duplicate check without header for a file without headers.")
                            return
                        if col_idx < 0 or col_idx >= len(row):
                            self._update_dup_status(f"Column index {col_idx} out of range.")
                            self._close_progress_popup_safe()
                            logging.warning(f"Column index {col_idx} out of range.")
                            return
                    if col_idx is None or col_idx >= len(row):
                        continue
                    value = row[col_idx]
                    value_counts[value] = value_counts.get(value, 0) + 1
            # Second pass: collect duplicate rows
            with open(self.filename, newline='', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter=self.get_delimiter())
                row_num = 0
                header = None
                col_idx = None
                matches = 0
                display_count = 0
                for row in reader:
                    row_num += 1
                    if row_num == 1 and self.has_header.get():
                        header = row
                        try:
                            col_idx = header.index(col)
                        except ValueError:
                            try:
                                col_idx = int(col)
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
                    elif row_num == 1:
                        try:
                            col_idx = int(col)
                        except ValueError:
                            self._update_dup_status("For files without headers, column must be an integer index (starting from 0).")
                            self._close_progress_popup_safe()
                            logging.warning("User attempted to run duplicate check without header for a file without headers.")
                            return
                        if col_idx < 0 or col_idx >= len(row):
                            self._update_dup_status(f"Column index {col_idx} out of range.")
                            self._close_progress_popup_safe()
                            logging.warning(f"Column index {col_idx} out of range.")
                            return
                    if col_idx is None or col_idx >= len(row):
                        continue
                    value = row[col_idx]
                    if value_counts.get(value, 0) > 1:
                        matches += 1
                        self.dup_results.append((row_num, (header[col_idx] if header else f"Column {col_idx+1}"), value))
                        if display_count < self.dup_max_display:
                            self._insert_dup_result(row_num, (header[col_idx] if header else f"Column {col_idx+1}"), value)
                            display_count += 1
                        if matches % 1000 == 0:
                            self._update_dup_status(f"Found {matches} duplicate rows so far...")
                self._update_dup_status(f"Done. Found {matches} duplicate rows.")
                if matches > 0:
                    self.dup_export_btn.config(state="normal")
                else:
                    self.dup_export_btn.config(state="disabled")
                logging.info(f"Duplicate check for column '{col}' completed. Found {matches} duplicates.")
        except Exception as e:
            self._update_dup_status(f"Error: {e}")
            logging.error(f"Error during duplicate check worker: {e}")
        self._close_progress_popup_safe()

    def _insert_dup_result(self, row_num, col_name, value):
        self.dup_tree.insert("", "end", values=(row_num, col_name, value))

    def _update_dup_status(self, msg):
        def update():
            self.dup_status.config(text=msg)
        self.root.after(0, update)
        logging.info(f"Duplicate status updated: {msg}")

    def export_dup_results(self):
        if not self.dup_results:
            messagebox.showinfo("Export Results", "There are no results to export.")
            logging.warning("User attempted to export duplicate results, but none were found.")
            return
        file = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save Results As"
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
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export results: {e}")
            self.set_status("Export failed.")
            logging.error(f"Failed to export duplicate results: {e}")

    # --- Find Extra Delimiters Logic ---
    def run_extra_check(self):
        if not self.filename:
            messagebox.showerror("Error", "Please select a CSV file.")
            logging.warning("User attempted to run extra delimiter check without a file.")
            return
        self.extra_tree.delete(*self.extra_tree.get_children())
        self.extra_status.config(text="Processing... (this may take a while for large files)")
        self.extra_export_btn.config(state="disabled")
        self.extra_results = []
        self.show_progress_popup()
        logging.info("User initiated extra delimiter check.")
        t = threading.Thread(target=self._extra_check_worker, daemon=True)
        t.start()
        self.processing_thread = t

    def _extra_check_worker(self):
        try:
            with open(self.filename, newline='', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter=self.get_delimiter())
                row_num = 0
                header = None
                expected_cols = None
                matches = 0
                display_count = 0
                for row in reader:
                    row_num += 1
                    if row_num == 1 and self.has_header.get():
                        header = row
                        expected_cols = len(header)
                        continue  # skip header row
                    elif row_num == 1:
                        expected_cols = len(row)
                        continue  # skip first data row
                    if expected_cols is None:
                        continue
                    if len(row) > expected_cols:
                        # Find extra column indices (1-based)
                        extras = [str(i+1) for i in range(expected_cols, len(row))]
                        matches += 1
                        row_data = ', '.join(row)
                        self.extra_results.append((row_num, ', '.join(extras), row_data))
                        if display_count < self.extra_max_display:
                            self._insert_extra_result(row_num, ', '.join(extras), row_data)
                            display_count += 1
                        if matches % 1000 == 0:
                            self._update_extra_status(f"Found {matches} problematic rows so far...")
                self._update_extra_status(f"Done. Found {matches} rows with extra delimiters.")
                if matches > 0:
                    self.extra_export_btn.config(state="normal")
                else:
                    self.extra_export_btn.config(state="disabled")
                logging.info(f"Extra delimiter check completed. Found {matches} problematic rows.")
        except Exception as e:
            self._update_extra_status(f"Error: {e}")
            logging.error(f"Error during extra delimiter check worker: {e}")
        self._close_progress_popup_safe()

    def _insert_extra_result(self, row_num, extra_cols, row_data):
        self.extra_tree.insert("", "end", values=(row_num, extra_cols, row_data))

    def _update_extra_status(self, msg):
        def update():
            self.extra_status.config(text=msg)
        self.root.after(0, update)
        logging.info(f"Extra delimiter status updated: {msg}")

    def export_extra_results(self):
        if not self.extra_results:
            messagebox.showinfo("Export Results", "There are no results to export.")
            logging.warning("User attempted to export extra delimiter results, but none were found.")
            return
        file = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save Results As"
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
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export results: {e}")
            self.set_status("Export failed.")
            logging.error(f"Failed to export extra delimiter results: {e}")

    def _not_implemented(self):
        messagebox.showinfo("Not Implemented", "This functionality will be implemented in the next steps.")
        logging.warning("User attempted to run a not implemented functionality.")

if __name__ == "__main__":
    root = tk.Tk()
    app = CSVAnalyzerApp(root)
    root.mainloop() 