# CSV Analyzer

A user-friendly, multi-tool CSV analysis application with a modern GUI (Tkinter). Designed to handle large files efficiently and provide comprehensive CSV analysis capabilities.

## 🚀 Features

### **Core Analysis Tools**
- **Column Length Checker**: Find rows with column values exceeding a specified length threshold
- **Find Duplicates**: Identify duplicate values in a specified column with full row export
- **Find Extra Delimiters**: Detect rows with more columns than expected and pinpoint exact positions

### **Smart File Handling**
- **Auto-delimiter Detection**: Automatically detects the correct delimiter when loading files
- **Analyze File**: Shows delimiter, column count, and row count for any CSV file
- **Backslash Delimiter Support**: Full support for backslash-delimited files
- **Large File Support**: Handles multi-GB files efficiently using streaming and threading

### **User Interface**
- **Modern GUI**: Clean, professional interface with tabbed layout
- **Progress Indicators**: Non-blocking progress popups with cancel button
- **Export Functionality**: Export results to CSV files
- **About Dialog**: Application information with GitHub link
- **Icon Support**: Custom application icon in all windows including progress popup
- **Comprehensive Popup Messages**: Clear feedback for all user actions

### **Advanced Options**
- **Header Detection**: Option to specify if file has headers
- **Ignore First Row**: Option to skip the first row of data (independent of header setting)
- **Customizable Delimiters**: Support for comma, tab, semicolon, pipe, and backslash
- **Smart Metadata Handling**: Automatically skips metadata lines in files with unusual structures

## 📋 Requirements

- Python 3.6+
- tkinter (usually included with Python)
- No additional dependencies required

## 🛠️ Installation & Usage

### **Option 1: Run as Python Script**
```bash
python csv_analyzer_gui.py
```

### **Option 2: Create Executable (Recommended)**
```bash
# Install PyInstaller if not already installed
pip install pyinstaller

# Create executable with icon
pyinstaller --onefile --windowed --add-data "magni.ico;." --icon=magni.ico csv_analyzer_gui.py

# The executable will be created in the dist/ folder
```

## 📖 How to Use

### **1. Loading Files**
- Click "📂 Browse..." to select a CSV file
- The app will automatically detect the delimiter
- The detected delimiter is displayed in the interface

### **2. Column Length Checker**
- **Column**: Enter column name or index (0-based)
- **Length threshold**: Enter maximum allowed character length
- **Options**: 
  - Check "File has header" if your file has column headers (unchecked by default)
  - Check "Ignore first row" to skip the first data row (checked by default)
- Click "Check" to analyze
- Results show rows with values exceeding the threshold
- Export results to CSV

### **3. Find Duplicates**
- **Column**: Enter column name or index (0-based)
- **Options**: Same header and ignore first row options
- Click "Find Duplicates" to analyze
- Results show all rows with duplicate values in the specified column
- Export results to CSV

### **4. Find Extra Delimiters**
- **Options**: Same header and ignore first row options
- Click "Check for Extra Delimiters" to analyze
- Results show rows with more columns than expected
- Displays the exact position of extra delimiters
- Export problematic rows to CSV
- **Smart Detection**: Automatically handles files with metadata lines

### **5. Analyze File**
- Click "Analyze File" to get file statistics
- Shows:
  - Delimiter used by the file
  - Number of columns
  - Number of rows
- **Smart Analysis**: Skips metadata lines for accurate counts

## 🔧 Supported Delimiters

| Delimiter | Character | Description |
|-----------|-----------|-------------|
| Comma | `,` | Standard CSV delimiter |
| Tab | `\t` | Tab-separated values |
| Semicolon | `;` | Common European CSV format |
| Pipe | `\|` | Pipe-separated values |
| Backslash | `\` | Custom delimiter support |

## 📊 Logging

The application creates a log file `csv_analyzer.log` in the same directory as the executable. This file contains:
- Application startup/shutdown events
- File loading and analysis operations
- Error messages and debugging information
- User actions and results

## 🚨 Troubleshooting

### **Common Issues**

1. **"tkinter not found"**
   - Reinstall Python with Tcl/Tk support
   - For Anaconda: `conda install tk`

2. **Large files are slow**
   - The app uses streaming for large files
   - Progress popups show current status
   - Results are displayed incrementally

3. **Wrong delimiter detected**
   - Use "Analyze File" to verify the detected delimiter
   - Check the log file for detailed detection information

4. **Export not working**
   - Ensure you have write permissions in the target directory
   - Check that results exist before trying to export

### **Performance Tips**

- For very large files (>1GB), consider splitting the file first
- Use specific column names instead of indices when possible
- The app processes files line-by-line to handle large datasets

## 📝 Version History

### **v1.3 (Current)**
- ✅ **Enhanced metadata handling** for files with unusual structures
- ✅ **Improved Find Extra Delimiters** detection logic
- ✅ **Updated default settings**: "Ignore first row" checked, "File has header" unchecked
- ✅ **Cancel button** in processing popup for all operations
- ✅ **Icon support** for all windows including progress popup
- ✅ **Comprehensive popup messages** for user feedback
- ✅ **Smart auto-delimiter detection** with metadata filtering
- ✅ **All previous features** from v1.0-v1.2

### **v1.2**
- ✅ Auto-delimiter detection
- ✅ Analyze File feature
- ✅ Backslash delimiter support
- ✅ Ignore first row option
- ✅ Enhanced UI and logging
- ✅ Fixed "Ignore first row" + "File has header" logic

### **v1.1**
- ✅ Enhanced UI with progress popups
- ✅ Improved error handling
- ✅ Better export functionality

### **v1.0**
- ✅ Basic CSV analyzer
- ✅ Column length checking
- ✅ Duplicate detection
- ✅ Extra delimiter detection
- ✅ Export functionality

## 👨‍💻 Development

### **File Structure**
```
TkinterGUI/
├── csv_analyzer_gui.py      # Main application
├── README.md               # This documentation
├── magni.ico              # Application icon
├── versions/               # Version history
│   ├── csv_analyzer_gui_v1.0.py
│   ├── csv_analyzer_gui_v1.1.py
│   ├── csv_analyzer_gui_v1.2.py
│   └── csv_analyzer_gui_v1.3.py
├── dist/                   # PyInstaller output
└── build/                  # PyInstaller build files
```

### **Key Classes**
- `CSVAnalyzerApp`: Main application class
- Worker methods: `_length_check_worker`, `_dup_check_worker`, `_extra_check_worker`
- Auto-detection: `auto_detect_delimiter`, `analyze_file_structure`

## 📞 Support

**Developer**: Xenofon Psychis - Filis  
**Contact**: p.xenophon@gmail.com  
**GitHub**: [View on GitHub](https://github.com/psycxeno/XenophonPsychisFilis/tree/main/CSV%20Analyzer)

## 📄 License


---

**Last Updated**: July 26, 2025  
**Version**: 1.3 
