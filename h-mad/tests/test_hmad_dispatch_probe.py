"""`hmad-dispatch probe <agent>`: is the agent behind a pin answering?

Measured 2026-09-05: `hmad-dispatch read agy` sat on a spinner for 20+ minutes while
`hmad-dispatch env` already reported `state=done last="340997"`, the correct answer to an
`8317 * 41` probe. A watcher grepping the pane would have looped forever. A hand-rolled probe
then matched a transposed literal (24265159 vs 24264959) and would have filed a live agent
as dead.

So the verb computes the question and the expected answer from ONE pair of operands, sends
the question, and polls the TUI-independent identity line `env` prints (`worktree ps`
`lastAssistantMessage`). It reports:
- `ALIVE` (rc 0): the answer appeared as a whole token;
- `NO_ANSWER` (rc 1): the listing was read and the answer never appeared;
- `UNREADABLE` (rc 2): the listing never answered, so liveness was not measured. That is
  kept distinct from `NO_ANSWER`, which would otherwise file a live agent as dead.

The fake `orca` below plays the agent: when live, it computes the product from the text it
was sent, so a verb whose expected answer is not the true product can never read ALIVE.
"""
import json
import os
import re
import subprocess
from pathlib import Path

import pytest

WRAPPER = Path(__file__).resolve().parent.parent / "scripts" / "hmad-dispatch.sh"

FAKE_ORCA = r"""#!/bin/bash
d="$FAKE_ORCA_DIR"
case "$1 $2" in
  "terminal list")
    printf '%s' '{"ok":true,"result":{"terminals":[{"handle":"term_codex","tabId":"tab1","leafId":"leaf1","title":"Codex"}]}}' ;;
  "worktree ps")
    [ -f "$d/ps_broken" ] && { echo "not json"; exit 1; }
    last="$(cat "$d/last" 2>/dev/null)"
    jq -n --arg l "$last" '{ok:true,result:{worktrees:[{agents:[{paneKey:"tab1:leaf1",agentType:"codex",state:"done",lastAssistantMessage:$l}]}]}}' ;;
  "terminal send")
    shift 2; text=""
    while [ $# -gt 0 ]; do case "$1" in --text) text="$2"; shift 2 ;; *) shift ;; esac; done
    printf '%s\n' "$text" >> "$d/sent"
    if [ -f "$d/live" ]; then
      expr="$(printf '%s' "$text" | grep -oE '[0-9]+ \* [0-9]+' | head -1)"
      n=$(( ${expr% \* *} * ${expr#* \* } ))
      printf 'The answer is %s%s.' "$n" "$(cat "$d/suffix" 2>/dev/null)" > "$d/last"
    fi
    echo '{"ok":true}' ;;
  *) echo '{"ok":true,"result":{}}' ;;
esac
"""


def _setup(tmp_path: Path, *, live: bool = True, suffix: str = "", broken: bool = False):
    state = tmp_path / "orca-state"
    state.mkdir()
    (state / "last").write_text("an older reply about something else", encoding="utf-8")
    if live:
        (state / "live").touch()
    if suffix:
        (state / "suffix").write_text(suffix, encoding="utf-8")
    if broken:
        (state / "ps_broken").touch()
    bindir = tmp_path / "bin"
    bindir.mkdir()
    orca = bindir / "orca"
    orca.write_text(FAKE_ORCA, encoding="utf-8")
    orca.chmod(0o755)
    return state, bindir


def _probe(tmp_path: Path, state: Path, bindir: Path, *args: str, substrate: str = "orca"):
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("HMAD_ORCA_", "ORCA_", "CMUX")) and k != "HMAD_SUBSTRATE"}
    env.update(PATH=f"{bindir}:/usr/bin:/bin:/opt/homebrew/bin:/usr/local/bin",
               HMAD_SUBSTRATE=substrate, HMAD_SKIP_PREFLIGHT="1", FAKE_ORCA_DIR=str(state),
               HMAD_ORCA_CODEX_TERMINAL="term_codex",
               HMAD_ORCA_PIN_FILE=str(tmp_path / "absent-pins.env"))
    return subprocess.run(["bash", str(WRAPPER), "probe", "codex", *args],
                          capture_output=True, text=True, env=env, timeout=60)


def _asked(state: Path) -> int:
    a, b = re.search(r"(\d+) \* (\d+)", (state / "sent").read_text()).groups()
    return int(a) * int(b)


def test_a_live_agent_is_alive_with_the_true_product(tmp_path):
    state, bindir = _setup(tmp_path)
    r = _probe(tmp_path, state, bindir, "--timeout", "10")
    assert r.returncode == 0, r.stdout + r.stderr
    assert re.search(rf"^PROBE: ALIVE agent=codex answer={_asked(state)} ", r.stdout, re.M), r.stdout


def test_a_silent_agent_is_no_answer_not_alive(tmp_path):
    state, bindir = _setup(tmp_path, live=False)
    r = _probe(tmp_path, state, bindir, "--timeout", "2")
    assert r.returncode == 1, r.stdout + r.stderr
    assert f"PROBE: NO_ANSWER agent=codex expected={_asked(state)}" in r.stdout, r.stdout


def test_the_answer_must_be_a_whole_token(tmp_path):
    # `3409970` contains `340997`; a substring match would call this agent alive.
    state, bindir = _setup(tmp_path, suffix="0")
    r = _probe(tmp_path, state, bindir, "--timeout", "2")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "PROBE: NO_ANSWER" in r.stdout, r.stdout


def test_an_unreadable_listing_is_not_filed_as_dead(tmp_path):
    state, bindir = _setup(tmp_path, broken=True)
    r = _probe(tmp_path, state, bindir, "--timeout", "2")
    assert r.returncode == 2, r.stdout + r.stderr
    assert "PROBE: UNREADABLE agent=codex" in r.stdout, r.stdout
    assert "NO_ANSWER" not in r.stdout


def test_each_probe_asks_a_fresh_question(tmp_path):
    state, bindir = _setup(tmp_path)
    for _ in range(3):
        _probe(tmp_path, state, bindir, "--timeout", "10")
    asked = re.findall(r"\d+ \* \d+", (state / "sent").read_text())
    assert len(asked) == 3 and len(set(asked)) == 3, asked


def test_a_non_orca_substrate_refuses_rather_than_guesses(tmp_path):
    state, bindir = _setup(tmp_path)
    r = _probe(tmp_path, state, bindir, "--timeout", "2", substrate="cmux")
    assert r.returncode == 2, r.stdout + r.stderr
    assert not (state / "sent").exists(), "nothing may be sent when liveness cannot be read back"


@pytest.mark.parametrize("bad", [["--timeout"], ["--timeout", "0"], ["--timeout", "x"], ["--bogus"]])
def test_bad_arguments_send_nothing(tmp_path, bad):
    state, bindir = _setup(tmp_path)
    r = _probe(tmp_path, state, bindir, *bad)
    assert r.returncode == 2, r.stdout + r.stderr
    assert not (state / "sent").exists()


def test_probe_is_a_listed_verb():
    r = subprocess.run(["bash", str(WRAPPER), "--help"], capture_output=True, text=True)
    assert " probe " in f" {r.stdout.split('verbs:', 1)[1].splitlines()[0]} "
