import os
import re
import csv
import argparse
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

def parse_docx_crf(file_path):
    print(f"Parsing DOCX CRF: {file_path}")
    doc = Document(file_path)
    variables = []
    
    # 1. Parse Tables
    for table in doc.tables:
        for row in table.rows:
            if len(row.cells) >= 2:
                col0 = row.cells[0].text.replace('\n', ' ').strip()
                col1 = row.cells[1].text.replace('\n', ' ').strip()
                
                match = re.search(r'\[(.*?)\]', col0)
                if match:
                    var_name = match.group(1).strip()
                    expr = col0.replace(f"[{match.group(1)}]", "").strip()
                    expr = re.sub(r'[\s:]+$', '', expr)
                    
                    # Avoid adding duplicates if multiple table rows share the same variable name (sometimes happens in DOCX tables due to merged cells)
                    if not any(v.get("Variable Name") == var_name for v in variables):
                        variables.append({
                            "Variable Expression": expr,
                            "Variable Name": var_name,
                            "Coding": col1
                        })

    # 2. Parse Paragraphs
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
        
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
            
        match = re.search(r'\[(.*?)\]', text)
        if match:
            # We found a variable
            if ':' in text:
                parts = text.split(':', 1)
                expr, var_name = extract_variable_parts(parts[0].strip())
                current_var = {
                    "Variable Expression": expr,
                    "Variable Name": var_name,
                    "Coding": format_coding(parts[1].strip())
                }
            else:
                expr, var_name = extract_variable_parts(text)
                current_var = {
                    "Variable Expression": expr,
                    "Variable Name": var_name,
                    "Coding": ""
                }
            variables.append(current_var)
        else:
            # Not a new variable, if we have a current_var, it's a continuation of its coding
            if current_var is not None:
                # If it was assigned as "Number (Unit: ...)", we might need to append inside or outside
                # But typically continuation lines are categorical multi-lines.
                # So let's strip the "Number (Unit: " wrapper if it was applied incorrectly
                # Actually, simpler: just reconstruct it
                if current_var["Coding"].startswith("Number (Unit: "):
                    base_coding = current_var["Coding"][14:-1] # strip wrapper
                    new_coding = base_coding + " " + text
                    current_var["Coding"] = format_coding(new_coding.strip())
                elif current_var["Coding"]:
                    current_var["Coding"] += " " + text
                else:
                    current_var["Coding"] = text
                    
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
    output_file = os.path.join(output_dir, "crf_mapping.csv")
    
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
