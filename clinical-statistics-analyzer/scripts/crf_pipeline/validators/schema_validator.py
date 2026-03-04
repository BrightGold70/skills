"""Schema-based validation for CRF config files using JSON Schema."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    logger.warning("jsonschema not installed; SchemaValidator disabled")


class SchemaValidationError:
    """A single schema validation failure."""

    def __init__(self, path: str, message: str, schema_path: str = ""):
        self.path = path          # JSON path to invalid element
        self.message = message    # Human-readable error
        self.schema_path = schema_path  # Schema rule that was violated

    def __repr__(self) -> str:
        return f"SchemaValidationError({self.path}: {self.message})"


class SchemaValidator:
    """Validate CRF config files against JSON schemas in schemas/ directory.

    Validates:
      - Field config structure (common_fields.json, aml_fields.json, etc.)
      - Validation rules structure (validation_rules.json)
      - Cross-config consistency (variable name uniqueness, SPSS mapping coverage)
    """

    # Expected structure for disease field config files
    FIELD_CONFIG_SCHEMA = {
        "type": "object",
        "required": ["version", "sections"],
        "properties": {
            "version": {"type": "string"},
            "disease": {"type": "string"},
            "description": {"type": "string"},
            "sections": {
                "type": "object",
                "additionalProperties": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string"},
                        "fields": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["crf_field", "variable", "type"],
                                "properties": {
                                    "crf_field": {"type": "string"},
                                    "variable": {"type": "string",
                                                 "pattern": "^[a-zA-Z_][a-zA-Z0-9_]*$"},
                                    "type": {"type": "string",
                                             "enum": ["string", "numeric",
                                                      "categorical", "date",
                                                      "text", "datetime"]},
                                    "extraction_method": {
                                        "type": "string",
                                        "enum": ["regex", "template", "llm",
                                                 "ocr", "derived"]
                                    },
                                    "required": {"type": "boolean"},
                                    "sps_code": {"type": "boolean"},
                                    "patterns": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    },
                                    "values": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    },
                                },
                            },
                        },
                    },
                },
            },
            "spss_value_mapping": {
                "type": "object",
                "additionalProperties": {"type": "object"},
            },
            "required_fields": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
    }

    VALIDATION_RULES_SCHEMA = {
        "type": "object",
        "properties": {
            "version": {"type": "string"},
            "range_checks": {
                "type": "object",
                "additionalProperties": {
                    "type": "object",
                    "required": ["min", "max"],
                    "properties": {
                        "min": {"type": "number"},
                        "max": {"type": "number"},
                        "unit": {"type": "string"},
                    },
                },
            },
            "consistency_rules": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["id", "description", "severity"],
                    "properties": {
                        "id": {"type": "string"},
                        "description": {"type": "string"},
                        "condition": {"type": "string"},
                        "require": {"type": "string"},
                        "severity": {
                            "type": "string",
                            "enum": ["error", "warning", "info"],
                        },
                    },
                },
            },
            "disease_specific_rules": {
                "type": "object",
                "additionalProperties": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["id", "description", "severity"],
                    },
                },
            },
            "required_fields": {
                "type": "array",
                "items": {"type": "string"},
            },
            "categorical_values": {
                "type": "object",
                "additionalProperties": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
        },
    }

    def __init__(self, schemas_dir: Optional[str] = None):
        """Initialize with optional external schemas directory.

        Args:
            schemas_dir: Path to directory containing JSON Schema files.
                         If None, uses built-in schemas only.
        """
        self.schemas_dir = Path(schemas_dir) if schemas_dir else None
        self._external_schemas: Dict[str, Dict] = {}

        if self.schemas_dir and self.schemas_dir.exists():
            self._load_external_schemas()

    def _load_external_schemas(self) -> None:
        """Load JSON schema files from schemas/ directory."""
        for schema_file in self.schemas_dir.glob("*.json"):
            try:
                with open(schema_file, encoding="utf-8") as f:
                    self._external_schemas[schema_file.stem] = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Failed to load schema %s: %s", schema_file, e)

    def validate_field_config(self, config: Dict) -> List[SchemaValidationError]:
        """Validate a field config file (common_fields.json or disease overlay)."""
        errors = []

        # JSON Schema validation
        if HAS_JSONSCHEMA:
            errors.extend(self._validate_against_schema(
                config, self.FIELD_CONFIG_SCHEMA, "field_config"
            ))

        # Semantic checks
        errors.extend(self._check_variable_uniqueness(config))
        errors.extend(self._check_spss_coverage(config))
        errors.extend(self._check_required_fields_exist(config))
        errors.extend(self._check_regex_patterns(config))

        return errors

    def validate_validation_rules(self, rules: Dict) -> List[SchemaValidationError]:
        """Validate the validation_rules.json structure."""
        errors = []

        if HAS_JSONSCHEMA:
            errors.extend(self._validate_against_schema(
                rules, self.VALIDATION_RULES_SCHEMA, "validation_rules"
            ))

        # Check range_checks have valid min < max
        for field, spec in rules.get("range_checks", {}).items():
            if spec.get("min", 0) > spec.get("max", 0):
                errors.append(SchemaValidationError(
                    path=f"range_checks.{field}",
                    message=f"min ({spec['min']}) > max ({spec['max']})",
                ))

        # Check consistency rule IDs are unique
        rule_ids = []
        for rule in rules.get("consistency_rules", []):
            rid = rule.get("id", "")
            if rid in rule_ids:
                errors.append(SchemaValidationError(
                    path=f"consistency_rules.{rid}",
                    message=f"Duplicate rule ID: {rid}",
                ))
            rule_ids.append(rid)

        for disease, d_rules in rules.get("disease_specific_rules", {}).items():
            for rule in d_rules:
                rid = rule.get("id", "")
                if rid in rule_ids:
                    errors.append(SchemaValidationError(
                        path=f"disease_specific_rules.{disease}.{rid}",
                        message=f"Duplicate rule ID: {rid}",
                    ))
                rule_ids.append(rid)

        return errors

    def validate_merged_config(self, config: Dict,
                               disease: str) -> List[SchemaValidationError]:
        """Validate a fully merged config (common + disease overlay)."""
        errors = self.validate_field_config(config)

        # Check disease-specific required fields are defined
        if "required_fields" in config:
            all_vars = set()
            for section_data in config.get("sections", {}).values():
                for f in section_data.get("fields", []):
                    all_vars.add(f.get("variable"))

            for rf in config["required_fields"]:
                if rf not in all_vars:
                    errors.append(SchemaValidationError(
                        path=f"required_fields",
                        message=f"Required field '{rf}' not found in sections",
                    ))

        return errors

    @staticmethod
    def _validate_against_schema(
        data: Dict, schema: Dict, context: str
    ) -> List[SchemaValidationError]:
        """Run jsonschema validation and collect errors."""
        if not HAS_JSONSCHEMA:
            return []

        errors = []
        validator = jsonschema.Draft7Validator(schema)
        for error in validator.iter_errors(data):
            path = ".".join(str(p) for p in error.absolute_path)
            errors.append(SchemaValidationError(
                path=path or context,
                message=error.message,
                schema_path=".".join(str(p) for p in error.absolute_schema_path),
            ))
        return errors

    @staticmethod
    def _check_variable_uniqueness(config: Dict) -> List[SchemaValidationError]:
        """Check that variable names are unique across all sections."""
        errors = []
        seen: Dict[str, str] = {}  # variable -> section

        for section_name, section_data in config.get("sections", {}).items():
            for field_data in section_data.get("fields", []):
                var = field_data.get("variable")
                if var in seen:
                    errors.append(SchemaValidationError(
                        path=f"sections.{section_name}.{var}",
                        message=(
                            f"Duplicate variable '{var}' "
                            f"(also in '{seen[var]}')"
                        ),
                    ))
                else:
                    seen[var] = section_name

        return errors

    @staticmethod
    def _check_spss_coverage(config: Dict) -> List[SchemaValidationError]:
        """Check that sps_code=true fields have SPSS mappings."""
        errors = []
        spss_mapping = config.get("spss_value_mapping", {})

        for section_name, section_data in config.get("sections", {}).items():
            for field_data in section_data.get("fields", []):
                if field_data.get("sps_code") and field_data["variable"] not in spss_mapping:
                    errors.append(SchemaValidationError(
                        path=f"sections.{section_name}.{field_data['variable']}",
                        message=(
                            f"Field '{field_data['variable']}' has sps_code=true "
                            f"but no spss_value_mapping entry"
                        ),
                    ))

        return errors

    @staticmethod
    def _check_required_fields_exist(config: Dict) -> List[SchemaValidationError]:
        """Verify required_fields list references actual variables."""
        errors = []
        all_vars = set()
        for section_data in config.get("sections", {}).values():
            for f in section_data.get("fields", []):
                all_vars.add(f.get("variable"))

        for rf in config.get("required_fields", []):
            if rf not in all_vars:
                errors.append(SchemaValidationError(
                    path="required_fields",
                    message=f"Required field '{rf}' not defined in any section",
                ))

        return errors

    @staticmethod
    def _check_regex_patterns(config: Dict) -> List[SchemaValidationError]:
        """Validate that regex patterns in field configs are compilable."""
        import re

        errors = []
        for section_name, section_data in config.get("sections", {}).items():
            for field_data in section_data.get("fields", []):
                for i, pattern in enumerate(field_data.get("patterns", [])):
                    try:
                        re.compile(pattern)
                    except re.error as e:
                        errors.append(SchemaValidationError(
                            path=f"sections.{section_name}.{field_data['variable']}.patterns[{i}]",
                            message=f"Invalid regex: {e}",
                        ))

        return errors
