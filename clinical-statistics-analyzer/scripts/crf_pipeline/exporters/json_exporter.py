"""JSON exporter with full ExtractionResult metadata."""

import json
import logging
from typing import List

from ..models.patient_record import PatientRecord
from .base import ExporterBase

logger = logging.getLogger(__name__)


class JsonExporter(ExporterBase):
    """Export with full ExtractionResult metadata (confidence, method, source)."""

    def export(self, records: List[PatientRecord],
               output_path: str, include_confidence: bool = True,
               **kwargs) -> str:
        if not records:
            logger.warning("No records to export")
            return output_path

        data = []
        for record in records:
            entry = {
                "case_no": record.case_no,
                "hospital": record.hospital,
                "disease": record.disease,
                "source_file": record.source_file,
                "mean_confidence": round(record.mean_confidence, 3),
                "fields": {},
            }

            for var, result in record.results.items():
                field_data = {"value": result.value}
                if include_confidence:
                    field_data.update({
                        "confidence": round(result.confidence, 3),
                        "method": result.method,
                        "needs_review": result.needs_review,
                    })
                    if result.error:
                        field_data["error"] = result.error
                entry["fields"][var] = field_data

            data.append(entry)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

        logger.info("Exported %d records to %s", len(records), output_path)
        return output_path
