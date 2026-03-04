"""Excel exporter for extracted CRF data."""

import logging
from typing import List

from ..models.patient_record import PatientRecord
from .base import ExporterBase

logger = logging.getLogger(__name__)


class ExcelExporter(ExporterBase):
    """Export patient records to Excel format."""

    def export(self, records: List[PatientRecord],
               output_path: str, **kwargs) -> str:
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas required for Excel export")

        if not records:
            logger.warning("No records to export")
            return output_path

        rows = []
        for record in records:
            row = {
                "case_no": record.case_no,
                "hospital": record.hospital,
                "disease": record.disease,
            }
            row.update(record.to_flat_dict())
            rows.append(row)

        df = pd.DataFrame(rows)
        df.to_excel(output_path, index=False, engine="openpyxl")
        logger.info("Exported %d records to %s", len(records), output_path)
        return output_path
