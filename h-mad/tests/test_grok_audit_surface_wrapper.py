"""Task 11/12 wrapper contracts and Task 18 Grok sandbox profiles."""

import json
import shutil
import sys
from pathlib import Path

import pytest

from grokfixtures import STUBS, f0_text
from test_hmad_dispatch import _bindir, run
from test_hmad_dispatch_exec_grok import HOSTILE_PROMPT
from test_hmad_dispatch_audit_cycle import (
    _audit_response,
    _dispatch_artifacts_by_pass,
    _script_dir_with_stub_assemble_and_real_cycle,
    auditcycle_lines,
    dispatch_args,
    dispatch_count,
    install_audit_cycle_stubs,
    project_with_docs,
    read_jsonl,
    run_audit_cycle,
    run_with_cmd_exec_stub,
)


def test_identical_prompts_halt_prompt_divergence(tmp_path):
    root = project_with_docs(tmp_path)
    script_dir, _assemble_calls, _cycle_calls = install_audit_cycle_stubs(tmp_path)
    capture = tmp_path / "agy.calls"

    result = run_audit_cycle(
        tmp_path,
        dispatch_args(root=root, passes="2"),
        env={
            "HMAD_AUDIT_CYCLE_SCRIPT_DIR": str(script_dir),
            "HMAD_ASSEMBLE_SAME_REPORT_P1": "1",
            "HMAD_ASSEMBLE_SAME_REPORT_P2": "1",
            "HMAD_STUB_HOSTILE": "all",
        },
        capture=capture,
    )

    assert result.returncode == 0, result.stderr
    assert auditcycle_lines(result.stdout) == [
        "AUDITCYCLE: UNVERIFIED reason=prompt_divergence passes=2 size_status=verified"
    ], "identical prompts must halt with the prompt_divergence verdict"
    assert dispatch_count(capture) == 0, "identical prompts must dispatch zero agents"


def _three_surface_dispatch(tmp_path):
    root = project_with_docs(tmp_path)
    result, trace = run_with_cmd_exec_stub(
        tmp_path,
        dispatch_args(root=root, passes="3") + ["--surfaces", "codex,agy,grok"],
        env={"HMAD_STUB_HOSTILE": "all"},
    )
    assert result.returncode == 0, result.stderr
    starts = [row for row in read_jsonl(trace) if row["kind"] == "cmd_exec_start"]
    assert len(starts) == 3, "three surfaces must dispatch all three passes"
    return result, starts


def test_three_surfaces_map_pass_index_to_agent(tmp_path):
    _result, starts = _three_surface_dispatch(tmp_path)
    artifacts = _dispatch_artifacts_by_pass(starts)
    by_pass = {
        next(iter(_dispatch_artifacts_by_pass([row]))): row["argv"][0]
        for row in starts
    }
    assert by_pass == {1: "codex", 2: "agy", 3: "grok"}, (
        "_cmd_audit_cycle must preserve the declared surface at each pass index"
    )
    for kind in ("out", "log", "report"):
        paths = [artifacts[i][kind] for i in (1, 2, 3)]
        assert all(paths) and len(set(paths)) == 3, (
            f"each surface must receive its own pass-indexed {kind} path"
        )


def test_three_surfaces_print_no_repeated_warning(tmp_path):
    result, _starts = _three_surface_dispatch(tmp_path)
    assert "one surface repeated" not in result.stderr, (
        "three distinct surfaces must not print the repeated-surface warning"
    )


def _real_cycle_stamps(tmp_path, surfaces, passes):
    feature = "gas-fx"
    root = project_with_docs(tmp_path, feature=feature)
    script_dir = _script_dir_with_stub_assemble_and_real_cycle(tmp_path)
    # run_audit_cycle installs its own agy-only bin, so supply a separate bin
    # with every requested surface and jq through its supported _BINDIR override.
    bindir = tmp_path / "surface-bin"
    bindir.mkdir()
    for name in ("codex", "agy", "grok"):
        (bindir / name).symlink_to(STUBS / name)
    jq = shutil.which("jq")
    assert jq, "the real-cycle fixture requires jq for CLI stream parsing"
    (bindir / "jq").symlink_to(jq)
    response = _audit_response(feature=feature, phase="design", cycle="1")
    result = run_audit_cycle(
        tmp_path,
        dispatch_args(feature=feature, phase="design", cycle="1", root=root,
                      passes=str(passes))
        + ["--surfaces", surfaces, "--report-grace", "0"],
        env={
            "_BINDIR": str(bindir),
            "HMAD_AUDIT_CYCLE_SCRIPT_DIR": str(script_dir),
            "HMAD_STUB_HOSTILE": "all",
            "HMAD_STUB_AGY_RESP": response,
            "HMAD_STUB_CODEX_LAST": response,
        },
    )
    assert result.returncode == 0, result.stderr
    stamps = sorted(root.rglob("*.gated.json"))
    assert [path.name for path in stamps] == [
        "gas-fx.design.audit.v1.p1.md.gated.json",
        "gas-fx.design.audit.v1.p2.md.gated.json",
    ], "the real cycle must stamp exactly the two delivered codex/agy reports"
    return [json.loads(path.read_text(encoding="utf-8")) for path in stamps]


def test_three_surface_stamps_carry_sorted_legs(tmp_path):
    stamps = _real_cycle_stamps(tmp_path, "codex,agy,grok", 3)
    assert [stamp["legs"] for stamp in stamps] == [["agy", "codex", "grok"]] * 2, (
        "both real gate stamps must carry the sorted three-surface leg set"
    )


def test_codex_agy_cycle_stamps_carry_the_legs_that_ran(tmp_path):
    stamps = _real_cycle_stamps(tmp_path, "codex,agy", 2)
    assert [stamp["legs"] for stamp in stamps] == [["agy", "codex"]] * 2, (
        "both real gate stamps must carry precisely the two surfaces that ran"
    )


def test_two_surfaces_for_three_passes_exit_2(tmp_path):
    root = project_with_docs(tmp_path)
    result, trace = run_with_cmd_exec_stub(
        tmp_path,
        dispatch_args(root=root, passes="3") + ["--surfaces", "codex,agy"],
        env={"HMAD_STUB_HOSTILE": "all"},
    )
    assert result.returncode == 2, "two surfaces for three passes must be a usage error"
    assert "lists 2 agents for 3 passes" in result.stderr, (
        "the surface-count refusal must identify the declared count mismatch"
    )
    assert not read_jsonl(trace), "a surface-count mismatch must stop before assembly/dispatch"


def test_m1_m2_raw_shapes_are_what_the_wrapper_says(tmp_path):
    shapes = [
        ("foreign", {"HMAD_ASSEMBLE_DIVERGE_P2": "1"}, "prompt_divergence", 0),
        ("identical", {"HMAD_ASSEMBLE_SAME_REPORT_P1": "1",
                       "HMAD_ASSEMBLE_SAME_REPORT_P2": "1"}, "prompt_divergence", 0),
        ("report-path-only", {}, None, 2),
        ("assemble-halt", {"HMAD_ASSEMBLE_HALT_P2": "1"}, "assemble_halt:p2", 0),
    ]
    for name, knobs, reason, dispatches in shapes:
        case = tmp_path / name
        case.mkdir()
        root = project_with_docs(case)
        script_dir, assemble_calls, cycle_calls = install_audit_cycle_stubs(case)
        capture = case / "agy.calls"
        result = run_audit_cycle(
            case, dispatch_args(root=root, passes="2"),
            env={"HMAD_AUDIT_CYCLE_SCRIPT_DIR": str(script_dir),
                 "HMAD_STUB_HOSTILE": "all", **knobs},
            capture=capture,
        )
        assert result.returncode == 0, f"{name}: {result.stderr}"
        expected = (
            f"AUDITCYCLE: UNVERIFIED reason={reason} passes=2 size_status=verified"
            if reason else
            "AUDITCYCLE: PASS must=0 should=0 passes=2 p1=0/0 p2=0/0 "
            "delivered=report-file,report-file size_status=verified"
        )
        assert auditcycle_lines(result.stdout) == [expected], (
            f"the real wrapper must classify raw {name} as its own declared verdict"
        )
        assert dispatch_count(capture) == dispatches, f"{name}: wrong dispatch count"
        assert len(read_jsonl(assemble_calls)) == 2, f"{name}: both passes must assemble"
        calls = read_jsonl(cycle_calls)
        assert len(calls) == 1, f"{name}: the wrapper must invoke the cycle helper once"
        if reason:
            assert calls[0][calls[0].index("--halt-reason") + 1] == reason
            assert "--pass" not in calls[0], f"{name}: halted shapes must supply no passes"
        else:
            assert "--halt-reason" not in calls[0]
            assert calls[0].count("--pass") == 2


def _profile_bindir(tmp_path):
    """Keep real CLIs off PATH; capture Grok's argv and actual child env."""
    tools = tmp_path / "profile-tools"
    tools.mkdir()
    bindir = _bindir(tools, ["codex", "agy"])
    capture = tmp_path / "grok-child.json"
    stream = tmp_path / "profile-stream.ndjson"
    stream.write_text(f0_text(), encoding="utf-8")
    stub = bindir / "grok"
    stub.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        f"with open({str(capture)!r}, 'w', encoding='utf-8') as out:\n"
        "    json.dump({'argv': sys.argv[1:], 'env': dict(os.environ)}, out)\n"
        f"with open({str(stream)!r}, encoding='utf-8') as stream:\n"
        "    sys.stdout.write(stream.read())\n",
        encoding="utf-8",
    )
    stub.chmod(0o755)
    return bindir, capture


def _profile_case(tmp_path, *, options=(), agent="grok", env=None, verb="exec"):
    bindir, capture = _profile_bindir(tmp_path)
    prompt = tmp_path / "profile prompt [*] 'quoted'.md"
    prompt.write_text(HOSTILE_PROMPT, encoding="utf-8")
    log = tmp_path / "profile run [*] 'quoted'.log"
    cli_calls = tmp_path / "other-cli.calls"
    result = run(
        [verb, agent, str(prompt), "--cd", str(tmp_path), "--log", str(log),
         *options],
        substrate="orca",
        env={"_BINDIR": str(bindir), "HMAD_STUB_HOSTILE": "all", **(env or {})},
        capture=cli_calls,
    )
    return result, capture, Path(str(log) + ".profile"), log, cli_calls


def _assert_profile_launch(result, capture, profile, sandbox, origin):
    assert result.returncode == 0, (
        f"exec grok must launch the permitted {sandbox} profile: {result.stderr}"
    )
    assert capture.exists(), "exec grok must reach the CLI for an allowed profile"
    argv = json.loads(capture.read_text(encoding="utf-8"))["argv"]
    assert argv.count("--sandbox") == 1, (
        f"exec grok must pass exactly one explicit --sandbox {sandbox}: {argv}"
    )
    assert argv[argv.index("--sandbox") + 1] == sandbox, (
        f"exec grok must pass the selected --sandbox {sandbox}: {argv}"
    )
    assert profile.exists(), "exec grok must write a profile record beside its log"
    assert profile.read_text(encoding="utf-8") == (
        f"GROK-PROFILE: profile={sandbox} origin={origin}\n"
    ), "exec grok must record the selected profile and its actual origin"


def test_exec_grok_defaults_to_strict(tmp_path):
    result, capture, profile, _log, _calls = _profile_case(tmp_path)
    _assert_profile_launch(result, capture, profile, "strict", "default")


def test_exec_grok_explicit_strict(tmp_path):
    result, capture, profile, _log, _calls = _profile_case(
        tmp_path, options=["--sandbox", "strict"],
    )
    _assert_profile_launch(result, capture, profile, "strict", "default")


def test_exec_grok_weaker_profile_refused(tmp_path):
    result, capture, profile, log, _calls = _profile_case(
        tmp_path, options=["--sandbox", "workspace"],
    )
    assert result.returncode == 2, "a weaker Grok profile without an override must exit 2"
    assert (
        "hmad-dispatch: exec: grok --sandbox workspace is weaker than strict or unknown; "
        "pass --allow-weaker-sandbox to run it, and it is recorded"
    ) in result.stderr.splitlines(), "the weaker-profile refusal must name the value and override"
    assert not capture.exists(), "a refused weaker profile must never launch Grok"
    assert not profile.exists(), "a refused weaker profile must create no profile record"
    assert not log.exists(), "a refused weaker profile must stop before creating its log"


def test_exec_grok_weaker_profile_with_override_is_recorded(tmp_path):
    result, capture, profile, _log, _calls = _profile_case(
        tmp_path, options=["--sandbox", "workspace", "--allow-weaker-sandbox"],
    )
    _assert_profile_launch(result, capture, profile, "workspace", "override")


@pytest.mark.parametrize("sandbox_options", [[], ["--sandbox", "strict"]],
                         ids=["no-sandbox", "strict"])
def test_exec_grok_override_alone_exits_2(tmp_path, sandbox_options):
    result, capture, profile, log, _calls = _profile_case(
        tmp_path, options=["--allow-weaker-sandbox", *sandbox_options],
    )
    assert result.returncode == 2, "an override without a weaker Grok profile must exit 2"
    assert "unknown option" not in result.stderr, (
        "Grok must recognize --allow-weaker-sandbox before refusing its profile combination"
    )
    assert (
        "hmad-dispatch: exec: --allow-weaker-sandbox needs a --sandbox weaker than strict"
    ) in result.stderr.splitlines(), "the override refusal must explain the required weaker profile"
    assert not capture.exists(), "an invalid override must never launch Grok"
    assert not profile.exists(), "an invalid override must create no profile record"
    assert not log.exists(), "an invalid override must stop before creating its log"


def test_exec_grok_child_has_no_grok_sandbox_env(tmp_path):
    result, capture, _profile, _log, _calls = _profile_case(
        tmp_path, env={"GROK_SANDBOX": "workspace", "KEEP_PROFILE_CONTROL": HOSTILE_PROMPT},
    )
    assert result.returncode == 0, f"exec grok must launch for child-env capture: {result.stderr}"
    assert capture.exists(), "the Grok child must run to observe its real environment"
    child_env = json.loads(capture.read_text(encoding="utf-8"))["env"]
    assert child_env.get("KEEP_PROFILE_CONTROL") == HOSTILE_PROMPT, (
        "the child-env capture must preserve the hostile unrelated control value"
    )
    assert "GROK_SANDBOX" not in child_env, (
        "exec grok must remove the caller's GROK_SANDBOX from the child environment"
    )


def test_audit_cycle_writes_a_profile_record_per_grok_pass(tmp_path):
    root = project_with_docs(tmp_path)
    script_dir, assemble_calls, cycle_calls = install_audit_cycle_stubs(tmp_path)
    bindir, capture = _profile_bindir(tmp_path)
    stem_dir = tmp_path / "profile stems [*] 'quoted'"
    stem_dir.mkdir()
    result = run_audit_cycle(
        tmp_path, dispatch_args(root=root, passes="2") + ["--surfaces", "agy,grok"],
        env={"_BINDIR": str(bindir), "HMAD_AUDIT_CYCLE_SCRIPT_DIR": str(script_dir),
             "HMAD_AUDIT_STEM_DIR": str(stem_dir), "HMAD_STUB_HOSTILE": "all"},
    )
    assert result.returncode == 0, f"the agy/grok audit cycle must complete: {result.stderr}"
    assert capture.exists(), "the audit cycle must really launch its Grok pass"
    assert len(read_jsonl(assemble_calls)) == 2, "the audit cycle must assemble both passes"
    calls = read_jsonl(cycle_calls)
    assert len(calls) == 1, "the audit cycle must invoke its cycle helper once"
    pass_specs = [calls[0][i + 1] for i, arg in enumerate(calls[0]) if arg == "--pass"]
    assert len(pass_specs) == 2, "the cycle helper must receive both completed passes"
    logs = {spec.split(":", 1)[0]: Path(spec.rsplit(":", 1)[1]) for spec in pass_specs}
    p2_profile = Path(str(logs["2"]) + ".profile")
    assert p2_profile.parent == stem_dir and p2_profile.name.endswith("_p2.log.profile"), (
        "the Grok record must be beside its pass-2 log in the stem directory"
    )
    assert p2_profile.exists(), "the audit cycle must write a profile record for its Grok pass"
    assert p2_profile.read_text(encoding="utf-8") == (
        "GROK-PROFILE: profile=strict origin=default\n"
    ), "the Grok audit pass must record the default strict profile"
    assert not Path(str(logs["1"]) + ".profile").exists(), (
        "the agy pass must not receive a Grok profile record"
    )


def test_exec_pane_still_refuses_grok(tmp_path):
    result, capture, _profile, _log, _calls = _profile_case(tmp_path, verb="exec-pane")
    assert result.returncode == 2, "exec-pane must continue refusing Grok with exit 2"
    assert "unknown agent 'grok' (expected codex|agy)" in result.stderr, (
        "exec-pane must reject Grok at its existing agent guard"
    )
    assert not capture.exists(), "exec-pane must never launch the Grok stub"


@pytest.mark.parametrize("agent", ["codex", "agy"])
def test_allow_weaker_sandbox_is_unknown_for_codex_and_agy(tmp_path, agent):
    result, capture, profile, log, cli_calls = _profile_case(
        tmp_path, agent=agent, options=["--allow-weaker-sandbox"],
    )
    assert result.returncode == 2, f"exec {agent} must refuse Grok's override flag with exit 2"
    assert (
        "hmad-dispatch: exec: unknown option '--allow-weaker-sandbox'"
    ) in result.stderr.splitlines(), f"exec {agent} must diagnose the Grok-only flag as unknown"
    assert not capture.exists() and not cli_calls.exists(), (
        f"exec {agent} must refuse the Grok-only flag before launching any CLI"
    )
    assert not profile.exists() and not log.exists(), (
        f"exec {agent} must refuse the Grok-only flag before creating log artifacts"
    )
