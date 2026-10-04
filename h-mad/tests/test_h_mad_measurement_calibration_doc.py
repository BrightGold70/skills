"""The calibration rule lives in the reference, not in one detector's docstring.

Skill-candidates row "calibrate a new detector against artifacts that already passed,
before wiring it": five precheck detectors filed as hard fired 104 / 49 / 48 times on
documents that had just passed 83 and 74 audit cycles, every hit correct usage. The
mechanism landed for one detector (`test_noise_floor_on_documents_that_survived_eighty_cycles`);
the reusable shape had no home, so the next detector's author had only a memory.
"""
from __future__ import annotations

import re
from pathlib import Path

DOC = Path(__file__).resolve().parents[1] / "references" / "measurement-discipline.md"
TEXT = DOC.read_text(encoding="utf-8")


def _section() -> str:
    m = re.search(r"(?ms)^## CALIBRATION\b.*?(?=^## )", TEXT)
    assert m, "no ## CALIBRATION section in measurement-discipline.md"
    return " ".join(m.group(0).split())


def test_the_section_names_the_corpus_and_the_order() -> None:
    body = _section()
    assert "already passed" in body
    assert "before it is wired" in body


def test_a_hit_on_a_known_good_artifact_is_triaged_not_ignored() -> None:
    body = _section()
    assert "demote" in body and "fix the detector" in body


def test_the_noise_floor_is_pinned_by_a_test() -> None:
    body = _section()
    assert "noise floor" in body
    assert "test_noise_floor_on_documents_that_survived_eighty_cycles" in body
