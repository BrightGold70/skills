"""Task 14f: a grok `grep` call's `pattern` is a content regex, not a path the call reads.

Run 4 (docs/03-analysis/grok-audit-surface.incident-2026-10-23-run4-toolscan-false-positive.md)
halted at S2 d2 on `out_of_root=1` from one call, whose regex was `python3\\.11|/opt/anaconda3`.
Only that argument stops being a path source. The call's `path`, `glob` and `locations`, and
every argument of every other tool, are still scanned.
"""
from __future__ import annotations

import json

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


def test_a_pattern_argument_of_another_tool_is_still_scanned(scan_module, scan_case, capsys):
    case = scan_case
    text = json.dumps({
        "type": "tool_call", "toolCallId": "call-r", "toolName": "read_file",
        "rawInput": {"pattern": "/opt/anaconda3/lib", "target_file": case["root"] + "/a.md"},
        "locations": [],
    }) + "\n"
    _assert_scan(scan_module, case, capsys, text, _token(word="OUT_OF_ROOT", out_of_root=1))
