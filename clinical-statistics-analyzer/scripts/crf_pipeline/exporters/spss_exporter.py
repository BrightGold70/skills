"""SPSS exporter with variable/value labels and code mapping."""

import logging
from typing import Dict, List, Optional

from ..models.field_definition import FieldDefinition
from ..models.patient_record import PatientRecord
from .base import ExporterBase

logger = logging.getLogger(__name__)


class SpssExporter(ExporterBase):
    """Export to .sav with variable labels, value labels, and code mapping."""

    def __init__(self, field_definitions: List[FieldDefinition],
                 spss_mapping: Dict):
        self.field_definitions = field_definitions
        self.spss_mapping = spss_mapping

    def export(self, records: List[PatientRecord],
               output_path: str,
               variable_labels: Optional[Dict] = None,
               value_labels: Optional[Dict] = None,
               **kwargs) -> str:
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas required for SPSS export")
        try:
            import pyreadstat
        except ImportError:
            raise ImportError("pyreadstat required for SPSS export")

        if not records:
            logger.warning("No records to export")
            return output_path

        # Build column order from field definitions
        col_order = ["case_no", "hospital", "disease"]
        col_order.extend(fd.variable for fd in self.field_definitions)

        rows = []
        for record in records:
            row = {
                "case_no": record.case_no,
                "hospital": record.hospital,
                "disease": record.disease,
            }
            flat = record.to_flat_dict()

            for fd in self.field_definitions:
                value = flat.get(fd.variable)
                # Apply SPSS code mapping
                if fd.sps_code and fd.variable in self.spss_mapping:
                    mapping = self.spss_mapping[fd.variable]
                    if value is not None and str(value) in mapping:
                        mapped = mapping[str(value)]
                        if isinstance(mapped, (int, float)):
                            value = mapped
                row[fd.variable] = value

            rows.append(row)

        df = pd.DataFrame(rows)

        # Reorder columns
        existing_cols = [c for c in col_order if c in df.columns]
        extra_cols = [c for c in df.columns if c not in existing_cols]
        df = df[existing_cols + extra_cols]

        # Generate labels
        if variable_labels is None:
            variable_labels = self._generate_variable_labels()
        if value_labels is None:
            value_labels = self._generate_value_labels()

        pyreadstat.write_sav(
            df, output_path,
            column_labels=variable_labels,
            variable_value_labels=value_labels,
        )
        logger.info("Exported %d records to %s", len(records), output_path)
        return output_path

    def _generate_variable_labels(self) -> Dict[str, str]:
        """Generate variable labels from field definitions."""
        labels = {
            "case_no": "Case Number",
            "hospital": "Hospital",
            "disease": "Disease Type",
        }
        for fd in self.field_definitions:
            labels[fd.variable] = fd.crf_field
        return labels

    def _generate_value_labels(self) -> Dict[str, Dict]:
        """Generate value labels from SPSS mapping."""
        labels = {}
        for variable, mapping in self.spss_mapping.items():
            val_label = {}
            for key, value in mapping.items():
                try:
                    code = int(key)
                    val_label[code] = str(value)
                except (ValueError, TypeError):
                    pass
            if val_label:
                labels[variable] = val_label
        return labels
