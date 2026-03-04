"""
data_parser.py
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
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import openpyxl  # noqa: F401
except ImportError:
    raise ImportError("openpyxl is required: pip install openpyxl")

try:
    import pandas as pd
except ImportError:
    raise ImportError("pandas is required: pip install pandas")

try:
    import pyreadstat
except ImportError:
    raise ImportError("pyreadstat is required: pip install pyreadstat")

logger = logging.getLogger(__name__)


class DataParser:
    """
    Parser for clinical trial data files.
    Supports XLSX, CSV, SPSS (.sav), and JSON formats.
    """

    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize the parser.

        Args:
            output_dir: Optional directory for any downstream output. Not used
                        internally by the parser itself; available for callers.
        """
        self.output_dir = Path(output_dir) if output_dir else None

        # Internal state — populated during parse()
        self.df: Optional[pd.DataFrame] = None
        self.metadata: Dict[str, Any] = {}
        self.parsed_data: Dict[str, Any] = {}
        self.summary: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def parse(self, input_path: str) -> Dict[str, Any]:
        """
        Parse a data file and return structured information.

        Args:
            input_path: Path to the data file.

        Returns:
            Dictionary containing parsed data information.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file format is not supported.
        """
        file_path = Path(input_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Data file not found: {file_path}")

        file_ext = file_path.suffix.lower()
        logger.info("Parsing data file: %s (format: %s)", file_path.name, file_ext)

        # Reset state for reentrant calls
        self.df = None
        self.metadata = {}
        self.summary = {}
        self.parsed_data = {}

        # Dispatch to format-specific parser
        if file_ext in (".xlsx", ".xls"):
            self._parse_xlsx(file_path)
        elif file_ext == ".csv":
            self._parse_csv(file_path)
        elif file_ext == ".sav":
            self._parse_spss(file_path)
        elif file_ext == ".json":
            self._parse_json(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")

        # Compute summary statistics
        self._calculate_summary()

        # Build final output structure
        self.parsed_data = {
            "metadata": self.metadata,
            "variables": self._extract_variables(),
            "summary": self._get_summary(),
            "records": len(self.df) if self.df is not None else 0,
            "parsed_date": datetime.now().isoformat(),
        }

        logger.info(
            "Parsed %d records with %d variables.",
            self.parsed_data["records"],
            len(self.parsed_data["variables"]),
        )
        return self.parsed_data

    def get_dataframe(self, input_path: str) -> pd.DataFrame:
        """
        Parse the file and return the resulting DataFrame.

        Args:
            input_path: Path to the data file.

        Returns:
            Parsed pandas DataFrame.
        """
        self.parse(input_path)
        return self.df

    def get_metadata(self) -> Dict[str, Any]:
        """Return file metadata (populated after parse())."""
        return self.metadata

    # ------------------------------------------------------------------
    # Private parsing methods
    # ------------------------------------------------------------------

    def _parse_xlsx(self, file_path: Path) -> None:
        """Parse XLSX/Excel file."""
        xls = pd.ExcelFile(file_path, engine="openpyxl")
        self.df = pd.read_excel(xls)
        self.metadata = {
            "file_name": file_path.name,
            "format": "xlsx",
            "sheet_names": xls.sheet_names,
            "encoding": "utf-8",
        }

    def _parse_csv(self, file_path: Path) -> None:
        """Parse CSV file."""
        encodings = ["utf-8", "cp949", "euc-kr", "latin-1"]
        encoding_used = "utf-8"

        for encoding in encodings:
            try:
                self.df = pd.read_csv(file_path, encoding=encoding)
                encoding_used = encoding
                break
            except UnicodeDecodeError:
                continue
        else:
            # Fallback with error replacement
            self.df = pd.read_csv(file_path, encoding="utf-8", errors="replace")

        self.metadata = {
            "file_name": file_path.name,
            "format": "csv",
            "encoding": encoding_used,
            "delimiter": ",",
        }

    def _parse_spss(self, file_path: Path) -> None:
        """Parse SPSS (.sav) file."""
        self.df, spss_meta = pyreadstat.read_sav(file_path)

        meta_dict: Dict[str, Any] = {
            "file_name": file_path.name,
            "format": "spss",
            "variable_count": len(spss_meta.column_names),
            "variable_labels": dict(
                zip(
                    spss_meta.column_names,
                    spss_meta.column_labels
                    if spss_meta.column_labels
                    else [""] * len(spss_meta.column_names),
                )
            ),
            "value_labels": {},
            "missing_values": {},
        }

        if hasattr(spss_meta, "value_labels") and spss_meta.value_labels:
            for var_name, labels in spss_meta.value_labels.items():
                meta_dict["value_labels"][var_name] = labels

        if hasattr(spss_meta, "missing_values") and spss_meta.missing_values:
            meta_dict["missing_values"] = spss_meta.missing_values

        self.metadata = meta_dict

    def _parse_json(self, file_path: Path) -> None:
        """Parse JSON file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            self.df = pd.DataFrame(data)
        elif isinstance(data, dict):
            if "records" in data:
                self.df = pd.DataFrame(data["records"])
            elif "data" in data:
                self.df = pd.DataFrame(data["data"])
            else:
                self.df = pd.DataFrame([data])

        self.metadata = {
            "file_name": file_path.name,
            "format": "json",
        }

    # ------------------------------------------------------------------
    # Private analysis methods
    # ------------------------------------------------------------------

    def _extract_variables(self) -> List[Dict[str, Any]]:
        """Extract variable information from the dataframe."""
        if self.df is None:
            return []

        variables = []
        for col in self.df.columns:
            var_info: Dict[str, Any] = {
                "name": col,
                "label": self._get_column_label(col),
                "data_type": str(self.df[col].dtype),
                "unique_count": int(self.df[col].nunique()),
                "missing_count": int(self.df[col].isna().sum()),
                "missing_pct": round(float(self.df[col].isna().mean() * 100), 2),
            }

            if pd.api.types.is_numeric_dtype(self.df[col]):
                var_info["min"] = (
                    float(self.df[col].min())
                    if not pd.isna(self.df[col].min())
                    else None
                )
                var_info["max"] = (
                    float(self.df[col].max())
                    if not pd.isna(self.df[col].max())
                    else None
                )
                var_info["mean"] = (
                    float(self.df[col].mean())
                    if not pd.isna(self.df[col].mean())
                    else None
                )
                var_info["median"] = (
                    float(self.df[col].median())
                    if not pd.isna(self.df[col].median())
                    else None
                )

            if self.df[col].nunique() < 20:
                value_counts = self.df[col].value_counts()
                var_info["values"] = {str(k): int(v) for k, v in value_counts.items()}

            variables.append(var_info)

        return variables

    def _get_column_label(self, col: str) -> str:
        """Return the label for a column (from SPSS metadata if available)."""
        if isinstance(self.metadata, dict) and "variable_labels" in self.metadata:
            return self.metadata["variable_labels"].get(col, col)
        return col

    def _calculate_summary(self) -> None:
        """Compute summary statistics and store in self.summary."""
        if self.df is None:
            return

        if len(self.df) == 0:
            self.summary = {
                "total_records": 0,
                "total_variables": len(self.df.columns),
                "complete_records": 0,
                "complete_records_pct": 0.0,
                "numeric_variables": 0,
                "categorical_variables": 0,
                "date_variables": 0,
                "memory_usage_mb": 0.0,
            }
            return

        self.summary = {
            "total_records": len(self.df),
            "total_variables": len(self.df.columns),
            "complete_records": int(self.df.dropna().shape[0]),
            "complete_records_pct": round(
                float(self.df.dropna().shape[0] / len(self.df) * 100), 2
            ),
            "numeric_variables": int(
                self.df.select_dtypes(include=["number"]).shape[1]
            ),
            "categorical_variables": int(
                self.df.select_dtypes(include=["object", "category"]).shape[1]
            ),
            "date_variables": int(
                self.df.select_dtypes(include=["datetime"]).shape[1]
            ),
            "memory_usage_mb": round(
                self.df.memory_usage(deep=True).sum() / 1024 / 1024, 2
            ),
        }

    def _get_summary(self) -> Dict[str, Any]:
        """Return the computed summary statistics."""
        return self.summary


class PatientDataParser(DataParser):
    """Specialized parser for patient-level clinical trial data."""

    def __init__(self, output_dir: Optional[str] = None):
        super().__init__(output_dir=output_dir)
        self.patient_id_col: Optional[str] = None

    def identify_patient_column(self, df: pd.DataFrame) -> Optional[str]:
        """
        Identify the patient/subject ID column in the given DataFrame.

        Args:
            df: DataFrame to inspect.

        Returns:
            Column name of the identified patient ID column, or None.
        """
        id_patterns = [
            r"subject[_\s]?id",
            r"patient[_\s]?id",
            r"mrn",
            r"study[_\s]?id",
            r"scrno",
            r"subject",
        ]

        for col in df.columns:
            col_lower = col.lower()
            for pattern in id_patterns:
                if re.match(pattern, col_lower):
                    self.patient_id_col = col
                    return col

        # Fall back: use first column if every value is unique (looks like an ID)
        if len(df) > 0:
            first_col = df.columns[0]
            if df[first_col].nunique() == len(df):
                self.patient_id_col = first_col
                return first_col

        return None

    def parse(self, input_path: str) -> Dict[str, Any]:
        """
        Parse the file and add patient-specific analysis.

        Args:
            input_path: Path to the data file.

        Returns:
            Dictionary containing parsed data with an additional
            ``patient_id_column`` key in the result.
        """
        result = super().parse(input_path)

        patient_col = self.identify_patient_column(self.df)

        result["patient_info"] = {
            "patient_id_column": patient_col,
            "total_patients": (
                int(self.df[patient_col].nunique())
                if patient_col
                else len(self.df)
            ),
            "unique_records": len(self.df),
        }

        logger.info(
            "Patient ID column: %s (%d unique patients).",
            patient_col,
            result["patient_info"]["total_patients"],
        )
        return result
