"""RED tests for the hostile-payload corpus selector in the Orca stub."""

import json
import os
import subprocess
from pathlib import Path


STUB = Path(__file__).resolve().parent / "stubs" / "orca"
TIDY_ENVELOPE = (
    '{"ok":true,"result":{"worktree":{"branch":"refs/heads/main",'
    '"path":"/x","comment":"c"}}}'
)
VALID_CORPORA = "markdown, newlines, markers, all"


def run_stub(*args, hostile=None):
    env = dict(os.environ)
    env.pop("HMAD_STUB_HOSTILE", None)
    if hostile is not None:
        env["HMAD_STUB_HOSTILE"] = hostile
    return subprocess.run(
        [str(STUB), *args], capture_output=True, text=True, env=env
    )


def comment_from(result):
    envelope = json.loads(result.stdout)
    return envelope["result"]["worktree"]["comment"]


def test_hostile_selector_accepts_all_valid_corpora():
    """AC-5.2: every documented corpus yields a non-tidy JSON envelope."""
    for corpus in ("markdown", "newlines", "markers", "all"):
        result = run_stub("worktree", "set", "--comment", "c", hostile=corpus)
        assert result.returncode == 0, corpus
        comment = comment_from(result)
        assert comment != "c", f"HMAD_STUB_HOSTILE={corpus} was ignored"


def test_markdown_corpus_contains_literal_glob_metacharacters():
    """AC-5.3: markdown data directly contains literal '[' and '*' characters."""
    result = run_stub("worktree", "set", "--comment", "c", hostile="markdown")
    comment = comment_from(result)
    assert "[" in comment, "markdown corpus must contain literal '['"
    assert "*" in comment, "markdown corpus must contain literal '*'"


def test_markers_corpus_round_trips_marker_syntax_as_json_data():
    """AC-5.4: marker-looking content remains data inside a valid envelope."""
    result = run_stub("worktree", "set", "--comment", "c", hostile="markers")
    assert result.returncode == 0
    comment = comment_from(result)
    assert "h-mad: " in comment, "markers corpus must carry the h-mad lead-in"
    assert "⟦/h-mad⟧" in comment, "markers corpus must carry the terminator"


def test_unknown_hostile_corpus_fails_without_json_envelope():
    """AC-5.5: typos fail non-zero, emit no JSON, and name valid corpora."""
    result = run_stub("worktree", "set", "--comment", "c", hostile="markdwn")
    assert result.returncode != 0, "unknown corpus must exit non-zero"
    assert result.stdout.strip() == "", "unknown corpus must emit no JSON envelope"
    assert VALID_CORPORA in result.stderr, "error must name all valid corpora"


def test_unset_hostile_selector_preserves_tidy_envelope_byte_for_byte():
    """AC-5.1: an unset selector leaves today's shared-stub value unchanged."""
    result = run_stub("worktree", "set", "--comment", "c")
    assert result.returncode == 0
    assert result.stdout == TIDY_ENVELOPE
