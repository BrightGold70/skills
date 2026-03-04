"""Layered configuration loader with deep merge support."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..models.field_definition import FieldDefinition

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Layered configuration loader with deep merge support.

    Resolution order (later overrides earlier):
        1. common_fields.json
        2. {disease}_fields.json
        3. study_overrides (if provided)
    """

    def __init__(self, config_dir: str):
        self.config_dir = Path(config_dir)
        self._cache: Dict[str, Dict] = {}

    def load(self, disease: str,
             study_overrides: Optional[Dict] = None) -> Dict:
        """Load merged configuration for a specific disease.

        Args:
            disease: One of "aml", "cml", "mds", "hct"
            study_overrides: Optional dict of per-study field overrides

        Returns:
            Merged config dict with sections, spss_value_mapping,
            ocr_cleanup_rules, validation_rules, required_fields.
        """
        cache_key = disease if study_overrides is None else None
        if cache_key and cache_key in self._cache:
            return self._cache[cache_key]

        common_path = self.config_dir / "common_fields.json"
        disease_path = self.config_dir / f"{disease}_fields.json"

        if not common_path.exists():
            raise FileNotFoundError(f"Common config not found: {common_path}")

        with open(common_path, encoding="utf-8") as f:
            config = json.load(f)

        if disease_path.exists():
            with open(disease_path, encoding="utf-8") as f:
                overlay = json.load(f)
            config = self.deep_merge(config, overlay)
            logger.info("Loaded disease overlay: %s", disease_path.name)
        else:
            logger.warning("No disease config for '%s', using common only", disease)

        if study_overrides:
            config = self.deep_merge(config, study_overrides)
            logger.info("Applied study overrides")

        # Load validation rules (shared)
        rules_path = self.config_dir / "validation_rules.json"
        if rules_path.exists():
            with open(rules_path, encoding="utf-8") as f:
                config["validation_rules"] = json.load(f)

        # Load OCR cleanup rules if separate file exists
        ocr_path = self.config_dir / "ocr_cleanup_rules.json"
        if ocr_path.exists():
            with open(ocr_path, encoding="utf-8") as f:
                config["ocr_cleanup_rules"] = json.load(f)

        if cache_key:
            self._cache[cache_key] = config

        return config

    def get_field_definitions(self, disease: str,
                              study_overrides: Optional[Dict] = None
                              ) -> List[FieldDefinition]:
        """Return flat list of all FieldDefinition objects for a disease."""
        config = self.load(disease, study_overrides)
        fields = []
        disease_tag = config.get("disease")

        for section_name, section_data in config.get("sections", {}).items():
            for field_data in section_data.get("fields", []):
                fields.append(
                    FieldDefinition.from_dict(
                        field_data, section=section_name, disease=disease_tag
                    )
                )
        return fields

    def load_analysis_profiles(self) -> Dict:
        """Load analysis_profiles.json for R script routing."""
        profiles_path = self.config_dir / "analysis_profiles.json"
        if not profiles_path.exists():
            logger.warning("No analysis_profiles.json found")
            return {}
        with open(profiles_path, encoding="utf-8") as f:
            return json.load(f)

    def get_validation_rules(self) -> Dict:
        """Load validation_rules.json (shared across diseases)."""
        rules_path = self.config_dir / "validation_rules.json"
        if not rules_path.exists():
            logger.warning("No validation_rules.json found")
            return {}
        with open(rules_path, encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def deep_merge(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge overlay into base.

        - Dict values: recursive merge
        - List values: overlay replaces base (not appended)
        - Scalar values: overlay replaces base
        """
        result = base.copy()
        for key, value in overlay.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = ConfigLoader.deep_merge(result[key], value)
            else:
                result[key] = value
        return result
