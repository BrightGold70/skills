"""
ProtocolConsistencyChecker — Tier 2 CSA Scientific Skill (Post-analysis)

Validates that R output key_statistics cover all primary and secondary
endpoints defined in the parsed protocol spec. Reports gaps as plain-text
warnings for investigator review.

Maps to: scientific-critical-thinking OpenCode skill
CSA Hook: integrate_skills_post_analysis()
"""

from __future__ import annotations

import json
from pathlib import Path

from ._base import CSASkillBase, CSASkillContext

# Canonical stat_key mappings for common endpoint strings
# Maps endpoint name fragment (lower) → expected key_statistics key
_ENDPOINT_TO_STAT_KEY: dict[str, str] = {
    "overall survival":             "os_median_months",
    "os":                           "os_median_months",
    "event-free survival":          "efs_median_months",
    "efs":                          "efs_median_months",
    "progression-free survival":    "pfs_median_months",
    "pfs":                          "pfs_median_months",
    "complete remission":           "cr_rate",
    "cr rate":                      "cr_rate",
    "composite cr":                 "ccr_rate",
    "ccr":                          "ccr_rate",
    "overall response rate":        "orr",
    "orr":                          "orr",
    "mmr":                          "mmr_12mo",
    "mmr at 12":                    "mmr_12mo",
    "tfr":                          "tfr_12mo",
    "treatment-free remission":     "tfr_12mo",
    "haematological improvement":   "hi_rate",
    "hi rate":                      "hi_rate",
    "acute gvhd":                   "agvhd_grade2_4_rate",
    "agvhd":                        "agvhd_grade2_4_rate",
    "chronic gvhd":                 "cgvhd_moderate_severe_rate",
    "cgvhd":                        "cgvhd_moderate_severe_rate",
    "grfs":                         "grfs_12mo",
    "adverse events":               "ae_grade3plus_rate",
    "grade 3":                      "ae_grade3plus_rate",
    "sample size":                  "n_total",
    "n total":                      "n_total",
    "dlt":                          "target_dlt_rate",
    "dose-limiting":                "target_dlt_rate",
    "eln risk":                     "eln_favorable_pct",
    "risk stratification":          "eln_favorable_pct",
    "sokal":                        "sokal_high_pct",
}


class ProtocolConsistencyChecker(CSASkillBase):
    """
    Checks that protocol-defined endpoints are represented in key_statistics.
    Writes gaps to context.protocol_gaps.
    """

    def invoke(self, prompt: str, **kwargs) -> str:
        try:
            return f"[ProtocolConsistencyChecker] {prompt[:200]}"
        except Exception:
            return ""

    def check(self, output_dir: Path | None = None, protocol_spec: dict | None = None) -> list:
        """
        Compare protocol endpoints against context.key_statistics keys.

        Protocol spec is loaded from {output_dir}/data/protocol_spec.json if not
        provided directly. Falls back gracefully if file is absent.

        Args:
            output_dir: CSA output directory (to locate protocol_spec.json)
            protocol_spec: Parsed protocol dict with "primary_endpoints" and
                           "secondary_endpoints" keys (list[str] each)

        Returns:
            list[str]: Gap descriptions. Writes to context.protocol_gaps.
        """
        try:
            spec = protocol_spec or self._load_protocol_spec(output_dir)
            if not spec:
                self._log.info(
                    "ProtocolConsistencyChecker: no protocol spec found — skipping"
                )
                return []

            present_keys = set(self.context.key_statistics.keys())
            gaps: list[str] = []

            all_endpoints = (
                spec.get("primary_endpoints", []) + spec.get("secondary_endpoints", [])
            )

            for ep in all_endpoints:
                ep_lower = ep.lower().strip()
                matched_key = self._find_stat_key(ep_lower)

                if matched_key is None:
                    gaps.append(
                        f"Protocol endpoint '{ep}' has no known key_statistics mapping — "
                        "verify R script coverage or add custom extraction rule."
                    )
                elif matched_key not in present_keys:
                    gaps.append(
                        f"Protocol endpoint '{ep}' maps to key '{matched_key}' "
                        "but it is absent from key_statistics — "
                        "check if the corresponding R script ran successfully."
                    )

            self.context.protocol_gaps = gaps
            self._log.info(
                "ProtocolConsistencyChecker: %d gaps found in %d endpoints",
                len(gaps), len(all_endpoints)
            )
            return gaps

        except Exception as exc:
            self._log.warning("ProtocolConsistencyChecker.check failed: %s", exc)
            return []

    def _find_stat_key(self, ep_lower: str) -> str | None:
        """Match endpoint string to a stat key. Returns None if unmatched."""
        for fragment, key in _ENDPOINT_TO_STAT_KEY.items():
            if fragment in ep_lower:
                return key
        return None

    def _load_protocol_spec(self, output_dir: Path | None) -> dict:
        """Load protocol_spec.json from data/ dir. Returns {} if not found."""
        if output_dir is None:
            return {}
        try:
            spec_path = Path(output_dir) / "data" / "protocol_spec.json"
            if spec_path.exists():
                return json.loads(spec_path.read_text(encoding="utf-8"))
        except Exception as exc:
            self._log.debug("Could not load protocol_spec.json: %s", exc)
        return {}
