"""CSV exporter for extracted CRF data."""

import csv
import logging
from typing import List

from ..models.patient_record import PatientRecord
from .base import ExporterBase

logger = logging.getLogger(__name__)


class CsvExporter(ExporterBase):
    """Export patient records to CSV format."""

    def export(self, records: List[PatientRecord],
               output_path: str, encoding: str = "utf-8", **kwargs) -> str:
        if not records:
            logger.warning("No records to export")
            return output_path

        # Collect all variable names across records
        all_vars = []
        seen = set()
        for record in records:
            for var in record.results:
                if var not in seen:
                    all_vars.append(var)
                    seen.add(var)

        header = ["case_no", "hospital", "disease"] + all_vars

        with open(output_path, "w", newline="", encoding=encoding) as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for record in records:
                flat = record.to_flat_dict()
                row = [record.case_no, record.hospital, record.disease]
                row.extend(flat.get(var) for var in all_vars)
                writer.writerow(row)

        logger.info("Exported %d records to %s", len(records), output_path)
        return output_path
