import csv
import os
import tkinter.font as tkFont
import tkinter as tk

# Try to import ttkthemes for a modern look
try:
    from ttkthemes import ThemedTk
    THEMES_AVAILABLE = True
except ImportError:
    THEMES_AVAILABLE = False
    from tkinter import Tk

from tkinter import filedialog, messagebox
from tkinter import ttk

APP_TITLE = "CSV Column Length Checker - EDW Team"
APP_VERSION = "1.0"
APP_AUTHOR = "Xenofon Psychis - Filis"
APP_DESCRIPTION = (
    "A tool to check if values in a specified column of a CSV file exceed a given length.\n"
    "- Supports files with or without headers.\n"
    "- Choose delimiter, column, and threshold.\n"
    "- Export matching rows to a new CSV file.\n\n"
)

MODERN_THEMES = [
    "arc", "plastik", "breeze", "clearlooks", "radiance", "equilux", "yaru", "adapta", "scidblue", "scidgreen", "scidgrey", "scidmint", "scidpurple"
]

class ColumnLengthApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.filename = None
        self.matching_rows = []  # Store (row_num, full_row) for export
        self.header_row = None   # Store header if present

        # Set window icon if available
        icon_path = os.path.join(os.path.dirname(__file__), 'app_icon.ico')
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                pass  # Ignore icon errors

        # Set minimum window size
        self.root.minsize(900, 500)

        # --- Menu Bar ---
        menubar = tk.Menu(root)
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open", command=self.browse_file)
        file_menu.add_command(label="Export Results", command=self.export_results)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        # Theme submenu
        if THEMES_AVAILABLE:
            theme_menu = tk.Menu(help_menu, tearoff=0)
            for theme in MODERN_THEMES:
                theme_menu.add_command(label=theme, command=lambda t=theme: self.set_theme(t))
            help_menu.add_cascade(label="Theme", menu=theme_menu)
        menubar.add_cascade(label="Help", menu=help_menu)
        root.config(menu=menubar)

        # --- Custom Fonts and Styles ---
        header_font = tkFont.Font(family="Segoe UI", size=13, weight="bold")
        label_font = tkFont.Font(family="Segoe UI", size=11)
        button_font = tkFont.Font(family="Segoe UI", size=11, weight="bold")
        table_font = tkFont.Font(family="Consolas", size=10)
        style = ttk.Style()
        if THEMES_AVAILABLE:
            root.set_theme("plastik")
        else:
            style.theme_use('clam')  # fallback
        style.configure("TButton", font=button_font, foreground="#1a237e", padding=6)
        style.configure("Treeview.Heading", font=header_font, background="#e3eafc", foreground="#1a237e")
        style.configure("Treeview", font=table_font, rowheight=24)
        style.configure("TLabel", font=label_font)
        style.configure("TLabelframe.Label", font=header_font)

        # Main frame
        main_frame = ttk.Frame(root, padding="10 10 10 10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        # File selection frame
        file_frame = ttk.Frame(main_frame)
        file_frame.grid(row=0, column=0, columnspan=4, sticky="ew", pady=(0, 10))
        file_frame.columnconfigure(0, weight=1)
        file_frame.columnconfigure(1, weight=0)
        self.file_label = ttk.Label(file_frame, text="No file selected", style="TLabel")
        self.file_label.grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.browse_btn = ttk.Button(file_frame, text="📂 Browse...", command=self.browse_file, style="TButton", width=15)
        self.browse_btn.grid(row=0, column=1, sticky="e", padx=(10, 0))

        # Options frame (symmetrical grid)
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="10 10 10 10")
        options_frame.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(0, 10))
        for i in range(4):
            options_frame.columnconfigure(i, weight=1)

        ttk.Label(options_frame, text="Delimiter:", style="TLabel").grid(row=0, column=0, sticky="e", padx=5, pady=2)
        self.delim_entry = ttk.Entry(options_frame, width=5)
        self.delim_entry.insert(0, ',')
        self.delim_entry.grid(row=0, column=1, sticky="w", padx=5, pady=2)

        self.has_header = tk.BooleanVar(value=True)
        # Standard checkbox for header
        self.header_check = ttk.Checkbutton(options_frame, text="File has header", variable=self.has_header)
        self.header_check.grid(row=0, column=2, sticky="w", padx=5, pady=2)

        # Empty label for symmetry
        ttk.Label(options_frame, text="", style="TLabel").grid(row=0, column=3)

        ttk.Label(options_frame, text="Column (name or index):", style="TLabel").grid(row=1, column=0, sticky="e", padx=5, pady=2)
        self.column_entry = ttk.Entry(options_frame, width=15)
        self.column_entry.grid(row=1, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(options_frame, text="Length threshold:", style="TLabel").grid(row=1, column=2, sticky="e", padx=5, pady=2)
        self.length_entry = ttk.Entry(options_frame, width=5)
        self.length_entry.insert(0, '25')
        self.length_entry.grid(row=1, column=3, sticky="w", padx=5, pady=2)

        # Action buttons frame for symmetry
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(0, 10))
        action_frame.columnconfigure(0, weight=1)
        action_frame.columnconfigure(1, weight=1)
        self.run_btn = ttk.Button(action_frame, text="🔍 Check", command=self.run_check, style="TButton", width=15)
        self.run_btn.grid(row=0, column=0, sticky="e", padx=(0, 10))
        self.export_btn = ttk.Button(action_frame, text="💾 Export Results", command=self.export_results, style="TButton", width=15)
        self.export_btn.grid(row=0, column=1, sticky="w", padx=(10, 0))

        # Results area - Treeview table
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding="5 5 5 5")
        results_frame.grid(row=3, column=0, columnspan=4, sticky="nsew")
        main_frame.rowconfigure(3, weight=1)
        results_frame.rowconfigure(0, weight=1)
        results_frame.columnconfigure(0, weight=1)

        columns = ("row", "column", "value")
        self.result_table = ttk.Treeview(results_frame, columns=columns, show="headings", height=20, style="Treeview")
        self.result_table.heading("row", text="Row")
        self.result_table.heading("column", text="Column")
        self.result_table.heading("value", text="Value")
        self.result_table.column("row", width=60, anchor="center")
        self.result_table.column("column", width=120, anchor="center")
        self.result_table.column("value", width=600, anchor="w")

        vsb = ttk.Scrollbar(results_frame, orient="vertical", command=self.result_table.yview)
        self.result_table.configure(yscrollcommand=vsb.set)
        self.result_table.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief="sunken", anchor="w", padding="5 2 5 2", style="TLabel")
        self.status_bar.grid(row=1, column=0, sticky="ew")
        root.rowconfigure(1, weight=0)

        # Focus the file browse button on startup
        self.browse_btn.focus_set()

    def set_theme(self, theme_name):
        if THEMES_AVAILABLE:
            self.root.set_theme(theme_name)
            self.set_status(f"Theme set to: {theme_name}")

    def set_status(self, message):
        self.status_var.set(message)
        self.status_bar.update_idletasks()

    def browse_file(self):
        filetypes = [("CSV files", "*.csv"), ("All files", "*.*")]
        filename = filedialog.askopenfilename(title="Select CSV file", filetypes=filetypes)
        if filename:
            self.filename = filename
            self.file_label.config(text=os.path.basename(filename))
            self.set_status(f"File loaded: {os.path.basename(filename)}")

    def show_about(self):
        messagebox.showinfo(
            "About",
            f"{APP_TITLE}\nVersion: {APP_VERSION}\nAuthor: {APP_AUTHOR}\n\n{APP_DESCRIPTION}"
        )

    def export_results(self):
        if not self.matching_rows:
            messagebox.showinfo("Export Results", "There are no results to export.")
            return
        file = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save Results As"
        )
        if not file:
            return
        try:
            with open(file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Write header if present, else generic column names
                if self.header_row:
                    writer.writerow(self.header_row)
                else:
                    # Use the length of the first row to generate generic column names
                    if self.matching_rows:
                        ncols = len(self.matching_rows[0][1])
                        writer.writerow([f"Column{i+1}" for i in range(ncols)])
                for _, row in self.matching_rows:
                    writer.writerow(row)
            self.set_status(f"Results exported to {os.path.basename(file)}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export results: {e}")
            self.set_status("Export failed.")

    def run_check(self):
        if not self.filename:
            messagebox.showerror("Error", "Please select a CSV file.")
            self.set_status("No file selected.")
            return
        delimiter = self.delim_entry.get()
        if not delimiter:
            messagebox.showerror("Error", "Please enter a delimiter.")
            self.set_status("No delimiter specified.")
            return
        has_header = self.has_header.get()
        column = self.column_entry.get().strip()
        if not column:
            messagebox.showerror("Error", "Please enter a column name or index.")
            self.set_status("No column specified.")
            return
        try:
            length_threshold = int(self.length_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Length threshold must be an integer.")
            self.set_status("Invalid length threshold.")
            return

        # Clear previous results
        for item in self.result_table.get_children():
            self.result_table.delete(item)
        self.matching_rows = []
        self.header_row = None
        found_count = 0
        try:
            with open(self.filename, newline='') as f:
                reader = csv.reader(f, delimiter=delimiter)
                if has_header:
                    header = next(reader)
                    self.header_row = header
                    try:
                        col_idx = header.index(column)
                        col_name = header[col_idx]
                    except ValueError:
                        try:
                            col_idx = int(column)
                            col_name = header[col_idx] if 0 <= col_idx < len(header) else str(col_idx)
                        except ValueError:
                            self.set_status("Column not found.")
                            return
                        if col_idx < 0 or col_idx >= len(header):
                            self.set_status("Column index out of range.")
                            return
                    for row_num, row in enumerate(reader, start=2):
                        if col_idx >= len(row):
                            continue
                        value = row[col_idx]
                        if len(str(value)) > length_threshold:
                            self.result_table.insert("", "end", values=(row_num, col_name, value))
                            self.matching_rows.append((row_num, row))
                            found_count += 1
                else:
                    try:
                        col_idx = int(column)
                        col_name = f"Column {col_idx+1}"
                    except ValueError:
                        self.set_status("Invalid column index.")
                        return
                    for row_num, row in enumerate(reader, start=1):
                        if col_idx >= len(row):
                            continue
                        value = row[col_idx]
                        if len(str(value)) > length_threshold:
                            self.result_table.insert("", "end", values=(row_num, col_name, value))
                            self.matching_rows.append((row_num, row))
                            found_count += 1
            self.set_status(f"Check complete: {found_count} rows found.")
        except Exception as e:
            self.set_status(f"Error: {e}")

if __name__ == "__main__":
    # Use ThemedTk if available, else fallback to Tk
    if THEMES_AVAILABLE:
        root = ThemedTk(theme="plastik")
    else:
        root = Tk()
        print("[INFO] For a more modern look, install ttkthemes: pip install ttkthemes")
    app = ColumnLengthApp(root)
    root.mainloop() 