import os
import re
import csv
import argparse
import datetime
from docx import Document
import PyPDF2
import pandas as pd

def extract_variable_parts(left_text):
    """
    Extracts 'Variable Expression' and 'Variable Name' from the left side.
    Look for [variable_name] instead of relying strictly on brackets at the end.
    """
    match = re.search(r'\[(.*?)\]', left_text)
    if match:
        var_name = match.group(1).strip()
        expr = left_text.replace(f"[{match.group(1)}]", "").strip()
        expr = re.sub(r'[\s:]+$', '', expr)
        return expr, var_name
    return left_text.strip(), ""

from docx.document import Document as _Document
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph

def iter_block_items(parent):
    if isinstance(parent, _Document):
        parent_elm = parent.element.body
    elif isinstance(parent, _Cell):
        parent_elm = parent._tc
    else:
        raise ValueError("something's not right")
        
    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)

def parse_docx_crf(file_path):
    print(f"Parsing DOCX CRF: {file_path}")
    doc = Document(file_path)
    variables = []
    
    current_var = None
    
    def format_coding(coding_text):
        if not coding_text:
            return ""
        # Check if it looks categorical (e.g., "0. None", "1. Yes")
        if re.search(r'\b\d+[\.\)]\s+', coding_text):
            return coding_text
        # Check if it contains multiple common categorical words
        if "Yes" in coding_text or "No" in coding_text or "Unknown" in coding_text:
            return coding_text
        # Otherwise, treat it as a unit for a number
        return f"Number (Unit: {coding_text})"
        
    for block in iter_block_items(doc):
        if isinstance(block, Table):
            table = block
            # Pre-scan the first row for column variables
            col_vars = {}
            if len(table.rows) > 0:
                for c_idx, cell in enumerate(table.rows[0].cells):
                    header_text = cell.text.replace('\n', ' ').strip()
                    match = re.search(r'\[(.*?)\]', header_text)
                    if match:
                        col_vars[c_idx] = match.group(1).strip()
                        
            for row in table.rows:
                if len(row.cells) >= 2:
                    col0 = row.cells[0].text.replace('\n', ' ').strip()
                    col1 = row.cells[1].text.replace('\n', ' ').strip()
                    
                    match = re.search(r'\[(.*?)\]', col0)
                    if match:
                        var_name = match.group(1).strip()
                        expr = col0.replace(f"[{match.group(1)}]", "").strip()
                        expr = re.sub(r'[\s:]+$', '', expr)
                        
                        if var_name.endswith('_'):
                            # Matrix variable
                            for c_idx in range(1, len(row.cells)):
                                if c_idx in col_vars:
                                    full_var_name = var_name + col_vars[c_idx]
                                    cell_text = row.cells[c_idx].text.replace('\n', ' ').strip()
                                    
                                    # Format date if applicable
                                    coding = cell_text
                                    date_match = re.search(r'\(((?:YYYY|DD|MM)[^)]*)\)', expr, re.IGNORECASE)
                                    if date_match:
                                        coding = f"Date ({date_match.group(1).upper()})"
                                    elif full_var_name.lower().endswith('_date') or full_var_name.lower().startswith('date_'):
                                        if not coding or coding.isspace(): coding = "Date"
                                    
                                    if not any(v.get("Variable Name") == full_var_name for v in variables):
                                        variables.append({
                                            "Variable Expression": expr,
                                            "Variable Name": full_var_name,
                                            "Coding": coding
                                        })
                        else:
                            # Standard variable
                            coding = col1
                            date_match = re.search(r'\(((?:YYYY|DD|MM)[^)]*)\)', expr, re.IGNORECASE)
                            if date_match:
                                coding = f"Date ({date_match.group(1).upper()})"
                            elif var_name.lower().endswith('_date') or var_name.lower().startswith('date_'):
                                if not coding or coding.isspace(): coding = "Date"
                                    
                            # Avoid adding duplicates if multiple table rows share the same variable name (sometimes happens in DOCX tables due to merged cells)
                            if not any(v.get("Variable Name") == var_name for v in variables):
                                variables.append({
                                    "Variable Expression": expr,
                                    "Variable Name": var_name,
                                    "Coding": coding
                                })
            current_var = None

        elif isinstance(block, Paragraph):
            para = block
            text = para.text.strip()
            if not text:
                continue
                
            matches = list(re.finditer(r'\[(.*?)\]', text))
            if matches:
                for i, match in enumerate(matches):
                    var_name = match.group(1).strip()
                    
                    # Expression for this var_name
                    start_idx = matches[i-1].end() if i > 0 else 0
                    expr_raw = text[start_idx:match.start()].strip()
                    expr_raw = re.sub(r'^[:\s]+', '', expr_raw)
                    expr_raw = re.sub(r'[\s:]+$', '', expr_raw)
                    
                    if re.search(r'\d[\.\)]', expr_raw):
                        last_opt = re.split(r'\d+[\.\)]', expr_raw)[-1].strip()
                        if last_opt:
                            expr_raw = last_opt
                    
                    # Coding for this var_name
                    end_idx = matches[i+1].start() if i + 1 < len(matches) else len(text)
                    coding_raw = text[match.end():end_idx].strip()
                    coding_raw = re.sub(r'^[:\s]+', '', coding_raw)
                    
                    coding = format_coding(coding_raw)
                    date_match = re.search(r'\(((?:YYYY|DD|MM)[^)]*)\)', expr_raw, re.IGNORECASE)
                    if date_match:
                        coding = f"Date ({date_match.group(1).upper()})"
                    elif var_name.lower().endswith('_date') or var_name.lower().startswith('date_'):
                        if not coding or coding.isspace(): coding = "Date"
                        
                    current_var = {
                        "Variable Expression": expr_raw,
                        "Variable Name": var_name,
                        "Coding": coding
                    }
                    variables.append(current_var)
            else:
                if current_var is not None:
                    is_coding_continuation = bool(re.match(r'^(\d+|[A-Za-z])[\.\)]\s+', text))
                    is_specify = "specify" in text.lower()
                    is_categorical = any(w in text.lower() for w in ["unknown", "yes", "no", "positive", "negative"])
                    hanging_previous = current_var["Coding"].strip().endswith(',') if current_var["Coding"] else False
                    
                    is_heading = text.isupper() or (len(text.split()) < 8 and not re.search(r'\d', text) and not is_categorical)
                    is_coding_date = current_var["Coding"] and current_var["Coding"].startswith("Date")
                    
                    if (is_coding_continuation or is_specify or is_categorical or hanging_previous) and not is_heading and not is_coding_date:
                        if current_var["Coding"].startswith("Number (Unit: "):
                            base_coding = current_var["Coding"][14:-1]
                            new_coding = base_coding + " " + text
                            current_var["Coding"] = format_coding(new_coding.strip())
                        elif current_var["Coding"]:
                            current_var["Coding"] += " " + text
                        else:
                            current_var["Coding"] = text
                    else:
                        current_var = None
                        
    return variables

def parse_pdf_crf(file_path):
    print(f"Parsing PDF CRF: {file_path}")
    variables = []
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        # Simple line-by-line parsing
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if line and ':' in line:
                parts = line.split(':', 1)
                expr, var_name = extract_variable_parts(parts[0].strip())
                variables.append({
                    "Variable Expression": expr,
                    "Variable Name": var_name,
                    "Coding": parts[1].strip()
                })
    return variables

def main():
    parser = argparse.ArgumentParser(description="Parse CRF files to extract variable definitions.")
    parser.add_argument("input_crf", help="Path to the input CRF file (.docx or .pdf)")
    parser.add_argument("--output_dir", default="/Users/kimhawk/Library/CloudStorage/Dropbox/Paper/Clinical_statistics_analyzer/data", help="Directory to save parsed output")
    parser.add_argument("--actual_data_xlsx", default=None, help="Optional actual Excel data file to map variables against")
    args = parser.parse_args()

    input_path = args.input_crf
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    if input_path.lower().endswith('.docx'):
        parsed_data = parse_docx_crf(input_path)
    elif input_path.lower().endswith('.pdf'):
        parsed_data = parse_pdf_crf(input_path)
    else:
        print("Unsupported file format. Please provide a .docx or .pdf file.")
        return

    def map_excel_columns(variables, excel_path):
        try:
            df = pd.read_excel(excel_path, header=None)
            excel_headers = []
            for i in range(len(df.columns)):
                val = df.iloc[2, i]
                if pd.isna(val):
                    val = df.iloc[1, i]
                if pd.isna(val):
                    val = df.iloc[0, i]
                raw_str = str(val).strip()
                if raw_str != 'nan' and raw_str:
                    excel_headers.append(raw_str)
                    
            for var in variables:
                expr = str(var.get("Variable Expression", "")).lower().replace('\ufeff', '').strip()
                matched_header = ""
                for eh in excel_headers:
                    eh_clean = eh.lower().replace('\ufeff', '').strip()
                    if eh_clean in expr or expr in eh_clean:
                        matched_header = eh
                        break
                var["Mapped Excel Column"] = matched_header
        except Exception as e:
            print(f"Error mapping Excel: {e}")
        return variables

    if args.actual_data_xlsx:
        print(f"Mapping against actual data: {args.actual_data_xlsx}")
        parsed_data = map_excel_columns(parsed_data, args.actual_data_xlsx)

    # Output to CSV instead of JSON to represent tabular data
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"crf_mapping_{timestamp}.csv")
    
    # Define CSV column headers
    fieldnames = ["Variable Expression", "Variable Name", "Coding"]
    if args.actual_data_xlsx:
        fieldnames.append("Mapped Excel Column")
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in parsed_data:
            writer.writerow(row)
    
    print(f"CRF parsing complete. Output saved to: {output_file}")

if __name__ == "__main__":
    main()
