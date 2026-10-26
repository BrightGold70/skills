"""bkit's SessionStart migration silently moves h-mad's state file.

h-mad keeps orchestrator state at `<project>/docs/.bkit-memory.json`, which is
bkit's LEGACY path. bkit's `hooks/startup/migration.js` renames that file to
`<project>/.bkit/state/memory.json` whenever the legacy file exists and the new
one does not (it skips when the target already exists). The first Claude session
started inside a fresh git worktree therefore MOVES h-mad's store, and the resume
oracle then answers `state_lost` for a feature whose record is intact one
directory over. Reproduced deterministically 2026-10-26.

Operator-chosen fix, "seed + detect":

* SEED -- every successful state write (and every `hmad-dispatch worktree-create`
  that learns the new checkout's path) makes sure `<root>/.bkit/state/memory.json`
  exists, so bkit always finds a target and never migrates. Never overwrites.
* DETECT -- when the state file is missing but the bkit target holds this
  feature's record, the oracle answers `migrated_by_bkit` (a STOP) and prints a
  restore-by-COPY hint, so bkit keeps a target and does not re-migrate.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "h-mad" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import h_mad_state_write as sw  # noqa: E402
from h_mad_resume_decision import decide  # noqa: E402

TARGET_REL = Path(".bkit/state/memory.json")


def _project(tmp_path: Path, records: dict | None = None) -> tuple[Path, Path]:
    """A project root with `docs/.bkit-memory.json` holding `records`."""
    root = tmp_path / "proj"
    (root / "docs").mkdir(parents=True)
    state = root / "docs" / ".bkit-memory.json"
    state.write_text(json.dumps({"version": 1, "orchestrator_state": records or {}}),
                     encoding="utf-8")
    return root, state


def _bkit_moved(tmp_path: Path, feature: str = "feat") -> tuple[Path, Path, Path]:
    """Fake bkit's rename: the record lives in `.bkit/state/memory.json`, docs/ has none."""
    root = tmp_path / "proj"
    (root / "docs").mkdir(parents=True)
    target = root / TARGET_REL
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps({"version": 1, "orchestrator_state": {
        feature: {"feature": feature, "last_completed_phase": 4, "current_phase": 5}}}),
        encoding="utf-8")
    return root, root / "docs" / ".bkit-memory.json", target


# --------------------------------------------------------------------------- SEED


class TestStateWriteSeedsTheBkitTarget:
    def test_absent_target_is_created_as_an_empty_object(self, tmp_path: Path) -> None:
        root, state = _project(tmp_path)
        sw.create_feature(state, "feat")
        target = root / TARGET_REL
        assert target.is_file(), "a successful state write must seed the bkit target"
        assert json.loads(target.read_text(encoding="utf-8")) == {}

    def test_every_write_verb_seeds_not_only_create(self, tmp_path: Path) -> None:
        root, state = _project(tmp_path)
        sw.create_feature(state, "feat")
        (root / TARGET_REL).unlink()
        sw.merge_fields(state, "feat", {"current_phase": 1})
        assert (root / TARGET_REL).is_file(), "merge_fields must seed too"

    def test_a_present_target_is_left_byte_identical(self, tmp_path: Path) -> None:
        root, state = _project(tmp_path)
        target = root / TARGET_REL
        target.parent.mkdir(parents=True)
        original = b'{"bkit": "owns this", "n": 1}\n  '
        target.write_bytes(original)
        before = os.stat(target).st_mtime_ns
        sw.create_feature(state, "feat")
        assert target.read_bytes() == original
        assert os.stat(target).st_mtime_ns == before

    def test_a_state_path_of_another_shape_is_not_seeded(self, tmp_path: Path) -> None:
        state = tmp_path / "state.json"
        state.write_text(json.dumps({"version": 1, "orchestrator_state": {}}), encoding="utf-8")
        sw.create_feature(state, "feat")
        assert not (tmp_path / ".bkit").exists()
        assert not (tmp_path.parent / ".bkit").exists()

    def test_a_docs_dir_with_a_different_file_name_is_not_seeded(self, tmp_path: Path) -> None:
        (tmp_path / "docs").mkdir()
        state = tmp_path / "docs" / "other-state.json"
        state.write_text(json.dumps({"version": 1, "orchestrator_state": {}}), encoding="utf-8")
        sw.create_feature(state, "feat")
        assert not (tmp_path / ".bkit").exists()

    def test_a_seed_failure_never_fails_the_write(self, tmp_path: Path, capsys) -> None:
        root, state = _project(tmp_path)
        (root / ".bkit").write_text("a FILE where the directory should be", encoding="utf-8")
        record = sw.create_feature(state, "feat")
        assert record["feature"] == "feat"
        assert json.loads(state.read_text())["orchestrator_state"]["feat"]["feature"] == "feat"
        assert "bkit" in capsys.readouterr().err.lower(), "a seed failure must warn on stderr"

    def test_the_cli_seeds_and_still_reports_ok(self, tmp_path: Path) -> None:
        root, state = _project(tmp_path)
        r = subprocess.run([sys.executable, str(SCRIPTS / "h_mad_state_write.py"), str(state),
                            "--feature", "feat", "--create"], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        assert "STATE-WRITE: OK" in r.stdout
        assert json.loads((root / TARGET_REL).read_text()) == {}


class TestStateWriteNamesTheMigration:
    def test_no_such_state_file_mentions_bkit_when_the_target_holds_state(self, tmp_path: Path) -> None:
        root, state, target = _bkit_moved(tmp_path)
        with pytest.raises(sw.StateWriteError) as exc:
            sw.merge_fields(state, "feat", {"current_phase": 6})
        msg = str(exc.value)
        assert "no such state file" in msg
        assert "bkit" in msg and str(target) in msg
        assert f"cp {target} {state}" in msg, "the repair must be a COPY, not a move"

    def test_no_such_state_file_stays_plain_without_a_migrated_store(self, tmp_path: Path) -> None:
        (tmp_path / "docs").mkdir()
        with pytest.raises(sw.StateWriteError) as exc:
            sw.create_feature(tmp_path / "docs" / ".bkit-memory.json", "feat")
        assert "bkit" not in str(exc.value).replace(".bkit-memory.json", "")


# ------------------------------------------------------------------------- DETECT


class TestTheOracleDetectsTheMigration:
    def test_a_migrated_record_is_migrated_by_bkit_not_state_lost(self, tmp_path: Path, capsys) -> None:
        root, state, target = _bkit_moved(tmp_path)
        # Phase documents exist too: without the new check this is exactly state_lost.
        (root / "docs/01-plan/features").mkdir(parents=True)
        (root / "docs/01-plan/features/feat.plan.md").write_text("# p\n", encoding="utf-8")
        assert decide(state, "feat") == "migrated_by_bkit"
        err = capsys.readouterr().err
        assert f"cp {target} {state}" in err, "stderr must carry the exact restore-by-copy command"
        assert "COPY" in err or "copy" in err

    def test_migrated_without_phase_docs_is_still_not_start_fresh(self, tmp_path: Path) -> None:
        _root, state, _target = _bkit_moved(tmp_path)
        assert decide(state, "feat") == "migrated_by_bkit"

    def test_the_cli_prints_the_token_and_the_hint(self, tmp_path: Path) -> None:
        _root, state, target = _bkit_moved(tmp_path)
        r = subprocess.run([sys.executable, str(SCRIPTS / "h_mad_resume_decision.py"),
                            "--state", str(state), "--feature", "feat", "--host", "claude"],
                           capture_output=True, text=True)
        assert r.returncode == 0
        assert r.stdout.strip() == "migrated_by_bkit"
        assert f"cp {target} {state}" in r.stderr

    def test_another_features_record_falls_through(self, tmp_path: Path) -> None:
        _root, state, _target = _bkit_moved(tmp_path, feature="other")
        assert decide(state, "feat") == "start_fresh"

    @pytest.mark.parametrize("content", [
        "{ truncated", "[]", '"a string"', '{"orchestrator_state": []}',
        '{"orchestrator_state": {"feat": null}}', "",
    ], ids=["bad-json", "list-root", "string-root", "list-state", "null-record", "empty"])
    def test_an_unusable_target_falls_through_without_crashing(self, tmp_path: Path, content: str) -> None:
        root = tmp_path / "proj"
        (root / "docs/01-plan/features").mkdir(parents=True)
        (root / "docs/01-plan/features/feat.plan.md").write_text("# p\n", encoding="utf-8")
        target = root / TARGET_REL
        target.parent.mkdir(parents=True)
        target.write_text(content, encoding="utf-8")
        assert decide(root / "docs" / ".bkit-memory.json", "feat") == "state_lost"

    def test_an_unreadable_target_falls_through(self, tmp_path: Path) -> None:
        root = tmp_path / "proj"
        (root / "docs").mkdir(parents=True)
        target = root / TARGET_REL
        target.parent.mkdir(parents=True)
        target.write_text('{"orchestrator_state": {"feat": {"x": 1}}}', encoding="utf-8")
        target.chmod(0o000)
        try:
            if os.access(target, os.R_OK):
                pytest.skip("running as root — the permission path is unreachable")
            assert decide(root / "docs" / ".bkit-memory.json", "feat") == "start_fresh"
        finally:
            target.chmod(0o600)

    def test_a_present_state_file_is_never_second_guessed(self, tmp_path: Path) -> None:
        root, state = _project(tmp_path, {"feat": {"last_completed_phase": 2}})
        target = root / TARGET_REL
        target.parent.mkdir(parents=True)
        target.write_text(json.dumps({"orchestrator_state": {"feat": {"last_completed_phase": 6}}}))
        assert decide(state, "feat") == "resume_manual"

    def test_a_state_path_outside_docs_is_not_probed(self, tmp_path: Path) -> None:
        target = tmp_path / TARGET_REL
        target.parent.mkdir(parents=True)
        target.write_text(json.dumps({"orchestrator_state": {"feat": {"x": 1}}}))
        assert decide(tmp_path / "elsewhere.json", "feat") == "cannot_judge"


# --------------------------------------------------------------------- TOKEN LISTS


def _flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


class TestTheTokenIsAStopEverywhereItIsListed:
    def test_h_mad_decision_table_has_a_stop_row(self) -> None:
        skill = (REPO_ROOT / "h-mad" / "SKILL.md").read_text(encoding="utf-8")
        row = next((ln for ln in skill.splitlines() if ln.startswith("| `migrated_by_bkit` |")), "")
        assert "**Stop." in row, "h-mad decision table must give migrated_by_bkit a STOP row"
        assert "cp " in row and "COPY" in row, "the row must prescribe restore by COPY"

    def test_h_mad_claim_preamble_counts_it_among_the_stops(self) -> None:
        flat = _flat(REPO_ROOT / "h-mad" / "SKILL.md")
        assert "`state_lost` or `migrated_by_bkit` (all four STOP" in flat
        assert "`cannot_judge`, `state_lost` and `migrated_by_bkit` STOP before any claim" in flat

    @pytest.mark.parametrize("adapter", ["codex", "agy", "grok"])
    def test_each_runtime_adapter_stops_on_it(self, adapter: str) -> None:
        text = _flat(REPO_ROOT / "h-mad" / "references" / f"{adapter}-runtime.md")
        assert "`migrated_by_bkit` STOPs too" in text, adapter

    def test_handover_step2_classifies_it_as_a_stop(self) -> None:
        handoff = _flat(REPO_ROOT / "handoff" / "SKILL.md")
        safe = handoff.split("→ no live owner. Safe to proceed.")[0].rsplit("- **one of", 1)[1]
        assert "`migrated_by_bkit`" not in safe, "migrated_by_bkit must not be on the safe list"
        assert "- **`migrated_by_bkit`** →" in handoff

    def test_takeover_stops_on_it_before_the_claim_catch_all(self) -> None:
        body = (REPO_ROOT / "handoff" / "SKILL.md").read_text(encoding="utf-8")
        takeover = body[body.index("### Step T2: Adopt it"):]
        stop = takeover.find("- `migrated_by_bkit` → STOP")
        claim = takeover.find("- anything else → claim it:")
        assert stop != -1, "TAKEOVER must STOP on migrated_by_bkit"
        assert claim != -1 and stop < claim

    def test_takeover_absent_file_path_stops_on_it(self) -> None:
        body = (REPO_ROOT / "handoff" / "SKILL.md").read_text(encoding="utf-8")
        takeover = " ".join(body[body.index("### Step T2: Adopt it"):].split())
        assert "`state_lost`, `migrated_by_bkit` (or `cannot_judge`) → STOP" in takeover


# --------------------------------------------------------------- WORKTREE-CREATE


WRAPPER = SCRIPTS / "hmad-dispatch.sh"
STUBS = REPO_ROOT / "h-mad" / "tests" / "stubs"


def _create(tmp_path: Path, payload: dict) -> subprocess.CompletedProcess:
    import shutil

    b = tmp_path / "bin"
    b.mkdir()
    (b / "orca").symlink_to(STUBS / "orca")
    jq = shutil.which("jq")
    if jq:
        (b / "jq").symlink_to(jq)
    env = {"PATH": f"{b}:/usr/bin:/bin", "HOME": str(tmp_path), "HMAD_SUBSTRATE": "orca",
           "HMAD_ORCA_PIN_FILE": str(tmp_path / "absent-pin"),
           "HMAD_STUB_ORCA_STDOUT": json.dumps(payload)}
    return subprocess.run(["bash", str(WRAPPER), "worktree-create", "m"],
                          capture_output=True, text=True, env=env)


class TestWorktreeCreateSeeds:
    def test_a_new_worktree_path_is_seeded(self, tmp_path: Path) -> None:
        wt = tmp_path / "wt"
        wt.mkdir()
        r = _create(tmp_path, {"result": {"worktree": {"id": "wt-9", "path": str(wt)}}})
        assert r.returncode == 0, r.stderr
        assert r.stdout == "wt-9\n", "the selector output must be unchanged"
        assert json.loads((wt / TARGET_REL).read_text()) == {}

    def test_an_existing_target_in_the_new_worktree_is_untouched(self, tmp_path: Path) -> None:
        wt = tmp_path / "wt"
        (wt / ".bkit/state").mkdir(parents=True)
        original = b'{"kept": true}'
        (wt / TARGET_REL).write_bytes(original)
        r = _create(tmp_path, {"result": {"worktree": {"id": "wt-9", "path": str(wt)}}})
        assert r.returncode == 0, r.stderr
        assert (wt / TARGET_REL).read_bytes() == original

    def test_no_path_in_the_response_seeds_nothing_and_still_succeeds(self, tmp_path: Path) -> None:
        r = _create(tmp_path, {"result": {"worktree": {"id": "wt-9"}}})
        assert r.returncode == 0, r.stderr
        assert r.stdout == "wt-9\n"
        assert not list(tmp_path.rglob("memory.json"))

    def test_a_path_that_is_not_a_directory_is_not_created(self, tmp_path: Path) -> None:
        ghost = tmp_path / "ghost"
        r = _create(tmp_path, {"result": {"worktree": {"id": "wt-9", "path": str(ghost)}}})
        assert r.returncode == 0, r.stderr
        assert not ghost.exists()
