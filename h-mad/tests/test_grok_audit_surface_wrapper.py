from test_hmad_dispatch_audit_cycle import (
    auditcycle_lines,
    dispatch_args,
    dispatch_count,
    install_audit_cycle_stubs,
    project_with_docs,
    run_audit_cycle,
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
