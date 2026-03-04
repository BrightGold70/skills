"""Abstract base class for data transformers."""

from abc import ABC, abstractmethod
from typing import Any, Dict

import pandas as pd


class AbstractTransformer(ABC):
    """Base class for all CRF-to-R data transformers.

    Each transformer takes a DataFrame and a config dict, applies a specific
    transformation, and returns the modified DataFrame.
    """

    @abstractmethod
    def transform(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Transform a DataFrame according to config.

        Args:
            df: Input DataFrame with CRF variable names.
            config: Merged disease config dict containing transformation rules.

        Returns:
            Transformed DataFrame.
        """
        pass
