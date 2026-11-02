"""Tests read the h-mad skill body through `scripts/h_mad_skill_corpus.py`.

The reader moved to `scripts/` (row 2930) because production reads the restored
SKILL.md too. This module keeps every test's `from skill_corpus import …` working.
"""
from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = str(Path(__file__).resolve().parents[1] / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from h_mad_skill_corpus import (  # noqa: E402,F401
    SKILL_DIR, SPLIT_REFERENCES, doc_text, skill_text,
)
