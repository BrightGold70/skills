"""Unit tests for ConfigLoader."""

import json
import os
import tempfile

import pytest

from crf_pipeline.config.loader import ConfigLoader


class TestDeepMerge:
    """Test ConfigLoader.deep_merge."""

    def test_scalar_override(self):
        base = {"version": "1.0", "name": "base"}
        overlay = {"version": "2.0"}
        result = ConfigLoader.deep_merge(base, overlay)
        assert result["version"] == "2.0"
        assert result["name"] == "base"

    def test_nested_dict_merge(self):
        base = {"sections": {"demo": {"fields": [1, 2]}}}
        overlay = {"sections": {"lab": {"fields": [3]}}}
        result = ConfigLoader.deep_merge(base, overlay)
        assert "demo" in result["sections"]
        assert "lab" in result["sections"]

    def test_list_replace_not_append(self):
        base = {"required_fields": ["a", "b"]}
        overlay = {"required_fields": ["c"]}
        result = ConfigLoader.deep_merge(base, overlay)
        assert result["required_fields"] == ["c"]

    def test_deep_nested_merge(self):
        base = {"a": {"b": {"c": 1, "d": 2}}}
        overlay = {"a": {"b": {"c": 3}}}
        result = ConfigLoader.deep_merge(base, overlay)
        assert result["a"]["b"]["c"] == 3
        assert result["a"]["b"]["d"] == 2

    def test_empty_overlay(self):
        base = {"x": 1}
        result = ConfigLoader.deep_merge(base, {})
        assert result == {"x": 1}

    def test_empty_base(self):
        overlay = {"x": 1}
        result = ConfigLoader.deep_merge({}, overlay)
        assert result == {"x": 1}

    def test_original_not_mutated(self):
        base = {"a": {"b": 1}}
        overlay = {"a": {"c": 2}}
        _ = ConfigLoader.deep_merge(base, overlay)
        assert "c" not in base["a"]


class TestConfigLoaderLoad:
    """Test ConfigLoader.load with real config files."""

    def test_load_common_only(self, config_dir):
        loader = ConfigLoader(config_dir)
        config = loader.load("nonexistent_disease")
        assert "sections" in config
        assert "demographics" in config["sections"]

    def test_load_aml_overlay(self, config_dir):
        loader = ConfigLoader(config_dir)
        config = loader.load("aml")
        assert "sections" in config
        # AML overlay adds molecular_markers section
        assert "molecular_markers" in config["sections"]
        # Common sections preserved
        assert "demographics" in config["sections"]

    def test_load_cml_overlay(self, config_dir):
        loader = ConfigLoader(config_dir)
        config = loader.load("cml")
        assert "molecular_markers" in config["sections"]
        # CML-specific fields
        fields_vars = [
            f["variable"]
            for s in config["sections"].values()
            for f in s.get("fields", [])
        ]
        assert "bcr_abl_baseline" in fields_vars

    def test_load_mds_overlay(self, config_dir):
        loader = ConfigLoader(config_dir)
        config = loader.load("mds")
        fields_vars = [
            f["variable"]
            for s in config["sections"].values()
            for f in s.get("fields", [])
        ]
        assert "ipss_r" in fields_vars

    def test_load_hct_overlay(self, config_dir):
        loader = ConfigLoader(config_dir)
        config = loader.load("hct")
        fields_vars = [
            f["variable"]
            for s in config["sections"].values()
            for f in s.get("fields", [])
        ]
        assert "donor_type" in fields_vars
        assert "conditioning" in fields_vars

    def test_validation_rules_loaded(self, config_dir):
        loader = ConfigLoader(config_dir)
        config = loader.load("aml")
        assert "validation_rules" in config
        assert "range_checks" in config["validation_rules"]
        assert "consistency_rules" in config["validation_rules"]

    def test_spss_mapping_merged(self, config_dir):
        loader = ConfigLoader(config_dir)
        config = loader.load("aml")
        spss = config.get("spss_value_mapping", {})
        # Common mapping
        assert "gender" in spss
        # AML-specific mapping
        assert "FLT3ITD" in spss or "cr_achieved" in spss

    def test_study_overrides_highest_precedence(self, config_dir):
        loader = ConfigLoader(config_dir)
        overrides = {"version": "override_version"}
        config = loader.load("aml", study_overrides=overrides)
        assert config["version"] == "override_version"

    def test_missing_common_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = ConfigLoader(tmpdir)
            with pytest.raises(FileNotFoundError):
                loader.load("aml")


class TestGetFieldDefinitions:
    """Test ConfigLoader.get_field_definitions."""

    def test_returns_field_definitions(self, config_dir):
        loader = ConfigLoader(config_dir)
        fields = loader.get_field_definitions("aml")
        assert len(fields) > 0
        # All are FieldDefinition objects
        from crf_pipeline.models.field_definition import FieldDefinition
        assert all(isinstance(f, FieldDefinition) for f in fields)

    def test_field_has_section(self, config_dir):
        loader = ConfigLoader(config_dir)
        fields = loader.get_field_definitions("aml")
        # At least one field from demographics
        demo_fields = [f for f in fields if f.section == "demographics"]
        assert len(demo_fields) > 0

    def test_field_counts_per_disease(self, config_dir):
        """Verify documented field counts."""
        loader = ConfigLoader(config_dir)
        aml = loader.get_field_definitions("aml")
        cml = loader.get_field_definitions("cml")
        mds = loader.get_field_definitions("mds")
        hct = loader.get_field_definitions("hct")
        # AML: 44, CML: 49, MDS: 50, HCT: 58 (from PDCA status)
        assert len(aml) >= 40
        assert len(cml) >= 45
        assert len(mds) >= 45
        assert len(hct) >= 50
