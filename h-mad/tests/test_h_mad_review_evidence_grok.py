"""CLI wiring checks for Grok review evidence and format precedence."""

import json
import subprocess
import sys
from pathlib import Path

from grokfixtures import (
    BASE_SHA,
    agy_transcript,
    banner_then_f0,
    deep_line_200k,
    f0_text,
    f_notools,
    f_trunc,
    mixed_agy_f0,
)


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "h-mad" / "scripts" / "h_mad_review_evidence.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _run(script: Path, log: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(script), str(log)],
                          capture_output=True, text=True, check=False)


def _log(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "review.log"
    path.write_text(text, encoding="utf-8")
    return path


def _base_script(tmp_path: Path) -> Path:
    source = subprocess.run(
        ["git", "show", f"{BASE_SHA}:h-mad/scripts/h_mad_review_evidence.py"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout
    path = tmp_path / "base_review_evidence.py"
    path.write_text(source, encoding="utf-8")
    return path


def test_cli_f0_prints_grok_evidence_pass(tmp_path):
    result = _run(SCRIPT, _log(tmp_path, f0_text()))
    assert result.stdout == (
        "EVIDENCE: PASS tools=2 ok=2 unresolved=0 thinking=121 "
        "format=grok stop_reason=end_turn\n"
    ), "main must publish scan_grok's completed F0 counts on the EVIDENCE line"
    assert result.returncode == 0, "main must accept a completed Grok stream"


def test_cli_f_notools_prints_none(tmp_path):
    result = _run(SCRIPT, _log(tmp_path, f_notools()))
    assert result.stdout == (
        "EVIDENCE: NONE tools=2 ok=0 unresolved=2 thinking=121 "
        "format=grok stop_reason=end_turn\n"
    ), "main must report unresolved Grok calls without claiming successful evidence"
    assert result.returncode == 0, "main must judge a complete Grok stream with no successful calls"


def test_cli_f_trunc_is_unreadable_without_counts(tmp_path):
    result = _run(SCRIPT, _log(tmp_path, f_trunc()))
    assert result.stdout == "EVIDENCE: UNREADABLE reason=truncated_no_end\n", (
        "main must refuse a Grok stream without an end event"
    )
    assert result.returncode == 2, "main must exit 2 for truncated Grok evidence"
    assert "tools=" not in result.stdout, "unreadable Grok evidence must publish no counts"


def test_cli_codex_text_output_is_byte_identical_to_base(tmp_path):
    base = _base_script(tmp_path)
    for name in ("codex-text-0-exec.log", "codex-text-8-exec.log"):
        log = FIXTURES / name
        expected = _run(base, log)
        actual = _run(SCRIPT, log)
        assert expected.stdout.startswith("CODEXEVIDENCE:"), name
        assert expected.stdout.endswith("EVIDENCE: UNREADABLE reason=unsupported_format\n"), name
        assert (actual.stdout, actual.returncode) == (expected.stdout, expected.returncode), (
            f"main must preserve the base CLI's codex-text stdout and exit code for {name}"
        )


def test_cli_banner_then_f0_keeps_codex_output(tmp_path):
    log = _log(tmp_path, banner_then_f0())
    expected = _run(_base_script(tmp_path), log)
    actual = _run(SCRIPT, log)
    assert expected.stdout.startswith("CODEXEVIDENCE:"), "base CLI must recognize the Codex banner"
    assert expected.stdout.endswith("EVIDENCE: UNREADABLE reason=unsupported_format\n")
    assert expected.returncode == 2
    assert (actual.stdout, actual.returncode) == (expected.stdout, expected.returncode), (
        "main must let the Codex banner win over embedded Grok events"
    )
    assert "format=grok" not in actual.stdout, "Codex banner output must not claim Grok format"


def test_cli_mixed_agy_f0_equals_agy_alone(tmp_path):
    agy = _run(SCRIPT, _log(tmp_path, agy_transcript()))
    mixed = _run(SCRIPT, _log(tmp_path, mixed_agy_f0()))
    assert agy.stdout.startswith("EVIDENCE: PASS tools=1 ok=1"), (
        "the agy-only control must contain a successful agy tool call"
    )
    assert agy.returncode == 0
    assert (mixed.stdout, mixed.returncode) == (agy.stdout, agy.returncode), (
        "main must preserve agy precedence when a Grok stream follows agy events"
    )
    assert "format=grok" not in mixed.stdout, "mixed agy evidence must not claim Grok format"


def test_cli_malformed_type_lines_print_f0_evidence(tmp_path):
    malformed = "".join(f'{{"type":{value}}}\n' for value in ("[]", "{}", "1", "null"))
    hostile = json.dumps({"type": "text", "data": "# agent\n[gate] `$(touch /tmp/nope)` **x**"}) + "\n"
    lines = f0_text().splitlines(keepends=True)
    noisy = malformed + deep_line_200k() + lines[0] + hostile + deep_line_200k() + "".join(lines[1:])
    result = _run(SCRIPT, _log(tmp_path, noisy))
    assert result.stdout == (
        "EVIDENCE: PASS tools=2 ok=2 unresolved=0 thinking=121 "
        "format=grok stop_reason=end_turn\n"
    ), "main must retain F0 evidence after malformed types, hostile text, and deep JSON lines"
    assert result.returncode == 0, "main must accept intact F0 evidence after malformed lines"
