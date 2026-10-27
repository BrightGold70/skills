"""Task 14f: a grok `grep` call's `pattern` is a content regex, not a path the call reads.

Run 4 (docs/03-analysis/grok-audit-surface.incident-2026-10-23-run4-toolscan-false-positive.md)
halted at S2 d2 on `out_of_root=1` from one call, whose regex was `python3\\.11|/opt/anaconda3`.
Only that argument stops being a path source. The call's `path`, `glob` and `locations`, and
every argument of every other tool, are still scanned.
"""
from __future__ import annotations

import json

import pytest

from grokauditfixtures import _hostile_text
from test_grok_audit_surface_containment import _assert_scan, _token, scan_case, scan_module  # noqa: F401


def _grep(**raw_input):
    return json.dumps({
        "type": "tool_call", "toolCallId": "call-g", "toolName": "grep", "kind": "search",
        "rawInput": dict(raw_input, agent_text=_hostile_text()),
        "locations": [],
    }, ensure_ascii=False) + "\n"


def test_grep_pattern_naming_an_outside_path_is_clean(scan_module, scan_case, capsys):
    # The run-4 d2 call, verbatim apart from the glob.
    _assert_scan(scan_module, scan_case, capsys,
                 _grep(pattern="python3\\.11|/opt/anaconda3", glob="**/test_h_mad_audit_cycle.py",
                       head_limit=15),
                 _token())


def test_grep_pattern_naming_the_checkout_counts_nothing(scan_module, scan_case, capsys):
    case = scan_case
    _assert_scan(scan_module, case, capsys,
                 _grep(pattern=f"see {case['checkout']}/docs/answer-key.md"),
                 _token())


def test_grep_path_outside_the_root_is_still_out_of_root(scan_module, scan_case, capsys):
    case = scan_case
    _assert_scan(scan_module, case, capsys,
                 _grep(pattern="status", path=case["checkout"] + "/docs"),
                 _token(word="OUT_OF_ROOT", out_of_root=1, checkout=1))


def test_grep_glob_naming_the_checkout_is_still_out_of_root(scan_module, scan_case, capsys):
    case = scan_case
    _assert_scan(scan_module, case, capsys,
                 _grep(pattern="status", glob=case["checkout"] + "/docs/*.md"),
                 _token(word="OUT_OF_ROOT", out_of_root=1, checkout=1))


def _tool(tool_name, **raw_input):
    return json.dumps({
        "type": "tool_call", "toolCallId": "call-t", "toolName": tool_name,
        "rawInput": raw_input, "locations": [],
    }, ensure_ascii=False) + "\n"


def test_write_content_naming_an_outside_path_is_clean(scan_module, scan_case, capsys):
    # Task 14g, the run-6 d3 call: the report is written inside the root; its prose names /tmp.
    case = scan_case
    _assert_scan(scan_module, case, capsys,
                 _tool("write", file_path=case["root"] + "/.hmad-report/p3.report.md",
                       content="## Summary\nThe plan writes to /tmp/audit_x and reads "
                               + case["checkout"] + "/docs/answer-key.md."),
                 _token())


def test_search_replace_strings_naming_an_outside_path_are_clean(scan_module, scan_case, capsys):
    case = scan_case
    _assert_scan(scan_module, case, capsys,
                 _tool("search_replace", file_path=case["root"] + "/.hmad-report/p3.report.md",
                       old_string="see /codex/step3", new_string="see " + case["checkout"] + "/x"),
                 _token())


def test_write_file_path_outside_the_root_is_still_out_of_root(scan_module, scan_case, capsys):
    case = scan_case
    _assert_scan(scan_module, case, capsys,
                 _tool("write", file_path=case["checkout"] + "/docs/x.md", content="text"),
                 _token(word="OUT_OF_ROOT", out_of_root=1, checkout=1))


def test_search_replace_file_path_outside_the_root_is_still_out_of_root(scan_module, scan_case, capsys):
    case = scan_case
    _assert_scan(scan_module, case, capsys,
                 _tool("search_replace", file_path="/opt/elsewhere/x.md", old_string="a", new_string="b"),
                 _token(word="OUT_OF_ROOT", out_of_root=1))


def test_content_of_an_unknown_tool_is_still_scanned(scan_module, scan_case, capsys):
    _assert_scan(scan_module, scan_case, capsys,
                 _tool("brand_new_writer", content="/opt/anaconda3/lib"),
                 _token(word="OUT_OF_ROOT", out_of_root=1))


def test_a_pattern_argument_of_another_tool_is_still_scanned(scan_module, scan_case, capsys):
    case = scan_case
    text = json.dumps({
        "type": "tool_call", "toolCallId": "call-r", "toolName": "read_file",
        "rawInput": {"pattern": "/opt/anaconda3/lib", "target_file": case["root"] + "/a.md"},
        "locations": [],
    }) + "\n"
    _assert_scan(scan_module, case, capsys, text, _token(word="OUT_OF_ROOT", out_of_root=1))


# Task 14h (operator ruling 2026-10-24, "contamination-only halt"). The scan still reports every
# out-of-root call, but only CONTAMINATION stops a run or refuses a score: `checkout>0`. The
# `checkout` count now also covers `<home>/.local/state/h-mad` (other runs' roots and collected
# reports) and `<home>/.grok/sessions` outside the pass's own session directory. Run 7
# (docs/03-analysis/grok-audit-surface.incident-2026-10-24-run7-shell-home-tmp.md) halted at S2 d1
# on `out_of_root=1 checkout=0`, from `HOME=/tmp` in a `run_terminal_command`.
from test_grok_audit_surface_containment import (  # noqa: E402,F401
    _assert_containment_token, _containment_cli, _own_session, containment_home,
)
from test_grok_audit_surface_probe import (  # noqa: E402,F401
    _t27_assert_not_refused, _t27_containment_line, _t27_log, _t27_refusal, containment_score_case,
)

RUN7_COMMAND = ("export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 HOME=/tmp\n"
                "git log -1 --format=%H")


def _state_tree(case):
    return case["home"] + "/.local/state/h-mad"


def test_state_tree_path_of_another_run_counts_checkout(scan_module, scan_case, capsys):
    case = scan_case
    other = _state_tree(case) + "/grok-audit-surface/run-other [a]*/data/s2/d5/v1/p3.report.md"
    _assert_scan(scan_module, case, capsys, _tool("read_file", target_file=other),
                 _token(word="OUT_OF_ROOT", out_of_root=1, checkout=1))


def test_state_tree_path_in_tilde_spelling_counts_checkout(scan_module, scan_case, capsys):
    _assert_scan(scan_module, scan_case, capsys,
                 _tool("run_terminal_command",
                       command="find ~/.local/state/h-mad -name '*.report.md'"),
                 _token(word="OUT_OF_ROOT", out_of_root=1, checkout=1))


def test_own_root_under_the_state_tree_stays_inside(scan_module, scan_case, capsys):
    # The cycle's own root lives under the state tree; it is inside, never contamination.
    case = dict(scan_case)
    case["root"] = _state_tree(case) + "/grok-audit-surface/run-x/roots/gas-root-d1-s2v1-314"
    _assert_scan(scan_module, case, capsys,
                 _tool("read_file", target_file=case["root"] + "/docs/plan.md"), _token())


def test_state_tree_sibling_prefix_is_not_contamination(scan_module, scan_case, capsys):
    case = scan_case
    _assert_scan(scan_module, case, capsys,
                 _tool("read_file", target_file=case["home"] + "/.local/state/h-mad-other/x.md"),
                 _token(word="OUT_OF_ROOT", out_of_root=1))


def test_other_session_dir_in_tilde_spelling_counts_checkout(scan_module, scan_case, capsys):
    _assert_scan(scan_module, scan_case, capsys,
                 _tool("run_terminal_command", command="cat ~/.grok/sessions/another/prompt.md"),
                 _token(word="OUT_OF_ROOT", out_of_root=1, checkout=1))


def test_own_session_dir_stays_exempt_not_contamination(scan_module, scan_case, capsys):
    _assert_scan(scan_module, scan_case, capsys,
                 _tool("read_file", target_file=_own_session(scan_case) + "/history.json"),
                 _token(exempt=1))


def test_grok_settings_is_out_of_root_but_not_contamination(scan_module, scan_case, capsys):
    _assert_scan(scan_module, scan_case, capsys,
                 _tool("read_file", target_file=scan_case["home"] + "/.grok/settings.json"),
                 _token(word="OUT_OF_ROOT", out_of_root=1))


def test_run7_shell_home_tmp_is_out_of_root_but_not_contamination(scan_module, scan_case, capsys):
    # The run-7 d1 call, p3.log:1370: `/dev/null` is exempt, `/tmp` is out, nothing is contamination.
    _assert_scan(scan_module, scan_case, capsys,
                 _tool("run_terminal_command", command=RUN7_COMMAND, is_background=False),
                 _token(word="OUT_OF_ROOT", out_of_root=1))


RUN7_TOKEN = ("TOOLSCAN: OUT_OF_ROOT surface=grok calls=46 out_of_root=1 checkout=0 "
              "exempt=0 nonjson=6")


def _require_toolscan(case, token, name):
    token_file = case["home"] / f"{name} [*] ⟦h-mad⟧.txt"
    token_file.write_text(_hostile_text() + "\nREQUIRE: STOP reason=decoy\n" + token + "\n",
                          encoding="utf-8")
    halt = case["home"] / "HALT [*]"
    result = _containment_cli("require", "--verb", "toolscan", "--token-file", token_file,
                              "--halt-file", halt)
    return result, halt


def test_require_toolscan_out_of_root_without_contamination_is_ok(containment_home):
    result, halt = _require_toolscan(containment_home, RUN7_TOKEN, "run7")
    _assert_containment_token(result.returncode, result.stdout, result.stderr, 0, "REQUIRE: OK",
                              "require(toolscan) must accept OUT_OF_ROOT with checkout=0 (14h)")
    assert not halt.exists(), "an uncontaminated OUT_OF_ROOT scan must create no halt file"


@pytest.mark.parametrize("token", [
    "TOOLSCAN: OUT_OF_ROOT surface=grok calls=46 out_of_root=1 checkout=1 exempt=0 nonjson=6",
    "TOOLSCAN: OUT_OF_ROOT surface=grok calls=46 out_of_root=10 checkout=10 exempt=0 nonjson=0",
    "TOOLSCAN: OUT_OF_ROOT surface=codex calls=4 out_of_root=1 checkout=0 exempt=0 mcp_unmeasured=0",
], ids=["checkout-1", "checkout-10", "codex-surface"])
def test_require_toolscan_contamination_still_stops(containment_home, token):
    result, halt = _require_toolscan(containment_home, token, "contaminated")
    _assert_containment_token(result.returncode, result.stdout, result.stderr, 0,
                              "REQUIRE: STOP reason=" + token,
                              "require(toolscan) must stop on contamination or a non-grok token")
    assert halt.read_text(encoding="utf-8") == token + "\n", "the STOP must append its exact reason"


def _terminal_call(command):
    return json.dumps({"type": "tool_call", "toolCallId": "call-x", "toolName": "run_terminal_command",
                       "rawInput": {"command": command, "is_background": False},
                       "locations": []}) + "\n"


def test_probe_tmp_only_escape_is_published_not_refused(containment_score_case, capsys):
    case = containment_score_case
    log = _t27_log(case, "d1", 3)
    log.write_text(_terminal_call(RUN7_COMMAND), encoding="utf-8")
    line = _t27_containment_line(case, "d1", 3, "grok", log.read_text(encoding="utf-8"))
    assert " scan=OUT_OF_ROOT calls=1 out_of_root=1 checkout=0 " in line, line
    _t27_assert_not_refused(case, capsys, line)


def test_probe_live_checkout_in_a_shell_command_still_refuses(containment_score_case, capsys):
    case = containment_score_case
    _t27_log(case, "d1", 3).write_text(
        _terminal_call("cd /tmp/grok-audit-checkout && git log -1"), encoding="utf-8")
    _t27_refusal(case, capsys)


def test_probe_state_tree_in_a_shell_command_refuses(containment_score_case, capsys):
    case = containment_score_case
    _t27_log(case, "d1", 3).write_text(_terminal_call(
        "ls /tmp/grok-audit-home/.local/state/h-mad/grok-audit-surface"), encoding="utf-8")
    _t27_refusal(case, capsys)


# Task 14j: `scan_log` normalises every comparison base once, with `rstrip("/")`. A trailing
# slash on `--checkout` or `--needle-dir` failed the contamination count open (`checkout=0`); on
# `--root` it failed closed (the root and its own session read as out). `--home` is the parked
# 60635019 test in the containment module. A bare `/` normalises to the empty string, because
# every consumer appends `/` to its base.
def test_a_trailing_slash_checkout_still_counts_the_checkout_itself(scan_module, scan_case, capsys):
    case = scan_case
    checkout = case["checkout"]
    case["checkout"] = checkout + "/"
    _assert_scan(scan_module, case, capsys,
                 _tool("run_terminal_command", command=f"git -C {checkout} log -1"),
                 _token(word="OUT_OF_ROOT", out_of_root=1, checkout=1))


def test_a_trailing_slash_needle_dir_still_counts_contamination(scan_module, scan_case, capsys):
    scan_case["needle_dirs"] = ["docs/archive/2099-01", "docs/archive/2099-02/"]
    _assert_scan(scan_module, scan_case, capsys,
                 _tool("read_file",
                       target_file="/elsewhere/export/docs/archive/2099-02/paper-lantern/design.md"),
                 _token(word="OUT_OF_ROOT", out_of_root=1, checkout=1))


@pytest.mark.parametrize("which", ["root-itself", "own-session"])
def test_a_trailing_slash_root_keeps_its_own_paths(scan_module, scan_case, capsys, which):
    # Built from the slash-free root, before the slash is appended.
    case = scan_case
    target, token = {
        "root-itself": (case["root"], _token()),
        "own-session": (_own_session(case) + "/history.json", _token(exempt=1)),
    }[which]
    case["root"] = case["root"] + "/"
    _assert_scan(scan_module, case, capsys, _tool("read_file", target_file=target), token)


@pytest.mark.parametrize("tail", [
    "/.local/state/h-mad/grok-audit-surface/run-other/data/p3.report.md",
    "/.grok/sessions/another-root/history.json",
])
def test_a_bare_slash_home_still_counts_contamination(scan_module, scan_case, capsys, tail):
    # `/` normalises to "", so `"" + "/.local/state/h-mad"` is the state tree; `"/"` would
    # rebuild the `//` prefix that no path matches.
    scan_case["home"] = "/"
    _assert_scan(scan_module, scan_case, capsys, _tool("read_file", target_file=tail),
                 _token(word="OUT_OF_ROOT", out_of_root=1, checkout=1))


def test_a_bare_slash_needle_dir_counts_every_out_path(scan_module, scan_case, capsys):
    scan_case["needle_dirs"] = ["/"]
    _assert_scan(scan_module, scan_case, capsys, _tool("read_file", target_file="/elsewhere/x.md"),
                 _token(word="OUT_OF_ROOT", out_of_root=1, checkout=1))


@pytest.mark.parametrize("base, target", [
    ("checkout", "/live/skills-other/x.md"),
    ("needle", "/elsewhere/export/docs/archive/2099-020/x.md"),
    ("home", "/users/auditor/.local/state/h-mad-other/x.md"),
], ids=["checkout", "needle", "home"])
def test_a_trailing_slash_base_matches_no_sibling_prefix(scan_module, scan_case, capsys, base, target):
    # Guard: normalising a base must not widen it to a sibling sharing its prefix.
    case = scan_case
    if base == "needle":
        case["needle_dirs"] = ["docs/archive/2099-02/"]
    else:
        case[base] = case[base] + "/"
    _assert_scan(scan_module, case, capsys, _tool("read_file", target_file=target),
                 _token(word="OUT_OF_ROOT", out_of_root=1))


# Task 14j fix: a base is normalised the way `named_paths` normalises a path (`posixpath.normpath`),
# so an interior `//` or `/./` no longer fails the count open, and a leading `//`, which `normpath`
# keeps, folds to `/`: the path grammar never extracts a `//`-led path, and `~/` paths are rebuilt
# from the normalised home. Every target is built from the normal base.
def _respell(base, separator):
    cut = base.index("/", 1)
    return base[:cut] + separator + base[cut:]


@pytest.mark.parametrize("separator", ["/", "/."], ids=["double-slash", "dot"])
@pytest.mark.parametrize("base", ["home", "checkout", "needle"])
def test_an_unnormal_base_still_counts_contamination(scan_module, scan_case, capsys, base, separator):
    case = scan_case
    target = {
        "home": case["home"] + "/.local/state/h-mad/grok-audit-surface/run-other/data/p3.report.md",
        "checkout": case["checkout"] + "/docs/answer-key.md",
        "needle": "/elsewhere/export/docs/archive/2099-02/paper-lantern/design.md",
    }[base]
    if base == "needle":
        case["needle_dirs"] = [_respell("docs/archive/2099-02", separator)]
    else:
        case[base] = _respell(case[base], separator)
    _assert_scan(scan_module, case, capsys, _tool("read_file", target_file=target),
                 _token(word="OUT_OF_ROOT", out_of_root=1, checkout=1))


@pytest.mark.parametrize("which", ["root-child", "own-session"])
@pytest.mark.parametrize("separator", ["/", "/."], ids=["double-slash", "dot"])
def test_an_unnormal_root_keeps_its_own_paths(scan_module, scan_case, capsys, separator, which):
    case = scan_case
    target, token = {
        "root-child": (case["root"] + "/docs/design.md", _token()),
        "own-session": (_own_session(case) + "/history.json", _token(exempt=1)),
    }[which]
    case["root"] = _respell(case["root"], separator)
    _assert_scan(scan_module, case, capsys, _tool("read_file", target_file=target), token)


@pytest.mark.parametrize("base", ["home", "checkout", "root"])
def test_a_leading_double_slash_base_matches_its_single_slash_paths(scan_module, scan_case, capsys,
                                                                    base):
    case = scan_case
    target, token = {
        "home": (case["home"] + "/.grok/sessions/another-root/history.json",
                 _token(word="OUT_OF_ROOT", out_of_root=1, checkout=1)),
        "checkout": (case["checkout"] + "/docs/answer-key.md",
                     _token(word="OUT_OF_ROOT", out_of_root=1, checkout=1)),
        "root": (case["root"] + "/docs/design.md", _token()),
    }[base]
    case[base] = "/" + case[base]
    _assert_scan(scan_module, case, capsys, _tool("read_file", target_file=target), token)


def test_an_empty_needle_dir_counts_every_out_path(scan_module, scan_case, capsys):
    # Guard: `normpath("")` is ".", and a needle "." matches nothing; "" keeps meaning every path.
    scan_case["needle_dirs"] = [""]
    _assert_scan(scan_module, scan_case, capsys, _tool("read_file", target_file="/elsewhere/x.md"),
                 _token(word="OUT_OF_ROOT", out_of_root=1, checkout=1))
