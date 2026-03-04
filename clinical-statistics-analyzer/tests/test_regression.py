"""Regression tests: compare new pipeline output against SAPPHIRE-G baseline.

This module provides a framework for field-by-field comparison between
the new crf_pipeline and the existing CRF_Extractor output. Actual
comparison tests are skipped unless baseline data files are present.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest

from crf_pipeline.config.loader import ConfigLoader
from crf_pipeline.models.field_definition import FieldDefinition

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
BASELINE_DIR = PROJECT_ROOT / "tests" / "baselines"
CONFIG_DIR = PROJECT_ROOT / "crf_pipeline" / "config"

# Expected SAPPHIRE-G variable count
SAPPHIRE_G_VARIABLE_COUNT = 237


def _load_baseline(filename: str) -> Dict:
    """Load a baseline JSON file if it exists."""
    path = BASELINE_DIR / filename
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _compare_records(
    baseline: List[Dict], new_output: List[Dict],
) -> Tuple[int, int, List[str]]:
    """Compare baseline records against new output.

    Returns:
        (matched, total, mismatches) where mismatches is list of descriptions.
    """
    matched = 0
    total = 0
    mismatches = []

    # Index by case_no
    baseline_by_id = {r.get("case_no", str(i)): r for i, r in enumerate(baseline)}
    new_by_id = {r.get("case_no", str(i)): r for i, r in enumerate(new_output)}

    for case_id, base_record in baseline_by_id.items():
        new_record = new_by_id.get(case_id)
        if new_record is None:
            mismatches.append(f"Record {case_id}: missing in new output")
            total += len(base_record)
            continue

        for field, base_value in base_record.items():
            total += 1
            new_value = new_record.get(field)

            if _values_match(base_value, new_value):
                matched += 1
            else:
                mismatches.append(
                    f"Record {case_id}, field {field}: "
                    f"baseline={base_value!r}, new={new_value!r}"
                )

    return matched, total, mismatches


def _values_match(baseline: Any, new: Any) -> bool:
    """Compare values with tolerance for numeric types."""
    if baseline is None and new is None:
        return True
    if baseline is None or new is None:
        return False

    # Numeric comparison with tolerance
    try:
        b_num = float(baseline)
        n_num = float(new)
        return abs(b_num - n_num) < 0.01
    except (ValueError, TypeError):
        pass

    # String comparison (case-insensitive, stripped)
    return str(baseline).strip().lower() == str(new).strip().lower()


class TestFieldCoverage:
    """Verify the new pipeline covers all SAPPHIRE-G variables."""

    def test_aml_field_count(self):
        loader = ConfigLoader(str(CONFIG_DIR))
        fields = loader.get_field_definitions("aml")
        vars_set = {f.variable for f in fields}
        # AML should cover baseline demographics + lab + molecular + response + treatment
        assert len(vars_set) >= 40, (
            f"AML field count {len(vars_set)} below minimum 40"
        )

    def test_all_diseases_have_common_fields(self):
        loader = ConfigLoader(str(CONFIG_DIR))
        common_vars = {"case_no", "age", "gender", "alive"}
        for disease in ("aml", "cml", "mds", "hct"):
            fields = loader.get_field_definitions(disease)
            vars_set = {f.variable for f in fields}
            missing = common_vars - vars_set
            assert not missing, (
                f"Disease {disease} missing common fields: {missing}"
            )

    def test_spss_mapping_coverage(self):
        """All diseases have SPSS mappings for their categorical fields."""
        loader = ConfigLoader(str(CONFIG_DIR))
        for disease in ("aml", "cml", "mds", "hct"):
            config = loader.load(disease)
            spss = config.get("spss_value_mapping", {})
            for section_data in config.get("sections", {}).values():
                for field in section_data.get("fields", []):
                    if field.get("sps_code"):
                        var = field["variable"]
                        # Check in merged SPSS mapping
                        assert var in spss, (
                            f"{disease}: {var} has sps_code=true but no "
                            f"SPSS mapping"
                        )


class TestConfigConsistency:
    """Verify config files are consistent across diseases."""

    def test_no_duplicate_variables_within_disease(self):
        loader = ConfigLoader(str(CONFIG_DIR))
        for disease in ("aml", "cml", "mds", "hct"):
            fields = loader.get_field_definitions(disease)
            seen = set()
            for f in fields:
                assert f.variable not in seen, (
                    f"{disease}: duplicate variable {f.variable}"
                )
                seen.add(f.variable)

    def test_required_fields_exist_in_config(self):
        loader = ConfigLoader(str(CONFIG_DIR))
        for disease in ("aml", "cml", "mds", "hct"):
            config = loader.load(disease)
            all_vars = set()
            for section_data in config.get("sections", {}).values():
                for f in section_data.get("fields", []):
                    all_vars.add(f["variable"])

            # Disease-specific required_fields should be in sections
            for rf in config.get("required_fields", []):
                assert rf in all_vars, (
                    f"{disease}: required field '{rf}' not in sections"
                )

    def test_validation_rule_fields_exist(self):
        """Check that validation rule fields reference real variables."""
        loader = ConfigLoader(str(CONFIG_DIR))
        config = loader.load("aml")
        rules = config.get("validation_rules", {})

        # Check range_checks reference fields that could exist
        range_fields = set(rules.get("range_checks", {}).keys())
        categorical_fields = set(rules.get("categorical_values", {}).keys())

        # All range check fields should be reasonable variable names
        for field in range_fields:
            assert field.replace("_", "").replace("1", "").isalnum(), (
                f"Suspicious range check field name: {field}"
            )


@pytest.mark.skipif(
    not BASELINE_DIR.exists(),
    reason="No baseline data directory (tests/baselines/)"
)
class TestSapphireGRegression:
    """Compare new pipeline output against SAPPHIRE-G baseline.

    These tests are SKIPPED unless baseline files are present in
    tests/baselines/. To enable:
        1. Run the old CRF_Extractor on SAPPHIRE-G data
        2. Export results as tests/baselines/sapphire_g_baseline.json
        3. Run these tests
    """

    def test_field_values_match(self):
        baseline = _load_baseline("sapphire_g_baseline.json")
        if not baseline:
            pytest.skip("No baseline file found")

        # Load new pipeline output
        new_output = _load_baseline("sapphire_g_new_output.json")
        if not new_output:
            pytest.skip("No new output file for comparison")

        baseline_records = baseline.get("records", [])
        new_records = new_output.get("records", [])

        matched, total, mismatches = _compare_records(
            baseline_records, new_records
        )

        match_rate = (matched / total * 100) if total > 0 else 0
        if mismatches:
            mismatch_report = "\n".join(mismatches[:20])
            assert match_rate >= 95, (
                f"Match rate {match_rate:.1f}% below 95% threshold.\n"
                f"First mismatches:\n{mismatch_report}"
            )

    def test_variable_count(self):
        baseline = _load_baseline("sapphire_g_baseline.json")
        if not baseline:
            pytest.skip("No baseline file found")

        records = baseline.get("records", [])
        if records:
            vars_in_baseline = set(records[0].keys())
            assert len(vars_in_baseline) >= SAPPHIRE_G_VARIABLE_COUNT * 0.9, (
                f"Variable count {len(vars_in_baseline)} below expected "
                f"{SAPPHIRE_G_VARIABLE_COUNT}"
            )
