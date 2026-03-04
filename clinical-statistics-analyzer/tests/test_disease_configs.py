#!/usr/bin/env python3
"""Test CML/MDS/HCT disease config loading, mock data generation, and pipeline execution.

Priority #4: Validate that non-AML disease configs work correctly with the CRF pipeline.

Usage:
    cd /Users/kimhawk/.config/opencode/skill/clinical-statistics-analyzer
    PYTHONPATH=. python tests/test_disease_configs.py
"""

import csv
import json
import os
import random
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.crf_pipeline.config.loader import ConfigLoader

CONFIG_DIR = PROJECT_ROOT / "scripts" / "crf_pipeline" / "config"
DISEASES = ["aml", "cml", "mds", "hct"]

# ── Section 1: Config Loading Validation ─────────────────────────────────────

def test_config_loading():
    """Validate ConfigLoader merges common + disease overlay correctly."""
    loader = ConfigLoader(str(CONFIG_DIR))
    results = {}
    all_pass = True

    for disease in DISEASES:
        print(f"\n{'='*60}")
        print(f"  Testing config: {disease.upper()}")
        print(f"{'='*60}")

        config = loader.load(disease)
        fields = loader.get_field_definitions(disease)

        # Basic structure checks
        checks = []

        # 1. Disease tag present
        has_disease = config.get("disease") == disease
        checks.append(("disease tag", has_disease))

        # 2. Sections from common_fields merged in
        common_sections = {"demographics", "laboratory", "dates", "outcomes"}
        merged_sections = set(config.get("sections", {}).keys())
        has_common = common_sections.issubset(merged_sections)
        checks.append(("common sections merged", has_common))
        if not has_common:
            missing = common_sections - merged_sections
            print(f"    MISSING common sections: {missing}")

        # 3. Disease-specific sections present
        disease_sections = {
            "aml": {"molecular_markers", "treatment"},
            "cml": {"molecular_markers", "risk_scores", "treatment", "response", "toxicity"},
            "mds": {"risk_scores", "molecular_markers", "transfusion", "treatment", "response"},
            "hct": {"donor", "conditioning", "engraftment", "gvhd", "outcomes_hct"},
        }
        expected = disease_sections[disease]
        has_disease_sections = expected.issubset(merged_sections)
        checks.append(("disease sections present", has_disease_sections))
        if not has_disease_sections:
            missing = expected - merged_sections
            print(f"    MISSING disease sections: {missing}")

        # 4. Fields resolved to FieldDefinition objects
        field_count = len(fields)
        has_fields = field_count > 0
        checks.append((f"fields loaded ({field_count})", has_fields))

        # 5. Required fields are specified
        required = config.get("required_fields", [])
        has_required = len(required) > 0
        checks.append((f"required_fields ({len(required)})", has_required))

        # 6. SPSS value mappings present
        spss_map = config.get("spss_value_mapping", {})
        has_spss = len(spss_map) > 0
        checks.append((f"spss_value_mapping ({len(spss_map)} vars)", has_spss))

        # 7. Validation rules loaded
        val_rules = config.get("validation_rules", {})
        has_rules = len(val_rules) > 0
        checks.append(("validation_rules loaded", has_rules))

        # 8. No duplicate variables across sections
        var_names = [f.variable for f in fields]
        dupes = [v for v in set(var_names) if var_names.count(v) > 1]
        no_dupes = len(dupes) == 0
        checks.append(("no duplicate variables", no_dupes))
        if not no_dupes:
            print(f"    DUPLICATE variables: {dupes}")

        # 9. SPSS mapping keys match actual field variables
        field_vars = set(var_names)
        spss_vars = set(spss_map.keys())
        orphan_spss = spss_vars - field_vars
        checks.append((f"spss keys align (orphans: {len(orphan_spss)})", len(orphan_spss) == 0))
        if orphan_spss:
            print(f"    ORPHAN spss mappings (no matching field): {orphan_spss}")

        # 10. All required_fields exist in field definitions
        missing_required = [r for r in required if r not in field_vars]
        checks.append(("required_fields exist", len(missing_required) == 0))
        if missing_required:
            print(f"    MISSING required fields: {missing_required}")

        # Print results
        for label, passed in checks:
            status = "PASS" if passed else "FAIL"
            marker = "  " if passed else "**"
            print(f"  {marker}[{status}] {label}")
            if not passed:
                all_pass = False

        results[disease] = {
            "sections": len(merged_sections),
            "fields": field_count,
            "required": len(required),
            "spss_mappings": len(spss_map),
            "all_checks_passed": all(p for _, p in checks),
        }

    return results, all_pass


# ── Section 2: Mock Data Generation ──────────────────────────────────────────

def _rand_date(start_year=2020, end_year=2025):
    start = date(start_year, 1, 1)
    delta = (date(end_year, 12, 31) - start).days
    return (start + timedelta(days=random.randint(0, delta))).isoformat()


def generate_mock_cml(n=15):
    """Generate mock CML patient dataset."""
    rows = []
    tkis = ["Imatinib", "Dasatinib", "Nilotinib", "Bosutinib"]
    phases = ["Chronic Phase", "Accelerated Phase", "Blast Crisis"]
    risks = ["Low", "Intermediate", "High"]

    for i in range(1, n + 1):
        rows.append({
            "case_no": f"CML-{i:03d}",
            "age": random.randint(25, 80),
            "gender": random.choice(["Male", "Female"]),
            "birth": _rand_date(1945, 2000),
            "diag": "CML",
            "cml_phase_dx": random.choices(phases, weights=[0.85, 0.10, 0.05])[0],
            "bcr_abl_type": random.choice(["e13a2", "e14a2"]),
            "bcr_abl_baseline": round(random.uniform(10, 100), 2),
            "bcr_abl_3m": round(random.uniform(0.5, 30), 2),
            "bcr_abl_6m": round(random.uniform(0.01, 10), 3),
            "bcr_abl_12m": round(random.uniform(0.001, 1), 4),
            "ph_positive": "Positive",
            "sokal_score": round(random.uniform(0.4, 2.5), 2),
            "sokal_risk": random.choice(risks),
            "tki_first_line": random.choice(tkis),
            "tki_start_date": _rand_date(2020, 2024),
            "tki_dose": random.choice([100, 140, 400, 600]),
            "chr_achieved": random.choice(["Yes", "No"]),
            "ccyr_achieved": random.choice(["Yes", "No"]),
            "mmr_achieved": random.choice(["Yes", "No"]),
            "wbc1": round(random.uniform(5, 300), 1),
            "hb1": round(random.uniform(7, 16), 1),
            "plt1": round(random.uniform(50, 1500), 0),
            "blast1": round(random.uniform(0, 15), 1),
            "alive": random.choices(["Alive", "Dead"], weights=[0.85, 0.15])[0],
            "date_last_fu": _rand_date(2024, 2025),
        })
    return rows


def generate_mock_mds(n=15):
    """Generate mock MDS patient dataset."""
    rows = []
    subtypes = ["MDS-5q", "MDS-SF3B1", "MDS-LB", "MDS-h", "MDS-IB1", "MDS-IB2"]
    ipssr_risks = ["Very Low", "Low", "Intermediate", "High", "Very High"]
    treatments = ["Azacitidine", "Decitabine", "Lenalidomide", "ESA", "BSC"]
    responses = ["CR", "mCR", "PR", "HI", "SD", "Failure"]

    for i in range(1, n + 1):
        rows.append({
            "case_no": f"MDS-{i:03d}",
            "age": random.randint(50, 90),
            "gender": random.choice(["Male", "Female"]),
            "birth": _rand_date(1935, 1975),
            "diag": "MDS",
            "mds_subtype": random.choice(subtypes),
            "ipss_r": round(random.uniform(0.5, 8.0), 1),
            "ipss_r_risk": random.choice(ipssr_risks),
            "cytogenetic_risk_r": random.choice(["Very Good", "Good", "Intermediate", "Poor", "Very Poor"]),
            "sf3b1": random.choice(["Positive", "Negative"]),
            "tp53": random.choices(["Positive", "Negative"], weights=[0.1, 0.9])[0],
            "transfusion_dependent": random.choice(["Yes", "No"]),
            "rbc_units_8w": random.randint(0, 12),
            "ferritin": round(random.uniform(100, 5000), 0),
            "primary_treatment": random.choice(treatments),
            "treatment_start_date": _rand_date(2020, 2024),
            "hma_cycles": random.randint(1, 12),
            "mds_response": random.choice(responses),
            "hi_e": random.choice(["Yes", "No"]),
            "hi_p": random.choice(["Yes", "No"]),
            "wbc1": round(random.uniform(0.5, 15), 1),
            "hb1": round(random.uniform(5, 12), 1),
            "plt1": round(random.uniform(10, 300), 0),
            "blast1": round(random.uniform(0, 19), 1),
            "alive": random.choices(["Alive", "Dead"], weights=[0.65, 0.35])[0],
            "date_last_fu": _rand_date(2024, 2025),
        })
    return rows


def generate_mock_hct(n=15):
    """Generate mock HCT patient dataset."""
    rows = []
    donors = ["MSD", "MUD", "MMUD", "Haplo"]
    intensities = ["MAC", "RIC", "NMA"]
    sources = ["PBSC", "BM"]
    severities = ["Mild", "Moderate", "Severe"]

    for i in range(1, n + 1):
        has_agvhd = random.random() < 0.45
        has_cgvhd = random.random() < 0.35
        rows.append({
            "case_no": f"HCT-{i:03d}",
            "age": random.randint(18, 70),
            "gender": random.choice(["Male", "Female"]),
            "birth": _rand_date(1955, 2005),
            "diag": random.choice(["AML", "ALL", "MDS", "MPN"]),
            "disease_status_hct": random.choice(["CR1", "CR2", "Active disease"]),
            "donor_type": random.choice(donors),
            "donor_age": random.randint(20, 60),
            "donor_sex": random.choice(["Male", "Female"]),
            "hla_match": random.choice(["8/8", "7/8", "10/10", "5/10"]),
            "cmv_donor": random.choice(["Positive", "Negative"]),
            "cmv_recipient": random.choice(["Positive", "Negative"]),
            "conditioning": random.choice(["BuCy", "FluBu4", "FluMel", "FluBu2", "TBI/Cy"]),
            "conditioning_intensity": random.choice(intensities),
            "stem_cell_source": random.choice(sources),
            "cd34_dose": round(random.uniform(2.0, 12.0), 1),
            "atg_used": random.choice(["Yes", "No"]),
            "ptcy_used": random.choice(["Yes", "No"]),
            "engraft_anc_days": random.randint(10, 28),
            "engraft_plt_days": random.randint(12, 45),
            "graft_failure": random.choices(["Yes", "No"], weights=[0.03, 0.97])[0],
            "chimerism_d30": round(random.uniform(85, 100), 1),
            "agvhd": "Yes" if has_agvhd else "No",
            "agvhd_grade": random.randint(1, 4) if has_agvhd else None,
            "cgvhd": "Yes" if has_cgvhd else "No",
            "cgvhd_severity": random.choice(severities) if has_cgvhd else None,
            "nrm": random.choices(["Yes", "No"], weights=[0.15, 0.85])[0],
            "cmv_reactivation": random.choice(["Yes", "No"]),
            "hct_date": _rand_date(2020, 2024),
            "wbc1": round(random.uniform(0.1, 50), 1),
            "hb1": round(random.uniform(6, 15), 1),
            "plt1": round(random.uniform(10, 400), 0),
            "blast1": round(random.uniform(0, 30), 1),
            "alive": random.choices(["Alive", "Dead"], weights=[0.70, 0.30])[0],
            "date_last_fu": _rand_date(2024, 2025),
        })
    return rows


def write_mock_csv(rows, path):
    """Write mock data rows to CSV."""
    if not rows:
        return
    fieldnames = rows[0].keys()
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# ── Section 3: Pipeline Execution Test ───────────────────────────────────────

def test_pipeline_parse_data(mock_dir, output_dir):
    """Run parse-data subcommand for each mock dataset."""
    results = {}

    for disease in ["cml", "mds", "hct"]:
        csv_path = os.path.join(mock_dir, f"mock_{disease}.csv")
        print(f"\n--- parse-data: {disease.upper()} ({csv_path}) ---")

        out_json = os.path.join(output_dir, f"{disease}_data_parsed.json")
        cmd = [
            sys.executable, "-m", "scripts.crf_pipeline",
            "parse-data", csv_path,
            "-o", out_json,
        ]
        proc = subprocess.run(
            cmd, capture_output=True, text=True,
            cwd=str(PROJECT_ROOT),
            env={**os.environ, "CRF_OUTPUT_DIR": output_dir},
        )

        passed = proc.returncode == 0
        print(f"  exit code: {proc.returncode}")
        if proc.stdout.strip():
            # Print just last 5 lines to keep output manageable
            lines = proc.stdout.strip().split("\n")
            for line in lines[-5:]:
                print(f"  stdout: {line}")
        if proc.stderr.strip():
            for line in proc.stderr.strip().split("\n")[-3:]:
                print(f"  stderr: {line}")

        results[disease] = {"parse_data": "PASS" if passed else "FAIL"}

    return results


def test_pipeline_validate(mock_dir, output_dir):
    """Run validate subcommand for each mock dataset."""
    results = {}

    for disease in ["cml", "mds", "hct"]:
        csv_path = os.path.join(mock_dir, f"mock_{disease}.csv")
        print(f"\n--- validate: {disease.upper()} ({csv_path}) ---")

        out_report = os.path.join(output_dir, f"{disease}_validation_report.json")
        cmd = [
            sys.executable, "-m", "scripts.crf_pipeline",
            "validate", csv_path,
            "-o", out_report,
        ]
        proc = subprocess.run(
            cmd, capture_output=True, text=True,
            cwd=str(PROJECT_ROOT),
            env={**os.environ, "CRF_OUTPUT_DIR": output_dir},
        )

        passed = proc.returncode == 0
        print(f"  exit code: {proc.returncode}")
        if proc.stdout.strip():
            lines = proc.stdout.strip().split("\n")
            for line in lines[-5:]:
                print(f"  stdout: {line}")
        if proc.stderr.strip():
            for line in proc.stderr.strip().split("\n")[-3:]:
                print(f"  stderr: {line}")

        results[disease] = {"validate": "PASS" if passed else "FAIL"}

    return results


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    random.seed(42)  # Reproducibility
    print("=" * 60)
    print("  CML/MDS/HCT Disease Config & Pipeline Test")
    print("=" * 60)

    # Phase 1: Config loading
    print("\n\n### PHASE 1: Config Loading Validation ###")
    config_results, configs_ok = test_config_loading()

    # Phase 2: Generate mock data
    print("\n\n### PHASE 2: Mock Data Generation ###")
    mock_dir = tempfile.mkdtemp(prefix="csa_mock_")
    output_dir = tempfile.mkdtemp(prefix="csa_output_")
    print(f"  Mock data dir: {mock_dir}")
    print(f"  Output dir:    {output_dir}")

    for disease, gen_fn in [("cml", generate_mock_cml), ("mds", generate_mock_mds), ("hct", generate_mock_hct)]:
        rows = gen_fn(15)
        csv_path = os.path.join(mock_dir, f"mock_{disease}.csv")
        write_mock_csv(rows, csv_path)
        print(f"  Generated mock_{disease}.csv ({len(rows)} rows, {len(rows[0])} columns)")

    # Phase 3: Pipeline parse-data
    print("\n\n### PHASE 3: Pipeline parse-data ###")
    parse_results = test_pipeline_parse_data(mock_dir, output_dir)

    # Phase 4: Pipeline validate
    print("\n\n### PHASE 4: Pipeline validate ###")
    validate_results = test_pipeline_validate(mock_dir, output_dir)

    # Summary
    print("\n\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)

    print(f"\n  Config Loading:")
    for disease in DISEASES:
        r = config_results[disease]
        status = "PASS" if r["all_checks_passed"] else "FAIL"
        print(f"    {disease.upper():4s}: [{status}] {r['fields']} fields, {r['sections']} sections, {r['spss_mappings']} SPSS mappings")

    print(f"\n  Pipeline parse-data:")
    for disease in ["cml", "mds", "hct"]:
        status = parse_results.get(disease, {}).get("parse_data", "SKIP")
        print(f"    {disease.upper():4s}: [{status}]")

    print(f"\n  Pipeline validate:")
    for disease in ["cml", "mds", "hct"]:
        status = validate_results.get(disease, {}).get("validate", "SKIP")
        print(f"    {disease.upper():4s}: [{status}]")

    # Overall
    all_parse = all(v.get("parse_data") == "PASS" for v in parse_results.values())
    all_validate = all(v.get("validate") == "PASS" for v in validate_results.values())
    overall = configs_ok and all_parse and all_validate
    print(f"\n  Overall: {'ALL PASS' if overall else 'SOME FAILURES'}")

    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())
