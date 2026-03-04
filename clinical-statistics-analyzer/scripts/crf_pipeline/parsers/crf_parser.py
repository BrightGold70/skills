"""CRF document parser — extracts variable definitions from .docx and .pdf CRFs."""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd
import pypdf
from docx import Document
from docx.document import Document as _Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table, _Cell
from docx.text.paragraph import Paragraph

from ..utils.fuzzy_matching import fuzzy_match

logger = logging.getLogger(__name__)


class CRFParser:
    """Parse CRF definition documents (.docx, .pdf) into structured variable mappings.

    Args:
        output_dir: Optional directory hint for callers; not used internally.
        excel_path: Optional path to an Excel data file for column mapping.
        fuzzy_threshold: Minimum fuzzy-match score (0–100) for Excel column matching.
    """

    def __init__(
        self,
        output_dir: Optional[str] = None,
        excel_path: Optional[str] = None,
        fuzzy_threshold: int = 60,
    ) -> None:
        self.output_dir: Optional[Path] = Path(output_dir) if output_dir else None
        self.excel_path: Optional[Path] = Path(excel_path) if excel_path else None
        self.fuzzy_threshold: int = fuzzy_threshold

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def parse(self, input_path: str) -> Dict[str, Any]:
        """Parse a CRF file and return structured variable definitions.

        Args:
            input_path: Absolute or relative path to a .docx or .pdf file.

        Returns:
            A dict with keys:
                - ``metadata``: source file info.
                - ``variables``: list of variable dicts (Variable Expression,
                  Variable Name, Coding, and optionally Mapped Excel Column).
                - ``validation_rules``: list of inferred validation rule dicts.

        Raises:
            ValueError: If the file extension is not .docx or .pdf.
        """
        path = Path(input_path)
        suffix = path.suffix.lower()

        if suffix == ".docx":
            variables = self._parse_docx(path)
        elif suffix == ".pdf":
            variables = self._parse_pdf(path)
        else:
            raise ValueError(
                f"Unsupported file format '{suffix}'. Provide a .docx or .pdf file."
            )

        if self.excel_path:
            variables = self._map_excel_columns(variables)

        validation_rules = {
            "total_variables": len(variables),
            "rules": [
                self._generate_validation_rule(
                    v.get("Variable Name", ""),
                    self._infer_variable_type(v.get("Coding", ""), v.get("Variable Name", "")),
                    v.get("Coding", ""),
                )
                for v in variables
            ],
        }

        return {
            "metadata": {
                "source_file": str(path),
                "excel_path": str(self.excel_path) if self.excel_path else None,
            },
            "variables": variables,
            "validation_rules": validation_rules,
        }

    # ------------------------------------------------------------------
    # Private parsers
    # ------------------------------------------------------------------

    def _parse_docx(self, file_path: Path) -> List[Dict[str, str]]:
        """Extract variable definitions from a .docx CRF."""
        logger.info("Parsing DOCX CRF: %s", file_path)
        doc = Document(str(file_path))
        variables: List[Dict[str, str]] = []
        seen: Set[str] = set()
        current_var: Optional[Dict[str, str]] = None

        for block in self._iter_block_items(doc):
            if isinstance(block, Table):
                self._parse_docx_tables(block, variables, seen)
                # Reset paragraph continuation state after processing a table
                current_var = None

            elif isinstance(block, Paragraph):
                current_var = self._parse_docx_paragraphs(
                    block, variables, seen, current_var
                )

        return variables

    def _parse_docx_tables(
        self,
        table: Table,
        variables: List[Dict[str, str]],
        seen: Set[str],
    ) -> None:
        """Extract variable definitions from a single .docx table."""
        # Pre-scan the first row for column variable names
        col_vars: Dict[int, str] = {}
        if table.rows:
            for c_idx, cell in enumerate(table.rows[0].cells):
                header_text = cell.text.replace("\n", " ").strip()
                m = re.search(r"\[(.*?)\]", header_text)
                if m:
                    col_vars[c_idx] = m.group(1).strip()

        for row in table.rows:
            if len(row.cells) >= 2:
                col0 = row.cells[0].text.replace("\n", " ").strip()
                col1 = row.cells[1].text.replace("\n", " ").strip()

                m = re.search(r"\[(.*?)\]", col0)
                if m:
                    var_name = m.group(1).strip()
                    expr = col0.replace(f"[{m.group(1)}]", "").strip()
                    expr = re.sub(r"[\s:]+$", "", expr)

                    if var_name.endswith("_"):
                        # Matrix variable — expand across column headers
                        for c_idx in range(1, len(row.cells)):
                            if c_idx in col_vars:
                                full_var_name = var_name + col_vars[c_idx]
                                cell_text = (
                                    row.cells[c_idx].text.replace("\n", " ").strip()
                                )
                                coding = self._infer_date_coding(
                                    expr, full_var_name, cell_text
                                )

                                if full_var_name not in seen:
                                    seen.add(full_var_name)
                                    variables.append(
                                        {
                                            "Variable Expression": expr,
                                            "Variable Name": full_var_name,
                                            "Coding": coding,
                                        }
                                    )
                    else:
                        # Standard variable
                        coding = self._infer_date_coding(expr, var_name, col1)

                        if var_name not in seen:
                            seen.add(var_name)
                            variables.append(
                                {
                                    "Variable Expression": expr,
                                    "Variable Name": var_name,
                                    "Coding": coding,
                                }
                            )

    def _parse_docx_paragraphs(
        self,
        block: Paragraph,
        variables: List[Dict[str, str]],
        seen: Set[str],
        current_var: Optional[Dict[str, str]],
    ) -> Optional[Dict[str, str]]:
        """Extract variable definitions from a single .docx paragraph.

        Returns the updated current_var for paragraph continuation tracking.
        """

        def format_coding(coding_text: str) -> str:
            if not coding_text:
                return ""
            if re.search(r"\b\d+[\.\)]\s+", coding_text):
                return coding_text
            if "Yes" in coding_text or "No" in coding_text or "Unknown" in coding_text:
                return coding_text
            return f"Number (Unit: {coding_text})"

        text = block.text.strip()
        if not text:
            return current_var

        matches = list(re.finditer(r"\[(.*?)\]", text))
        if matches:
            for i, m in enumerate(matches):
                var_name = m.group(1).strip()

                start_idx = matches[i - 1].end() if i > 0 else 0
                expr_raw = text[start_idx : m.start()].strip()
                expr_raw = re.sub(r"^[:\s]+", "", expr_raw)
                expr_raw = re.sub(r"[\s:]+$", "", expr_raw)

                if re.search(r"\d[\.\)]", expr_raw):
                    last_opt = re.split(r"\d+[\.\)]", expr_raw)[-1].strip()
                    if last_opt:
                        expr_raw = last_opt

                end_idx = (
                    matches[i + 1].start() if i + 1 < len(matches) else len(text)
                )
                coding_raw = text[m.end() : end_idx].strip()
                coding_raw = re.sub(r"^[:\s]+", "", coding_raw)

                coding = format_coding(coding_raw)
                coding = self._infer_date_coding(expr_raw, var_name, coding)

                current_var = {
                    "Variable Expression": expr_raw,
                    "Variable Name": var_name,
                    "Coding": coding,
                }
                if var_name not in seen:
                    seen.add(var_name)
                    variables.append(current_var)
        else:
            if current_var is not None:
                is_coding_continuation = bool(
                    re.match(r"^(\d+|[A-Za-z])[\.\)]\s+", text)
                )
                is_specify = "specify" in text.lower()
                is_categorical = any(
                    w in text.lower()
                    for w in ["unknown", "yes", "no", "positive", "negative"]
                )
                hanging_previous = (
                    current_var["Coding"].strip().endswith(",")
                    if current_var["Coding"]
                    else False
                )
                is_heading = text.isupper() or (
                    len(text.split()) < 8
                    and not re.search(r"\d", text)
                    and not is_categorical
                )
                is_coding_date = current_var["Coding"] and current_var[
                    "Coding"
                ].startswith("Date")

                if (
                    (
                        is_coding_continuation
                        or is_specify
                        or is_categorical
                        or hanging_previous
                    )
                    and not is_heading
                    and not is_coding_date
                ):
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

        return current_var

    def _parse_pdf(self, file_path: Path) -> List[Dict[str, str]]:
        """Extract variable definitions from a .pdf CRF via text extraction."""
        logger.info("Parsing PDF CRF: %s", file_path)
        logger.warning(
            "PDF extraction has lower fidelity than .docx; "
            "consider converting to .docx for more accurate parsing."
        )
        variables: List[Dict[str, str]] = []

        with open(file_path, "rb") as fh:
            reader = pypdf.PdfReader(fh)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"

        for line in text.split("\n"):
            line = line.strip()
            if not line or ":" not in line:
                continue
            # Skip lines shorter than 5 chars
            if len(line) < 5:
                continue
            # Skip lines longer than 500 chars
            if len(line) > 500:
                continue
            # Skip page numbers (bare digits)
            if re.match(r"^\d+$", line):
                continue
            # Skip ALL CAPS headers with fewer than 3 words
            words = line.split()
            if line.isupper() and len(words) < 3:
                continue

            parts = line.split(":", 1)
            expr, var_name = self._extract_variable_parts(parts[0].strip())
            variables.append(
                {
                    "Variable Expression": expr,
                    "Variable Name": var_name,
                    "Coding": parts[1].strip(),
                }
            )

        return variables

    # ------------------------------------------------------------------
    # Instance method — requires self.excel_path / self.fuzzy_threshold
    # ------------------------------------------------------------------

    def _map_excel_columns(self, variables: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Attempt to map each variable to a column header in the Excel data file."""
        if not self.excel_path:
            return variables

        try:
            df = pd.read_excel(str(self.excel_path), header=None)

            # Forward-fill the first 3 rows to handle merged cells
            df.iloc[0:3] = df.iloc[0:3].ffill(axis=1)

            excel_headers: List[str] = []
            for i in range(len(df.columns)):
                h0 = str(df.iloc[0, i]).strip() if not pd.isna(df.iloc[0, i]) else ""
                h1 = str(df.iloc[1, i]).strip() if not pd.isna(df.iloc[1, i]) else ""
                h2 = str(df.iloc[2, i]).strip() if not pd.isna(df.iloc[2, i]) else ""

                parts: List[str] = []
                for h in (h0, h1, h2):
                    if h and h != "nan" and not h.startswith("Unnamed:") and h not in parts:
                        parts.append(h)

                combined = " | ".join(parts)
                if combined:
                    excel_headers.append(combined)

            for var in variables:
                expr = (
                    str(var.get("Variable Expression", ""))
                    .lower()
                    .replace("\ufeff", "")
                    .strip()
                )
                matched_header = ""
                if expr and excel_headers:
                    best_match, score = fuzzy_match(
                        expr, excel_headers, threshold=self.fuzzy_threshold
                    )
                    if best_match is not None:
                        matched_header = best_match

                var["Mapped Excel Column"] = matched_header

        except (FileNotFoundError, ValueError, KeyError, IndexError):
            logger.exception("Error mapping Excel columns from %s", self.excel_path)

        return variables

    # ------------------------------------------------------------------
    # Static helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _iter_block_items(parent: Any):
        """Yield Paragraph and Table objects from a Document or cell, in order."""
        if isinstance(parent, _Document):
            parent_elm = parent.element.body
        elif isinstance(parent, _Cell):
            parent_elm = parent._tc
        else:
            raise ValueError("parent must be a Document or _Cell instance")

        for child in parent_elm.iterchildren():
            if isinstance(child, CT_P):
                yield Paragraph(child, parent)
            elif isinstance(child, CT_Tbl):
                yield Table(child, parent)

    @staticmethod
    def _extract_variable_parts(left_text: str) -> Tuple[str, str]:
        """Extract (Variable Expression, Variable Name) from bracket notation.

        Looks for ``[variable_name]`` anywhere in *left_text*.

        Returns:
            A tuple ``(expression, variable_name)``; variable_name is empty
            string when no bracket pattern is found.
        """
        m = re.search(r"\[(.*?)\]", left_text)
        if m:
            var_name = m.group(1).strip()
            expr = left_text.replace(f"[{m.group(1)}]", "").strip()
            expr = re.sub(r"[\s:]+$", "", expr)
            return expr, var_name
        return left_text.strip(), ""

    @staticmethod
    def _infer_date_coding(expr: str, var_name: str, current_coding: str) -> str:
        """Infer date coding from expression or variable name, returning updated coding."""
        date_match = re.search(
            r"\(((?:YYYY|DD|MM)[^)]*)\)", expr, re.IGNORECASE
        )
        if date_match:
            return f"Date ({date_match.group(1).upper()})"
        if var_name.lower().endswith("_date") or var_name.lower().startswith("date_"):
            if not current_coding or current_coding.isspace():
                return "Date"
        return current_coding

    @staticmethod
    def _infer_variable_type(coding_text: str, var_name: str) -> str:
        """Infer variable type from coding description and variable name.

        Returns:
            One of ``'categorical'``, ``'numeric'``, ``'date'``, or ``'text'``.
        """
        coding_lower = (coding_text or "").lower()
        name_lower = var_name.lower()

        date_keywords = ["date", "yyyy", "mm/dd", "time", "datetime", "dob", "birth"]
        if any(kw in name_lower for kw in date_keywords):
            return "date"
        if any(kw in coding_lower for kw in date_keywords):
            return "date"

        numeric_keywords = [
            "number", "count", "age", "dose", "mg", "ml", "duration",
            "days", "months", "years", "weight", "height",
        ]
        if any(kw in name_lower for kw in numeric_keywords):
            return "numeric"
        if "number" in coding_lower or re.search(r"\d+[\-\.]\d+", coding_lower):
            return "numeric"
        if re.search(r"\(unit:", coding_lower):
            return "numeric"

        categorical_keywords = [
            "yes", "no", "unknown", "male", "female", "positive", "negative",
            "none", "mild", "moderate", "severe", "cr", "pr", "sd", "pd", "response",
        ]
        if any(kw in coding_lower for kw in categorical_keywords):
            return "categorical"

        return "text"

    @staticmethod
    def _infer_categorical_values(coding_text: str) -> List[str]:
        """Extract possible categorical values from a coding description."""
        if not coding_text:
            return []

        # Numbered categories: "1. None, 2. Mild, 3. Moderate"
        numbered_pattern = r"(\d+)[\.\)]\s*([A-Za-z\s]+?)(?=\d+[\.\)]|$)"
        matches = re.findall(numbered_pattern, coding_text)
        if matches:
            return [m[1].strip() for m in matches]

        # Yes/No style
        yes_no_pattern = r"\b(yes|no|unknown|positive|negative)\b"
        matches = re.findall(yes_no_pattern, coding_text.lower())
        if matches:
            return list(set(matches))

        return []

    @staticmethod
    def _generate_validation_rule(
        var_name: str, var_type: str, coding_text: str
    ) -> Dict[str, Any]:
        """Generate a validation rule dict for a variable.

        Args:
            var_name: Variable name string.
            var_type: One of ``'categorical'``, ``'numeric'``, ``'date'``, ``'text'``.
            coding_text: Raw coding / description text from the CRF.

        Returns:
            A dict describing the validation rule.
        """
        rule: Dict[str, Any] = {"variable": var_name, "type": var_type, "required": False}

        if var_type == "categorical":
            values = CRFParser._infer_categorical_values(coding_text)
            if values:
                rule["allowed_values"] = values

        elif var_type == "numeric":
            range_match = re.search(r"(\d+\.?\d*)\s*-\s*(\d+\.?\d*)", coding_text)
            if range_match:
                rule["min_value"] = float(range_match.group(1))
                rule["max_value"] = float(range_match.group(2))

            unit_match = re.search(r"\(unit:\s*([^)]+)\)", coding_text, re.IGNORECASE)
            if unit_match:
                rule["unit"] = unit_match.group(1).strip()

        elif var_type == "date":
            if "yyyy" in coding_text.lower():
                rule["format"] = "%Y-%m-%d"
            elif "mm/dd" in coding_text.lower():
                rule["format"] = "%m/%d/%Y"

        return rule
