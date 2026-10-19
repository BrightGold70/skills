"""Task 11 prompt divergence and Task 12 unchanged wrapper contracts."""

import json
import shutil

from grokfixtures import STUBS
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
