"""An installed hook that nothing references is indistinguishable from a passing one.

`h_mad_install_check.py` proves the symlinks resolve. Nothing proved any settings
file points at them, and that gap is silent in the worst direction: writes sail
through exactly as they would if the TDD gate had approved them, and the context
budget goes unreported. SKILL.md has named the hole since the TDD gate shipped; the
advisor advisory made it two — and the two live under DIFFERENT hook events, which
is its own way to be silently unwired (J44).

The tests are written against the ways this check reports the WRONG thing, because a
wiring checker that cries wolf gets deleted and a lenient one restores the original
blindness:

  * literal-path matching. The live wiring is `bash $HOME/.claude/.../hook.sh`, an
    unexpanded variable inside a longer command line.
  * "referenced" read as "wired". `Write` alone never fires for `Edit`; the gate then
    stands down on half its surface with nothing to show for it.
  * a missing settings file read as "not wired". Nothing was read -- that is a
    cannot-judge, and it is the likeliest false FAIL on a machine whose hooks live
    somewhere this script does not enumerate.
"""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "h-mad" / "scripts" / "h_mad_hook_wiring.py"

sys.path.insert(0, str(SCRIPT.parent))
import h_mad_hook_wiring as hw  # noqa: E402

TDD = "h-mad-tdd-gate.sh"
ADV = "h-mad-advisor-warn.sh"


def _settings(tmp_path, entries, name="settings.json", event="PreToolUse"):
    p = tmp_path / name
    p.write_text(json.dumps({"hooks": {event: entries}}))
    return p


def _settings_by_event(tmp_path, by_event, name="settings.json"):
    """The two h-mad hooks live under DIFFERENT events: the TDD gate blocks on
    PreToolUse, the advisor advisory injects on PostToolUse (it cannot block —
    `advisor` is a server-side tool no tool-scoped event fires for, J44)."""
    p = tmp_path / name
    p.write_text(json.dumps({"hooks": by_event}))
    return p


def _entry(matcher, command):
    return {"matcher": matcher, "hooks": [{"type": "command", "command": command}]}


def _hooks_dir(tmp_path):
    d = tmp_path / "hooks"
    d.mkdir(exist_ok=True)
    for name in (TDD, ADV):
        (d / name).write_text("#!/bin/bash\n")
    return d


def _wired(tmp_path, tdd_matcher="Write|Edit", adv_matcher="*"):
    d = _hooks_dir(tmp_path)
    return _settings_by_event(tmp_path, {
        "PreToolUse": [_entry(tdd_matcher, f"bash {d / TDD}")],
        "PostToolUse": [_entry(adv_matcher, f"bash {d / ADV}")],
    })


class TestTheHealthyShape:
    def test_both_hooks_wired_is_clean(self, tmp_path):
        issues, read = hw.check(sources=[_wired(tmp_path)])
        assert read and issues == []

    def test_match_all_matchers_cover_everything(self, tmp_path):
        issues, _ = hw.check(sources=[_wired(tmp_path, "*", "*")])
        assert issues == []

    def test_env_vars_and_tildes_in_the_command_are_expanded(self, tmp_path, monkeypatch):
        """The live wiring is literally `bash $HOME/.claude/skills/...`. Comparing
        the raw string against the filesystem reports a stale path for a hook that
        is present and working."""
        monkeypatch.setenv("HOME", str(tmp_path))
        _hooks_dir(tmp_path)
        s = _settings_by_event(tmp_path, {
            "PreToolUse": [_entry("Write|Edit", f"bash $HOME/hooks/{TDD}")],
            "PostToolUse": [_entry("*", f"bash ~/hooks/{ADV}")],
        })
        issues, _ = hw.check(sources=[s])
        assert issues == []

    def test_hook_inside_a_longer_command_still_counts(self, tmp_path):
        d = _hooks_dir(tmp_path)
        s = _settings_by_event(tmp_path, {
            "PreToolUse": [_entry("Write|Edit", f"cd /tmp && bash {d / TDD} --quiet || true")],
            "PostToolUse": [_entry("*", f"bash {d / ADV}")],
        })
        issues, _ = hw.check(sources=[s])
        assert issues == []

    def test_sources_are_merged_not_overridden(self, tmp_path):
        """A project file wiring one hook and the user file wiring the other is a
        healthy install; scoring either file alone reports a false NOT_WIRED."""
        d = _hooks_dir(tmp_path)
        a = _settings(tmp_path, [_entry("Write|Edit", f"bash {d / TDD}")], "a.json")
        b = _settings(tmp_path, [_entry("*", f"bash {d / ADV}")], "b.json",
                      event="PostToolUse")
        issues, _ = hw.check(sources=[a, b])
        assert issues == []


class TestWhatItCatches:
    def test_missing_hook_is_reported_by_name(self, tmp_path):
        d = _hooks_dir(tmp_path)
        s = _settings(tmp_path, [_entry("Write|Edit", f"bash {d / TDD}")])
        issues, _ = hw.check(sources=[s])
        assert issues == [f"HOOK_NOT_WIRED:{ADV}"]

    def test_a_matcher_covering_half_the_surface_fails(self, tmp_path):
        """`Write` never fires for `Edit`. The gate stands down on Edit silently --
        the exact shape of blindness this check exists for."""
        issues, _ = hw.check(sources=[_wired(tmp_path, tdd_matcher="Write")])
        assert len(issues) == 1
        assert issues[0].startswith(f"HOOK_WIRED_WRONG_MATCHER:{TDD}")
        assert "uncovered=Edit" in issues[0]

    def test_a_matcher_for_the_wrong_tool_fails(self, tmp_path):
        issues, _ = hw.check(sources=[_wired(tmp_path, adv_matcher="Bash")])
        assert any(i.startswith(f"HOOK_WIRED_WRONG_MATCHER:{ADV}") for i in issues)

    def test_an_invalid_regex_matcher_is_not_a_pass(self, tmp_path):
        """`re.search` raises on a bad pattern; an uncaught raise would crash the
        check, and a bare `except: return True` would pass it."""
        issues, _ = hw.check(sources=[_wired(tmp_path, adv_matcher="advisor(")])
        assert any("WRONG_MATCHER" in i for i in issues)

    def test_a_command_naming_a_missing_file_is_stale(self, tmp_path):
        s = _wired(tmp_path)
        # delete AFTER the settings file is built: `_wired` recreates the hooks dir,
        # so unlinking first is silently undone and the test passes for no reason.
        (tmp_path / "hooks" / ADV).unlink()
        issues, _ = hw.check(sources=[s])
        assert any(i.startswith(f"HOOK_WIRED_STALE_PATH:{ADV}") for i in issues)

    def test_the_advisory_wired_under_pretooluse_is_not_wired(self, tmp_path):
        """J44's exact shape, at the wiring layer. `advisor` is a server-side tool
        that no tool-scoped event fires for, so the old PreToolUse registration ran
        zero times while looking installed. An event-blind check would call this
        healthy — which is precisely how the defect survived for days."""
        d = _hooks_dir(tmp_path)
        s = _settings_by_event(tmp_path, {
            "PreToolUse": [_entry("Write|Edit", f"bash {d / TDD}"),
                           _entry("*", f"bash {d / ADV}")],
        })

        issues, _ = hw.check(sources=[s])

        assert issues == [f"HOOK_NOT_WIRED:{ADV}"]

    def test_a_narrow_postooluse_matcher_leaves_tools_uncovered(self, tmp_path):
        """The advisory must fire on every tool: context grows through all of them,
        and a `Write`-only matcher reports the budget on a fraction of the turns."""
        d = _hooks_dir(tmp_path)
        s = _settings_by_event(tmp_path, {
            "PreToolUse": [_entry("Write|Edit", f"bash {d / TDD}")],
            "PostToolUse": [_entry("Write", f"bash {d / ADV}")],
        })

        issues, _ = hw.check(sources=[s])

        assert any(i.startswith(f"HOOK_WIRED_WRONG_MATCHER:{ADV}") for i in issues)
        assert "Bash" in "".join(issues)

    def test_wired_twice_with_one_good_matcher_is_covered(self, tmp_path):
        """The harness runs every matching entry, so one correct entry is enough.
        Reporting the other as a defect would train the operator to ignore this."""
        d = _hooks_dir(tmp_path)
        s = _settings_by_event(tmp_path, {
            "PreToolUse": [_entry("Write|Edit", f"bash {d / TDD}")],
            "PostToolUse": [_entry("Bash", f"bash {d / ADV}"),
                            _entry("*", f"bash {d / ADV}")],
        })
        issues, _ = hw.check(sources=[s])
        assert issues == []


class TestCannotJudge:
    def test_no_readable_settings_is_not_a_failure(self, tmp_path):
        issues, read = hw.check(sources=[tmp_path / "absent.json"])
        assert issues == [] and read is False

    def test_malformed_json_does_not_hide_a_readable_sibling(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{not json")
        issues, read = hw.check(sources=[bad, _wired(tmp_path)])
        assert read and issues == []

    def test_only_malformed_sources_is_a_cannot_judge(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{not json")
        issues, read = hw.check(sources=[bad])
        assert issues == [] and read is False

    def test_settings_without_hooks_is_read_but_unwired(self, tmp_path):
        """Distinct from "unreadable": the file was parsed and simply wires nothing,
        which IS the finding."""
        p = tmp_path / "s.json"
        p.write_text(json.dumps({"model": "opus"}))
        issues, read = hw.check(sources=[p])
        assert read is True
        assert sorted(issues) == sorted([f"HOOK_NOT_WIRED:{TDD}", f"HOOK_NOT_WIRED:{ADV}"])


class TestSourceResolution:
    def test_claude_config_dir_relocates_the_user_scope(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "cfg"))
        got = hw.settings_sources(None)
        assert got[0] == tmp_path / "cfg" / "settings.json"

    def test_project_settings_are_searched_up_the_tree(self, tmp_path, monkeypatch):
        """Claude Code walks up to find project settings. Checking only the
        directory it was handed reports a wired repo as unwired."""
        monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
        deep = tmp_path / "repo" / "a" / "b"
        deep.mkdir(parents=True)
        got = hw.settings_sources(deep)
        assert (tmp_path / "repo" / ".claude" / "settings.json") in got

    def test_a_hook_wired_by_an_ancestor_counts_as_wired(self, tmp_path, monkeypatch):
        monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
        monkeypatch.setenv("HOME", str(tmp_path / "nohome"))
        d = _hooks_dir(tmp_path)
        repo = tmp_path / "repo"
        (repo / "sub").mkdir(parents=True)
        (repo / ".claude").mkdir()
        (repo / ".claude" / "settings.json").write_text(json.dumps({"hooks": {
            "PreToolUse": [_entry("Write|Edit", f"bash {d / TDD}")],
            "PostToolUse": [_entry("*", f"bash {d / ADV}")]}}))
        issues, read = hw.check(project_root=repo / "sub")
        assert read and issues == []


class TestCli:
    def _run(self, root):
        return subprocess.run([sys.executable, str(SCRIPT), "--project-root", str(root)],
                              capture_output=True, text=True)

    def test_unknown_exits_2_and_carries_no_issue_count(self, tmp_path, monkeypatch):
        r = subprocess.run(
            [sys.executable, str(SCRIPT), "--project-root", str(tmp_path)],
            capture_output=True, text=True,
            env={"HOME": str(tmp_path), "PATH": "/usr/bin:/bin"})
        assert r.returncode == 2
        assert r.stdout.strip() == "WIRING: UNKNOWN reason=no_settings"
        assert "issues=" not in r.stdout
        assert "ERROR:" in r.stderr

    def test_fail_prints_a_verdict_then_detail_lines_and_exits_0(self, tmp_path):
        home = tmp_path / "home"
        (home / ".claude").mkdir(parents=True)
        (home / ".claude" / "settings.json").write_text(
            json.dumps({"hooks": {"PreToolUse": []}}))
        r = subprocess.run(
            [sys.executable, str(SCRIPT), "--project-root", str(tmp_path)],
            capture_output=True, text=True,
            env={"HOME": str(home), "PATH": "/usr/bin:/bin"})
        assert r.returncode == 0, "a verdict is not an operational error"
        lines = r.stdout.strip().splitlines()
        assert lines[0] == "WIRING: FAIL issues=2"
        assert all(l.startswith("HOOK_NOT_WIRED:") for l in lines[1:])


def test_every_required_hook_exists_in_the_checkout():
    """A required name that no longer exists would make this check permanently FAIL
    on a healthy install."""
    for basename in hw.REQUIRED_HOOKS:
        assert (REPO_ROOT / "h-mad" / "hooks" / basename).is_file(), basename


# ── docs must carry the check, its tokens, and a runnable remedy for each ────

SKILL_MD = REPO_ROOT / "h-mad" / "SKILL.md"


def _wiring_section() -> str:
    text = SKILL_MD.read_text()
    marker = "### Wired, not just installed"
    assert marker in text, "the wiring section is gone"
    body = text.split(marker, 1)[1]
    kept, in_fence = [], False
    for line in body.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            kept.append(line)
            continue
        if not in_fence and line.startswith("#"):
            break
        kept.append(line)
    section = "\n".join(kept)
    assert len(section.splitlines()) < 90, "section boundary ran away"
    return " ".join(section.split())


def test_docs_name_the_command_and_all_three_verdicts():
    s = _wiring_section()
    assert "h_mad_hook_wiring.py" in s
    for token in ("WIRING: PASS", "WIRING: FAIL", "WIRING: UNKNOWN"):
        assert token in s, token


def test_docs_forbid_halting_bootstrap_on_a_wiring_failure():
    """The whole reason this is not folded into INSTALL: a settings source the
    check cannot see would otherwise halt a run that no local edit can clear."""
    s = _wiring_section()
    assert "never halt bootstrap" in s
    assert "not a reason to stop" in s


def test_every_detail_line_is_documented_with_a_remedy_and_implemented():
    """Bidirectional, like the install-check contract: a token in one and not the
    other is how docs and implementation drift without anything failing."""
    s = _wiring_section()
    script = SCRIPT.read_text()
    for token in ("HOOK_NOT_WIRED", "HOOK_WIRED_WRONG_MATCHER", "HOOK_WIRED_STALE_PATH"):
        assert token in s, f"{token} implemented but not documented"
        assert token in script, f"{token} documented but not implemented"
    # the remedies must be runnable text, not descriptions
    assert '"matcher"' in s and "settings.json" in s
    assert "$HOME/.claude/skills/h-mad/hooks/" in s


def test_docs_explain_the_uncovered_field_and_the_source_search():
    s = _wiring_section()
    assert "uncovered=" in s
    assert "CLAUDE_CONFIG_DIR" in s
    # precedence trap: `a and b or c` is `(a and b) or c` -- assert one claim each
    assert "from the working directory **up**" in s or "from the working directory up" in s
    assert "wired by an ancestor still counts" in s


def test_docs_say_wiring_is_only_confirmable_live():
    """Hooks snapshot at session start, so a PASS describes the next session."""
    s = _wiring_section()
    assert "snapshotted at session start" in s
    assert "next" in s


def test_helper_registry_lists_it():
    text = SKILL_MD.read_text()
    registry = text.split("## Helper scripts", 1)[1]
    assert "h_mad_hook_wiring.py" in registry


def test_bootstrap_obliges_the_wiring_check_to_be_run():
    """A check nothing is obliged to run is advisory, and this one exists precisely
    because the failure it detects is invisible everywhere else."""
    text = SKILL_MD.read_text()
    boot = text.split("## First-run auto-bootstrap", 1)[1].split("\n## ", 1)[0]
    boot = " ".join(boot.split())
    assert "h_mad_hook_wiring.py" in boot
    assert "not optional to *run*" in boot
