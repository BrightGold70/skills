"""Task 21 RED: D19's out-of-root tool-call scan and exact CLI tokens.

The new module is loaded inside each test, so its absence is a per-node RED,
not a collection failure. No real session store or checkout is inspected.
"""

import json
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

import pytest

from grokauditfixtures import _hostile_text, load_probe


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/h_mad_tool_calls.py"
SPELLINGS = ("absolute", "tilde", "home", "brace")


@pytest.fixture
def scan_module(request):
    def load():
        try:
            return load_probe(SCRIPT)
        except FileNotFoundError as exc:
            exc.add_note(
                f"{request.node.name}: new h_mad_tool_calls module is absent; "
                "the test below pins the named D19 behavior through main(scan)."
            )
            raise
    return load


@pytest.fixture
def scan_case(tmp_path, monkeypatch):
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")
    monkeypatch.delenv("HMAD_DISPATCH_BOUNDARY", raising=False)
    return {
        "root": "/audit/roots/gas-root-d1-s2v1-314",
        "checkout": "/live/skills",
        "home": "/users/auditor",
        "needle_dirs": [],
        "log": tmp_path / "agent [a]* ⟦h-mad⟧.log",
    }


def _grok(*paths):
    return json.dumps({
        "type": "tool_call", "toolCallId": "call-1", "toolName": "read_file",
        "rawInput": {"nested": [{"path": path} for path in paths],
                     "agent_text": _hostile_text()},
        "locations": [],
    }, ensure_ascii=False) + "\n"


def _own_session(case):
    return f"{case['home']}/.grok/sessions/{quote(case['root'], safe='')}"


def _spell(path, spelling, home):
    prefixes = {"absolute": home + "/", "tilde": "~/",
                "home": "$HOME/", "brace": "${HOME}/"}
    assert path.startswith(home + "/"), "fixture spelling must refer to the synthetic home"
    return prefixes[spelling] + path[len(home) + 1:]


def _argv(case, surface="grok"):
    args = ["scan", "--surface", surface, "--log", str(case["log"]),
            "--root", case["root"], "--checkout", case["checkout"],
            "--home", case["home"]]
    for needle in case["needle_dirs"]:
        args.extend(["--needle-dir", needle])
    return args


def _token(surface="grok", word="CLEAN", *, calls=1, out_of_root=0,
           checkout=0, exempt=0, nonjson=0, mcp_unmeasured=0):
    last = (f"mcp_unmeasured={mcp_unmeasured}" if surface == "codex"
            else f"nonjson={nonjson}")
    return (f"TOOLSCAN: {word} surface={surface} calls={calls} "
            f"out_of_root={out_of_root} checkout={checkout} exempt={exempt} {last}")


def _assert_scan(scan_module, case, capsys, text, token, *, surface="grok", rc=0,
                 extra=()):
    module = scan_module()
    if text is not None:
        case["log"].write_text(text, encoding="utf-8")
    capsys.readouterr()
    actual_rc = module.main([*_argv(case, surface), *extra])
    out, err = capsys.readouterr()
    assert (actual_rc, out.splitlines()[-1:]) == (rc, [token]), (
        f"D19 {token}: main(scan) must return {rc} and the exact last stdout line; "
        f"stdout={out!r}; stderr={err!r}"
    )
    assert sum(line.startswith("TOOLSCAN:") for line in out.splitlines()) == 1, (
        "main(scan) must emit exactly one TOOLSCAN token"
    )
    assert "Traceback" not in out + err, "declared scan outcomes must have no traceback"
    return module


def test_scan_grok_clean(scan_module, scan_case, capsys):
    case = scan_case
    path = case["root"] + "/nested/../docs/design.md"
    module = _assert_scan(scan_module, case, capsys, _grok(path), _token())
    assert module.named_paths([f"cat '{path}'"], case["home"]) == [
        case["root"] + "/docs/design.md"
    ], "named_paths must extract quoted absolute paths and lexically fold .."
    assert module.classify_path(case["root"], "grok", root=case["root"],
                                home=case["home"]) == "inside", "the root itself is inside"


def test_scan_counts_an_escape_after_a_non_json_line(scan_module, scan_case, capsys):
    case = scan_case
    expected = _token(word="OUT_OF_ROOT", out_of_root=1, nonjson=1)
    # ValueError and RecursionError both have to skip just this line. Each run
    # has only one malformed line followed by the same single escaped call.
    for bad_line in (_hostile_text().replace("\n", " "), "[" * 2000):
        _assert_scan(scan_module, case, capsys,
                     bad_line + "\n" + _grok(case["root"] + "-sibling/key.md"), expected)


def test_scan_grok_live_checkout_counts_checkout(scan_module, scan_case, capsys):
    _assert_scan(scan_module, scan_case, capsys,
                 _grok(scan_case["checkout"] + "/docs/answer-key.md"),
                 _token(word="OUT_OF_ROOT", out_of_root=1, checkout=1))


def test_scan_grok_absent_log_is_unreadable(scan_module, scan_case, capsys):
    _assert_scan(scan_module, scan_case, capsys, None,
                 "TOOLSCAN: UNREADABLE reason=log_absent", rc=2)


def test_scan_grok_no_event_is_unreadable(scan_module, scan_case, capsys):
    _assert_scan(scan_module, scan_case, capsys, _hostile_text() + "\n",
                 "TOOLSCAN: UNREADABLE reason=no_event", rc=2)


def test_scan_dev_path_is_exempt(scan_module, scan_case, capsys):
    _assert_scan(scan_module, scan_case, capsys, _grok("/dev/null"), _token(exempt=1))


@pytest.mark.parametrize("spelling", SPELLINGS, ids=SPELLINGS)
def test_scan_own_session_dir_is_exempt(scan_module, scan_case, capsys, spelling):
    case = scan_case
    path = _spell(_own_session(case) + "/history.json", spelling, case["home"])
    module = _assert_scan(scan_module, case, capsys, _grok(path), _token(exempt=1))
    assert module.named_paths([path], case["home"]) == [_own_session(case) + "/history.json"], (
        f"named_paths must expand the {spelling} spelling before classification"
    )


@pytest.mark.parametrize("spelling", SPELLINGS, ids=SPELLINGS)
def test_scan_grok_skills_is_exempt(scan_module, scan_case, capsys, spelling):
    case = scan_case
    path = _spell(case["home"] + "/.grok/skills/audit/SKILL.md", spelling, case["home"])
    _assert_scan(scan_module, case, capsys, _grok(path), _token(exempt=1))


def test_scan_other_session_dir_is_out_of_root(scan_module, scan_case, capsys):
    # A sibling with the own key as a prefix must not inherit its exemption.
    _assert_scan(scan_module, scan_case, capsys,
                 _grok(_own_session(scan_case) + "-other/history.json"),
                 _token(word="OUT_OF_ROOT", out_of_root=1))


def test_scan_sessions_dir_itself_is_out_of_root(scan_module, scan_case, capsys):
    _assert_scan(scan_module, scan_case, capsys,
                 _grok(scan_case["home"] + "/.grok/sessions"),
                 _token(word="OUT_OF_ROOT", out_of_root=1))


def test_scan_other_grok_path_is_out_of_root(scan_module, scan_case, capsys):
    case = scan_case
    # locations is an independent path source, not agent narration or rawOutput.
    text = json.dumps({"type": "tool_call", "rawInput": {"note": _hostile_text()},
                       "locations": [{"path": case["home"] + "/.grok/settings.json"}]}) + "\n"
    _assert_scan(scan_module, case, capsys, text, _token(word="OUT_OF_ROOT", out_of_root=1))


def test_scan_mixed_exempt_and_out_of_root_counts_out_of_root(scan_module, scan_case, capsys):
    _assert_scan(scan_module, scan_case, capsys, _grok("/dev/null", "/outside/key.md"),
                 _token(word="OUT_OF_ROOT", out_of_root=1, exempt=0))


def test_scan_codex_own_looking_session_path_is_out_of_root(scan_module, scan_case, capsys):
    text = f"exec\ncat '{_own_session(scan_case)}/history.json'\n succeeded in 1ms:\n"
    _assert_scan(scan_module, scan_case, capsys, text,
                 _token("codex", "OUT_OF_ROOT", out_of_root=1), surface="codex")


def test_scan_codex_no_call_is_unmeasured(scan_module, scan_case, capsys):
    text = ('tool filesystem.read_file({"path":"/outside/key.md"})\n'
            + "codex\n" + _hostile_text() + "\n")
    _assert_scan(scan_module, scan_case, capsys, text,
                 _token("codex", "UNMEASURED", calls=0, mcp_unmeasured=1), surface="codex")


def test_scan_codex_skips_the_prompt_echo(scan_module, scan_case, capsys):
    root = scan_case["root"]
    boundary = "===HMAD-DISPATCH-BOUNDARY==="
    text = (f"exec\ncat /outside/echo.md\n{boundary}\n"
            f"exec\ncat /outside/older-echo.md\n{boundary}\n"
            f"exec\ncat {root}/docs/plan.md in {root}\n succeeded in 1ms:\n"
            "/outside/tool-output.md\ncodex\n" + _hostile_text() + "\n")
    _assert_scan(scan_module, scan_case, capsys, text, _token("codex"), surface="codex")


def test_scan_agy_groups_active_and_done_events(scan_module, scan_case, capsys):
    events = []
    # Both key components matter: one repeated step in a different conversation
    # and a different step in the first conversation are distinct calls.
    for conversation, index in (("a", 7), ("b", 7), ("a", 8)):
        for state in ("ACTIVE", "DONE"):
            events.append(json.dumps({"event": "step_update", "step_update": {
                "step_type": "tool", "conversation_id": conversation, "step_index": index,
                "state": state, "tool_info": {"parameters": {
                    "nested": [{"path": scan_case["root"] + "/docs/plan.md"}],
                    "agent_text": _hostile_text(),
                }},
            }}))
    _assert_scan(scan_module, scan_case, capsys, "\n".join(events) + "\n",
                 _token("agy", calls=3), surface="agy")


def test_scan_cli_and_function_agree(scan_module, scan_case, capsys):
    case = scan_case
    text = _grok("/dev/null") + _grok(case["root"] + "/docs/plan.md")
    expected = _token(calls=2, exempt=1)
    module = _assert_scan(scan_module, case, capsys, text, expected)
    result = module.scan_log(text, "grok", **{
        key: case[key] for key in ("root", "checkout", "home", "needle_dirs")
    })
    assert {key: result[key] for key in ("calls", "out_of_root", "checkout", "exempt", "nonjson")} == {
        "calls": 2, "out_of_root": 0, "checkout": 0, "exempt": 1, "nonjson": 0,
    }, "scan_log and main(scan) must report the same per-call classification counts"
    cli = subprocess.run([sys.executable, str(SCRIPT), *_argv(case)],
                         capture_output=True, text=True, timeout=15)
    assert (cli.returncode, cli.stdout.splitlines()[-1:]) == (0, [expected]), (
        f"standalone CLI must agree with main and scan_log: {cli.stdout!r}; {cli.stderr!r}"
    )
    assert sum(line.startswith("TOOLSCAN:") for line in cli.stdout.splitlines()) == 1
    assert "Traceback" not in cli.stdout + cli.stderr
    assert "json.load(" not in SCRIPT.read_text(encoding="utf-8"), (
        "D19 forbids a whole-stream json.load reader"
    )


def test_scan_grok_needle_dir_counts_checkout(scan_module, scan_case, capsys):
    scan_case["needle_dirs"] = ["docs/archive/2099-01", "docs/archive/2099-02"]
    _assert_scan(scan_module, scan_case, capsys,
                 _grok("/elsewhere/export/docs/archive/2099-02/paper-lantern/design.md"),
                 _token(word="OUT_OF_ROOT", out_of_root=1, checkout=1))


def test_scan_grok_unreadable_log_is_unreadable(scan_module, scan_case, capsys):
    scan_case["log"].mkdir()
    _assert_scan(scan_module, scan_case, capsys, None,
                 "TOOLSCAN: UNREADABLE reason=log_unreadable", rc=2)


def test_scan_usage_error_is_internal(scan_module, scan_case, capsys):
    _assert_scan(scan_module, scan_case, capsys, _grok(scan_case["root"]),
                 "TOOLSCAN: UNREADABLE reason=internal:UsageError", rc=2,
                 extra=("--unknown-scan-flag",))
