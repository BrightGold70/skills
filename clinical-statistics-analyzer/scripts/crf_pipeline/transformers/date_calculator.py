"""Date calculator: computes time-to-event variables from date pairs."""

import logging
from typing import Any, Dict, Optional

import pandas as pd

from .base import AbstractTransformer

logger = logging.getLogger(__name__)

# Common date formats to try when parsing
DATE_FORMATS = [
    "%Y-%m-%d",       # ISO 8601
    "%d/%m/%Y",       # DD/MM/YYYY
    "%m/%d/%Y",       # MM/DD/YYYY
    "%Y/%m/%d",       # YYYY/MM/DD
    "%d-%m-%Y",       # DD-MM-YYYY
    "%m-%d-%Y",       # MM-DD-YYYY
    "%Y.%m.%d",       # YYYY.MM.DD
    "%d.%m.%Y",       # DD.MM.YYYY
]


def _parse_dates(series: pd.Series) -> pd.Series:
    """Parse a Series to datetime, trying multiple formats.

    First tries pandas' built-in parser (handles ISO and many formats).
    Falls back to trying explicit formats for ambiguous dates.
    """
    # Fast path: already datetime
    if pd.api.types.is_datetime64_any_dtype(series):
        return series

    # Try pandas infer_datetime_format first
    try:
        return pd.to_datetime(series, errors="coerce", dayfirst=False)
    except Exception:
        pass

    # Try each format explicitly
    for fmt in DATE_FORMATS:
        try:
            parsed = pd.to_datetime(series, format=fmt, errors="coerce")
            if parsed.notna().sum() > 0:
                return parsed
        except Exception:
            continue

    return pd.to_datetime(series, errors="coerce")


def _date_diff_months(
    df: pd.DataFrame,
    from_col: str,
    to_col: str,
    censor_col: Optional[str] = None,
) -> pd.Series:
    """Compute time difference in months between two date columns.

    For censored observations (where ``to_col`` is missing), uses ``censor_col``
    as the end date instead.

    Returns:
        Series of float values representing months (days / 30.4375).
    """
    start = _parse_dates(df[from_col])
    end = _parse_dates(df[to_col])

    # Fill missing end dates with censor date
    if censor_col and censor_col in df.columns:
        censor = _parse_dates(df[censor_col])
        end = end.fillna(censor)

    diff_days = (end - start).dt.days
    # Convert to months (average month = 365.25/12 = 30.4375 days)
    return (diff_days / 30.4375).round(2)


class DateCalculator(AbstractTransformer):
    """Compute time-to-event columns from date pairs.

    Processes ``derived_columns`` entries with ``type: "date_diff_months"``.

    Config example::

        "derived_columns": {
            "OS_months": {
                "type": "date_diff_months",
                "from": "induction_date",
                "to": "date_death",
                "censor": "date_last_fu"
            }
        }
    """

    def transform(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        derived = config.get("derived_columns", {})
        if not derived:
            return df

        for col_name, spec in derived.items():
            if spec.get("type") != "date_diff_months":
                continue

            from_col = spec["from"]
            to_col = spec["to"]
            censor_col = spec.get("censor")

            # Check required columns exist
            if from_col not in df.columns:
                logger.warning(
                    "date_diff_months: source column '%s' not found for '%s'",
                    from_col, col_name,
                )
                continue
            if to_col not in df.columns and (
                not censor_col or censor_col not in df.columns
            ):
                logger.warning(
                    "date_diff_months: neither '%s' nor censor '%s' found for '%s'",
                    to_col, censor_col, col_name,
                )
                continue

            # Ensure to_col exists (may be all NaN if no deaths)
            if to_col not in df.columns:
                df[to_col] = pd.NaT

            df[col_name] = _date_diff_months(df, from_col, to_col, censor_col)
            valid_count = df[col_name].notna().sum()
            logger.info(
                "Derived '%s' from '%s' → '%s' (censor='%s'): %d/%d valid",
                col_name, from_col, to_col, censor_col, valid_count, len(df),
            )

        return df
