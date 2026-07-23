"""learn.py: hitting the length cap must cost ONE step, not a guess-loop.

The cap is deliberate (docs/learnings.md is grepped one-liners), but rejecting a
long kernel with only a char count forces the caller to trim by eyeball and
re-submit — observed overshooting 243 -> 216 -> 207 before landing, three wasted
round-trips for one learning. The fix makes an over-length kernel recoverable in
one step: `--trim` word-boundary-trims and stores, and the plain rejection prints
a ready-to-paste <=MAX_KERNEL suggestion so even a manual retry is deterministic.
Assertions reference learn.MAX_KERNEL (raised 200 -> 240) so a future bump can't
silently strand them.
"""
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import learn  # noqa: E402


def _args(pattern, *, trim=False, category="gotcha", confidence=0.7, tags="t"):
    return types.SimpleNamespace(pattern=pattern, trim=trim, category=category,
                                 confidence=confidence, tags=tags)


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    out = tmp_path / "learnings.md"
    monkeypatch.setattr(learn, "_learnings_path", lambda: out)
    monkeypatch.setattr(learn, "_project_root", lambda: tmp_path)
    return out


# --- _trim_to -----------------------------------------------------------------

def test_trim_is_identity_under_the_limit():
    s = "short kernel"
    assert learn._trim_to(s, 200) == s


def test_trim_result_is_within_the_limit():
    s = "x" * 500
    assert len(learn._trim_to(s, 200)) <= 200


def test_trim_cuts_on_a_word_boundary_not_mid_word():
    s = "aa " * 100  # 3-char words: a naive limit-1 cut lands MID-word
    out = learn._trim_to(s, 200)
    assert out.endswith("…"), "a trimmed kernel must be marked as trimmed"
    body = out[:-1]  # drop the ellipsis
    # Discriminating: the char in the SOURCE immediately after the kept body must
    # be a space (we cut on a boundary) or end-of-string. `s.startswith(body)` is
    # true for any prefix, so it does NOT test the boundary — a mid-word cut left
    # this green under mutation until the assertion was tightened.
    assert s.startswith(body), "body is not a prefix of the source"
    nxt = s[len(body):len(body) + 1]
    assert nxt in (" ", ""), f"cut mid-word (next source char is {nxt!r})"
    assert body == body.rstrip(), "trailing space left before ellipsis"


# --- cmd_add ------------------------------------------------------------------

def test_over_limit_without_trim_rejects_with_a_paste_ready_suggestion(capsys):
    long = "A guard behind a resolve-check is no guard. " * 6  # ~260
    rc = learn.cmd_add(_args(long))
    assert rc == 1
    err = capsys.readouterr().err
    assert f"exceeds {learn.MAX_KERNEL}" in err
    assert "--trim" in err, "the error must name the one-shot escape"
    # the suggestion it prints must itself be within the cap, or pasting it fails too
    suggestion = err.split('"')[1] if '"' in err else ""
    assert 0 < len(suggestion) <= learn.MAX_KERNEL, f"suggestion is {len(suggestion)} chars"


def test_over_limit_with_trim_saves_a_within_limit_line(_isolated):
    long = "A guard behind a resolve-check is no guard for a destructive verb. " * 5
    rc = learn.cmd_add(_args(long, trim=True))
    assert rc == 0
    saved = _isolated.read_text()
    entry = next(l for l in saved.splitlines() if l.startswith("- "))
    # the kernel text after the em-dash is within the cap
    kernel = entry.split("—", 1)[1].strip() if "—" in entry else entry
    assert len(kernel) <= learn.MAX_KERNEL
    assert "…" in entry


def test_within_limit_is_unchanged(_isolated):
    rc = learn.cmd_add(_args("a tidy short kernel"))
    assert rc == 0
    assert "a tidy short kernel" in _isolated.read_text()


def test_trim_flag_exists_on_the_parser():
    # The flag has to be reachable from the CLI, not just cmd_add.
    parser = learn._build_parser() if hasattr(learn, "_build_parser") else None
    if parser is None:
        pytest.skip("no _build_parser to introspect")
    ns = parser.parse_args(["add", "x", "--category", "gotcha", "--trim"])
    assert ns.trim is True
