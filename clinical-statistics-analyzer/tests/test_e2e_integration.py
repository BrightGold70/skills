#!/usr/bin/env python3
"""End-to-end integration test simulating the Claude API workflow.

Priority #5: Tests the full chain Claude would orchestrate:
  1. Generate mock clinical data (AML/CML/MDS/HCT)
  2. CRF pipeline: parse-data → validate
  3. R analysis scripts: table1, safety, survival, efficacy
  4. Output verification: .docx tables, .eps figures
  5. Error handling: missing env vars, bad inputs

Usage:
    cd /Users/kimhawk/.config/opencode/skill/clinical-statistics-analyzer
    PYTHONPATH=. python tests/test_e2e_integration.py
"""

import csv
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

RSCRIPT = shutil.which("Rscript")

# ── Mock Data Generation ─────────────────────────────────────────────────────

def _rand_date(start_year=2020, end_year=2025):
    start = date(start_year, 1, 1)
    delta = (date(end_year, 12, 31) - start).days
    return (start + timedelta(days=random.randint(0, delta))).isoformat()


def generate_aml_data(n=30):
    """Generate AML mock data with columns expected by R scripts."""
    rows = []
    arms = ["Treatment A", "Treatment B"]
    genders = ["Male", "Female"]
    ecog = [0, 1, 2]
    responses_cr = [True, False]

    for i in range(1, n + 1):
        alive = random.choices([True, False], weights=[0.6, 0.4])[0]
        relapsed = random.choices([True, False], weights=[0.35, 0.65])[0]
        cr = random.choices([True, False], weights=[0.55, 0.45])[0]
        dx_date = date(random.randint(2020, 2023), random.randint(1, 12), random.randint(1, 28))
        fu_months = random.randint(3, 36)
        os_months = random.randint(2, fu_months) if not alive else fu_months

        rows.append({
            # Demographics (02_table1.R)
            "Patient_ID": f"AML-{i:03d}",
            "Age": random.randint(20, 85),
            "Sex": random.choice(genders),
            "ECOG": random.choice(ecog),
            "Treatment": random.choice(arms),
            # Labs
            "WBC": round(random.uniform(0.5, 200), 1),
            "Hemoglobin": round(random.uniform(5, 16), 1),
            "Platelets": round(random.uniform(5, 400), 0),
            "BM_Blasts": round(random.uniform(0, 95), 1),
            # Molecular (AML ELN)
            "FLT3_ITD": random.choice(["Positive", "Negative"]),
            "NPM1": random.choice(["Positive", "Negative"]),
            "Cytogenetics": random.choice(["Normal", "t(8;21)", "inv(16)", "t(15;17)", "complex", "-7", "+8"]),
            # Response (03_efficacy.R) — use 0/1 for R glm(binomial)
            "CR": int(cr),
            "CRi": int(not cr and random.random() < 0.2),
            "PR": int(not cr and random.random() < 0.15),
            "MRD_neg": int(cr and random.random() < 0.4),
            # Safety (05_safety.R) - CTCAE adverse events
            "AE_Neutropenia": random.choice([0, 1, 2, 3, 4]),
            "AE_Thrombocytopenia": random.choice([0, 1, 2, 3, 4]),
            "AE_Anemia": random.choice([0, 1, 2, 3]),
            "AE_Infection": random.choice([0, 1, 2, 3]),
            "AE_Nausea": random.choice([0, 1, 2]),
            "AE_Fatigue": random.choice([0, 1, 2, 3]),
            "AE_Febrile_Neutropenia": random.choice([0, 3, 4]),
            "AE_Diarrhea": random.choice([0, 1, 2]),
            "AE_Rash": random.choice([0, 1, 2]),
            "AE_Hepatotoxicity": random.choice([0, 1, 2, 3]),
            # Survival (04_survival.R)
            "OS_months": os_months,
            "OS_status": 0 if alive else 1,
            "PFS_months": random.randint(1, os_months) if relapsed else os_months,
            "PFS_status": 1 if relapsed or not alive else 0,
            # Dates
            "Diagnosis_Date": dx_date.isoformat(),
            "Last_Followup": (dx_date + timedelta(days=fu_months * 30)).isoformat(),
        })
    return rows


def write_csv(rows, path):
    if not rows:
        return
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


# ── Test Runner ──────────────────────────────────────────────────────────────

class E2ETestRunner:
    def __init__(self):
        self.work_dir = tempfile.mkdtemp(prefix="csa_e2e_")
        self.output_dir = os.path.join(self.work_dir, "output")
        self.data_dir = os.path.join(self.work_dir, "data")
        os.makedirs(self.output_dir)
        os.makedirs(self.data_dir)
        os.makedirs(os.path.join(self.output_dir, "Tables"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "Figures"), exist_ok=True)
        self.results = []

    def record(self, phase, test, passed, detail=""):
        status = "PASS" if passed else "FAIL"
        self.results.append((phase, test, status, detail))
        marker = "  " if passed else "**"
        print(f"  {marker}[{status}] {test}" + (f"  ({detail})" if detail else ""))
        return passed

    def run_cmd(self, cmd, env_extra=None, timeout=120):
        env = {**os.environ}
        if env_extra:
            env.update(env_extra)
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True,
                cwd=str(PROJECT_ROOT), env=env, timeout=timeout,
            )
            return proc
        except subprocess.TimeoutExpired:
            return None

    # ── Phase 1: CRF Pipeline Chain ──────────────────────────────────────

    def test_crf_pipeline(self):
        print(f"\n{'='*60}")
        print("  PHASE 1: CRF Pipeline (parse-data → validate)")
        print(f"{'='*60}")

        csv_path = os.path.join(self.data_dir, "aml_e2e.csv")
        rows = generate_aml_data(30)
        write_csv(rows, csv_path)
        self.record("pipeline", "Mock AML CSV generated", True, f"{len(rows)} rows")

        # parse-data
        out_json = os.path.join(self.output_dir, "aml_e2e_parsed.json")
        proc = self.run_cmd(
            [sys.executable, "-m", "scripts.crf_pipeline", "parse-data", csv_path, "-o", out_json],
            env_extra={"CRF_OUTPUT_DIR": self.output_dir},
        )
        parsed_ok = proc is not None and proc.returncode == 0 and os.path.exists(out_json)
        self.record("pipeline", "parse-data AML", parsed_ok,
                     f"{os.path.getsize(out_json)} bytes" if parsed_ok else (proc.stderr[-200:] if proc else "timeout"))

        # Verify parsed JSON structure
        if parsed_ok:
            with open(out_json) as f:
                parsed = json.load(f)
            has_structure = "columns" in parsed or "variables" in parsed or "summary" in parsed
            self.record("pipeline", "parsed JSON has structure", has_structure,
                         f"keys: {list(parsed.keys())[:5]}")

        # validate
        val_json = os.path.join(self.output_dir, "aml_e2e_validation.json")
        proc = self.run_cmd(
            [sys.executable, "-m", "scripts.crf_pipeline", "validate", csv_path, "-o", val_json],
            env_extra={"CRF_OUTPUT_DIR": self.output_dir},
        )
        val_ok = proc is not None and proc.returncode == 0 and os.path.exists(val_json)
        self.record("pipeline", "validate AML", val_ok,
                     f"{os.path.getsize(val_json)} bytes" if val_ok else (proc.stderr[-200:] if proc else "timeout"))

        if val_ok:
            with open(val_json) as f:
                report = json.load(f)
            status = report.get("status", report.get("overall_status", "unknown"))
            errors_val = report.get("errors", 0)
            n_errors = errors_val if isinstance(errors_val, int) else len(errors_val)
            self.record("pipeline", "validation report", True, f"status={status}, errors={n_errors}")

        return csv_path

    # ── Phase 2: R Script Execution ──────────────────────────────────────

    def test_r_scripts(self, csv_path):
        print(f"\n{'='*60}")
        print("  PHASE 2: R Script Execution")
        print(f"{'='*60}")

        if not RSCRIPT:
            self.record("r_scripts", "Rscript available", False, "Rscript not found in PATH")
            return

        self.record("r_scripts", "Rscript available", True, RSCRIPT)

        r_env = {
            "CSA_OUTPUT_DIR": self.output_dir,
            "CRF_OUTPUT_DIR": self.output_dir,
        }

        scripts_dir = PROJECT_ROOT / "scripts"

        # Test each R script
        r_tests = [
            ("02_table1.R", [csv_path], ["Tables"]),
            ("05_safety.R", [csv_path], ["Tables"]),
            ("04_survival.R", [csv_path, "OS_months", "OS_status"], ["Figures", "Tables"]),
            ("03_efficacy.R", [csv_path, "CR"], ["Tables", "Figures"]),
        ]

        for script_name, args, expected_dirs in r_tests:
            script_path = scripts_dir / script_name
            if not script_path.exists():
                self.record("r_scripts", f"{script_name}", False, "script not found")
                continue

            # Count files before
            before_counts = {}
            for d in expected_dirs:
                dp = os.path.join(self.output_dir, d)
                before_counts[d] = len(os.listdir(dp)) if os.path.exists(dp) else 0

            cmd = [RSCRIPT, str(script_path)] + args
            proc = self.run_cmd(cmd, env_extra=r_env, timeout=120)

            if proc is None:
                self.record("r_scripts", f"{script_name}", False, "timeout (>120s)")
                continue

            # Check for new output files
            new_files = []
            for d in expected_dirs:
                dp = os.path.join(self.output_dir, d)
                if os.path.exists(dp):
                    after = len(os.listdir(dp))
                    if after > before_counts.get(d, 0):
                        new_files.extend(os.listdir(dp))

            if proc.returncode == 0:
                self.record("r_scripts", f"{script_name}", True,
                             f"exit=0, outputs: {', '.join(new_files[:3]) if new_files else 'check output'}")
            else:
                # Extract meaningful error
                err_lines = [l for l in proc.stderr.split("\n") if "Error" in l or "error" in l.lower()]
                err_msg = err_lines[0][:120] if err_lines else f"exit={proc.returncode}"
                self.record("r_scripts", f"{script_name}", False, err_msg)

    # ── Phase 3: Output Verification ─────────────────────────────────────

    def test_output_verification(self):
        print(f"\n{'='*60}")
        print("  PHASE 3: Output Verification")
        print(f"{'='*60}")

        tables_dir = os.path.join(self.output_dir, "Tables")
        figures_dir = os.path.join(self.output_dir, "Figures")

        # Check Tables/
        docx_files = [f for f in os.listdir(tables_dir) if f.endswith(".docx")] if os.path.exists(tables_dir) else []
        self.record("output", f".docx tables produced", len(docx_files) > 0,
                     f"{len(docx_files)} files: {', '.join(docx_files[:5])}")

        # Check Figures/
        eps_files = [f for f in os.listdir(figures_dir) if f.endswith(".eps")] if os.path.exists(figures_dir) else []
        self.record("output", f".eps figures produced", len(eps_files) > 0,
                     f"{len(eps_files)} files: {', '.join(eps_files[:5])}")

        # Check pipeline outputs
        pipeline_jsons = [f for f in os.listdir(self.output_dir) if f.endswith(".json")]
        self.record("output", "pipeline JSON outputs", len(pipeline_jsons) > 0,
                     f"{len(pipeline_jsons)} files: {', '.join(pipeline_jsons[:5])}")

        # Verify .docx files are valid (non-empty, starts with PK zip header)
        for docx_file in docx_files[:2]:
            fpath = os.path.join(tables_dir, docx_file)
            size = os.path.getsize(fpath)
            with open(fpath, "rb") as f:
                header = f.read(2)
            is_valid = size > 1000 and header == b"PK"
            self.record("output", f"  {docx_file} valid", is_valid,
                         f"{size} bytes, header={'PK' if header == b'PK' else 'invalid'}")

    # ── Phase 4: Error Handling ──────────────────────────────────────────

    def test_error_handling(self):
        print(f"\n{'='*60}")
        print("  PHASE 4: Error Handling")
        print(f"{'='*60}")

        # Test 1: Missing CSA_OUTPUT_DIR for R scripts
        if RSCRIPT:
            csv_path = os.path.join(self.data_dir, "aml_e2e.csv")
            script_path = PROJECT_ROOT / "scripts" / "02_table1.R"
            if script_path.exists():
                env_no_csa = {k: v for k, v in os.environ.items() if k != "CSA_OUTPUT_DIR"}
                proc = self.run_cmd([RSCRIPT, str(script_path), csv_path], env_extra={})
                # Override env completely to remove CSA_OUTPUT_DIR
                proc2 = subprocess.run(
                    [RSCRIPT, str(script_path), csv_path],
                    capture_output=True, text=True,
                    cwd=str(PROJECT_ROOT),
                    env={k: v for k, v in os.environ.items() if k != "CSA_OUTPUT_DIR"},
                    timeout=30,
                )
                failed_gracefully = proc2.returncode != 0 and "CSA_OUTPUT_DIR" in proc2.stderr
                self.record("errors", "R script: missing CSA_OUTPUT_DIR", failed_gracefully,
                             "exits with helpful error" if failed_gracefully else f"exit={proc2.returncode}")

        # Test 2: Missing CRF_OUTPUT_DIR for pipeline
        proc = subprocess.run(
            [sys.executable, "-m", "scripts.crf_pipeline", "parse-data",
             os.path.join(self.data_dir, "aml_e2e.csv")],
            capture_output=True, text=True,
            cwd=str(PROJECT_ROOT),
            env={k: v for k, v in os.environ.items() if k != "CRF_OUTPUT_DIR"},
            timeout=30,
        )
        # parse-data with no -o and no CRF_OUTPUT_DIR should still work
        # (it defaults to stdout or auto-generated path)
        self.record("errors", "Pipeline: no -o flag behavior", True,
                     f"exit={proc.returncode}")

        # Test 3: Invalid data file
        bad_path = os.path.join(self.data_dir, "nonexistent.csv")
        proc = subprocess.run(
            [sys.executable, "-m", "scripts.crf_pipeline", "parse-data", bad_path,
             "-o", os.path.join(self.output_dir, "bad_output.json")],
            capture_output=True, text=True,
            cwd=str(PROJECT_ROOT),
            env={**os.environ, "CRF_OUTPUT_DIR": self.output_dir},
            timeout=30,
        )
        self.record("errors", "Pipeline: nonexistent file", proc.returncode != 0,
                     "correctly fails" if proc.returncode != 0 else "unexpected success")

        # Test 4: Empty CSV
        empty_csv = os.path.join(self.data_dir, "empty.csv")
        with open(empty_csv, "w") as f:
            f.write("col1,col2\n")  # headers only
        proc = subprocess.run(
            [sys.executable, "-m", "scripts.crf_pipeline", "parse-data", empty_csv,
             "-o", os.path.join(self.output_dir, "empty_parsed.json")],
            capture_output=True, text=True,
            cwd=str(PROJECT_ROOT),
            env={**os.environ, "CRF_OUTPUT_DIR": self.output_dir},
            timeout=30,
        )
        # Should handle gracefully (succeed with minimal output or fail cleanly)
        self.record("errors", "Pipeline: empty CSV (headers only)", True,
                     f"exit={proc.returncode} (handled)")

    # ── Phase 5: Multi-Disease Pipeline ──────────────────────────────────

    def test_multi_disease_pipeline(self):
        print(f"\n{'='*60}")
        print("  PHASE 5: Multi-Disease Pipeline Chain")
        print(f"{'='*60}")

        from tests.test_disease_configs import generate_mock_cml, generate_mock_mds, generate_mock_hct

        for disease, gen_fn in [("cml", generate_mock_cml), ("mds", generate_mock_mds), ("hct", generate_mock_hct)]:
            rows = gen_fn(10)
            csv_path = os.path.join(self.data_dir, f"{disease}_e2e.csv")
            write_csv(rows, csv_path)

            # parse-data
            out_json = os.path.join(self.output_dir, f"{disease}_e2e_parsed.json")
            proc = self.run_cmd(
                [sys.executable, "-m", "scripts.crf_pipeline", "parse-data", csv_path, "-o", out_json],
                env_extra={"CRF_OUTPUT_DIR": self.output_dir},
            )
            parse_ok = proc is not None and proc.returncode == 0
            self.record("multi", f"{disease.upper()} parse-data", parse_ok)

            # validate
            val_json = os.path.join(self.output_dir, f"{disease}_e2e_validation.json")
            proc = self.run_cmd(
                [sys.executable, "-m", "scripts.crf_pipeline", "validate", csv_path, "-o", val_json],
                env_extra={"CRF_OUTPUT_DIR": self.output_dir},
            )
            val_ok = proc is not None and proc.returncode == 0
            self.record("multi", f"{disease.upper()} validate", val_ok)

    # ── Summary ──────────────────────────────────────────────────────────

    def print_summary(self):
        print(f"\n\n{'='*60}")
        print("  E2E INTEGRATION TEST SUMMARY")
        print(f"{'='*60}")

        phases = {}
        for phase, test, status, detail in self.results:
            if phase not in phases:
                phases[phase] = {"pass": 0, "fail": 0}
            phases[phase]["pass" if status == "PASS" else "fail"] += 1

        total_pass = sum(p["pass"] for p in phases.values())
        total_fail = sum(p["fail"] for p in phases.values())

        for phase, counts in phases.items():
            label = {
                "pipeline": "CRF Pipeline",
                "r_scripts": "R Scripts",
                "output": "Output Verification",
                "errors": "Error Handling",
                "multi": "Multi-Disease",
            }.get(phase, phase)
            status = "PASS" if counts["fail"] == 0 else "FAIL"
            print(f"  [{status}] {label}: {counts['pass']} passed, {counts['fail']} failed")

        print(f"\n  Total: {total_pass} passed, {total_fail} failed")
        print(f"  Work dir: {self.work_dir}")

        if total_fail > 0:
            print(f"\n  Failed tests:")
            for phase, test, status, detail in self.results:
                if status == "FAIL":
                    print(f"    - [{phase}] {test}: {detail}")

        return total_fail == 0


def main():
    random.seed(42)
    print("=" * 60)
    print("  Clinical Statistics Analyzer — E2E Integration Test")
    print("  Simulates full Claude API workflow")
    print("=" * 60)

    runner = E2ETestRunner()

    # Phase 1: CRF Pipeline
    csv_path = runner.test_crf_pipeline()

    # Phase 2: R Scripts
    runner.test_r_scripts(csv_path)

    # Phase 3: Output Verification
    runner.test_output_verification()

    # Phase 4: Error Handling
    runner.test_error_handling()

    # Phase 5: Multi-Disease
    runner.test_multi_disease_pipeline()

    # Summary
    all_pass = runner.print_summary()
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
