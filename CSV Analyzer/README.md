# CSV Analyzer

A user-friendly, multi-tool CSV analysis application with a modern GUI. Designed for both technical and non-technical users to quickly analyze large CSV/TXT files.

## Features
- **Column Length Checker:** Find rows with column values exceeding a length threshold.
- **Find Duplicates:** Identify duplicate values in a specified column.
- **Find Extra Delimiters:** Detect rows with more columns than expected and pinpoint extra delimiter positions.
- **Handles huge files (multi-GB):** Efficient streaming and threading keep the app responsive.
- **Export results:** Save analysis results to CSV.
- **Customizable delimiter and header options.**
- **Modern, tabbed interface.**

## How to Run

### As a Python Script
1. Make sure you have Python 3.7+ installed (with Tkinter).
2. Place your CSV/TXT files and `magni.ico` (icon) in the same folder as `csv_analyzer_gui.py`.
3. Run:
   ```sh
   python csv_analyzer_gui.py
   ```

### As a Standalone Executable
1. Double-click the `.exe` file (created with PyInstaller) to launch the app.
2. The log file (`csv_analyzer.log`) will be created in the same folder as the `.exe`.

## How to Use
1. **Select your file:** Click **Browse...** and choose a CSV/TXT file.
2. **Set delimiter:** Choose the correct delimiter from the dropdown (e.g., `,`, `\t`, `;`, etc.).
3. **Header:** Check or uncheck "File has header" as appropriate.
4. **Choose a tab:**
   - **Column Length Checker:** Enter column name/index and length threshold, then click **Check**.
   - **Find Duplicates:** Enter column name/index, then click **Check**.
   - **Find Extra Delimiters:** Just click **Check**.
5. **View results:** Results appear in the table below. Only the first 1000 matches are shown for performance.
6. **Export results:** Click **Export Results** to save all matches to a CSV file.
7. **Clear:** Click **Clear** to reset the app and start over.

## Logging
- All actions and errors are logged to `csv_analyzer.log` in the app folder.
- Useful for troubleshooting and support.

## Troubleshooting
- **No icon in taskbar:** Make sure `magni.ico` is present and included with the executable (see PyInstaller `--add-data` flag).
- **Large files:** The app is optimized for huge files, but exporting or displaying all results may take time.
- **Tkinter errors:** Ensure Python is installed with Tkinter support. On Windows, this is included by default.
- **Delimiter issues:** For tab, use `\t` in the dropdown.
- **Log file not created:** Make sure you have write permissions in the folder where the app is located.

## Credits
- Developed by Xenofon Psychis - Filis.
- For support or suggestions, contact: [p.xenophon@gmail.com] 