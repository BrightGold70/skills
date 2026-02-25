#!/usr/bin/env python3
"""
08_parse_data.py
Clinical Trial Data File Parser

Parses clinical trial data files in various formats:
- XLSX (Excel)
- CSV
- SPSS (.sav)
- JSON

Extracts:
- Patient/subject records
- Variable names and types
- Data summary statistics
- Missing value patterns

Author: Clinical Statistics Analyzer
Version: 1.0.0
"""

import json
import re
import sys
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from collections import Counter

# Try to import required libraries
try:
    import openpyxl
except ImportError:
    print("Installing openpyxl...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl", "-q"])
    import openpyxl

try:
    import pandas as pd
except ImportError:
    print("Installing pandas...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas", "-q"])
    import pandas as pd

try:
    import pyreadstat
except ImportError:
    print("Installing pyreadstat for SPSS support...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyreadstat", "-q"])
    import pyreadstat


class DataParser:
    """
    Parser for clinical trial data files.
    Supports XLSX, CSV, SPSS (.sav), and JSON formats.
    """
    
    def __init__(self, file_path: str):
        """
        Initialize the parser with a data file.
        
        Args:
            file_path: Path to the data file
        """
        self.file_path = Path(file_path)
        self.file_ext = self.file_path.suffix.lower()
        self.parsed_data = {}
        self.df = None
        self.metadata = {}
        
    def parse(self) -> Dict[str, Any]:
        """
        Parse the data file and extract structured data.
        
        Returns:
            Dictionary containing parsed data information
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"Data file not found: {self.file_path}")
        
        # Parse based on file type
        if self.file_ext in ['.xlsx', '.xls']:
            self._parse_xlsx()
        elif self.file_ext == '.csv':
            self._parse_csv()
        elif self.file_ext == '.sav':
            self._parse_spss()
        elif self.file_ext == '.json':
            self._parse_json()
        else:
            raise ValueError(f"Unsupported file format: {self.file_ext}")
        
        # Extract summary statistics
        self._calculate_summary()
        
        # Build final data structure
        self.parsed_data = {
            "metadata": self.metadata,
            "variables": self._extract_variables(),
            "summary": self._get_summary(),
            "records": len(self.df) if self.df is not None else 0,
            "parsed_date": datetime.now().isoformat()
        }
        
        return self.parsed_data
    
    def _parse_xlsx(self) -> None:
        """Parse XLSX/Excel file."""
        # Read Excel file
        self.df = pd.read_excel(self.file_path, engine='openpyxl')
        
        self.metadata = {
            "file_name": self.file_path.name,
            "format": "xlsx",
            "sheet_names": pd.ExcelFile(self.file_path).sheet_names,
            "encoding": "utf-8"
        }
    
    def _parse_csv(self) -> None:
        """Parse CSV file."""
        # Try different encodings
        encodings = ['utf-8', 'cp949', 'euc-kr', 'latin-1']
        
        for encoding in encodings:
            try:
                self.df = pd.read_csv(self.file_path, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            # Fallback to with error handling
            self.df = pd.read_csv(self.file_path, encoding='utf-8', errors='replace')
        
        self.metadata = {
            "file_name": self.file_path.name,
            "format": "csv",
            "encoding": encoding,
            "delimiter": ","
        }
    
    def _parse_spss(self) -> None:
        """Parse SPSS (.sav) file."""
        self.df, self.metadata = pyreadstat.read_sav(self.file_path)
        
        # Convert metadata to serializable format
        meta_dict = {
            "file_name": self.file_path.name,
            "format": "spss",
            "variable_count": len(self.metadata.column_names),
            "variable_labels": dict(zip(
                self.metadata.column_names,
                self.metadata.column_labels if self.metadata.column_labels else [''] * len(self.metadata.column_names)
            )),
            "value_labels": {},
            "missing_values": {}
        }
        
        # Add value labels if available
        if hasattr(self.metadata, 'value_labels') and self.metadata.value_labels:
            for var_name, labels in self.metadata.value_labels.items():
                meta_dict["value_labels"][var_name] = labels
        
        # Add missing values if available
        if hasattr(self.metadata, 'missing_values') and self.metadata.missing_values:
            meta_dict["missing_values"] = self.metadata.missing_values
        
        self.metadata = meta_dict
    
    def _parse_json(self) -> None:
        """Parse JSON file."""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different JSON structures
        if isinstance(data, list):
            self.df = pd.DataFrame(data)
        elif isinstance(data, dict):
            # Check if it's a structured format
            if 'records' in data:
                self.df = pd.DataFrame(data['records'])
            elif 'data' in data:
                self.df = pd.DataFrame(data['data'])
            else:
                self.df = pd.DataFrame([data])
        
        self.metadata = {
            "file_name": self.file_path.name,
            "format": "json"
        }
    
    def _extract_variables(self) -> List[Dict[str, Any]]:
        """Extract variable information from dataframe."""
        if self.df is None:
            return []
        
        variables = []
        
        for col in self.df.columns:
            var_info = {
                "name": col,
                "label": self._get_column_label(col),
                "data_type": str(self.df[col].dtype),
                "unique_count": int(self.df[col].nunique()),
                "missing_count": int(self.df[col].isna().sum()),
                "missing_pct": round(float(self.df[col].isna().mean() * 100), 2)
            }
            
            # Add type-specific info
            if pd.api.types.is_numeric_dtype(self.df[col]):
                var_info["min"] = float(self.df[col].min()) if not pd.isna(self.df[col].min()) else None
                var_info["max"] = float(self.df[col].max()) if not pd.isna(self.df[col].max()) else None
                var_info["mean"] = float(self.df[col].mean()) if not pd.isna(self.df[col].mean()) else None
                var_info["median"] = float(self.df[col].median()) if not pd.isna(self.df[col].median()) else None
            
            # Add categorical info
            if self.df[col].nunique() < 20:
                value_counts = self.df[col].value_counts()
                var_info["values"] = {
                    str(k): int(v) for k, v in value_counts.items()
                }
            
            variables.append(var_info)
        
        return variables
    
    def _get_column_label(self, col: str) -> str:
        """Get label for a column (from metadata if available)."""
        if isinstance(self.metadata, dict):
            if 'variable_labels' in self.metadata:
                return self.metadata['variable_labels'].get(col, col)
        return col
    
    def _calculate_summary(self) -> None:
        """Calculate summary statistics."""
        if self.df is None:
            return
        
        self.summary = {
            "total_records": len(self.df),
            "total_variables": len(self.df.columns),
            "complete_records": int(self.df.dropna().shape[0]),
            "complete_records_pct": round(float(self.df.dropna().shape[0] / len(self.df) * 100), 2),
            "numeric_variables": int(self.df.select_dtypes(include=['number']).shape[1]),
            "categorical_variables": int(self.df.select_dtypes(include=['object', 'category']).shape[1]),
            "date_variables": int(self.df.select_dtypes(include=['datetime']).shape[1]),
            "memory_usage_mb": round(self.df.memory_usage(deep=True).sum() / 1024 / 1024, 2)
        }
    
    def _get_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        return getattr(self, 'summary', {})
    
    def get_dataframe(self) -> pd.DataFrame:
        """Get the parsed dataframe."""
        return self.df
    
    def get_metadata(self) -> Dict:
        """Get file metadata."""
        return self.metadata
    
    def save_json(self, output_path: Optional[str] = None) -> str:
        """Save parsed data to JSON file."""
        import datetime as dt
        
        if not self.parsed_data:
            raise ValueError("No parsed data available. Run parse() first.")
        
        if output_path is None:
            output_path = self.file_path.parent / f"{self.file_path.stem}_data_parsed.json"
        
        # Make JSON serializable
        output_data = self.parsed_data.copy()
        
        # Convert dataframe to records (limited for large files)
        def make_serializable(obj):
            if isinstance(obj, (dt.datetime, dt.date, pd.Timestamp)):
                return obj.isoformat()
            elif hasattr(obj, '__dict__'):
                return str(obj)
            return obj
        
        if len(self.df) > 1000:
            records = self.df.head(100).to_dict(orient='records')
            output_data["note"] = "Only first 100 records included"
        else:
            records = self.df.to_dict(orient='records')
        
        # Convert records
        def convert_records(records):
            result = []
            for record in records:
                new_record = {}
                for k, v in record.items():
                    new_record[k] = make_serializable(v)
                result.append(new_record)
            return result
        
        output_data["records"] = convert_records(records)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        return str(output_path)
    
    def export_csv(self, output_path: Optional[str] = None) -> str:
        """Export data to CSV file."""
        if self.df is None:
            raise ValueError("No data parsed. Run parse() first.")
        
        if output_path is None:
            output_path = self.file_path.parent / f"{self.file_path.stem}_export.csv"
        
        self.df.to_csv(output_path, index=False, encoding='utf-8')
        
        return str(output_path)


class PatientDataParser(DataParser):
    """Specialized parser for patient-level clinical trial data."""
    
    def __init__(self, file_path: str):
        super().__init__(file_path)
        self.patient_id_col = None
        
    def identify_patient_column(self) -> Optional[str]:
        """Identify the patient/subject ID column."""
        if self.df is None:
            return None
        
        # Common patient ID column names
        id_patterns = [
            r'subject[_\s]?id',
            r'patient[_\s]?id',
            r'mrn',
            r'study[_\s]?id',
            r'scrno',
            r'subject'
        ]
        
        for col in self.df.columns:
            col_lower = col.lower()
            for pattern in id_patterns:
                if re.match(pattern, col_lower):
                    self.patient_id_col = col
                    return col
        
        # If no pattern match, use first column if it looks like an ID
        if len(self.df) > 0:
            first_col = self.df.columns[0]
            if self.df[first_col].nunique() == len(self.df):
                self.patient_id_col = first_col
                return first_col
        
        return None
    
    def parse(self) -> Dict[str, Any]:
        """Parse and add patient-specific analysis."""
        # Run parent parse
        result = super().parse()
        
        # Identify patient column
        patient_col = self.identify_patient_column()
        
        # Add patient-specific info
        result["patient_info"] = {
            "patient_id_column": patient_col,
            "total_patients": int(self.df[patient_col].nunique()) if patient_col else len(self.df),
            "unique_records": len(self.df)
        }
        
        return result


def main():
    """Main function for command-line usage."""
    if len(sys.argv) < 2:
        print("Usage: python 08_parse_data.py <data_file> [output_json]")
        print("\nSupported formats:")
        print("  - XLSX/ XLS (Excel)")
        print("  - CSV")
        print("  - SPSS (.sav)")
        print("  - JSON")
        print("\nExample:")
        print("  python 08_parse_data.py patient_data.xlsx")
        print("  python 08_parse_data.py patient_data.sav output.json")
        sys.exit(1)
    
    data_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        print(f"Parsing data file: {data_file}")
        parser = PatientDataParser(data_file)
        data = parser.parse()
        
        # Print summary
        print("\n" + "="*60)
        print("Data File Parsed Successfully")
        print("="*60)
        print(f"Total Records: {data['records']}")
        print(f"Total Variables: {data['summary']['total_variables']}")
        print(f"Complete Records: {data['summary']['complete_records']} ({data['summary']['complete_records_pct']}%)")
        
        if "patient_info" in data:
            print(f"Unique Patients: {data['patient_info']['total_patients']}")
        
        print("\nVariable Summary:")
        print(f"  Numeric: {data['summary']['numeric_variables']}")
        print(f"  Categorical: {data['summary']['categorical_variables']}")
        print(f"  Date: {data['summary']['date_variables']}")
        
        print("="*60)
        
        # Save to file
        output_path = parser.save_json(output_file)
        print(f"\nSaved to: {output_path}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
