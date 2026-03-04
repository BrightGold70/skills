"""Analysis orchestrator: chains data transformation with R script execution."""

import json
import logging
import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from .config.loader import ConfigLoader
from .transformers.column_mapper import ColumnMapper
from .transformers.date_calculator import DateCalculator
from .transformers.value_recoder import ValueRecoder
from .journal_themes import JournalThemes
from .pdf_exporter import PDFExporter
from .report_generator import ReportGenerator
from .html_exporter import HTMLExporter

logger = logging.getLogger(__name__)


@dataclass
class ScriptResult:
    """Result from a single R script execution."""

    script: str
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    elapsed_time: float = 0.0
    output_files: List[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.exit_code == 0


@dataclass
class AnalysisResult:
    """Result from a full analysis orchestration run."""

    status: str = "success"  # "success" | "partial" | "error"
    data_path: str = ""
    transformed_csv: str = ""
    disease: str = ""
    total_scripts: int = 0
    successful_scripts: int = 0
    failed_scripts: int = 0
    script_results: List[ScriptResult] = field(default_factory=list)
    output_files: List[str] = field(default_factory=list)
    elapsed_time: float = 0.0
    errors: List[str] = field(default_factory=list)
    steps: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "data_path": self.data_path,
            "transformed_csv": self.transformed_csv,
            "disease": self.disease,
            "total_scripts": self.total_scripts,
            "successful_scripts": self.successful_scripts,
            "failed_scripts": self.failed_scripts,
            "script_results": [
                {
                    "script": r.script,
                    "exit_code": r.exit_code,
                    "elapsed_time": r.elapsed_time,
                    "output_files": r.output_files,
                    "error": r.error,
                }
                for r in self.script_results
            ],
            "output_files": self.output_files,
            "elapsed_time": round(self.elapsed_time, 2),
            "errors": self.errors,
            "steps": self.steps,
        }


class AnalysisOrchestrator:
    """Orchestrates the full analysis pipeline: transform → R scripts → summary.

    Args:
        config_dir: Path to CRF pipeline config directory.
        disease: Disease type (aml, cml, mds, hct).
        output_dir: Base output directory (CSA_OUTPUT_DIR).
        scripts_dir: Directory containing R scripts.
        script_filter: Optional list of script names to run (default: all for disease).
    """

    def __init__(
        self,
        config_dir: str,
        disease: str,
        output_dir: str,
        scripts_dir: Optional[str] = None,
        script_filter: Optional[List[str]] = None,
    ):
        self.disease = disease
        self.output_dir = Path(output_dir)
        self.script_filter = script_filter

        # Resolve scripts directory (default: scripts/ relative to crf_pipeline/)
        if scripts_dir:
            self.scripts_dir = Path(scripts_dir)
        else:
            self.scripts_dir = Path(__file__).parent.parent

        # Load config
        self.config_loader = ConfigLoader(config_dir)
        self.config = self.config_loader.load(disease)
        self.analysis_profiles = self.config_loader.load_analysis_profiles()

        # Build transformers
        self.column_mapper = ColumnMapper()
        self.date_calculator = DateCalculator()
        self.value_recoder = ValueRecoder()

    def _load_data(self, data_path: str) -> pd.DataFrame:
        """Load a data file into a DataFrame.

        Supports CSV, XLSX, SAV (SPSS), and JSON formats.
        """
        path = Path(data_path)
        ext = path.suffix.lower()

        if ext == ".csv":
            return pd.read_csv(data_path)
        elif ext in (".xlsx", ".xls"):
            return pd.read_excel(data_path)
        elif ext == ".sav":
            import pyreadstat
            df, meta = pyreadstat.read_sav(data_path)
            return df
        elif ext == ".json":
            return pd.read_json(data_path)
        else:
            raise ValueError(f"Unsupported data file format: {ext}")

    def transform(self, data_path: str) -> str:
        """Load data, apply transformations, and save R-ready CSV.

        Execution order:
            1. Derive new columns (date calculations, recoding, binning)
               using original CRF variable names.
            2. Rename columns from CRF names to R-expected names.

        Args:
            data_path: Path to input data file.

        Returns:
            Path to the transformed R-ready CSV file.
        """
        logger.info("Loading data from %s", data_path)
        df = self._load_data(data_path)
        logger.info("Loaded %d rows x %d columns", len(df), len(df.columns))

        # Step 1: Derive new columns (using original CRF names)
        df = self.date_calculator.transform(df, self.config)
        df = self.value_recoder.transform(df, self.config)

        # Step 2: Rename columns (CRF → R names)
        df = self.column_mapper.transform(df, self.config)

        # Save R-ready CSV
        data_dir = self.output_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        csv_path = data_dir / f"r_ready_{self.disease}.csv"
        df.to_csv(csv_path, index=False)
        logger.info("Saved R-ready CSV: %s (%d rows x %d cols)", csv_path, len(df), len(df.columns))

        return str(csv_path)

    def _get_scripts_for_disease(self) -> List[Dict[str, Any]]:
        """Get the list of R scripts to run for the current disease."""
        profiles = self.analysis_profiles.get("profiles", {})
        disease_profile = profiles.get(self.disease, {})
        scripts = disease_profile.get("scripts", [])

        if self.script_filter:
            scripts = [s for s in scripts if s["name"] in self.script_filter]

        return scripts

    def _resolve_args(
        self,
        args_template: List[str],
        csv_path: str,
        overrides: Optional[Dict[str, str]] = None,
    ) -> List[str]:
        """Resolve placeholders in script argument templates.

        Supported placeholders: ``{dataset}``, ``{output_dir}``, ``{disease}``,
        ``{outcome_var}``, ``{time_var}``, ``{status_var}``.  Per-disease
        defaults are read from the analysis profile; *overrides* (e.g. from
        ``run_variants``) take precedence.
        """
        profile = self.analysis_profiles.get("profiles", {}).get(self.disease, {})
        defaults = {
            "dataset": csv_path,
            "output_dir": str(self.output_dir),
            "disease": self.disease,
            "outcome_var": profile.get("default_outcome_var", "Response"),
            "time_var": profile.get("default_time_var", "OS_months"),
            "status_var": profile.get("default_status_var", "OS_status"),
        }
        if overrides:
            defaults.update(overrides)

        resolved = []
        for arg in args_template:
            if arg.startswith("{") and arg.endswith("}"):
                key = arg[1:-1]
                resolved.append(str(defaults.get(key, arg)))
            else:
                resolved.append(arg)
        return resolved

    def _check_required_columns(self, csv_path: str, script_name: str) -> Optional[str]:
        """Check if the CSV has columns needed by a specific script.

        Returns an error message if required columns are missing, else None.
        """
        # Read just the header
        try:
            header = pd.read_csv(csv_path, nrows=0).columns.tolist()
        except Exception as e:
            return f"Cannot read CSV header: {e}"

        # Define required columns per script type
        required_map = {
            "02_table1.R": ["Patient_ID", "Age", "Sex"],
            "04_survival.R": ["OS_months", "OS_status"],
        }

        required = required_map.get(script_name, [])
        missing = [c for c in required if c not in header]
        if missing:
            return f"Missing columns for {script_name}: {missing}"
        return None

    def run_scripts(self, csv_path: str) -> List[ScriptResult]:
        """Execute R scripts for the current disease.

        Args:
            csv_path: Path to the transformed R-ready CSV file.

        Returns:
            List of ScriptResult for each script executed.
        """
        scripts = self._get_scripts_for_disease()
        if not scripts:
            logger.warning("No analysis scripts configured for disease '%s'", self.disease)
            return []

        results = []
        # Ensure output subdirectories exist
        (self.output_dir / "Tables").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "Figures").mkdir(parents=True, exist_ok=True)

        for script_spec in scripts:
            script_name = script_spec["name"]
            required = script_spec.get("required", True)

            # Check required columns
            col_error = self._check_required_columns(csv_path, script_name)
            if col_error:
                if required:
                    logger.error("Required script %s: %s", script_name, col_error)
                    results.append(ScriptResult(
                        script=script_name, exit_code=1,
                        error=col_error,
                    ))
                else:
                    logger.info("Skipping optional script %s: %s", script_name, col_error)
                continue

            variants = script_spec.get("run_variants")
            if variants:
                # Run once per variant (e.g. OS and PFS for survival)
                for variant in variants:
                    # Check if variant columns exist in the CSV
                    try:
                        header = pd.read_csv(csv_path, nrows=0).columns.tolist()
                    except Exception:
                        header = []
                    time_col = variant.get("time_var", "")
                    status_col = variant.get("status_var", "")
                    if time_col and time_col not in header:
                        logger.info(
                            "Skipping variant %s: column '%s' not in data",
                            variant.get("suffix", ""), time_col,
                        )
                        continue
                    if status_col and status_col not in header:
                        logger.info(
                            "Skipping variant %s: column '%s' not in data",
                            variant.get("suffix", ""), status_col,
                        )
                        continue

                    result = self._run_single_script(
                        script_name, script_spec, csv_path,
                        overrides=variant, suffix=variant.get("suffix"),
                    )
                    results.append(result)
                    if result.success:
                        logger.info("Script %s (%s) completed in %.1fs",
                                    script_name, variant.get("suffix", ""), result.elapsed_time)
                    else:
                        level = logging.ERROR if required else logging.WARNING
                        logger.log(level, "Script %s (%s) failed (exit=%d): %s",
                                   script_name, variant.get("suffix", ""),
                                   result.exit_code, result.error)
            else:
                result = self._run_single_script(script_name, script_spec, csv_path)
                results.append(result)

                if result.success:
                    logger.info("Script %s completed in %.1fs", script_name, result.elapsed_time)
                else:
                    level = logging.ERROR if required else logging.WARNING
                    logger.log(level, "Script %s failed (exit=%d): %s",
                               script_name, result.exit_code, result.error)

        return results

    def _run_single_script(
        self,
        script_name: str,
        script_spec: Dict[str, Any],
        csv_path: str,
        overrides: Optional[Dict[str, str]] = None,
        suffix: Optional[str] = None,
    ) -> ScriptResult:
        """Run a single R script via subprocess."""
        script_path = self.scripts_dir / script_name
        args_template = script_spec.get("args", ["{dataset}"])
        resolved_args = self._resolve_args(args_template, csv_path, overrides=overrides)
        display_name = f"{script_name} ({suffix})" if suffix else script_name

        cmd = ["Rscript", str(script_path)] + resolved_args
        env = os.environ.copy()
        env["CSA_OUTPUT_DIR"] = str(self.output_dir)

        logger.info("Running: %s", " ".join(cmd))
        start = time.time()

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout per script
                env=env,
            )
            elapsed = time.time() - start

            # Collect output files
            output_files = self._find_output_files(script_spec.get("expected_outputs", []))

            return ScriptResult(
                script=script_name,
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                elapsed_time=elapsed,
                output_files=output_files,
                error=proc.stderr.strip() if proc.returncode != 0 else None,
            )

        except subprocess.TimeoutExpired:
            return ScriptResult(
                script=script_name,
                exit_code=-1,
                elapsed_time=time.time() - start,
                error="Script timed out after 300 seconds",
            )
        except FileNotFoundError:
            return ScriptResult(
                script=script_name,
                exit_code=-1,
                elapsed_time=0.0,
                error=f"Rscript not found or script missing: {script_path}",
            )
        except Exception as e:
            return ScriptResult(
                script=script_name,
                exit_code=-1,
                elapsed_time=time.time() - start,
                error=str(e),
            )

    def _find_output_files(self, expected: List[str]) -> List[str]:
        """Find expected output files in Tables/ and Figures/ directories."""
        found = []
        for name in expected:
            for subdir in ["Tables", "Figures"]:
                path = self.output_dir / subdir / name
                if path.exists():
                    found.append(str(path))
        return found

    def post_process(
        self,
        csv_path: str,
        script_results: List[ScriptResult],
        journal: Optional[str] = None,
        generate_pdf: bool = False,
        generate_html: bool = False,
        generate_csr: bool = True,
    ) -> Dict[str, Any]:
        """Post-process R script outputs: journal themes, PDF, HTML, mini-CSR.

        Called after run_scripts() in run_full(). All steps are optional
        and failures do not affect the standard analysis outputs.

        Returns:
            Dict with keys: journal_files, pdf_files, html_path, csr_path
        """
        result: Dict[str, Any] = {
            "journal_files": [],
            "pdf_files": {"tables": [], "figures": []},
            "html_path": "",
            "csr_path": "",
        }

        tables_dir = str(self.output_dir / "Tables")
        figures_dir = str(self.output_dir / "Figures")

        # 1. Journal themes
        if journal:
            try:
                themes = JournalThemes()
                styled = themes.apply(tables_dir, journal)
                result["journal_files"] = styled
                logger.info("Applied %s journal theme to %d files", journal, len(styled))
            except Exception as e:
                logger.warning("Journal theme application failed: %s", e)

        # 2. PDF export
        if generate_pdf:
            try:
                exporter = PDFExporter(str(self.output_dir))
                pdf_result = exporter.export_all(tables_dir, figures_dir)
                result["pdf_files"] = pdf_result
                total = len(pdf_result.get("tables", [])) + len(pdf_result.get("figures", []))
                logger.info("Generated %d PDF files", total)
            except Exception as e:
                logger.warning("PDF export failed: %s", e)

        # 3. Mini-CSR report
        if generate_csr:
            try:
                generator = ReportGenerator(str(self.output_dir), self.disease)
                csr_path = generator.generate(script_results)
                result["csr_path"] = csr_path
                logger.info("Generated mini-CSR: %s", csr_path)
            except Exception as e:
                logger.warning("Mini-CSR generation failed: %s", e)

        # 4. HTML dashboard
        if generate_html:
            try:
                html_exp = HTMLExporter(str(self.output_dir), self.disease)
                html_path = html_exp.generate(csv_path, script_results)
                result["html_path"] = html_path
                logger.info("Generated HTML dashboard: %s", html_path)
            except Exception as e:
                logger.warning("HTML dashboard generation failed: %s", e)

        return result

    def run_full(
        self,
        data_path: str,
        skip_validation: bool = False,
        journal: Optional[str] = None,
        generate_pdf: bool = False,
        generate_html: bool = False,
        generate_csr: bool = True,
    ) -> AnalysisResult:
        """Run the complete analysis pipeline: parse → validate → transform → R scripts.

        Args:
            data_path: Path to input data file.
            skip_validation: Whether to skip the validation step.

        Returns:
            AnalysisResult with status, script results, and output files.
        """
        start_time = time.time()
        result = AnalysisResult(
            data_path=data_path,
            disease=self.disease,
        )

        # Step 1: Parse data (structure analysis)
        step_start = time.time()
        try:
            from .parsers.data_parser import DataParser
            parser = DataParser()
            parse_result = parser.parse(data_path)
            result.steps["parse"] = {
                "status": "success",
                "elapsed_time": round(time.time() - step_start, 2),
                "rows": parse_result.get("total_records", 0),
                "columns": parse_result.get("total_variables", 0),
            }
            logger.info("Parse complete: %d rows, %d columns",
                        parse_result.get("total_records", 0),
                        parse_result.get("total_variables", 0))
        except Exception as e:
            result.steps["parse"] = {
                "status": "error",
                "error": str(e),
                "elapsed_time": round(time.time() - step_start, 2),
            }
            result.errors.append(f"Parse failed: {e}")
            result.status = "error"
            result.elapsed_time = time.time() - start_time
            return result

        # Step 2: Validate (optional)
        if not skip_validation:
            step_start = time.time()
            try:
                from .validators.temporal_validator import TemporalValidator
                df = parser.get_dataframe(data_path)
                validator = TemporalValidator()
                issues = validator.validate(df)
                error_count = sum(1 for i in issues if i.severity.value == "error")
                warning_count = sum(1 for i in issues if i.severity.value == "warning")
                result.steps["validate"] = {
                    "status": "success",
                    "elapsed_time": round(time.time() - step_start, 2),
                    "errors": error_count,
                    "warnings": warning_count,
                    "total_issues": len(issues),
                }
                if error_count > 0:
                    logger.warning("Validation found %d errors, %d warnings",
                                   error_count, warning_count)
                else:
                    logger.info("Validation passed with %d warnings", warning_count)
            except Exception as e:
                result.steps["validate"] = {
                    "status": "error",
                    "error": str(e),
                    "elapsed_time": round(time.time() - step_start, 2),
                }
                result.errors.append(f"Validation failed: {e}")
                logger.error("Validation error: %s", e)
        else:
            result.steps["validate"] = {"status": "skipped"}

        # Step 3: Transform
        step_start = time.time()
        try:
            csv_path = self.transform(data_path)
            result.transformed_csv = csv_path
            result.steps["transform"] = {
                "status": "success",
                "elapsed_time": round(time.time() - step_start, 2),
                "output": csv_path,
            }
        except Exception as e:
            result.steps["transform"] = {
                "status": "error",
                "error": str(e),
                "elapsed_time": round(time.time() - step_start, 2),
            }
            result.errors.append(f"Transform failed: {e}")
            result.status = "error"
            result.elapsed_time = time.time() - start_time
            return result

        # Step 4: Run R scripts
        step_start = time.time()
        script_results = self.run_scripts(csv_path)
        result.script_results = script_results
        result.total_scripts = len(script_results)
        result.successful_scripts = sum(1 for r in script_results if r.success)
        result.failed_scripts = result.total_scripts - result.successful_scripts

        # Collect all output files
        all_outputs = []
        for sr in script_results:
            all_outputs.extend(sr.output_files)
        result.output_files = all_outputs

        result.steps["r_scripts"] = {
            "status": "success" if result.failed_scripts == 0 else "partial",
            "elapsed_time": round(time.time() - step_start, 2),
            "total": result.total_scripts,
            "successful": result.successful_scripts,
            "failed": result.failed_scripts,
        }

        for sr in script_results:
            if sr.error:
                result.errors.append(f"{sr.script}: {sr.error}")

        # Final status
        result.elapsed_time = time.time() - start_time
        if result.failed_scripts == 0 and not result.errors:
            result.status = "success"
        elif result.successful_scripts > 0:
            result.status = "partial"
        else:
            result.status = "error"

        # Save summary report
        self._save_summary(result)

        # Step 5: Post-processing (journal themes, PDF, HTML, mini-CSR)
        if any([journal, generate_pdf, generate_html, generate_csr]):
            step_start = time.time()
            try:
                post_result = self.post_process(
                    csv_path=csv_path,
                    script_results=script_results,
                    journal=journal,
                    generate_pdf=generate_pdf,
                    generate_html=generate_html,
                    generate_csr=generate_csr,
                )
                result.steps["post_process"] = {
                    "status": "success",
                    "elapsed_time": round(time.time() - step_start, 2),
                    **post_result,
                }
            except Exception as e:
                result.steps["post_process"] = {
                    "status": "error",
                    "error": str(e),
                    "elapsed_time": round(time.time() - step_start, 2),
                }
                logger.warning("Post-processing failed: %s", e)

        # Update elapsed time to include post-processing
        result.elapsed_time = time.time() - start_time

        logger.info(
            "Analysis complete: %d/%d scripts succeeded, %.1fs elapsed",
            result.successful_scripts, result.total_scripts, result.elapsed_time,
        )

        return result

    def _save_summary(self, result: AnalysisResult) -> None:
        """Save a JSON summary report of the analysis run."""
        summary_path = self.output_dir / "analysis_summary.json"
        try:
            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump(result.to_dict(), f, indent=2, default=str)
            logger.info("Saved analysis summary: %s", summary_path)
        except Exception as e:
            logger.error("Failed to save summary: %s", e)
