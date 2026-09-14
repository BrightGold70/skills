"""Tests for `h_mad_check_plugin_hooks.py`.

Two kinds of test live here and they fail for opposite reasons.

`TestAgainstTheLiveBinary` re-derives the two key sets from the installed
Claude Code binary on every run. It is the only thing that can notice the
validator's contract changing under us, and it is written to SKIP — never pass
— when the binary cannot be found or read. A check that silently degrades to a
pass is the failure this whole script exists to replace.

Everything else runs off FIXTURES, not off the vendor cache. The pre-patch
`hooks.json` that produced the recorded warning lived in
`~/.claude/plugins/cache/bkit-marketplace/bkit/<version>/hooks/` and was wiped
by the upgrade that followed; a test reading that path would have skipped
forever afterwards while reporting nothing wrong. So the two warning texts this
repo actually recorded are pinned as literal strings against synthesised
configs that reproduce them:

    unknown keys "$schema", "once" in hooks.SessionStart[0] ignored   (bkit 2.0.8)
    unknown key "$schema" ignored                                     (bkit 2.1.38, pre-patch)

The singular/plural swap between them is not cosmetic — it is `len(findings)`,
and a mutant that always writes "keys" passes every test that only greps for
`$schema`.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from h_mad_check_plugin_hooks import (  # noqa: E402
    MATCHER,
    MAXKEYS,
    TOP,
    TRUNC,
    check,
    findings,
    message,
)

SCRIPT = SCRIPTS / "h_mad_check_plugin_hooks.py"

# The exact lines this repo recorded from the TUI, verbatim.
RECORDED_TWO = 'hooks.json: unknown keys "$schema", "once" in hooks.SessionStart[0] ignored'
RECORDED_ONE = 'hooks.json: unknown key "$schema" ignored'

# The pre-patch shape that produced RECORDED_TWO: an unknown top-level key AND
# an unknown matcher-level key, in that order.
PRE_PATCH_TWO = {
    "$schema": "https://json.schemastore.org/claude-code-hooks.json",
    "description": "bkit hooks",
    "hooks": {
        "SessionStart": [
            {
                "matcher": "startup",
                "once": True,
                "hooks": [{"type": "command", "command": "echo hi"}],
            }
        ]
    },
}

# The pre-patch shape that produced RECORDED_ONE: the matcher-level key was
# already gone, leaving a single top-level finding.
PRE_PATCH_ONE = {
    "$schema": "https://json.schemastore.org/claude-code-hooks.json",
    "description": "bkit hooks",
    "hooks": {
        "SessionStart": [
            {"matcher": "startup", "hooks": [{"type": "command", "command": "echo hi"}]}
        ]
    },
}

# What the patch left behind, and what the live cache is expected to look like.
PATCHED = {k: v for k, v in PRE_PATCH_ONE.items() if k != "$schema"}


def stage(tmp_path: Path, cfg: object, name: str = "hooks.json") -> Path:
    p = tmp_path / name
    p.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    return p


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True
    )


def _claude_binary() -> Path | None:
    """Resolve the running Claude Code binary. The versioned directory moves on
    every upgrade, so this must be looked up, never hardcoded."""
    which = subprocess.run(
        ["which", "claude"], capture_output=True, text=True
    )
    if which.returncode != 0 or not which.stdout.strip():
        return None
    resolved = subprocess.run(
        ["readlink", "-f", which.stdout.strip()], capture_output=True, text=True
    )
    target = (resolved.stdout.strip() if resolved.returncode == 0 else "") or which.stdout.strip()
    p = Path(target)
    return p if p.is_file() else None


class TestAgainstTheLiveBinary:
    """Re-derive the contract instead of trusting the transcription.

    These grep for the SET CONTENTS, never for the minified identifiers
    (`yko`, `_ko`, `bko`, `npn`) — those are regenerated per build and a test
    that pins them goes red on a rename that changed nothing.
    """

    def _blob(self) -> bytes:
        binary = _claude_binary()
        if binary is None:
            pytest.skip("claude binary not found — cannot verify, and will not pass")
        try:
            return binary.read_bytes()
        except OSError as exc:
            pytest.skip(f"claude binary unreadable ({exc}) — cannot verify")

    def test_top_level_key_set_still_matches(self) -> None:
        blob = self._blob()
        hits = re.findall(
            rb'new Set\(\[("description","hooks","modules","surface")\]\)', blob
        )
        assert hits, (
            "the top-level key set is no longer spelled "
            '["description","hooks","modules","surface"] in the binary — '
            "TOP in h_mad_check_plugin_hooks.py may be stale"
        )
        found = {k.strip('"') for k in hits[0].decode().split(",")}
        assert found == TOP

    def test_matcher_level_key_set_still_matches(self) -> None:
        blob = self._blob()
        hits = re.findall(rb'new Set\(\[("matcher","hooks")\]\)', blob)
        assert hits, (
            'the matcher-level key set is no longer spelled ["matcher","hooks"] '
            "in the binary — MATCHER may be stale"
        )
        found = {k.strip('"') for k in hits[0].decode().split(",")}
        assert found == MATCHER

    def test_the_two_numeric_constants_are_still_five_and_forty(self) -> None:
        """`bko=5`/`npn=40` sit immediately after the two Sets in the emitter's
        declaration run. Anchor on that run, not on the names."""
        blob = self._blob()
        m = re.search(
            rb'new Set\(\["matcher","hooks"\]\),\w+=(\d+),\w+=(\d+)', blob
        )
        assert m, "the declaration run after the matcher Set no longer parses"
        assert (int(m.group(1)), int(m.group(2))) == (MAXKEYS, TRUNC)


class TestTheRecordedWarnings:
    """The negative controls: configs that MUST produce the exact recorded text."""

    def test_bkit_208_shape_reproduces_the_two_key_line_verbatim(self) -> None:
        assert message(findings(PRE_PATCH_TWO)) == RECORDED_TWO

    def test_bkit_2138_shape_reproduces_the_one_key_line_verbatim(self) -> None:
        assert message(findings(PRE_PATCH_ONE)) == RECORDED_ONE

    def test_the_plural_tracks_the_count_not_the_content(self) -> None:
        """One finding says "key", two say "keys". A mutant that hardcodes
        either passes half these tests and fails this one."""
        assert message(findings(PRE_PATCH_ONE)).startswith("hooks.json: unknown key ")
        assert message(findings(PRE_PATCH_TWO)).startswith("hooks.json: unknown keys ")

    def test_the_matcher_finding_names_its_site(self) -> None:
        found = findings(PRE_PATCH_TWO)
        assert found == ['"$schema"', '"once" in hooks.SessionStart[0]']

    def test_a_second_matcher_is_indexed_from_zero(self) -> None:
        cfg = {
            "hooks": {
                "PreToolUse": [
                    {"matcher": "Bash", "hooks": []},
                    {"matcher": "Bash", "when": "always", "hooks": []},
                ]
            }
        }
        assert findings(cfg) == ['"when" in hooks.PreToolUse[1]']


class TestThePatchedShapeIsClean:
    """The positive control. Without it, a `findings()` that always returns []
    would satisfy nothing here but would satisfy a suite that only tested warns."""

    def test_patched_config_renders_no_message(self) -> None:
        assert findings(PATCHED) == []
        assert message(findings(PATCHED)) is None

    def test_every_allowed_top_level_key_is_accepted(self) -> None:
        cfg = {k: {} if k == "hooks" else "x" for k in TOP}
        assert findings(cfg) == []

    def test_the_live_bkit_cache_is_clean_if_it_is_installed(self) -> None:
        """Reads the vendor cache when present, SKIPS when it is not — the cache
        is wiped and re-created by upgrades and its absence is not a failure."""
        matches = sorted(
            Path.home().glob(
                ".claude/plugins/cache/bkit-marketplace/bkit/*/hooks/hooks.json"
            )
        )
        if not matches:
            pytest.skip("no bkit hooks.json in the plugin cache")
        for path in matches:
            state, _, msg = check(path, path.parts[-3])
            assert state == "CLEAN", f"{path} -> {msg}"


class TestUnreadableIsNotClean:
    def test_malformed_json_reports_unreadable(self, tmp_path: Path) -> None:
        p = tmp_path / "hooks.json"
        p.write_text("{ not json", encoding="utf-8")
        state, _, msg = check(p, "broken")
        assert state == "UNREADABLE"
        assert msg

    def test_a_missing_file_is_absent_not_clean(self, tmp_path: Path) -> None:
        state, _, msg = check(tmp_path / "nope.json", "gone")
        assert state == "ABSENT"
        assert msg is None

    def test_a_json_array_at_the_top_level_finds_nothing(self) -> None:
        """The emitter's own guard: a non-object config short-circuits."""
        assert findings([1, 2, 3]) == []


class TestTruncationAndOverflow:
    """The literals 40 and 5 are written out here on purpose.

    Deriving the expected value from `TRUNC`/`MAXKEYS` makes every assertion
    self-referential: raise TRUNC to 50 and the test raises its own expectation
    to match, so the mutation harness reported both of these as SURVIVORS on
    their first run, killed only by the binary-grep test — i.e. for the wrong
    reason. Pinning the literal is what makes a drift in the rendering path
    visible independently of whether the binary happens to be readable.
    """

    def test_a_long_key_is_elided_at_forty_characters(self) -> None:
        assert findings({"z" * 50: 1}) == [f'"{"z" * 40}..."']

    def test_a_key_exactly_at_the_limit_is_not_elided(self) -> None:
        assert findings({"z" * 40: 1}) == [f'"{"z" * 40}"']

    def test_a_key_one_over_the_limit_is_elided(self) -> None:
        assert findings({"z" * 41: 1}) == [f'"{"z" * 40}..."']

    def test_more_than_five_findings_collapse_into_and_n_more(self) -> None:
        rendered = message(findings({f"k{i}": 1 for i in range(8)}))
        assert rendered.endswith(" and 3 more ignored")
        assert rendered.count('"k') == 5

    def test_exactly_five_findings_have_no_tail(self) -> None:
        assert "more" not in message(findings({f"k{i}": 1 for i in range(5)}))

    def test_six_findings_list_five_and_say_one_more(self) -> None:
        rendered = message(findings({f"k{i}": 1 for i in range(6)}))
        assert rendered.endswith(" and 1 more ignored")
        assert rendered.count('"k') == 5

    def test_the_module_constants_agree_with_the_literals_pinned_above(self) -> None:
        """Keeps the literals honest without letting them be derived."""
        assert (MAXKEYS, TRUNC) == (5, 40)


class TestCLI:
    def test_a_warning_file_exits_one_and_names_the_plugin(self, tmp_path: Path) -> None:
        p = stage(tmp_path, PRE_PATCH_ONE)
        r = run_cli(f"bkit={p}")
        assert r.returncode == 1
        assert "WARN" in r.stdout
        assert f"Plugin bkit: {RECORDED_ONE}" in r.stdout

    def test_a_clean_file_exits_zero(self, tmp_path: Path) -> None:
        p = stage(tmp_path, PATCHED)
        r = run_cli(f"bkit={p}")
        assert r.returncode == 0
        assert "CLEAN" in r.stdout

    def test_one_warning_among_several_clean_files_still_exits_one(
        self, tmp_path: Path
    ) -> None:
        good = stage(tmp_path, PATCHED, "good.json")
        bad = stage(tmp_path, PRE_PATCH_TWO, "bad.json")
        r = run_cli(f"a={good}", f"b={bad}", f"c={good}")
        assert r.returncode == 1

    def test_unreadable_exits_one(self, tmp_path: Path) -> None:
        p = tmp_path / "hooks.json"
        p.write_text("{", encoding="utf-8")
        assert run_cli(f"x={p}").returncode == 1

    def test_an_absent_file_alone_exits_zero(self, tmp_path: Path) -> None:
        r = run_cli(f"x={tmp_path / 'nope.json'}")
        assert r.returncode == 0
        assert "ABSENT" in r.stdout

    def test_no_arguments_is_a_usage_error_not_a_pass(self) -> None:
        r = run_cli()
        assert r.returncode == 2
        assert "usage" in r.stderr

    def test_an_argument_without_an_equals_is_refused(self, tmp_path: Path) -> None:
        r = run_cli(str(tmp_path / "hooks.json"))
        assert r.returncode == 2
