import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = REPO_ROOT / "h-mad" / "scripts"
PRECONDITIONS_SOURCE = SCRIPT_DIR / "h_mad_do_preconditions.py"
sys.path.insert(0, str(SCRIPT_DIR))

from h_mad_audit_gate import classify  # noqa: E402
from h_mad_do_preconditions import _count_must_fix, check  # noqa: E402


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


def test_count_must_fix_honors_acknowledged_sidecar(tmp_path: Path) -> None:
    # Operator-override preservation: a Must-fix item waived under
    # ## Acknowledged-not-fixed must NOT count, or /h-mad do locks out.
    audit_file = tmp_path / "audit.md"
    audit_file.write_text(
        "## Must-fix\n- waived item\n## Acknowledged-not-fixed\n- waived item\n",
        encoding="utf-8",
    )

    assert _count_must_fix(audit_file) == 0


def test_preconditions_has_no_duplicate_audit_discovery_implementation() -> None:
    source = PRECONDITIONS_SOURCE.read_text(encoding="utf-8")

    assert "AUDIT_VERSION_RE" not in source
    assert "_latest_audit" not in source


def test_archive_only_audits_do_not_satisfy_live_preconditions(tmp_path: Path) -> None:
    feature = "f"
    docs_root = tmp_path / "docs"
    (docs_root / "01-plan" / "features").mkdir(parents=True)
    (docs_root / "02-design" / "features").mkdir(parents=True)
    (docs_root / "01-plan" / "features" / f"{feature}.plan.md").write_text(
        "", encoding="utf-8"
    )
    (docs_root / "02-design" / "features" / f"{feature}.design.md").write_text(
        "", encoding="utf-8"
    )
    archive = docs_root / "archive" / "2019-01" / feature
    archive.mkdir(parents=True)
    clean_audit = "## Must-fix\nNone\n## Should-fix\nNone\n"
    (archive / f"{feature}.plan.audit.v1.md").write_text(clean_audit, encoding="utf-8")
    (archive / f"{feature}.design.audit.v1.md").write_text(clean_audit, encoding="utf-8")

    rc, issues = check(tmp_path, feature)

    assert rc == 1
    assert any("MISSING:" in issue and ".plan.audit.v*.md" in issue for issue in issues)
    assert any("MISSING:" in issue and ".design.audit.v*.md" in issue for issue in issues)
    # Deliberately NO source-inspection assertion here. This behaviour is already
    # correct before the refactor, so this is a REGRESSION GUARD, not a RED test: it
    # must pass both before and after. Bundling the "duplicate implementation is gone"
    # check into it would manufacture a failure and conflate the two purposes -
    # test_preconditions_has_no_duplicate_audit_discovery_implementation owns that.
    #
    # What it guards: do_preconditions gates /h-mad do on a LIVE audited plan and
    # design. If the delegation started passing include_archive=True, a shipped
    # feature's archived audits would satisfy the precondition for new work reusing
    # its name - a behaviour change disguised as a refactor.


def test_latest_live_audit_still_uses_highest_version(tmp_path: Path) -> None:
    feature = "f"
    docs_root = tmp_path / "docs"
    plan_dir = docs_root / "01-plan" / "features"
    design_dir = docs_root / "02-design" / "features"
    plan_dir.mkdir(parents=True)
    design_dir.mkdir(parents=True)
    (plan_dir / f"{feature}.plan.md").write_text("", encoding="utf-8")
    (design_dir / f"{feature}.design.md").write_text("", encoding="utf-8")
    (plan_dir / f"{feature}.plan.audit.v1.md").write_text(
        "## Must-fix\n- real issue\n## Should-fix\nNone\n", encoding="utf-8"
    )
    clean_audit = "## Must-fix\nNone\n## Should-fix\nNone\n"
    (plan_dir / f"{feature}.plan.audit.v2.md").write_text(clean_audit, encoding="utf-8")
    (design_dir / f"{feature}.design.audit.v1.md").write_text(clean_audit, encoding="utf-8")

    rc, issues = check(tmp_path, feature)

    assert rc == 0
    assert issues == ["OK"]
    # Regression guard, not a RED test - see the note in
    # test_archive_only_audits_do_not_satisfy_live_preconditions. "Latest means
    # highest version" already holds before the refactor; what this pins is that
    # delegating to h_mad_cycle_counts.latest_audit_path does not quietly change it
    # to "first found" or "most recently modified". v1 carries a real must-fix and
    # v2 is clean, so reading the wrong file reports DIRTY instead of OK.
