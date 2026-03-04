"""Structured logging setup for CRF pipeline."""

import logging
import os
from pathlib import Path
from typing import Optional


def setup_logging(log_level: str = "INFO",
                  output_dir: Optional[str] = None) -> logging.Logger:
    """Configure logging for the CRF pipeline.

    Args:
        log_level: Logging level string (DEBUG, INFO, WARNING, ERROR)
        output_dir: If provided, also log to a file in this directory
    """
    root_logger = logging.getLogger("crf_pipeline")
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Console handler
    if not root_logger.handlers:
        console = logging.StreamHandler()
        console.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        ))
        root_logger.addHandler(console)

    # File handler
    if output_dir:
        log_dir = Path(output_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "crf_pipeline.log"
        file_handler = logging.FileHandler(str(log_path), encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        ))
        root_logger.addHandler(file_handler)

    return root_logger
