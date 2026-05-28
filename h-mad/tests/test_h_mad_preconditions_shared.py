import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = REPO_ROOT / "h-mad" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from h_mad_audit_gate import classify  # noqa: E402
from h_mad_do_preconditions import _count_must_fix  # noqa: E402


@pytest.mark.parametrize(
    "text",
    [
        "## Must-fix\nNone\n## Should-fix\nNone\n",
        "## Must-fix\n## Should-fix\n- should issue\n",
        "## Notes\n- not blocking\n## Must-fix\n- real issue\n",
        "## Must-fix\n- None\n## Should-fix\nNone\n",
    ],
)
def test_count_must_fix_matches_shared_audit_gate(tmp_path: Path, text: str) -> None:
    audit_file = tmp_path / "audit.md"
    audit_file.write_text(text, encoding="utf-8")

    assert _count_must_fix(audit_file) == classify(text)["must_count"]


def test_count_must_fix_does_not_treat_dash_none_as_dirty(tmp_path: Path) -> None:
    audit_file = tmp_path / "audit.md"
    audit_file.write_text("## Must-fix\n- None\n## Should-fix\nNone\n", encoding="utf-8")

    assert _count_must_fix(audit_file) == 0


def test_count_must_fix_counts_real_must_fix_bullet(tmp_path: Path) -> None:
    audit_file = tmp_path / "audit.md"
    audit_file.write_text("## Must-fix\n- real issue\n## Should-fix\nNone\n", encoding="utf-8")

    assert _count_must_fix(audit_file) == 1
