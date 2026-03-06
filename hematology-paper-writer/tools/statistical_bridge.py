"""Statistical Bridge — connects CSA outputs to HPW manuscript generation.

Reads hpw_manifest.json produced by CSA orchestrator.py and provides:
  - Typed access to tables, figures, key statistics
  - Template-driven prose generation (Methods paragraph, Results sections)
  - Numeric verification against manuscript text

All methods are pure: no file writes, no subprocess calls.
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

SUPPORTED_SCHEMA_MAJOR = "1"


# ── Custom Exceptions ──────────────────────────────────────────────────────────

class ManifestError(Exception):
    """Raised when hpw_manifest.json cannot be loaded or is invalid."""


class ManifestVersionError(ManifestError):
    """Raised when schema_version major version is incompatible."""


# ── Data Containers ────────────────────────────────────────────────────────────

@dataclass
class TableRef:
    id: str
    label: str          # "Table 1. Baseline characteristics"
    path: Path          # absolute path to .docx
    type: str           # "table1" | "efficacy" | "safety"
    source_script: str


@dataclass
class FigureRef:
    id: str
    label: str          # "Figure 1. Overall survival"
    path: Path          # absolute path to .eps
    type: str           # "km_os" | "km_pfs" | "forest_plot" | "swimmer" | "waterfall"
    source_script: str


@dataclass
class StatValue:
    value: Union[float, int]
    unit: Optional[str] = None          # "percent" | "patients" | "months"
    ci_lower: Optional[float] = None
    ci_upper: Optional[float] = None
    p_value: Optional[float] = None
    n_events: Optional[int] = None
    reference: Optional[str] = None


@dataclass
class VerificationIssue:
    text_fragment: str          # sentence containing the suspect number
    found_value: str            # numeric string found in text
    stat_key: Optional[str]     # matching key in key_statistics, or None
    expected_value: Optional[str]   # what key_statistics says
    severity: str               # "warning" | "error"
    message: str


# ── Internal lookup tables ────────────────────────────────────────────────────

# Per-disease canonical required statistics (design spec FR-02)
_REQUIRED_STATS: Dict[str, List[str]] = {
    "aml": ["n_total", "orr", "os_median_months", "ae_grade3plus_rate"],
    "cml": ["n_total", "mmr_12mo", "os_median_months", "ae_grade3plus_rate"],
    "mds": ["n_total", "orr", "os_median_months", "ae_grade3plus_rate"],
    "hct": ["n_total", "agvhd_grade2_4_rate", "os_median_months", "ae_grade3plus_rate"],
}

_ENRICHMENT_QUERIES: Dict[Tuple[str, str], str] = {
    # AML — ELN 2022
    ("aml", "eln_favorable_pct"):         "What defines ELN 2022 favorable risk in AML?",
    ("aml", "eln_intermediate_pct"):      "What defines ELN 2022 intermediate risk in AML?",
    ("aml", "eln_adverse_pct"):           "What defines ELN 2022 adverse risk in AML?",
    ("aml", "ccr_rate"):                  "What is composite complete response (cCR) per ELN 2022?",
    ("aml", "cr_rate"):                   "What is complete remission (CR) per ELN 2022 in AML?",
    ("aml", "cri_rate"):                  "What is CRi (CR with incomplete count recovery) per ELN 2022?",
    ("aml", "target_dlt_rate"):           "What is the target DLT rate in BOIN dose-finding?",
    ("aml", "orr"):                       "What is overall response rate definition in AML per ELN 2022?",
    # CML — ELN 2020
    ("cml", "mmr_12mo"):                  "What is major molecular response (MMR) per ELN 2020 in CML?",
    ("cml", "tfr_12mo"):                  "What is treatment-free remission (TFR) per ELN 2020 in CML?",
    ("cml", "tfr_24mo"):                  "What is the 24-month TFR milestone per ELN 2020 in CML?",
    ("cml", "sokal_high_pct"):            "How is Sokal high-risk score defined in CML?",
    # HCT — NIH 2014
    ("hct", "agvhd_grade2_4_rate"):       "How is grade 2-4 acute GVHD graded per NIH 2014 consensus?",
    ("hct", "agvhd_grade3_4_rate"):       "How is grade 3-4 acute GVHD defined per NIH 2014?",
    ("hct", "cgvhd_moderate_severe_rate"):"How is moderate-severe chronic GVHD defined per NIH 2014?",
    ("hct", "grfs_12mo"):                 "What is GVHD-free relapse-free survival (GRFS)?",
    # Cross-disease — CTCAE
    ("aml", "ae_grade3plus_rate"):        "How are CTCAE grade 3 or higher adverse events classified?",
    ("cml", "ae_grade3plus_rate"):        "How are CTCAE grade 3 or higher adverse events classified?",
    ("hct", "ae_grade3plus_rate"):        "How are CTCAE grade 3 or higher adverse events classified?",
    ("mds", "ae_grade3plus_rate"):        "How are CTCAE grade 3 or higher adverse events classified?",
}

_ABSTRACT_KEYS: Dict[str, List[str]] = {
    "aml": ["n_total", "ccr_rate", "orr", "eln_adverse_pct", "os_median_months",
            "os_hr", "ae_grade3plus_rate"],
    "cml": ["n_total", "mmr_rate", "mmr_12mo", "ccyr_rate", "tfr_12mo",
            "os_median_months", "ae_grade3plus_rate"],
    "mds": ["n_total", "orr", "hi_rate", "os_median_months", "ae_grade3plus_rate"],
    "hct": ["n_total", "engraftment_days_median", "agvhd_grade2_4_rate",
            "grfs_event_rate", "os_median_months", "ae_grade3plus_rate"],
}


# ── Main class ────────────────────────────────────────────────────────────────

class StatisticalBridge:
    """
    Reads hpw_manifest.json produced by CSA orchestrator.
    Provides typed access to statistical outputs and template-driven prose generation.
    All methods are pure (no file writes, no subprocess calls).
    """

    def __init__(self, manifest_path: Path) -> None:
        """Load and validate manifest. Raises ManifestError on schema mismatch."""
        self._manifest_path = Path(manifest_path)
        self._manifest_dir = self._manifest_path.parent
        self._data: Dict[str, Any] = {}
        self._loaded = False
        self._load()

    def _load(self) -> None:
        if not self._manifest_path.exists():
            raise ManifestError(f"hpw_manifest.json not found: {self._manifest_path}")
        try:
            with open(self._manifest_path, encoding="utf-8") as f:
                self._data = json.load(f)
        except json.JSONDecodeError as exc:
            raise ManifestError(f"Invalid JSON in manifest: {exc}") from exc

        version = self._data.get("schema_version", "0")
        major = str(version).split(".")[0]
        if major != SUPPORTED_SCHEMA_MAJOR:
            raise ManifestVersionError(
                f"Manifest schema version {version!r} is not compatible "
                f"(expected major version {SUPPORTED_SCHEMA_MAJOR}). "
                "Please re-run CSA with an updated orchestrator."
            )
        self._loaded = True

    # ── Alternative constructors ───────────────────────────────────────────────

    @classmethod
    def from_project(cls, phase_manager: Any) -> Optional[StatisticalBridge]:
        """
        Convenience constructor from PhaseManager.
        Returns None if csa_output_dir not set or hpw_manifest.json not found.
        """
        csa_dir = getattr(getattr(phase_manager, "metadata", None), "csa_output_dir", None)
        if csa_dir is None:
            return None
        manifest_path = Path(csa_dir) / "hpw_manifest.json"
        if not manifest_path.exists():
            logger.debug("hpw_manifest.json not found at %s", manifest_path)
            return None
        try:
            return cls(manifest_path)
        except ManifestError as exc:
            logger.warning("Could not load StatisticalBridge: %s", exc)
            return None

    @classmethod
    def from_env(cls) -> Optional[StatisticalBridge]:
        """
        Load from $CSA_OUTPUT_DIR/hpw_manifest.json.
        Returns None if env var not set or file not found.
        """
        csa_dir = os.environ.get("CSA_OUTPUT_DIR")
        if not csa_dir:
            return None
        manifest_path = Path(csa_dir) / "hpw_manifest.json"
        if not manifest_path.exists():
            return None
        try:
            return cls(manifest_path)
        except ManifestError as exc:
            logger.warning("Could not load StatisticalBridge from env: %s", exc)
            return None

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def is_available(self) -> bool:
        """True if manifest loaded successfully."""
        return self._loaded

    @property
    def disease(self) -> str:
        """Disease code: 'aml' | 'cml' | 'mds' | 'hct'"""
        return self._data.get("disease", "")

    @property
    def schema_version(self) -> str:
        return self._data.get("schema_version", "")

    @property
    def scripts_run(self) -> List[str]:
        return list(self._data.get("scripts_run", []))

    @property
    def r_version(self) -> str:
        return self._data.get("r_version", "")

    @property
    def r_packages(self) -> List[str]:
        return list(self._data.get("r_packages", []))

    @property
    def analysis_notes(self) -> Dict[str, str]:
        return dict(self._data.get("analysis_notes", {}))

    @property
    def study_context(self) -> Dict[str, str]:
        """Study metadata from manifest: study_name, protocol_id, trial_phase, sponsor, data_cutoff_date."""
        return dict(self._data.get("study_context", {}))

    @property
    def study_name(self) -> str:
        """Shortcut to study_context['study_name'], or empty string."""
        return self.study_context.get("study_name", "")

    @property
    def trial_phase(self) -> str:
        """Shortcut to study_context['trial_phase'], or empty string."""
        return self.study_context.get("trial_phase", "")

    # ── Reference access ──────────────────────────────────────────────────────

    def get_table_references(self) -> List[TableRef]:
        """All tables in order, with absolute paths resolved from manifest dir."""
        return [
            TableRef(
                id=t["id"],
                label=t["label"],
                path=self._manifest_dir / t["path"],
                type=t.get("type", ""),
                source_script=t.get("source_script", ""),
            )
            for t in self._data.get("tables", [])
        ]

    def get_figure_references(self) -> List[FigureRef]:
        """All figures in order, with absolute paths resolved from manifest dir."""
        return [
            FigureRef(
                id=f["id"],
                label=f["label"],
                path=self._manifest_dir / f["path"],
                type=f.get("type", ""),
                source_script=f.get("source_script", ""),
            )
            for f in self._data.get("figures", [])
        ]

    def _get_ds_stat(self, ds: str, key: str) -> Optional[StatValue]:
        """Get a stat from disease_specific[ds][key], or None if absent.

        Supports manifests that store disease-specific stats in a sub-dict.
        Falls back to key_statistics[key] for backwards compatibility.
        """
        ds_data = self._data.get("disease_specific", {})
        raw = ds_data.get(ds, {}).get(key)
        if raw is not None:
            if isinstance(raw, (int, float)):
                return StatValue(value=raw)
            return StatValue(
                value=raw.get("value"),
                unit=raw.get("unit"),
                ci_lower=raw.get("ci_lower"),
                ci_upper=raw.get("ci_upper"),
                p_value=raw.get("p_value"),
            )
        # Fall back to key_statistics
        return self.get_stat(key)

    def validate_stats_completeness(self) -> List[str]:
        """Return list of required stat keys missing for this disease.

        Uses _REQUIRED_STATS schema (design spec FR-02).
        Returns empty list if disease unknown or all required keys present.
        """
        required = _REQUIRED_STATS.get(self.disease, [])
        return [k for k in required if self.get_stat(k) is None]

    def get_stat(self, key: str) -> Optional[StatValue]:
        """Get a specific statistic by key_statistics key. Returns None if absent."""
        raw = self._data.get("key_statistics", {}).get(key)
        if raw is None:
            return None
        if isinstance(raw, (int, float)):
            return StatValue(value=raw)
        return StatValue(
            value=raw.get("value"),
            unit=raw.get("unit"),
            ci_lower=raw.get("ci_lower"),
            ci_upper=raw.get("ci_upper"),
            p_value=raw.get("p_value"),
            n_events=raw.get("n_events"),
            reference=raw.get("reference"),
        )

    # ── Formatting helpers ────────────────────────────────────────────────────

    def format_stat(self, key: str, fmt: str = "standard") -> str:
        """
        Format a stat as a string ready for manuscript insertion.
        fmt='standard': '67.3% (95% CI 54.1–78.7%; p = 0.001)'
        fmt='short':    '67.3% (54.1–78.7%)'
        fmt='hr':       'HR 0.62 (95% CI 0.41–0.94; p = 0.024)'
        """
        sv = self.get_stat(key)
        if sv is None:
            return "[DATA UNAVAILABLE]"

        is_pct = sv.unit == "percent"
        val_str = f"{sv.value:.1f}%" if is_pct else str(sv.value)

        if fmt == "hr":
            s = f"HR {sv.value}"
            if sv.ci_lower is not None and sv.ci_upper is not None:
                s += f" (95% CI {sv.ci_lower}–{sv.ci_upper}"
                if sv.p_value is not None:
                    s += f"; p = {sv.p_value}"
                s += ")"
            return s

        if fmt == "short":
            if sv.ci_lower is not None and sv.ci_upper is not None:
                ci_l = f"{sv.ci_lower:.1f}%" if is_pct else str(sv.ci_lower)
                ci_u = f"{sv.ci_upper:.1f}%" if is_pct else str(sv.ci_upper)
                return f"{val_str} ({ci_l}–{ci_u})"
            return val_str

        # "standard"
        parts = []
        if sv.ci_lower is not None and sv.ci_upper is not None:
            ci_l = f"{sv.ci_lower:.1f}%" if is_pct else str(sv.ci_lower)
            ci_u = f"{sv.ci_upper:.1f}%" if is_pct else str(sv.ci_upper)
            parts.append(f"95% CI {ci_l}–{ci_u}")
        if sv.p_value is not None:
            parts.append(f"p = {sv.p_value}")
        if sv.n_events is not None:
            n_total_sv = self.get_stat("n_total")
            if n_total_sv is not None:
                parts.append(f"n = {sv.n_events}/{int(n_total_sv.value)}")
            else:
                parts.append(f"n = {sv.n_events}")
        if parts:
            return f"{val_str} ({'; '.join(parts)})"
        return val_str

    def _fmt_opt(self, key: str, fmt: str = "short") -> str:
        """Like format_stat but returns empty string (not '[DATA UNAVAILABLE]') when absent."""
        if self.get_stat(key) is None:
            return ""
        return self.format_stat(key, fmt)

    # ── NLM enrichment ────────────────────────────────────────────────────────

    def _load_nlm_config(self) -> Optional[Dict[str, str]]:
        """
        Read notebooklm_config.json from the HPW root directory (next to cli.py).
        Returns dict with 'base_url' and 'notebook_id', or None if absent/invalid.
        Result is cached on the instance so the file is read at most once.
        """
        if hasattr(self, "_nlm_config"):
            return self._nlm_config  # type: ignore[return-value]

        config_path = Path(__file__).parent.parent / "notebooklm_config.json"
        try:
            with open(config_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if "base_url" in data and "notebook_id" in data:
                self._nlm_config: Optional[Dict[str, str]] = data
            else:
                self._nlm_config = None
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            self._nlm_config = None

        return self._nlm_config

    @staticmethod
    def _extract_parenthetical(answer: str) -> str:
        """
        Convert a free-text NLM answer into a ≤80-char parenthetical string.

        Algorithm:
        1. Take the first sentence (up to the first '.', '?', or '!').
        2. Strip leading articles ('A ', 'An ', 'The ').
        3. Truncate at the last complete word that keeps length ≤ 80 chars.
        4. Return empty string if the result is blank.
        """
        if not answer:
            return ""

        # First sentence only — match ". " or ".\n" or end of string to avoid
        # splitting on decimal points like "0.1" or abbreviations like "ELN 2022".
        m = re.search(r"[.!?](?:\s|$)", answer)
        if m:
            answer = answer[: m.start()]

        answer = answer.strip()

        # Strip leading articles
        for article in ("The ", "An ", "A "):
            if answer.startswith(article):
                answer = answer[len(article):]
                break

        answer = answer.strip()
        if not answer:
            return ""

        # Truncate at ≤80-char word boundary
        if len(answer) <= 80:
            return answer

        truncated = answer[:80]
        last_space = truncated.rfind(" ")
        if last_space > 0:
            truncated = truncated[:last_space]
        return truncated.rstrip(",:;")

    def _enrich_with_nlm(self, disease: str, stat_key: str) -> str:
        """
        Query open-notebook for a guideline parenthetical for (disease, stat_key).

        Returns a ≤80-char string suitable for insertion as a parenthetical, e.g.
        "(ELN 2022 favorable: NPM1mut without FLT3-ITD, t(8;21), ...)".
        Returns '' on any error (missing config, network failure, unexpected response).
        This method is intentionally silent — callers must not depend on its output.
        """
        query = _ENRICHMENT_QUERIES.get((disease.lower(), stat_key))
        if not query:
            return ""

        cfg = self._load_nlm_config()
        if not cfg:
            return ""

        try:
            from tools.notebooklm_integration import NotebookLMIntegration  # noqa: PLC0415

            nlm = NotebookLMIntegration(base_url=cfg["base_url"])
            answer = nlm.ask(query, notebook_id=cfg["notebook_id"], timeout=5)
            return self._extract_parenthetical(answer)
        except Exception:  # noqa: BLE001
            return ""

    # ── Prose generation ──────────────────────────────────────────────────────

    def generate_methods_paragraph(self) -> str:
        """
        Returns publication-ready 'Statistical Analysis' paragraph for Methods section.
        Template-driven from scripts_run, r_packages, r_version, analysis_notes.
        """
        scripts = set(self.scripts_run)
        packages = set(self.r_packages)
        notes = self.analysis_notes

        sentences = [
            f"Statistical analyses were performed using R version {self.r_version} "
            "(R Foundation for Statistical Computing, Vienna, Austria)."
        ]

        if "02_table1.R" in scripts:
            sentences.append(
                "Baseline characteristics were summarized using descriptive statistics; "
                "continuous variables are reported as medians with interquartile ranges, "
                "and categorical variables as counts with percentages."
            )

        if "04_survival.R" in scripts or "survival" in packages:
            sentences.append(
                "Survival outcomes were estimated using the Kaplan–Meier method, "
                "and differences between groups were compared using the log-rank test."
            )
            survival_model = notes.get("survival_model", "")
            if "cox" in survival_model.lower() or "survival" in packages:
                sentences.append(
                    "Multivariable analyses were performed using Cox proportional hazards "
                    "regression; the proportional hazards assumption was verified using "
                    "Schoenfeld residuals (cox.zph)."
                )

        if "cmprsk" in packages or "competing_risks" in notes or "07_competing_risks.R" in scripts:
            cr_note = notes.get("competing_risks", "")
            if "Fine" in cr_note or "Gray" in cr_note or "cmprsk" in packages:
                sentences.append(
                    "Cumulative incidences in the presence of competing risks were estimated "
                    "using the Fine–Gray subdistribution hazard model."
                )

        if "03_efficacy.R" in scripts or "06_response.R" in scripts:
            sentences.append(
                "Response rates are reported with 95% confidence intervals calculated "
                "using the Wilson score method."
            )

        multiple_testing = notes.get("multiple_testing", "")
        if multiple_testing:
            sentences.append(multiple_testing.rstrip(".") + ".")
        else:
            sentences.append(
                "All statistical tests were two-sided; a p-value of less than 0.05 "
                "was considered statistically significant."
            )

        return " ".join(sentences)

    def generate_results_prose(self) -> Dict[str, str]:
        """
        Returns prose dict keyed by section.
        Only sections with available scripts_run data are populated.
        Keys: 'baseline' | 'efficacy' | 'survival' | 'safety'
        """
        scripts = set(self.scripts_run)
        prose: Dict[str, str] = {}

        # Baseline
        if "02_table1.R" in scripts:
            n = self.get_stat("n_total")
            n_str = str(int(n.value)) if n else "[N]"
            fu = self.get_stat("follow_up_median_months")
            fu_str = self.format_stat("follow_up_median_months", "short") if fu else "[FOLLOW-UP]"
            tables = self.get_table_references()
            t1_label = next(
                (t.label for t in tables if t.type == "table1"),
                "Table 1"
            )
            prose["baseline"] = (
                f"A total of {n_str} patients were included in this analysis "
                f"({t1_label}). The median follow-up was {fu_str} months."
            )

        # Efficacy
        if "03_efficacy.R" in scripts or "06_response.R" in scripts:
            parts = []
            orr = self.get_stat("orr")
            cr = self.get_stat("cr_rate")
            if orr:
                parts.append(
                    f"The overall response rate (ORR) was {self.format_stat('orr')} (Table 2)."
                )
            if cr:
                parts.append(
                    f"The complete response (CR) rate was {self.format_stat('cr_rate')}."
                )
            if parts:
                prose["efficacy"] = " ".join(parts)

        # Survival
        if "04_survival.R" in scripts:
            parts = []
            os_med = self.get_stat("os_median_months")
            os_hr = self.get_stat("os_hr")
            pfs = self.get_stat("pfs_median_months")
            if os_med:
                parts.append(
                    f"The median overall survival (OS) was "
                    f"{self.format_stat('os_median_months', 'short')} months."
                )
            if os_hr:
                parts.append(
                    f"Treatment was associated with a significant improvement in OS "
                    f"({self.format_stat('os_hr', 'hr')}) (Figure 1)."
                )
            if pfs:
                parts.append(
                    f"Median progression-free survival (PFS) was "
                    f"{self.format_stat('pfs_median_months', 'short')} months."
                )
            if parts:
                prose["survival"] = " ".join(parts)

        # Safety
        if "05_safety.R" in scripts:
            parts = []
            ae = self.get_stat("ae_grade3plus_rate")
            dc = self.get_stat("discontinuation_rate")
            if ae:
                ae_enrich = self._enrich_with_nlm(self.disease, "ae_grade3plus_rate")
                ae_paren = f" ({ae_enrich})" if ae_enrich else ""
                parts.append(
                    f"Grade 3 or higher adverse events occurred in "
                    f"{self.format_stat('ae_grade3plus_rate', 'short')} of patients{ae_paren}."
                )
            if dc:
                parts.append(
                    f"Treatment discontinuation due to adverse events occurred in "
                    f"{self.format_stat('discontinuation_rate', 'short')} of patients."
                )
            if parts:
                prose["safety"] = " ".join(parts)

        # AML – disease-specific
        if self.disease == "aml":
            aml_parts = []
            if "20_aml_eln_risk.R" in scripts:
                fav = self._fmt_opt("eln_favorable_pct", "short")
                interm = self._fmt_opt("eln_intermediate_pct", "short")
                adv = self._fmt_opt("eln_adverse_pct", "short")
                risk_items = []
                if fav:
                    risk_items.append(f"favorable-risk {fav}")
                if interm:
                    risk_items.append(f"intermediate-risk {interm}")
                if adv:
                    risk_items.append(f"adverse-risk {adv}")
                if risk_items:
                    eln_enrich = self._enrich_with_nlm("aml", "eln_favorable_pct")
                    eln_paren = f" ({eln_enrich})" if eln_enrich else ""
                    aml_parts.append(
                        "By ELN 2022 risk classification, patients were distributed as "
                        + ", ".join(risk_items) + eln_paren + "."
                    )
            if "21_aml_composite_response.R" in scripts:
                ccr = self._fmt_opt("ccr_rate", "standard")
                if ccr:
                    ccr_enrich = self._enrich_with_nlm("aml", "ccr_rate")
                    ccr_paren = f" ({ccr_enrich})" if ccr_enrich else ""
                    aml_parts.append(
                        f"The composite complete response (cCR) rate was {ccr}{ccr_paren}."
                    )
            if "25_aml_phase1_boin.R" in scripts:
                lam_e = self.get_stat("lambda_e")
                lam_d = self.get_stat("lambda_d")
                target_dlt = self._fmt_opt("target_dlt_rate", "short")
                if lam_e and lam_d and target_dlt:
                    dlt_enrich = self._enrich_with_nlm("aml", "target_dlt_rate")
                    dlt_note = f"; {dlt_enrich}" if dlt_enrich else ""
                    aml_parts.append(
                        f"Dose escalation was guided by the BOIN design "
                        f"(target DLT rate {target_dlt}; "
                        f"\u03bbe = {lam_e.value}, \u03bbd = {lam_d.value}{dlt_note})."
                    )
            # Split into per-script granular keys matching design spec
            eln_parts = []
            ccr_parts = []
            boin_parts = []
            for part in aml_parts:
                if "ELN 2022" in part:
                    eln_parts.append(part)
                elif "cCR" in part or "composite" in part:
                    ccr_parts.append(part)
                elif "BOIN" in part:
                    boin_parts.append(part)
                else:
                    eln_parts.append(part)  # fallback
            if eln_parts:
                prose["aml_eln_risk"] = " ".join(eln_parts)
            if ccr_parts:
                prose["aml_composite_response"] = " ".join(ccr_parts)
            if boin_parts:
                prose["aml_composite_response"] = (
                    prose.get("aml_composite_response", "") + " " + " ".join(boin_parts)
                ).strip()

        # CML – disease-specific (granular keys per design spec)
        if self.disease == "cml":
            if "22_cml_tfr_analysis.R" in scripts:
                mmr12 = self._fmt_opt("mmr_12mo", "short")
                tfr12 = self._fmt_opt("tfr_12mo", "short")
                tfr24 = self._fmt_opt("tfr_24mo", "short")
                mol_parts = []
                tfr_parts = []
                if mmr12:
                    mmr_enrich = self._enrich_with_nlm("cml", "mmr_12mo")
                    mmr_paren = f" ({mmr_enrich})" if mmr_enrich else ""
                    mol_parts.append(
                        f"The major molecular response (MMR) rate at 12 months was {mmr12}{mmr_paren}."
                    )
                if tfr12 and tfr24:
                    tfr_enrich = self._enrich_with_nlm("cml", "tfr_12mo")
                    tfr_paren = f" ({tfr_enrich})" if tfr_enrich else ""
                    tfr_parts.append(
                        f"Treatment-free remission (TFR) rates at 12 and 24 months were "
                        f"{tfr12} and {tfr24}, respectively{tfr_paren}."
                    )
                elif tfr12:
                    tfr_enrich = self._enrich_with_nlm("cml", "tfr_12mo")
                    tfr_paren = f" ({tfr_enrich})" if tfr_enrich else ""
                    tfr_parts.append(
                        f"The treatment-free remission (TFR) rate at 12 months was {tfr12}{tfr_paren}."
                    )
                if mol_parts:
                    prose["cml_molecular"] = " ".join(mol_parts)
                if tfr_parts:
                    prose["cml_tfr"] = " ".join(tfr_parts)
            if "23_cml_scores.R" in scripts:
                sokal_high = self._fmt_opt("sokal_high_pct", "short")
                if sokal_high:
                    prose["cml_scores"] = (
                        f"By Sokal score, high-risk patients comprised {sokal_high} of the cohort."
                    )

        # HCT – disease-specific (granular key per design spec)
        if self.disease == "hct":
            hct_parts = []
            if "24_hct_gvhd_analysis.R" in scripts:
                agvhd_24 = self._fmt_opt("agvhd_grade2_4_rate", "short")
                cgvhd = self._fmt_opt("cgvhd_any_rate", "short")
                grfs = self._fmt_opt("grfs_event_rate", "short")
                engraft = self._fmt_opt("neutrophil_engraftment_rate", "short")
                engraft_days = self._fmt_opt("median_neutrophil_engraftment_days", "short")
                if agvhd_24:
                    agvhd_enrich = self._enrich_with_nlm("hct", "agvhd_grade2_4_rate")
                    agvhd_paren = f" ({agvhd_enrich})" if agvhd_enrich else ""
                    hct_parts.append(
                        f"The cumulative incidence of grade II–IV acute GVHD was {agvhd_24}{agvhd_paren}."
                    )
                if cgvhd:
                    cgvhd_enrich = self._enrich_with_nlm("hct", "cgvhd_moderate_severe_rate")
                    cgvhd_paren = f" ({cgvhd_enrich})" if cgvhd_enrich else ""
                    hct_parts.append(
                        f"Chronic GVHD of any grade occurred in {cgvhd} of patients{cgvhd_paren}."
                    )
                if grfs:
                    grfs_enrich = self._enrich_with_nlm("hct", "grfs_12mo")
                    grfs_paren = f" ({grfs_enrich})" if grfs_enrich else ""
                    hct_parts.append(
                        f"The GVHD-relapse-free survival (GRFS) event rate was {grfs}{grfs_paren}."
                    )
                if engraft and engraft_days:
                    hct_parts.append(
                        f"Neutrophil engraftment was achieved in {engraft} of patients "
                        f"at a median of {engraft_days} days."
                    )
            if hct_parts:
                prose["hct_gvhd"] = " ".join(hct_parts)

        return prose

    def get_abstract_statistics(self) -> Dict[str, Any]:
        """
        Returns the 3–5 highest-priority stats for Abstract injection.
        Priority: n_total, primary endpoint (orr/mmr/hi), os_median, os_hr, ae_grade3plus.
        Returns dict of StatValue objects keyed by stat name.
        """
        keys = _ABSTRACT_KEYS.get(
            self.disease,
            ["n_total", "os_median_months", "ae_grade3plus_rate"],
        )
        return {k: sv for k in keys if (sv := self.get_stat(k)) is not None}

    # ── Verification ──────────────────────────────────────────────────────────

    def verify_manuscript_statistics(
        self,
        text: str,
        strictness: str = "warn",
        scope: Optional[List[str]] = None,
    ) -> List[VerificationIssue]:
        """
        Regex-extracts all percentages, decimals, and integers from text.
        Cross-references against key_statistics values (±0.1 tolerance for rounding).
        Returns list of VerificationIssues; empty if all verified or strictness='off'.
        """
        if strictness == "off":
            return []

        key_stats = self._data.get("key_statistics", {})
        value_lookup: Dict[float, str] = {}
        for k, v in key_stats.items():
            if isinstance(v, (int, float)):
                value_lookup[float(v)] = k
            elif isinstance(v, dict) and "value" in v:
                value_lookup[float(v["value"])] = k

        issues: List[VerificationIssue] = []
        number_pattern = re.compile(r"\b(\d+\.?\d*)\s*%?")
        sentences = re.split(r"(?<=[.!?])\s+", text)

        for sentence in sentences:
            for match in number_pattern.finditer(sentence):
                found_str = match.group(1)
                try:
                    found_val = float(found_str)
                except ValueError:
                    continue
                if found_val < 1:
                    continue  # Skip tiny fractions unlikely to be clinical stats

                closest_key: Optional[str] = None
                closest_diff = float("inf")
                for expected_val, stat_key in value_lookup.items():
                    diff = abs(found_val - expected_val)
                    if diff < closest_diff:
                        closest_diff = diff
                        closest_key = stat_key

                if closest_key and 0.1 < closest_diff <= 1.0:
                    sv = self.get_stat(closest_key)
                    issues.append(VerificationIssue(
                        text_fragment=sentence[:120],
                        found_value=found_str,
                        stat_key=closest_key,
                        expected_value=str(sv.value) if sv else None,
                        severity="warning" if strictness == "warn" else "error",
                        message=(
                            f"Value {found_str!r} differs from "
                            f"{closest_key}={sv.value!r} by {closest_diff:.2f}; "
                            "possible rounding discrepancy."
                        ),
                    ))

        return issues
