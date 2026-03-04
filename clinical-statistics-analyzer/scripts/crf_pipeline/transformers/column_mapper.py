"""Column name mapper: renames CRF variables to R-expected column names."""

import logging
from typing import Any, Dict

import pandas as pd

from .base import AbstractTransformer

logger = logging.getLogger(__name__)


class ColumnMapper(AbstractTransformer):
    """Rename DataFrame columns from CRF variable names to R-expected names.

    Reads the ``column_mapping`` dict from config and applies ``df.rename()``.
    Columns not in the mapping are left unchanged.
    """

    def transform(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        mapping = config.get("column_mapping", {})
        if not mapping:
            logger.debug("No column_mapping in config; skipping rename")
            return df

        # Only rename columns that actually exist in the DataFrame
        applicable = {k: v for k, v in mapping.items() if k in df.columns}
        if not applicable:
            logger.debug("No column_mapping keys match DataFrame columns")
            return df

        skipped = set(mapping) - set(applicable)
        if skipped:
            logger.debug("column_mapping keys not in DataFrame: %s", skipped)

        df = df.rename(columns=applicable)
        logger.info(
            "Renamed %d columns: %s",
            len(applicable),
            ", ".join(f"{k}->{v}" for k, v in applicable.items()),
        )
        return df
