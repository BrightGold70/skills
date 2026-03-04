"""FieldDefinition dataclass for CRF field configuration."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class FieldDefinition:
    """Single CRF field definition loaded from config."""

    variable: str              # SPSS variable name (e.g., "FLT3ITD")
    crf_field: str             # Human label (e.g., "FLT3 ITD")
    field_type: str            # "string" | "numeric" | "categorical" | "date" | "text"
    extraction_method: str     # "regex" | "template" | "llm" | "ocr" | "derived"
    section: str               # Section name (e.g., "clinical_data_diagnosis")
    required: bool = False
    sps_code: bool = False     # Whether to map to SPSS numeric code
    patterns: List[str] = field(default_factory=list)
    values: List[str] = field(default_factory=list)  # Allowed categorical values
    disease: Optional[str] = None  # None = common, "aml" | "cml" | "mds" | "hct"

    @classmethod
    def from_dict(cls, data: dict, section: str,
                  disease: Optional[str] = None) -> "FieldDefinition":
        """Create FieldDefinition from a config dict entry."""
        return cls(
            variable=data["variable"],
            crf_field=data["crf_field"],
            field_type=data.get("type", "string"),
            extraction_method=data.get("extraction_method", "regex"),
            section=section,
            required=data.get("required", False),
            sps_code=data.get("sps_code", False),
            patterns=data.get("patterns", []),
            values=data.get("values", []),
            disease=disease,
        )
