"""Main CRF pipeline orchestrator."""

import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from .config.loader import ConfigLoader
from .exporters.csv_exporter import CsvExporter
from .exporters.excel_exporter import ExcelExporter
from .exporters.json_exporter import JsonExporter
from .exporters.spss_exporter import SpssExporter
from .extractors.extraction_chain import ExtractionChain
from .extractors.llm_extractor import LLMExtractor
from .extractors.ocr_postprocessor import OCRPostprocessor
from .extractors.regex_extractor import RegexExtractor
from .extractors.template_extractor import TemplateExtractor
from .models.patient_record import PatientRecord
from .processors.docx_processor import DocxProcessor
from .processors.pdf_processor import PDFProcessor
from .validators.quality_reporter import QualityReporter
from .validators.rule_validator import RuleValidator

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Output from a complete pipeline run."""

    status: str = "success"            # "success" | "partial" | "error"
    records_processed: int = 0         # Documents found
    records_extracted: int = 0         # Successfully extracted
    elapsed_time: float = 0.0          # Seconds
    mean_confidence: float = 0.0       # Average across all fields
    low_confidence_count: int = 0      # Fields needing review
    outputs: Dict[str, str] = field(default_factory=dict)
    validation: Optional[Dict] = None
    errors: List[str] = field(default_factory=list)


class CRFPipeline:
    """Main pipeline orchestrator (replaces CRF_Extractor/main.py)."""

    def __init__(self, config_dir: str,
                 disease: str,
                 output_dir: str,
                 use_llm: bool = False,
                 anthropic_api_key: Optional[str] = None,
                 study_overrides: Optional[Dict] = None):
        self.config_dir = config_dir
        self.disease = disease
        self.output_dir = output_dir
        self.use_llm = use_llm
        self.anthropic_api_key = anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.study_overrides = study_overrides

        # Load config
        self.config_loader = ConfigLoader(config_dir)
        self.config = self.config_loader.load(disease, study_overrides)
        self.field_definitions = self.config_loader.get_field_definitions(
            disease, study_overrides
        )

        # Build processors
        self.processors = [PDFProcessor(), DocxProcessor()]

        # Build extraction chain
        spss_mapping = self.config.get("spss_value_mapping", {})
        extractors = [
            RegexExtractor(spss_mapping=spss_mapping),
            TemplateExtractor(spss_mapping=spss_mapping),
        ]
        if use_llm:
            extractors.append(LLMExtractor(api_key=self.anthropic_api_key))

        ocr_rules = self.config.get("ocr_cleanup_rules", {})
        llm_ext = extractors[-1] if use_llm and extractors else None
        ocr_post = OCRPostprocessor(
            ocr_rules,
            use_llm=use_llm,
            llm_client=llm_ext.client if isinstance(llm_ext, LLMExtractor) else None,
        ) if ocr_rules else None

        self.extraction_chain = ExtractionChain(
            extractors=extractors,
            ocr_postprocessor=ocr_post,
        )

        # Build validator
        validation_rules = self.config.get("validation_rules", {})
        self.validator = RuleValidator(validation_rules, disease=disease)
        self.quality_reporter = QualityReporter()

        # Build exporters
        self.exporters = {
            "csv": CsvExporter(),
            "excel": ExcelExporter(),
            "json": JsonExporter(),
            "spss": SpssExporter(
                field_definitions=self.field_definitions,
                spss_mapping=spss_mapping,
            ),
        }

    def run(self, input_dir: str,
            skip_validation: bool = False) -> PipelineResult:
        """Execute full extraction pipeline."""
        start_time = time.time()
        result = PipelineResult()
        out_path = Path(self.output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        # 1. Process documents
        logger.info("Processing documents from %s", input_dir)
        doc_results = []
        for processor in self.processors:
            try:
                doc_results.extend(processor.process_directory(input_dir))
            except Exception as e:
                logger.error("Processor error: %s", e)
                result.errors.append(str(e))

        result.records_processed = len(doc_results)
        if not doc_results:
            result.status = "error"
            result.errors.append("No documents found")
            result.elapsed_time = time.time() - start_time
            return result

        # 2. Extract fields
        logger.info("Extracting fields from %d documents", len(doc_results))
        records = []
        for doc in doc_results:
            if doc.error:
                result.errors.append(f"{doc.file_name}: {doc.error}")
                continue

            try:
                extraction_results = self.extraction_chain.extract_all(
                    self.field_definitions, doc
                )
                record = PatientRecord(
                    case_no=None,
                    hospital=doc.hospital,
                    source_file=doc.file_path,
                    disease=self.disease,
                )
                for er in extraction_results:
                    record.results[er.variable] = er
                    if er.variable == "case_no" and er.value:
                        record.case_no = str(er.value)

                records.append(record)
            except Exception as e:
                logger.error("Extraction error for %s: %s", doc.file_name, e)
                result.errors.append(f"{doc.file_name}: {e}")

        result.records_extracted = len(records)

        # 3. Validate
        if not skip_validation and records:
            logger.info("Validating %d records", len(records))
            validation_result = self.validator.validate_dataset(records)
            result.validation = {
                "total": validation_result.total_records,
                "valid": validation_result.valid_records,
                "errors": validation_result.error_count,
                "warnings": validation_result.warning_count,
                "completeness": validation_result.completeness,
            }

            # Quality report
            report = self.quality_reporter.generate_report(
                validation_result, records
            )
            report_path = out_path / "quality_report.md"
            report_path.write_text(report, encoding="utf-8")
            result.outputs["quality_report"] = str(report_path)

        # 4. Export
        if records:
            logger.info("Exporting %d records", len(records))
            data_dir = out_path / "data"
            data_dir.mkdir(exist_ok=True)

            for fmt, exporter in self.exporters.items():
                try:
                    ext_map = {
                        "csv": ".csv", "excel": ".xlsx",
                        "json": ".json", "spss": ".sav",
                    }
                    export_path = str(
                        data_dir / f"crf_data_{self.disease}{ext_map[fmt]}"
                    )
                    exporter.export(records, export_path)
                    result.outputs[fmt] = export_path
                except Exception as e:
                    logger.error("Export error (%s): %s", fmt, e)
                    result.errors.append(f"Export {fmt}: {e}")

        # 5. Statistics
        if records:
            confidences = [r.mean_confidence for r in records]
            result.mean_confidence = (sum(confidences) / len(confidences)) if confidences else 0.0
            result.low_confidence_count = sum(
                len(r.get_low_confidence_fields()) for r in records
            )

        result.elapsed_time = time.time() - start_time
        result.status = (
            "success" if not result.errors
            else "partial" if records
            else "error"
        )

        logger.info(
            "Pipeline complete: %d/%d records, %.1fs, confidence=%.2f",
            result.records_extracted, result.records_processed,
            result.elapsed_time, result.mean_confidence,
        )

        return result
