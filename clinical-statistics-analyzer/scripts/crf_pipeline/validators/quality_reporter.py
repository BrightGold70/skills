"""Quality report generation with confidence breakdown."""

import logging
from collections import defaultdict
from typing import Dict, List, Tuple

from ..models.patient_record import PatientRecord
from ..models.validation_issue import ValidationResult, ValidationSeverity

logger = logging.getLogger(__name__)


class QualityReporter:
    """Generate markdown quality reports from validation results."""

    def generate_report(self, validation: ValidationResult,
                        records: List[PatientRecord]) -> str:
        """Generate a markdown quality report with confidence breakdown."""
        lines = [
            "# CRF Data Quality Report",
            "",
            "## Summary",
            "",
            f"- **Total records**: {validation.total_records}",
            f"- **Valid records**: {validation.valid_records}",
            f"- **Completeness**: {validation.completeness:.1f}%",
            f"- **Errors**: {validation.error_count}",
            f"- **Warnings**: {validation.warning_count}",
            "",
        ]

        # Overall confidence
        if records:
            confidences = [r.mean_confidence for r in records]
            avg_conf = sum(confidences) / len(confidences)
            low_conf_count = sum(
                len(r.get_low_confidence_fields()) for r in records
            )
            lines.extend([
                "## Extraction Confidence",
                "",
                f"- **Mean confidence**: {avg_conf:.2f}",
                f"- **Fields needing review**: {low_conf_count}",
                "",
            ])

            # Confidence by method
            method_stats = self._confidence_by_method(records)
            if method_stats:
                lines.extend(["### By Extraction Method", ""])
                lines.append(
                    "| Method | Fields | Mean Confidence | Low Confidence |"
                )
                lines.append(
                    "|--------|--------|----------------|----------------|"
                )
                for method, stats in sorted(method_stats.items()):
                    lines.append(
                        f"| {method} | {stats['count']} | "
                        f"{stats['mean']:.2f} | {stats['low']} |"
                    )
                lines.append("")

            # Confidence by section
            section_stats = self._confidence_by_section(records)
            if section_stats:
                lines.extend(["### By Section", ""])
                lines.append(
                    "| Section | Fields | Mean Confidence | Low Confidence |"
                )
                lines.append(
                    "|---------|--------|----------------|----------------|"
                )
                for section, stats in sorted(section_stats.items()):
                    lines.append(
                        f"| {section} | {stats['count']} | "
                        f"{stats['mean']:.2f} | {stats['low']} |"
                    )
                lines.append("")

            # Per-record confidence distribution
            lines.extend(self._confidence_distribution(records))

            # Fields needing review
            lines.extend(self._review_fields(records))

        # Issues by severity
        if validation.issues:
            lines.extend(["## Validation Issues", ""])

            errors = [
                i for i in validation.issues
                if i.severity == ValidationSeverity.ERROR
            ]
            warnings = [
                i for i in validation.issues
                if i.severity == ValidationSeverity.WARNING
            ]

            if errors:
                lines.extend(["### Errors", ""])
                for issue in errors:
                    lines.append(
                        f"- **{issue.record_id}** [{issue.rule_id or 'UNKNOWN'}] "
                        f"{issue.field}: {issue.message}"
                    )
                lines.append("")

            if warnings:
                lines.extend(["### Warnings", ""])
                for issue in warnings:
                    lines.append(
                        f"- **{issue.record_id}** [{issue.rule_id or 'UNKNOWN'}] "
                        f"{issue.field}: {issue.message}"
                    )
                lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _confidence_by_method(
        records: List[PatientRecord],
    ) -> Dict[str, Dict]:
        """Aggregate confidence statistics by extraction method."""
        method_data: Dict[str, List[float]] = defaultdict(list)

        for record in records:
            for er in record.results.values():
                method_data[er.method].append(er.confidence)

        stats = {}
        for method, confs in method_data.items():
            stats[method] = {
                "count": len(confs),
                "mean": sum(confs) / len(confs) if confs else 0.0,
                "low": sum(1 for c in confs if c < 0.5),
            }
        return stats

    @staticmethod
    def _confidence_by_section(
        records: List[PatientRecord],
    ) -> Dict[str, Dict]:
        """Aggregate confidence statistics by field section.

        Uses the variable name prefix or groups by known sections.
        """
        # Group by first component of variable name (heuristic for section)
        section_data: Dict[str, List[float]] = defaultdict(list)

        # Known variable-to-section mappings
        section_map = {
            "case_no": "demographics", "name": "demographics",
            "birth": "demographics", "age": "demographics",
            "gender": "demographics",
            "wbc1": "laboratory", "hb1": "laboratory",
            "plt1": "laboratory", "blast1": "laboratory",
            "perf1": "laboratory", "ECOG1": "laboratory",
            "alive": "outcomes", "date_death": "outcomes",
            "relapse": "outcomes", "relapse_date": "outcomes",
            "cause_death": "outcomes",
            "FLT3ITD": "molecular_markers", "FLT3TKD": "molecular_markers",
            "NPM1": "molecular_markers", "CEBPA": "molecular_markers",
            "IDH1": "molecular_markers", "IDH2": "molecular_markers",
            "cr_achieved": "response", "cr_date": "response",
            "mrd_status": "response",
        }

        for record in records:
            for var, er in record.results.items():
                section = section_map.get(var, "other")
                section_data[section].append(er.confidence)

        stats = {}
        for section, confs in section_data.items():
            if confs:
                stats[section] = {
                    "count": len(confs),
                    "mean": sum(confs) / len(confs),
                    "low": sum(1 for c in confs if c < 0.5),
                }
        return stats

    @staticmethod
    def _confidence_distribution(
        records: List[PatientRecord],
    ) -> List[str]:
        """Generate confidence distribution histogram."""
        if not records:
            return []

        # Collect all confidence values
        all_confs = []
        for record in records:
            for er in record.results.values():
                all_confs.append(er.confidence)

        if not all_confs:
            return []

        # Bucket into ranges
        buckets = {"0.0-0.2": 0, "0.2-0.4": 0, "0.4-0.6": 0,
                    "0.6-0.8": 0, "0.8-1.0": 0}
        for c in all_confs:
            if c < 0.2:
                buckets["0.0-0.2"] += 1
            elif c < 0.4:
                buckets["0.2-0.4"] += 1
            elif c < 0.6:
                buckets["0.4-0.6"] += 1
            elif c < 0.8:
                buckets["0.6-0.8"] += 1
            else:
                buckets["0.8-1.0"] += 1

        total = len(all_confs)
        lines = [
            "### Confidence Distribution",
            "",
            "| Range | Count | Percentage |",
            "|-------|-------|------------|",
        ]
        for range_label, count in buckets.items():
            pct = (count / total) * 100 if total else 0
            lines.append(f"| {range_label} | {count} | {pct:.1f}% |")
        lines.append("")

        return lines

    @staticmethod
    def _review_fields(records: List[PatientRecord]) -> List[str]:
        """List specific fields that need human review."""
        review_items: List[Tuple[str, str, float, str]] = []  # record_id, variable, conf, method

        for record in records:
            record_id = record.case_no or record.source_file
            for er in record.get_low_confidence_fields():
                review_items.append(
                    (record_id, er.variable, er.confidence, er.method)
                )

        if not review_items:
            return []

        # Cap at 50 items to keep report manageable
        lines = [
            "### Fields Needing Review",
            "",
            f"Total: {len(review_items)} fields below confidence threshold (0.5)",
            "",
        ]

        if len(review_items) > 50:
            lines.append(f"*Showing first 50 of {len(review_items)}*")
            lines.append("")

        lines.append("| Record | Variable | Confidence | Method |")
        lines.append("|--------|----------|------------|--------|")
        for record_id, var, conf, method in review_items[:50]:
            lines.append(f"| {record_id} | {var} | {conf:.2f} | {method} |")
        lines.append("")

        return lines
