"""PatientRecord dataclass for per-patient extraction results."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .extraction_result import ExtractionResult


@dataclass
class PatientRecord:
    """Collection of ExtractionResults for a single patient CRF."""

    case_no: Optional[str]
    hospital: str
    source_file: str
    disease: str               # "aml" | "cml" | "mds" | "hct"
    results: Dict[str, ExtractionResult] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_flat_dict(self) -> Dict[str, Any]:
        """Convert to flat dict for export (variable -> value)."""
        return {var: r.value for var, r in self.results.items()}

    def get_low_confidence_fields(
        self, threshold: float = 0.5
    ) -> List[ExtractionResult]:
        """Return fields needing human review."""
        return [r for r in self.results.values() if r.confidence < threshold]

    @property
    def mean_confidence(self) -> float:
        """Average confidence across all extracted fields."""
        if not self.results:
            return 0.0
        return sum(r.confidence for r in self.results.values()) / len(self.results)
