"""Value recoder: remap categorical values and bin numeric columns."""

import logging
from typing import Any, Dict

import numpy as np
import pandas as pd

from .base import AbstractTransformer

logger = logging.getLogger(__name__)


class ValueRecoder(AbstractTransformer):
    """Recode categorical values and bin numeric columns.

    Processes ``derived_columns`` entries with types:
    - ``recode``: Map values using an explicit mapping dict.
    - ``bin``: Bin a numeric column into labeled categories.

    Config examples::

        "derived_columns": {
            "OS_status": {
                "type": "recode",
                "source": "alive",
                "mapping": {"1": 0, "2": 1}
            },
            "Age_group": {
                "type": "bin",
                "source": "age",
                "bins": [0, 60, 200],
                "labels": ["<60", ">=60"]
            }
        }
    """

    # Keywords that indicate the "positive" label for binary outcome coding (1)
    POSITIVE_KEYWORDS = frozenset({
        "CR", "cCR", "ORR", "Yes", "Positive", "Male",
        "CHR", "CCyR", "MMR", "DMR", "MR4", "MR4.5", "MR5",
        "Achieved", "Response", "CRi", "CRh", "MLFS",
    })

    def transform(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        derived = config.get("derived_columns", {})
        for col_name, spec in derived.items():
            col_type = spec.get("type")
            if col_type == "recode":
                df = self._recode(df, col_name, spec)
            elif col_type == "bin":
                df = self._bin(df, col_name, spec)

        # Apply SPSS value labels with dual-column output for binary outcomes
        df = self._apply_spss_labels(df, config)

        return df

    def _apply_spss_labels(
        self, df: pd.DataFrame, config: Dict[str, Any]
    ) -> pd.DataFrame:
        """Apply SPSS value labels and create ``_numeric`` columns for binary outcomes.

        For each entry in ``spss_value_mapping``:
        1. Replace numeric codes with human-readable labels in-place.
        2. If the column has exactly 2 distinct labels (e.g. CR/Non-CR),
           also create a ``{col}_numeric`` column with positive=1 / negative=0.
        """
        spss_map = config.get("spss_value_mapping", {})
        column_mapping = config.get("column_mapping", {})

        if not spss_map:
            return df

        for crf_var, mapping in spss_map.items():
            # Find the target column (could be original CRF name or already mapped R name)
            r_col = column_mapping.get(crf_var, crf_var)
            if r_col in df.columns:
                target = r_col
            elif crf_var in df.columns:
                target = crf_var
            else:
                continue

            # Build numeric-key → label mapping (only entries where key is a number).
            # Normalise keys so both "1" and "1.0" formats match stringified values.
            num_to_label: Dict[str, str] = {}
            canonical_labels: set = set()  # one entry per original mapping pair
            for k, v in mapping.items():
                if isinstance(v, str):
                    try:
                        fval = float(k)
                        num_to_label[k] = v
                        canonical_labels.add(v)
                        # Also add int-style and float-style keys for robustness
                        if fval == int(fval):
                            num_to_label[str(int(fval))] = v
                            num_to_label[f"{fval}"] = v
                    except (ValueError, TypeError):
                        pass

            if not num_to_label:
                continue

            # Apply labels: map stringified values to labels
            original = df[target].copy()
            df[target] = (
                df[target]
                .astype(str)
                .map(num_to_label)
                .fillna(original.astype(str))
            )
            df[target] = df[target].replace("nan", pd.NA)

            # For binary outcomes, create a _numeric column (positive=1, negative=0).
            # Use canonical_labels (all distinct labels) to decide — do NOT
            # strip "Unknown" before counting, so 3-category vars stay non-binary.
            canonical_labels.discard(None)
            if len(canonical_labels) == 2:
                positive_label = None
                for lbl in canonical_labels:
                    if lbl in self.POSITIVE_KEYWORDS:
                        positive_label = lbl
                        break

                # Fallback: treat SPSS code "1.0" / "1" value as positive
                if positive_label is None:
                    positive_label = num_to_label.get("1.0") or num_to_label.get("1")

                if positive_label:
                    # Use the R-mapped column name for the _numeric column
                    r_name = column_mapping.get(crf_var, target)
                    numeric_col = f"{r_name}_numeric"
                    df[numeric_col] = (df[target] == positive_label).astype(float)
                    df.loc[
                        df[target].isna() | (df[target] == "Unknown"),
                        numeric_col,
                    ] = float("nan")
                    logger.info(
                        "Created binary numeric column '%s' (positive='%s')",
                        numeric_col,
                        positive_label,
                    )

            mapped_count = df[target].notna().sum()
            logger.info(
                "Applied SPSS labels to '%s': %d/%d values mapped",
                target, mapped_count, len(df),
            )

        return df

    def _recode(
        self, df: pd.DataFrame, col_name: str, spec: Dict[str, Any]
    ) -> pd.DataFrame:
        """Remap values using an explicit mapping dict."""
        source = spec["source"]
        mapping = spec["mapping"]

        if source not in df.columns:
            logger.warning("recode: source column '%s' not found for '%s'", source, col_name)
            return df

        # Build mapping with both string and numeric key variants
        full_mapping = {}
        for k, v in mapping.items():
            full_mapping[k] = v
            # Also map numeric versions if key is a digit string
            try:
                full_mapping[int(k)] = v
            except (ValueError, TypeError):
                pass
            try:
                full_mapping[float(k)] = v
            except (ValueError, TypeError):
                pass

        df[col_name] = df[source].map(full_mapping)
        mapped_count = df[col_name].notna().sum()
        logger.info(
            "Recoded '%s' → '%s': %d/%d values mapped",
            source, col_name, mapped_count, len(df),
        )
        return df

    def _bin(
        self, df: pd.DataFrame, col_name: str, spec: Dict[str, Any]
    ) -> pd.DataFrame:
        """Bin a numeric column into labeled categories."""
        source = spec["source"]
        bins = spec["bins"]
        labels = spec["labels"]

        if source not in df.columns:
            logger.warning("bin: source column '%s' not found for '%s'", source, col_name)
            return df

        numeric_col = pd.to_numeric(df[source], errors="coerce")
        df[col_name] = pd.cut(
            numeric_col,
            bins=bins,
            labels=labels,
            right=False,
            include_lowest=True,
        )
        valid_count = df[col_name].notna().sum()
        logger.info(
            "Binned '%s' → '%s' with %d bins: %d/%d valid",
            source, col_name, len(labels), valid_count, len(df),
        )
        return df
