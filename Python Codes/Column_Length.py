import csv

filename = 'large_file.csv'
length_threshold = 25
delimiter = ','
has_header = True  # Set to True if your file has a header row

# Specify the column to check:
# If has_header=True, use the column name (e.g., "Name")
# If has_header=False, use the column index (starting from 0)
column_to_check = 'Email'  # Example: 1 means the second column

with open(filename, newline='') as f:
    reader = csv.reader(f, delimiter=delimiter)
    if has_header:
        header = next(reader)
        if isinstance(column_to_check, str):
            col_idx = header.index(column_to_check)
        else:
            col_idx = column_to_check
        for row_num, row in enumerate(reader, start=2):
            value = row[col_idx]
            if len(str(value)) > length_threshold:
                print(f"Row {row_num} column '{header[col_idx]}' has value longer than {length_threshold}: {value}")
    else:
        col_idx = column_to_check
        for row_num, row in enumerate(reader, start=1):
            if col_idx >= len(row):
                continue  # Skip if the row is too short
            value = row[col_idx]
            if len(str(value)) > length_threshold:
                print(f"Row {row_num} column {col_idx+1} has value longer than {length_threshold}: {value}")
