# Design for Updating 01_parse_crf.py

## 1. Overview
The goal is to update `01_parse_crf.py` to correctly parse matrix variables (ending in `_`) and date variables (ending in `_date`) from a DOCX clinical report form (CRF) file.

## 2. Matrix Variables (Table parsing)
Currently, tabular variables are read as pairs from `col0` and `col1`. This works for 2-column tables but fails for matrix tables where columns 1..N represent sub-variables.
**Design:**
- When iterating over rows in a table, if the first cell (assumed to be row index) contains a variable ending in `_` (e.g. `[row_var_]`), it indicates a matrix row.
- In this case, iterate through columns from index 1 to N.
- The column header (row 0) should be queried. If row 0 cell `c` contains `[col_var]`, strip the brackets and build `full_var = row_var_ + col_var`.
- Extract the text of the cell at (current row, current column) and use it as `Coding`.
- Append `{ "Variable Expression": expr, "Variable Name": full_var, "Coding": cell_text }`.

## 3. Date Variables
Date variables may appear in either tables or paragraphs. They are identifiable by the suffix `_date` in the variable name. We want the extracted data to make the format clear.
**Design:**
- During extraction, monitor the extracted variable name.
- If `var_name.endswith('_date')` is true:
  - Search the `Variable Expression` for parenthesis strings typically denoting date formats, e.g., `(YYYY-MM-DD)`.
  - Override or prepend the `Coding` value with the matched format text so it's clearly identifiable downstream. Alternatively, just ensure `Coding` captures the format text correctly.

## 4. Updates to Functions
- `parse_docx_crf(file_path)`: Update the `for table in doc.tables` block to implement header scanning and matrix logic.
- Add logic at the end of variable extraction (both table and paragraph) to check if `var_name.endswith('_date')` and update `Coding` appropriately using a regex search on the expression string.

## 5. Output structure
The CSV output will look like this:
```csv
Variable Expression,Variable Name,Coding
"Date", "eri1_date", "(YYYY-MM-DD)"
"Performance 0", "perf_0", "1. Unknown or not done 2. Positive 3. Negative"
```
