"""Shared test fixtures for CRF pipeline tests."""

import json
import os
import tempfile
from pathlib import Path
from typing import Dict

import pytest

# Project root and config directory
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "crf_pipeline" / "config"
SCHEMAS_DIR = PROJECT_ROOT / "schemas"


@pytest.fixture
def config_dir():
    """Path to the real config directory."""
    return str(CONFIG_DIR)


@pytest.fixture
def schemas_dir():
    """Path to the real schemas directory."""
    return str(SCHEMAS_DIR)


@pytest.fixture
def common_config() -> Dict:
    """Load common_fields.json as dict."""
    with open(CONFIG_DIR / "common_fields.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def aml_config() -> Dict:
    """Load aml_fields.json as dict."""
    with open(CONFIG_DIR / "aml_fields.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def validation_rules() -> Dict:
    """Load validation_rules.json as dict."""
    with open(CONFIG_DIR / "validation_rules.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def temp_config_dir(common_config, aml_config, validation_rules):
    """Create a temporary config directory with test configs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "common_fields.json"), "w") as f:
            json.dump(common_config, f)
        with open(os.path.join(tmpdir, "aml_fields.json"), "w") as f:
            json.dump(aml_config, f)
        with open(os.path.join(tmpdir, "validation_rules.json"), "w") as f:
            json.dump(validation_rules, f)
        yield tmpdir


@pytest.fixture
def sample_document_text():
    """Sample CRF document text for extraction testing."""
    return """
    Case Number: SAPH-001
    Name: K.H.
    Birthday: 1960-05-15
    Age: 65 years
    Gender: Male
    Hospital: Seoul National University Hospital

    Diagnosis: AML
    Date of Diagnosis: 2025-01-15

    WBC: 45.2 x10^9/L
    Hemoglobin: 8.5 g/dL
    Platelet: 45 x10^9/L
    Bone marrow blast: 75%

    Karnofsky: 80
    ECOG: 1

    FLT3 ITD: Positive
    NPM1: Negative
    CEBPA: Negative

    Induction chemotherapy: 7+3 (Cytarabine + Daunorubicin)
    Induction date: 2025-01-20

    CR achieved: Yes
    CR date: 2025-02-28

    Survival status: Alive
    Date of last follow-up: 2025-12-01

    Relapse: No
    HCT performed: Yes
    HCT date: 2025-05-10
    """


@pytest.fixture
def sample_patient_data():
    """Pre-extracted patient data dict for validator testing."""
    return {
        "case_no": "SAPH-001",
        "age": "65",
        "gender": "Male",
        "alive": "Alive",
        "wbc1": "45.2",
        "hb1": "8.5",
        "plt1": "45",
        "blast1": "75",
        "perf1": "80",
        "ECOG1": "1",
        "cr_achieved": "Yes",
        "cr_date": "2025-02-28",
        "date_death": None,
        "reg_date": "2025-01-15",
        "induction_date": "2025-01-20",
        "hct_date": "2025-05-10",
        "relapse_date": None,
        "FLT3ITD": "Positive",
        "NPM1": "Negative",
    }
