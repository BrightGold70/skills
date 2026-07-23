"""`ask` — the highest-recurrence skill candidate (rec 12+): send → wait → read.

`docs/skill-candidates.md`: "assemble prompt → hmad-dispatch send → background
poll on idle marker + schema token → parse verdict" ran 12+ times per session.
The three verbs are always used together for an AUDIT/REVIEW dispatch (the
orchestration path is `dispatch`+`await`; the file path is `report-wait`; this is
the screen-scrape path they lacked a single verb for).

`ask` composes the EXISTING commands so their guarantees carry:
  * send enforces the preflight receipt and picks inline vs file-indirection;
  * wait uses the full-buffer idle check (J3), not a tail;
  * read --from-start returns the whole buffer, past the retained viewport.

Verdict extraction stays a separate `h_mad_extract_verdict.py` call: it needs
--feature/--phase for its contract and belongs to python, not the shell. `ask`
gets you the buffer; extraction reads it.
"""
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_hmad_dispatch import _bindir, run  # noqa: E402


def _prompt(tmp_path, text="tiny prompt"):
    p = tmp_path / "prompt.txt"
    p.write_text(text)
    return p


def _env(b, tmp_path, **extra):
    e = {"_BINDIR": b, "HMAD_ORCA_AGY_TERMINAL": "term_a",
         "HMAD_ORCA_PIN_FILE": str(tmp_path / "pins.env"),
         "HMAD_SKIP_PREFLIGHT": "1", "HMAD_WAIT_POLL_INTERVAL": "0",
         "HMAD_STUB_ORCA_STDOUT": "the agent reply buffer"}
    e.update(extra)
    return e


def test_ask_sends_then_waits_then_reads_full_buffer(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    pf = _prompt(tmp_path)
    r = run(["ask", "agy", str(pf)], substrate="orca",
            env=_env(b, tmp_path), capture=cap)
    assert r.returncode == 0, r.stderr
    argv = cap.read_text()
    # Order: send, then wait, then a cursor-0 (full buffer) read.
    i_send = argv.index("terminal send")
    i_wait = argv.index("terminal wait")
    i_read = argv.index("terminal read --terminal term_a --cursor 0")
    assert i_send < i_wait < i_read, f"wrong order:\n{argv}"
    assert "the agent reply buffer" in r.stdout


def test_ask_never_reads_a_tail(tmp_path):
    # The whole point of composing on read --from-start (J3): a 6-line tail can
    # be a stale overdrawn frame. `ask` must not introduce one.
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    r = run(["ask", "agy", str(_prompt(tmp_path))], substrate="orca",
            env=_env(b, tmp_path), capture=cap)
    assert r.returncode == 0, r.stderr
    assert "terminal read --terminal term_a --limit 6" not in cap.read_text()


def test_ask_passes_timeout_through_to_wait(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    r = run(["ask", "agy", str(_prompt(tmp_path)), "--timeout", "30"],
            substrate="orca", env=_env(b, tmp_path), capture=cap)
    assert r.returncode == 0, r.stderr
    assert "--timeout-ms 30000" in cap.read_text()


def test_ask_writes_to_out_file_when_given(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    out = tmp_path / "reply.txt"
    r = run(["ask", "agy", str(_prompt(tmp_path)), "--out", str(out)],
            substrate="orca", env=_env(b, tmp_path))
    assert r.returncode == 0, r.stderr
    assert "the agent reply buffer" in out.read_text()
    assert "the agent reply buffer" not in r.stdout


def test_ask_fails_fast_without_a_preflight_receipt(tmp_path):
    # send refuses without a receipt; ask must NOT go on to wait/read a pane it
    # never dispatched into. The receipt guard is the whole reason send exists.
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    env = _env(b, tmp_path)
    del env["HMAD_SKIP_PREFLIGHT"]
    r = run(["ask", "agy", str(_prompt(tmp_path))], substrate="orca",
            env=env, capture=cap)
    assert r.returncode != 0
    argv = cap.read_text()
    assert "terminal wait" not in argv, "waited despite a refused send"
    assert "terminal read" not in argv, "read despite a refused send"


def test_ask_rejects_unknown_flag(tmp_path):
    # P1 discipline: a misspelled flag must fail loudly, not be dropped.
    b = _bindir(tmp_path, ["orca"])
    r = run(["ask", "agy", str(_prompt(tmp_path)), "--timeut", "5"],
            substrate="orca", env=_env(b, tmp_path))
    assert r.returncode == 2
    assert "unknown option" in r.stderr.lower()
    assert "--timeut" in r.stderr


def test_ask_requires_agent_and_prompt(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    r = run(["ask", "agy"], substrate="orca", env=_env(b, tmp_path))
    assert r.returncode != 0
