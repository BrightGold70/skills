"""Korean encoding detection and handling."""

import logging

logger = logging.getLogger(__name__)

ENCODINGS = ["utf-8", "cp949", "euc-kr", "utf-16", "latin-1"]


def detect_encoding(file_path: str) -> str:
    """Detect file encoding by trying common Korean encodings."""
    for enc in ENCODINGS:
        try:
            with open(file_path, "r", encoding=enc) as f:
                f.read(1024)
            return enc
        except (UnicodeDecodeError, UnicodeError):
            continue
    logger.warning("Could not detect encoding for %s, defaulting to utf-8", file_path)
    return "utf-8"


def read_file_safe(file_path: str) -> str:
    """Read a file with automatic encoding detection."""
    enc = detect_encoding(file_path)
    with open(file_path, "r", encoding=enc) as f:
        return f.read()
