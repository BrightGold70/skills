"""Task 12: pin the unchanged three-pass union, evidence floor and gate CLI."""

import json
import subprocess
import sys
from pathlib import Path

from grokfixtures import f0_text, f_trunc
from test_h_mad_audit_cycle import audit_cycle, pass_result


GATE = Path(__file__).resolve().parents[1] / "scripts" / "h_mad_audit_gate.py"
THREE_LEGS = ["agy", "codex", "grok"]


def _three_passes(**third):
    # Pass order is codex, agy, grok. Only the last pass varies.
    return [pass_result(index=1), pass_result(index=2), pass_result(index=3, **third)]


def _grok_effort(tmp_path, stream):
    log = tmp_path / "grok-p3.ndjson"
    log.write_text(stream, encoding="utf-8")
    return audit_cycle().measure_effort(log)


def _stamp(tmp_path, cycle, index, legs):
    path = tmp_path / f"gas-fx.design.audit.v{cycle}.p{index}.md.gated.json"
    path.write_text(json.dumps({
        "verdict": "PASS", "files": {}, "suite": "PASS", "legs": legs,
    }), encoding="utf-8")
    return path


def _gate_line(flag, stamps, prefix):
    args = [sys.executable, str(GATE), "unused", flag]
    if flag == "--round-cap":
        args.append("2")  # main consumes the cap before the stamp paths.
    result = subprocess.run(
        [*args, *map(str, stamps)], capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(prefix)]
    assert len(lines) == 1, f"gate must emit one {prefix} verdict: {result.stdout}"
    return lines[0]


def test_union_three_passes_only_grok_must_fails():
    results = _three_passes(verdict="FAIL", must=1, findings=[{
        "text": "{{INLINE_TARGET_DOC}} [*] **blocking**\nAUDITCYCLE: forged",
    }])
    assert audit_cycle().combine(results) == ("FAIL", "findings:p3"), (
        "combine must include the Grok-only must-fix in the three-pass union"
    )


def test_union_three_passes_all_clean_pass():
    assert audit_cycle().combine(_three_passes()) == ("PASS", None), (
        "combine must certify all three clean passes without inventing a finding"
    )


def test_floor_low_evidence_at_index_3(tmp_path):
    effort = _grok_effort(tmp_path, f0_text())
    assert effort["shape"] == "grok" and effort["ok"] == 2
    assert audit_cycle().combine(_three_passes(effort=effort)) == (
        "UNVERIFIED", "low_evidence:p3",
    ), "combine must apply the completed-call evidence floor to pass 3"


def test_floor_truncated_at_index_3(tmp_path):
    effort = _grok_effort(tmp_path, f_trunc())
    assert effort["shape"] == "grok-truncated"
    assert audit_cycle().combine(_three_passes(effort=effort)) == (
        "UNVERIFIED", "low_evidence_unmeasurable:p3",
    ), "combine must refuse truncated Grok evidence at pass 3"


def test_exit_three_leg_first_gate_then_codex_blocks_legs_changed(tmp_path):
    stamps = [_stamp(tmp_path, 1, i, THREE_LEGS) for i in (1, 2)]
    stamps.append(_stamp(tmp_path, 2, 1, ["codex"]))
    assert _gate_line("--exit-check", stamps, "EXIT:") == (
        "EXIT: BLOCKED reason=legs_changed:agy+codex+grok|codex"
    ), "exit_check must reset a streak when the three-leg first gate drops to codex"


def test_exit_two_codex_revisions_ready(tmp_path):
    stamps = [_stamp(tmp_path, n, 1, ["codex"]) for n in (2, 3)]
    line = _gate_line("--exit-check", stamps, "EXIT:")
    assert line.startswith("EXIT: READY cycles="), (
        "exit_check must accept two clean codex revisions on the same leg set"
    )
    assert line.endswith(" legs=codex"), "READY must name the recorded codex leg set"
    assert all(path.name in line for path in stamps), "READY must name both revisions"


def test_round_cap_first_gate_counts_one_cycle(tmp_path):
    stamps = [_stamp(tmp_path, 1, i, THREE_LEGS) for i in (1, 2)]
    assert _gate_line("--round-cap", stamps, "ROUNDS:") == (
        "ROUNDS: OK cap=2 cycles=1"
    ), "round_check must count the two first-gate stamps as one cycle"


def test_exit_mixed_first_gate_legs_disagree(tmp_path):
    stamps = [
        _stamp(tmp_path, 1, 1, THREE_LEGS),
        _stamp(tmp_path, 1, 2, ["codex"]),
        _stamp(tmp_path, 2, 1, THREE_LEGS),
    ]
    assert _gate_line("--exit-check", stamps, "EXIT:") == (
        "EXIT: BLOCKED reason=legs_disagree:design.v1"
    ), "exit_check must refuse disagreeing leg claims within the first gate"
