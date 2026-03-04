"""Exporter abstract base class."""

from abc import ABC, abstractmethod
from typing import List

from ..models.patient_record import PatientRecord


class ExporterBase(ABC):
    """Base class for data exporters."""

    @abstractmethod
    def export(self, records: List[PatientRecord],
               output_path: str, **kwargs) -> str:
        """Export records to file. Returns output path."""
