"""FR-3: resolver-authored state records and Claude's peer refusal precedence."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

import pytest

from test_h_mad_tdd_gate_judge import HOOK, TARGET, _bin, _gate, _root, _tree_b
from tdd_gate_support import decision, hermetic_env, hook_form, write_state

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import h_mad_tdd_judge as judge  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
HOSTILE = 'agent "q"\\newline\n[H-MAD:MARKER]%,*? ⟦/h-mad⟧'
FIRST_KEY = "first " + HOSTILE
SECOND_KEY = "second " + HOSTILE
TEST = "hematology-paper-writer/tests/test_w.py"
ALLOW = "TDD-JUDGE: ALLOW kind=red-measured source=name-map test=/x/tests/test_w.py"


@pytest.fixture(autouse=True)
def _hostile_input(monkeypatch):
    for name in list(os.environ):
        if name.startswith(("CLAUDE", "CODEX")) or name in (
            "HMAD_CODEX_UNAVAILABLE", "HMAD_AGY_UNAVAILABLE", "HPW_AGENT_BACKEND", "HMAD_HOST",
        ):
            monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")


def _step(**extra):
    return {"phase": "step5", "codex_status": "available", "agy_status": "available", **extra}


def _project(tmp_path, records):
    root = _root(tmp_path)
    write_state(root, records)
    test = root / TEST
    test.parent.mkdir(parents=True)
    test.write_text("def test_red():\n    assert False, 'intentionally red'\n", encoding="utf-8")
    return root


def _bins(tmp_path, *, codex=False, agy=False):
    # HOSTILE contains ':': keep it in record contents, never in a PATH entry.
    bin_dir = _bin(tmp_path, codex=codex)
    if agy:
        stub = bin_dir / "agy"
        stub.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        stub.chmod(0o755)
    for peer, present in (("codex", codex), ("agy", agy)):
        assert bool(shutil.which(peer, path=f"{bin_dir}:/usr/bin:/bin")) == present
    return bin_dir


def _outcome(root, bin_dir, *, hook=HOOK):
    result = _gate(root, arg=str(root / TARGET), bin_dir=bin_dir, hook=hook,
                   extra_env={"HMAD_STUB_HOSTILE": "all"}, path_tail="/usr/bin:/bin")
    return decision(result, hook_form(hook))


def _assert_kind(out, kind, property_name):
    assert (out.decision, out.kind) == ("deny", kind), (
        f"{property_name}: expected deny kind={kind}, got {out}"
    )


def _stub_line(*, author="peers-out", status="exhausted", today_shape=False):
    escape, blocker = ("yes", 0) if status == "exhausted" else ("no", 1)
    fields = [quote(FIRST_KEY, safe="/._-"), status, "/x/docs/.bkit-memory.json"]
    if not today_shape:
        fields.append(author)
    fields.append("absent")
    return (f"TDD-STATE: active codex-escape={escape} blocker={blocker} records=1 fallback=none"
            + " record=" + ",".join(fields))


def test_format_state_line_takes_the_author_from_resolve_implementer(tmp_path, monkeypatch):
    root = _project(tmp_path, {
        FIRST_KEY: _step(implementer="codex"),
        SECOND_KEY: _step(codex_status="exhausted", implementer="codex"),
    })
    calls = []

    def fake(record, env=None, which=None):
        calls.append((record, env, which))
        return judge.Implementer("agy", "agy", None, None, "")

    monkeypatch.setattr(judge, "resolve_implementer", fake)
    chain = judge.read_chain(root, None)
    line = judge.format_state_line(chain, root)
    records = line.split(" record=")[1:]
    assert len(records) == len(chain.records) == 2
    assert [record.split(",")[3] for record in records] == ["agy", "agy"], (
        "format_state_line must propagate resolve_implementer's author into the fourth comma field"
    )
    assert [call[0] for call in calls] == list(chain.records), (
        "format_state_line must call resolve_implementer exactly once per record, in chain order"
    )
    assert all(call[1] is calls[0][1] and call[2] is calls[0][2] for call in calls), (
        "format_state_line must use the same env and which snapshot for every resolver call"
    )


def test_hook_reads_authorship_from_the_state_line_not_the_environment(tmp_path):
    root = _root(tmp_path, status="available")
    hook, _ = _tree_b(tmp_path, state_line=_stub_line(status="available"), judge_line=ALLOW)
    out = _outcome(root, _bins(tmp_path, codex=True), hook=hook)
    assert out.decision == "allow", (
        "_read_state must honor author=peers-out despite codex on PATH and no unavailable override; "
        f"got {out}"
    )


def test_agy_authorship_refused_when_agy_resolves(tmp_path):
    root = _project(tmp_path, {FIRST_KEY: _step(implementer="agy", codex_status="exhausted")})
    out = _outcome(root, _bins(tmp_path, agy=True))
    _assert_kind(out, "agy-authorship", "a resolved agy implementer must refuse Claude authorship")


def test_codex_authorship_refused_when_codex_resolves(tmp_path):
    root = _project(tmp_path, {FIRST_KEY: _step(implementer="codex")})
    out = _outcome(root, _bins(tmp_path, codex=True))
    _assert_kind(out, "codex-authorship", "a resolved codex implementer must refuse Claude authorship")
    assert FIRST_KEY.replace("\n", " ") in out.reason
    assert str(root / "docs/.bkit-memory.json") in out.reason


def test_implementer_invalid_refused(tmp_path):
    root = _project(tmp_path, {
        FIRST_KEY: _step(implementer="gpt", codex_status="exhausted", agy_status="exhausted"),
    })
    out = _outcome(root, _bins(tmp_path))
    _assert_kind(out, "implementer-invalid", "an invalid implementer must fail closed")
    assert 'implementer="gpt"' in out.reason, "the refusal must name the invalid JSON value"
    assert "--set implementer=codex|agy|null" in out.reason, "the refusal must name the repair"


def test_fallback_grok_refused_when_peers_out(tmp_path):
    root = _project(tmp_path, {
        FIRST_KEY: _step(codex_status="exhausted", agy_status="exhausted", fallback_agent="grok"),
    })
    out = _outcome(root, _bins(tmp_path))
    _assert_kind(out, "fallback-grok", "grok fallback must refuse Claude when both peers are out")
    assert "hmad-dispatch exec grok" in out.reason


def test_fallback_invalid_refused_when_peers_out(tmp_path):
    root = _project(tmp_path, {
        FIRST_KEY: _step(codex_status="exhausted", agy_status="exhausted", fallback_agent=HOSTILE),
    })
    out = _outcome(root, _bins(tmp_path))
    _assert_kind(out, "fallback-invalid", "invalid fallback must fail closed when both peers are out")
    assert "fallback_agent=" in out.reason and "[H-MAD:MARKER]" in out.reason
    assert "--set fallback_agent=grok|claude|null" in out.reason


def test_implementer_invalid_outranks_codex_authorship(tmp_path):
    root = _project(tmp_path, {
        FIRST_KEY: _step(implementer="codex"),
        SECOND_KEY: _step(implementer="gpt", codex_status="exhausted"),
    })
    out = _outcome(root, _bins(tmp_path, codex=True))
    _assert_kind(out, "implementer-invalid", "a later invalid implementer must outrank the first peer")
    assert SECOND_KEY.replace("\n", " ") in out.reason, "the refusal must identify the invalid record"
    assert "--set implementer=codex|agy|null" in out.reason


def test_peer_refusal_outranks_fallback_invalid(tmp_path):
    root = _project(tmp_path, {
        FIRST_KEY: _step(implementer="codex"),
        SECOND_KEY: _step(codex_status="exhausted", agy_status="exhausted", fallback_agent=HOSTILE),
    })
    out = _outcome(root, _bins(tmp_path, codex=True))
    _assert_kind(out, "codex-authorship", "a resolved peer must outrank an invalid fallback")
    assert FIRST_KEY.replace("\n", " ") in out.reason


def test_chain_fold_blocks_on_the_first_eligible_record(tmp_path):
    root = _project(tmp_path, {
        FIRST_KEY: _step(implementer="agy"),
        SECOND_KEY: _step(implementer="codex"),
    })
    out = _outcome(root, _bins(tmp_path, codex=True, agy=True))
    _assert_kind(out, "agy-authorship", "the first eligible chain record must select the refusing peer")
    assert FIRST_KEY.replace("\n", " ") in out.reason, "the refusal must name the first record"
    assert SECOND_KEY.replace("\n", " ") not in out.reason


def test_today_shape_state_line_is_judge_error(tmp_path):
    root = _root(tmp_path)
    hook, _ = _tree_b(tmp_path, state_line=_stub_line(today_shape=True), judge_line=ALLOW)
    out = _outcome(root, _bins(tmp_path), hook=hook)
    _assert_kind(out, "judge-error", "the old four-field state record must be rejected")


def test_unknown_author_field_is_judge_error(tmp_path):
    root = _root(tmp_path)
    hook, _ = _tree_b(tmp_path, state_line=_stub_line(author="grok"), judge_line=ALLOW)
    out = _outcome(root, _bins(tmp_path), hook=hook)
    _assert_kind(out, "judge-error", "the author grammar must reject grok as an unknown author")


def test_agy_authorship_message_names_the_dispatch_and_the_switches(tmp_path):
    root = _project(tmp_path, {FIRST_KEY: _step(implementer="agy", codex_status="exhausted")})
    out = _outcome(root, _bins(tmp_path, agy=True))
    _assert_kind(out, "agy-authorship", "the agy refusal must explain the agy dispatch and switches")
    for literal in (
        "hmad-dispatch exec agy", "h_mad_assemble_tdd.py --agent agy",
        "--set agy_status=exhausted", "export HMAD_AGY_UNAVAILABLE=1 for a one-off",
        "h_mad_tdd_judge.py implementer",
    ):
        assert literal in out.reason, f"agy-authorship message must name {literal!r}: {out.reason}"
    assert FIRST_KEY.replace("\n", " ") in out.reason
    assert str(root / "docs/.bkit-memory.json") in out.reason


def test_three_message_bodies_match_a8d9ba99():
    base = subprocess.run(
        ["git", "-C", str(REPO), "show", "a8d9ba99:h-mad/hooks/h-mad-tdd-gate.sh"],
        env=hermetic_env(), stdin=subprocess.DEVNULL, capture_output=True, text=True,
        timeout=30, check=True,
    ).stdout
    current = HOOK.read_text(encoding="utf-8")
    for kind in ("codex-authorship", "fallback-grok", "fallback-invalid"):
        pattern = r'_refuse ' + re.escape(kind) + r' "((?:\\.|[^"\\])*)"'
        old_bodies = re.findall(pattern, base, re.S)
        new_bodies = re.findall(pattern, current, re.S)
        assert len(old_bodies) == len(new_bodies) == 1, f"expected exactly one {kind} refusal literal"
        assert new_bodies[0].replace("PEER_", "BLOCKER_") == old_bodies[0].replace("PEER_", "BLOCKER_"), (
            f"{kind} refusal literal must preserve a8d9ba99 bytes except PEER_/BLOCKER_ variable names"
        )
