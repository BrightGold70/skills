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


# Task 22 RED: quarantine and token consumption. Load the new module per node.
CONTAINMENT_SCRIPT = SCRIPT.with_name("h_mad_grok_containment.py")


@pytest.fixture
def containment_module(request):
    def load():
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "h_mad_grok_containment_under_test", CONTAINMENT_SCRIPT,
        )
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except FileNotFoundError as exc:
            exc.add_note(
                f"{request.node.name}: new containment module is absent; "
                "main(quarantine/require) must enforce the behavior asserted below."
            )
            raise
        return module
    return load


@pytest.fixture
def containment_home(tmp_path, monkeypatch):
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")
    home = tmp_path / "home [*] 'quoted' ⟦h-mad⟧"
    store = home / ".grok/sessions"
    store.mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    return {
        "home": home, "store": store,
        "parent": home / ".local/state/h-mad/grok-audit-surface",
    }


def _containment_cli(*argv):
    return subprocess.run(
        [sys.executable, str(CONTAINMENT_SCRIPT), *map(str, argv)],
        capture_output=True, text=True, timeout=15,
    )


def _containment_main(module, capsys, *argv):
    capsys.readouterr()
    rc = module.main(list(map(str, argv)))
    out, err = capsys.readouterr()
    return rc, out, err


def _assert_containment_token(rc, out, err, expected_rc, token, property_name):
    assert (rc, out.splitlines()[-1:]) == (expected_rc, [token]), (
        f"{property_name}: exit and exact last stdout token must agree; "
        f"stdout={out!r}; stderr={err!r}"
    )
    assert "Traceback" not in out + err, f"{property_name}: no traceback may escape"


def _assert_quarantine_verified(case, rc, out, err, count):
    import re

    last = out.splitlines()[-1:]
    prefix = f"QUARANTINE: VERIFIED moved={count} dest="
    assert (rc, bool(last and last[0].startswith(prefix))) == (0, True), (
        f"quarantine must verify exactly {count} renamed entries: "
        f"stdout={out!r}; stderr={err!r}"
    )
    destination = Path(last[0][len(prefix):])
    _assert_containment_token(
        rc, out, err, 0, prefix + str(destination), "quarantine verification",
    )
    assert destination.is_absolute() and destination.parent == case["parent"], (
        "quarantine destination must be absolute and under the stand-in HOME state directory"
    )
    assert re.fullmatch(r"grok-quarantine-\d{8}T\d{6}Z", destination.name), (
        "quarantine directory must use the documented UTC timestamp spelling"
    )
    assert destination.is_dir(), "verified quarantine must exist"
    assert list(case["parent"].iterdir()) == [destination], "create exactly one quarantine"
    return destination


def _session_directory(case, name="session-gas-root-d1 [*] ⟦h-mad⟧"):
    path = case["store"] / name
    path.mkdir()
    (path / "history [a]*.txt").write_text(_hostile_text(), encoding="utf-8")
    return path


def test_quarantine_verifies_and_moves_every_match(containment_home):
    case = containment_home
    directory = _session_directory(case)
    ordinary = _session_directory(case, "ordinary [a]* **bold**")
    (case["store"] / "gas-root-file [*]").write_text(_hostile_text(), encoding="utf-8")
    outside = case["home"] / "outside [*]"
    outside.mkdir()
    (outside / "gas-root-do-not-follow").write_text(_hostile_text(), encoding="utf-8")
    link = case["store"] / "link-gas-root-symlink"
    link.symlink_to(outside, target_is_directory=True)
    dangling = case["store"] / "dangling-gas-root-link"
    dangling.symlink_to(case["home"] / "absent target")
    matching = {directory.name, "gas-root-file [*]", link.name, dangling.name}
    result = _containment_cli("quarantine")
    dest = _assert_quarantine_verified(case, result.returncode, result.stdout, result.stderr, 4)
    assert {p.name for p in dest.iterdir()} == matching, "move every matching entry of any kind"
    assert {p.name for p in case["store"].iterdir()} == {ordinary.name}, (
        "nonmatching sessions must stay in the store"
    )
    assert sorted(result.stdout.splitlines()[:-1]) == sorted(f"MOVED: {n}" for n in matching), (
        "publish exactly one MOVED line per renamed entry"
    )
    assert (dest / directory.name / "history [a]*.txt").read_text(encoding="utf-8") == _hostile_text()
    assert (dest / link.name).is_symlink() and (dest / dangling.name).is_symlink(), (
        "rename symlinks themselves, including dangling symlinks"
    )
    assert {p.name for p in outside.iterdir()} == {"gas-root-do-not-follow"}, (
        "never traverse or move a matching symlink target"
    )
    assert (outside / "gas-root-do-not-follow").read_text(encoding="utf-8") == _hostile_text()


def test_quarantine_verifies_zero_matches(containment_home):
    case = containment_home
    ordinary = _session_directory(case, "ordinary [a]*")
    result = _containment_cli("quarantine")
    dest = _assert_quarantine_verified(case, result.returncode, result.stdout, result.stderr, 0)
    assert not list(dest.iterdir()), "zero matches must create an empty verified quarantine"
    assert list(case["store"].iterdir()) == [ordinary], "zero matches must preserve ordinary sessions"
    assert len(result.stdout.splitlines()) == 1, "zero moves must publish no MOVED lines"


def test_quarantine_refuses_an_existing_quarantine(containment_module, containment_home,
                                                  monkeypatch, capsys):
    module, case = containment_module(), containment_home
    session = _session_directory(case)
    real_mkdir = module.os.mkdir
    collisions = []

    def mkdir_with_collision(path, *args, **kwargs):
        candidate = Path(path)
        if candidate.name.startswith("grok-quarantine-") and not collisions:
            real_mkdir(path, *args, **kwargs)
            (candidate / "preserve.txt").write_text(_hostile_text(), encoding="utf-8")
            collisions.append(candidate)
        return real_mkdir(path, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(module.os, "mkdir", mkdir_with_collision)
        rc, out, err = _containment_main(module, capsys, "quarantine")
    _assert_containment_token(rc, out, err, 0, "QUARANTINE: REFUSED reason=quarantine_exists",
                              "an existing quarantine must refuse before any move")
    assert len(collisions) == 1, "exclusive os.mkdir must attempt the quarantine path"
    assert (collisions[0] / "preserve.txt").read_text(encoding="utf-8") == _hostile_text()
    assert session.is_dir() and "MOVED:" not in out, "collision must preserve all store entries"


def test_quarantine_refuses_a_failed_move(containment_module, containment_home,
                                         monkeypatch, capsys):
    module, case = containment_module(), containment_home
    failed = _session_directory(case, "failed-gas-root-entry")
    moved = _session_directory(case, "other-gas-root-entry")
    real_rename = module.os.rename

    def fail_one(src, dst, *args, **kwargs):
        if Path(src).name == failed.name:
            raise OSError("synthetic cross-filesystem move refusal")
        return real_rename(src, dst, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(module.os, "rename", fail_one)
        rc, out, err = _containment_main(module, capsys, "quarantine")
    _assert_containment_token(rc, out, err, 0, "QUARANTINE: REFUSED reason=move_failed:1",
                              "a failed rename takes precedence over matching residue")
    assert failed.is_dir() and not moved.exists(), "one failed rename must not prevent other moves"
    assert out.splitlines()[:-1] == [f"MOVED: {moved.name}"], "only successful moves are published"
    assert (next(case["parent"].iterdir()) / moved.name).is_dir(), "successful moves are retained"


def test_quarantine_refuses_residue(containment_module, containment_home, monkeypatch, capsys):
    module, case = containment_module(), containment_home
    original = _session_directory(case)
    real_rename = module.os.rename

    def rename_and_plant_residue(src, dst, *args, **kwargs):
        result = real_rename(src, dst, *args, **kwargs)
        _session_directory(case, "late-gas-root-residue")
        # Also create a count mismatch, pinning residue's earlier priority.
        (Path(dst).parent / "unexpected.txt").write_text(_hostile_text(), encoding="utf-8")
        return result

    with monkeypatch.context() as patch:
        patch.setattr(module.os, "rename", rename_and_plant_residue)
        rc, out, err = _containment_main(module, capsys, "quarantine")
    _assert_containment_token(rc, out, err, 0, "QUARANTINE: REFUSED reason=residue:1",
                              "post-move matching residue takes precedence over count mismatch")
    assert not original.exists() and (case["store"] / "late-gas-root-residue").is_dir()


def test_quarantine_refuses_a_count_mismatch(containment_module, containment_home,
                                            monkeypatch, capsys):
    module, case = containment_module(), containment_home
    session = _session_directory(case)
    real_rename = module.os.rename

    def rename_and_plant_extra(src, dst, *args, **kwargs):
        result = real_rename(src, dst, *args, **kwargs)
        (Path(dst).parent / "extra-gas-root-entry").mkdir()
        return result

    with monkeypatch.context() as patch:
        patch.setattr(module.os, "rename", rename_and_plant_extra)
        rc, out, err = _containment_main(module, capsys, "quarantine")
    _assert_containment_token(rc, out, err, 0, "QUARANTINE: REFUSED reason=count_mismatch",
                              "a quarantine listing count different from the source count must refuse")
    assert not session.exists() and not list(case["store"].iterdir()), "no residue masks the count check"


def test_quarantine_refuses_an_unreadable_store(containment_home):
    case = containment_home
    # Use a different synthetic HOME with no store; no permission/chmod assumptions.
    import os

    env = os.environ.copy()
    env["HOME"] = str(case["home"] / "missing store home [*]")
    result = subprocess.run([sys.executable, str(CONTAINMENT_SCRIPT), "quarantine"],
                            env=env, capture_output=True, text=True, timeout=15)
    _assert_containment_token(result.returncode, result.stdout, result.stderr, 0,
                              "QUARANTINE: REFUSED reason=unreadable",
                              "an absent store must be an unreadable determined verdict")


def test_quarantine_never_deletes(containment_module, containment_home, monkeypatch, capsys):
    import shutil

    module, case = containment_module(), containment_home
    entries = [_session_directory(case, f"directory-gas-root-{n} [*]") for n in range(3)]
    inodes = {entry.name: entry.stat().st_ino for entry in entries}
    calls = []

    def record(*args, **kwargs):
        calls.append((args, kwargs))

    with monkeypatch.context() as patch:
        patch.setattr(shutil, "rmtree", record)
        patch.setattr(module.os, "unlink", record)
        patch.setattr(module.os, "rmdir", record)
        rc, out, err = _containment_main(module, capsys, "quarantine")
    assert not calls, "quarantine must never call rmtree, unlink or rmdir, including copy-then-delete"
    dest = _assert_quarantine_verified(case, rc, out, err, len(entries))
    for entry in entries:
        locations = [p for p in (entry, dest / entry.name) if p.exists()]
        assert len(locations) == 1, "each directory must remain in exactly the store or quarantine"
        assert locations[0].stat().st_ino == inodes[entry.name], "moves must preserve directory identity"
        assert (locations[0] / "history [a]*.txt").read_text(encoding="utf-8") == _hostile_text()
    source = CONTAINMENT_SCRIPT.read_text(encoding="utf-8")
    import re

    assert not re.search(r"shutil\.(copy|rmtree)|os\.(unlink|remove|rmdir)", source), (
        "AC-T22.2: quarantine source must contain no copy or delete calls before Task 23"
    )


def test_quarantine_internal_on_an_injected_exception(containment_module, containment_home,
                                                      monkeypatch, capsys):
    module, case = containment_module(), containment_home
    entries = [_session_directory(case, f"session-gas-root-{n}") for n in range(2)]

    def explode(*args, **kwargs):
        raise RuntimeError("synthetic move-step failure")

    with monkeypatch.context() as patch:
        patch.setattr(module.os, "rename", explode)
        rc, out, err = _containment_main(module, capsys, "quarantine")
    _assert_containment_token(rc, out, err, 2, "QUARANTINE: REFUSED reason=internal:RuntimeError",
                              "an unexpected move exception must reach the exit-2 last resort")
    assert all(entry.is_dir() for entry in entries), "an injected pre-move exception must preserve every match"
    assert "MOVED:" not in out, "a raised move must never be published as successful"


def test_quarantine_internal_on_a_usage_error(containment_home):
    case = containment_home
    session = _session_directory(case)
    result = _containment_cli("quarantine", "--no-such-flag")
    _assert_containment_token(result.returncode, result.stdout, result.stderr, 2,
                              "QUARANTINE: REFUSED reason=internal:UsageError",
                              "quarantine usage errors must print the exact exit-2 last-resort token")
    assert session.is_dir(), "a usage error must move nothing"
    assert not case["parent"].exists(), "a usage error must create no quarantine"


def test_quarantine_creates_the_quarantine_before_listing_the_store(
        containment_module, tmp_path, monkeypatch, capsys):
    import re

    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")
    module = containment_module()
    collision_home = tmp_path / "collision home [*] 'quoted' ⟦h-mad⟧"
    collision_home.mkdir()
    monkeypatch.setenv("HOME", str(collision_home))
    assert not (collision_home / ".grok/sessions").exists()
    real_mkdir = module.os.mkdir
    collisions = []

    def mkdir_with_collision(path, *args, **kwargs):
        candidate = Path(path)
        if candidate.name.startswith("grok-quarantine-") and not collisions:
            real_mkdir(path, *args, **kwargs)
            collisions.append(candidate)
        return real_mkdir(path, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(module.os, "mkdir", mkdir_with_collision)
        rc, out, err = _containment_main(module, capsys, "quarantine")
    _assert_containment_token(
        rc, out, err, 0, "QUARANTINE: REFUSED reason=quarantine_exists",
        "D20 must attempt exclusive quarantine creation before listing an absent store",
    )
    assert len(collisions) == 1, "exclusive quarantine creation must be attempted once"

    unreadable_home = tmp_path / "unreadable home [*] 'quoted' ⟦h-mad⟧"
    unreadable_home.mkdir()
    monkeypatch.setenv("HOME", str(unreadable_home))
    assert not (unreadable_home / ".grok/sessions").exists()
    rc, out, err = _containment_main(module, capsys, "quarantine")
    _assert_containment_token(
        rc, out, err, 0, "QUARANTINE: REFUSED reason=unreadable",
        "D20 must create the quarantine before reporting the absent store as unreadable",
    )
    parent = unreadable_home / ".local/state/h-mad/grok-audit-surface"
    assert parent.is_dir(), "quarantine parent must exist when store listing fails"
    destinations = list(parent.iterdir())
    assert len(destinations) == 1, "an absent store must leave exactly one quarantine"
    destination = destinations[0]
    assert destination.is_dir(), "the created quarantine entry must be a directory"
    assert re.fullmatch(r"grok-quarantine-\d{8}T\d{6}Z", destination.name), (
        "the created quarantine must use the documented UTC timestamp spelling"
    )
    assert not list(destination.iterdir()), "an absent store must leave the quarantine empty"


@pytest.mark.parametrize("verb,token", [
    ("toolscan", "TOOLSCAN: CLEAN surface=grok calls=1 out_of_root=0 checkout=0 exempt=0 nonjson=0"),
    ("grok-canary", "GROK-CANARY: PASS"),
    ("quarantine", "QUARANTINE: VERIFIED moved=2 dest=/synthetic/quarantine"),
], ids=["toolscan", "grok-canary", "quarantine"])
def test_require_ok_per_verb(containment_home, verb, token):
    token_file = containment_home["home"] / "clean [*] ⟦h-mad⟧.txt"
    token_file.write_text(_hostile_text() + "\nREQUIRE: STOP reason=decoy\n" + token + "\n",
                          encoding="utf-8")
    halt = containment_home["home"] / "HALT"
    result = _containment_cli("require", "--verb", verb, "--token-file", token_file,
                              "--halt-file", halt)
    _assert_containment_token(result.returncode, result.stdout, result.stderr, 0, "REQUIRE: OK",
                              f"require({verb}) must accept its own clean last line only")
    assert not halt.exists(), "an accepted token must create no halt file"


@pytest.mark.parametrize("verb,token", [
    ("toolscan", "TOOLSCAN: OUT_OF_ROOT surface=grok calls=1 out_of_root=1 checkout=1 exempt=0 nonjson=0"),
    ("toolscan", "TOOLSCAN: CLEAN surface=codex calls=1 out_of_root=0 checkout=0 exempt=0 mcp_unmeasured=0"),
    ("grok-canary", "GROK-CANARY: REFUSED reason=escaped"),
    ("quarantine", "QUARANTINE: REFUSED reason=residue:1"),
], ids=["toolscan", "toolscan-codex-clean", "grok-canary", "quarantine"])
def test_require_stop_on_another_token(containment_home, verb, token):
    token_file = containment_home["home"] / "refused [*].txt"
    earlier_ok = {"toolscan": "TOOLSCAN: CLEAN surface=grok calls=0",
                  "grok-canary": "GROK-CANARY: PASS",
                  "quarantine": "QUARANTINE: VERIFIED moved=0 dest=/synthetic"}[verb]
    token_file.write_text(earlier_ok + "\n" + _hostile_text() + "\n" + token + "\n",
                          encoding="utf-8")
    result = _containment_cli("require", "--verb", verb, "--token-file", token_file)
    _assert_containment_token(result.returncode, result.stdout, result.stderr, 0,
                              "REQUIRE: STOP reason=" + token,
                              f"require({verb}) must reject this last token despite an earlier clean line")


def test_require_stop_on_an_empty_file(containment_home):
    token_file = containment_home["home"] / "empty [*].txt"
    token_file.write_text("", encoding="utf-8")
    result = _containment_cli("require", "--verb", "toolscan", "--token-file", token_file)
    _assert_containment_token(result.returncode, result.stdout, result.stderr, 0,
                              f"REQUIRE: STOP reason=no_token:{token_file}",
                              "require must stop with no_token for an empty token file")


def test_require_stop_on_an_absent_file(containment_home):
    token_file = containment_home["home"] / "absent [*].txt"
    result = _containment_cli("require", "--verb", "toolscan", "--token-file", token_file)
    _assert_containment_token(result.returncode, result.stdout, result.stderr, 0,
                              f"REQUIRE: STOP reason=no_token:{token_file}",
                              "require must stop with no_token for an absent token file")


def test_require_toolscan_stop_writes_the_halt_file(containment_module, containment_home,
                                                   monkeypatch, capsys):
    module, case = containment_module(), containment_home
    token_file, halt = case["home"] / "scan [*].txt", case["home"] / "HALT [*]"
    reason = "TOOLSCAN: OUT_OF_ROOT surface=grok calls=1 out_of_root=1 checkout=1 exempt=0 nonjson=0"
    token_file.write_text(_hostile_text() + "\n" + reason + "\n", encoding="utf-8")
    real_open = module.os.open
    opened = []

    def observe_open(path, flags, *args, **kwargs):
        if Path(path) == halt:
            opened.append(flags)
        return real_open(path, flags, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(module.os, "open", observe_open)
        rc, out, err = _containment_main(module, capsys, "require", "--verb", "toolscan",
                                         "--token-file", token_file, "--halt-file", halt)
        _assert_containment_token(rc, out, err, 0, f"REQUIRE: STOP reason={reason}",
                                  "toolscan STOP must append its exact reason before returning")
        assert halt.read_text(encoding="utf-8") == reason + "\n", "create halt with one exact reason line"
        # An existing file must be appended to rather than truncated.
        halt.write_text(_hostile_text() + "\n", encoding="utf-8")
        rc, out, err = _containment_main(module, capsys, "require", "--verb", "toolscan",
                                         "--token-file", token_file, "--halt-file", halt)
    _assert_containment_token(rc, out, err, 0, f"REQUIRE: STOP reason={reason}",
                              "toolscan STOP must preserve an existing halt record")
    assert halt.read_text(encoding="utf-8") == _hostile_text() + "\n" + reason + "\n"
    assert opened and all(flags & module.os.O_APPEND and flags & module.os.O_CREAT for flags in opened), (
        "halt writes must use os.open with O_APPEND and O_CREAT"
    )


def test_require_internal_error_still_writes_the_halt_file(containment_module, containment_home,
                                                          monkeypatch, capsys):
    module, case = containment_module(), containment_home
    token_file, halt = case["home"] / "clean [*].txt", case["home"] / "HALT"
    token_file.write_text(_hostile_text() + "\nTOOLSCAN: CLEAN surface=grok calls=0\n", encoding="utf-8")

    def reader_raises(*args, **kwargs):
        raise RuntimeError("synthetic token reader failure")

    monkeypatch.setattr(module, "read_last_line", reader_raises)
    rc, out, err = _containment_main(module, capsys, "require", "--verb", "toolscan",
                                     "--token-file", token_file, "--halt-file", halt)
    reason = "internal:RuntimeError"
    _assert_containment_token(rc, out, err, 2, f"REQUIRE: STOP reason={reason}",
                              "an internal reader error must fail closed with exit 2")
    assert halt.read_text(encoding="utf-8") == reason + "\n", (
        "the internal-error path must persist its exact halt reason"
    )
