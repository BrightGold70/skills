"""Tests for the off-contract artifact locator (J30).

The defect it addresses: `exec agy` honoured neither the `--report-file` slot nor
the sentinel pair, yet wrote a real report -- once as a workspace **dotfile**
(`.design.audit.v14.md`, invisible to the `*audit.v14*` glob the orchestrator
searches, which is how one cycle concluded "no file was written" and re-dispatched
over completed work) and once into `~/.gemini/antigravity-cli/scratch/` while
narrating "the current workspace". The artifact was unfindable, not absent.

The assertions that matter are the ones that keep the search from re-acquiring the
blind spots that caused the defect: dotfiles must be found, the `audit.vN` stem must
NOT be assumed, and "I could not search" must never print the same token as "I
searched and found nothing".
"""

import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "h-mad" / "scripts" / "h_mad_offcontract_scan.py"
sys.path.insert(0, str(SCRIPT.parent))

import h_mad_offcontract_scan as oc  # noqa: E402


REPORT_BODY = (
    "AUDIT-demo-design-v3-BEGIN\n"
    "## Summary\n"
    "One Must-fix.\n"
    "AUDIT-demo-design-v3-END\n"
)


@pytest.fixture
def empty_scratch(tmp_path, monkeypatch):
    """Point the agy-scratch root at an empty dir.

    Without this every test also walks the real `~/.gemini/antigravity-cli/scratch`,
    which holds this defect's own artifacts -- a fixture that passes because of the
    operator's home directory is not a test.
    """
    scratch = tmp_path / "agy-scratch"
    scratch.mkdir()
    monkeypatch.setattr(oc, "AGY_SCRATCH", scratch)
    return scratch


def _run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          capture_output=True, text=True)


def _token(out):
    lines = [l for l in out.splitlines() if l.startswith("OFFCONTRACT:")]
    assert len(lines) == 1, f"expected exactly one verdict line, got {lines!r}"
    return lines[0]


class TestFinds:
    def test_finds_a_workspace_dotfile(self, tmp_path, empty_scratch):
        """`.design.audit.v14.md` is the artifact that started this."""
        ws = tmp_path / "ws"
        ws.mkdir()
        (ws / ".design.audit.v14.md").write_text(REPORT_BODY, encoding="utf-8")

        found = oc.scan([ws], since=0, expected=None)
        assert [Path(c["path"]).name for c in found] == [".design.audit.v14.md"]
        assert found[0]["hidden"] is True

    def test_finds_a_name_that_does_not_carry_the_audit_stem(self, tmp_path,
                                                             empty_scratch):
        """The agent chose the name; assuming `audit.vN` re-creates the blind spot."""
        ws = tmp_path / "ws"
        ws.mkdir()
        (ws / "audit_report.md").write_text(REPORT_BODY, encoding="utf-8")
        (ws / "findings.md").write_text(REPORT_BODY, encoding="utf-8")

        names = {Path(c["path"]).name for c in oc.scan([ws], since=0, expected=None)}
        assert names == {"audit_report.md", "findings.md"}

    def test_searches_the_agy_scratch_root(self, tmp_path, empty_scratch):
        """The second observed drop landed here, not in the workspace."""
        ws = tmp_path / "ws"
        ws.mkdir()
        (empty_scratch / "audit_report.md").write_text(REPORT_BODY, encoding="utf-8")

        found = oc.scan([ws, oc.AGY_SCRATCH], since=0, expected=None)
        assert [Path(c["path"]).name for c in found] == ["audit_report.md"]

    def test_report_shaped_files_rank_above_noise(self, tmp_path, empty_scratch):
        """A scratch dir accumulates junk; the operator needs the report first."""
        ws = tmp_path / "ws"
        ws.mkdir()
        noise = ws / "notes.md"
        noise.write_text("just some text\n", encoding="utf-8")
        # Written second, so a newest-first sort alone would put the noise on top.
        report = ws / "r.md"
        report.write_text(REPORT_BODY, encoding="utf-8")
        noise.touch()

        found = oc.scan([ws], since=0, expected=None)
        assert [Path(c["path"]).name for c in found] == ["r.md", "notes.md"]
        assert found[0]["score"] > found[1]["score"]


class TestExcludes:
    def test_the_expected_path_is_not_reported_as_a_find(self, tmp_path,
                                                         empty_scratch):
        """If the contract path exists there is nothing to recover."""
        ws = tmp_path / "ws"
        ws.mkdir()
        expected = ws / "report.md"
        expected.write_text(REPORT_BODY, encoding="utf-8")

        assert oc.scan([ws], since=0, expected=expected) == []

    def test_files_older_than_the_floor_are_excluded(self, tmp_path, empty_scratch):
        """A previous cycle's report must not be recovered as this cycle's."""
        ws = tmp_path / "ws"
        ws.mkdir()
        stale = ws / "old.md"
        stale.write_text(REPORT_BODY, encoding="utf-8")
        old = time.time() - 86_400
        import os
        os.utime(stale, (old, old))

        assert oc.scan([ws], since=time.time() - 3600, expected=None) == []

    def test_empty_files_are_not_candidates(self, tmp_path, empty_scratch):
        ws = tmp_path / "ws"
        ws.mkdir()
        (ws / "empty.md").write_text("", encoding="utf-8")

        assert oc.scan([ws], since=0, expected=None) == []

    def test_git_internals_are_not_walked(self, tmp_path, empty_scratch):
        ws = tmp_path / "ws"
        (ws / ".git").mkdir(parents=True)
        (ws / ".git" / "COMMIT_EDITMSG.md").write_text(REPORT_BODY, encoding="utf-8")

        assert oc.scan([ws], since=0, expected=None) == []


class TestVerdictLine:
    def test_none_and_unreadable_are_different_tokens(self, tmp_path,
                                                      empty_scratch, monkeypatch):
        """"I could not search" must never print what "I found nothing" prints."""
        ws = tmp_path / "ws"
        ws.mkdir()
        monkeypatch.setenv("HMAD_AGY_SCRATCH", str(empty_scratch))

        found_nothing = _run("--cd", str(ws), "--minutes", "5")
        assert found_nothing.returncode == 0
        assert _token(found_nothing.stdout).startswith("OFFCONTRACT: NONE")

        cannot_look = _run("--cd", str(tmp_path / "nope"), "--minutes", "5")
        assert cannot_look.returncode == 2
        assert _token(cannot_look.stdout) == "OFFCONTRACT: UNREADABLE reason=no_workspace"

    def test_a_find_carries_the_do_not_trust_it_warning(self, tmp_path,
                                                        empty_scratch, monkeypatch):
        """A recovered report has had NO schema enforcement applied to it."""
        ws = tmp_path / "ws"
        ws.mkdir()
        (ws / ".design.audit.v14.md").write_text(REPORT_BODY, encoding="utf-8")
        monkeypatch.setenv("HMAD_AGY_SCRATCH", str(empty_scratch))

        r = _run("--cd", str(ws), "--minutes", "5")
        assert r.returncode == 0
        assert _token(r.stdout) == "OFFCONTRACT: FOUND 1"
        assert ".design.audit.v14.md" in r.stdout
        assert "falsify every premise against the source" in r.stdout

    def test_scratch_root_is_overridable_by_env(self, tmp_path, monkeypatch):
        """The path is an agy install detail, not a contract."""
        ws = tmp_path / "ws"
        ws.mkdir()
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        (elsewhere / "audit_report.md").write_text(REPORT_BODY, encoding="utf-8")
        monkeypatch.setenv("HMAD_AGY_SCRATCH", str(elsewhere))

        r = _run("--cd", str(ws), "--minutes", "5")
        assert _token(r.stdout) == "OFFCONTRACT: FOUND 1"
        assert "audit_report.md" in r.stdout
