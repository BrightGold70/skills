"""J11: the mandated substrate record was an unexecutable instruction.

SKILL.md said, in BOTH §"Phase 5 (Implementation) sub-steps" and §"Audit prompt
assembly": *"Record the printed substrate + agent mapping via
`scripts/h_mad_telemetry.py` so the run log states which environment it
dispatched under."*

`h_mad_telemetry.py record` takes only --feature/--state/--out/--docs-root, its
row has no substrate field, and it is shaped as a Phase-7 close-out recorder --
so it could not serve a Phase-5-start instruction even in principle. Consequence:
no run has ever recorded its substrate, and nothing surfaced that, because an
orchestrator either skips the step or calls `record` and reads its cycle-count
output as success.

Fixed by making state the carrier and telemetry the reporter, which is also what
§"Single-source contract" wants: Phase 5 writes `substrate` into
orchestrator_state via the existing generic `--set`, and Phase 7's `record`
copies it onto the row it already builds from that same record.
"""
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "h-mad" / "scripts"
SKILL_MD = REPO_ROOT / "h-mad" / "SKILL.md"
STATE_WRITE = SCRIPTS / "h_mad_state_write.py"
TELEMETRY = SCRIPTS / "h_mad_telemetry.py"

SUBSTRATE = json.dumps({"name": "orca",
                        "agents": {"codex": "term_abc", "agy": "term_def"}})


def _state(tmp_path: Path) -> Path:
    p = tmp_path / "bkit.json"
    p.write_text(json.dumps({"version": 1, "orchestrator_state": {}}))
    return p


def _run(*args):
    return subprocess.run([sys.executable, *map(str, args)],
                          capture_output=True, text=True)


def _create(state: Path, feature: str = "demo"):
    r = _run(STATE_WRITE, state, "--feature", feature, "--create",
             "--started-ts", "2026-07-23T00:00:00+00:00")
    assert r.returncode == 0, r.stderr
    return r


def test_state_accepts_a_substrate_record(tmp_path):
    # The strict schema is additionalProperties:false, so an unknown key is
    # REFUSED -- which is why the Phase-5 instruction had nowhere to write.
    state = _state(tmp_path)
    _create(state)
    r = _run(STATE_WRITE, state, "--feature", "demo", "--set", f"substrate={SUBSTRATE}")
    assert r.returncode == 0, f"strict schema rejected substrate: {r.stderr}"
    rec = json.loads(state.read_text())["orchestrator_state"]["demo"]
    assert rec["substrate"]["name"] == "orca"
    assert rec["substrate"]["agents"]["codex"] == "term_abc"


def test_substrate_is_optional_for_backward_compatibility(tmp_path):
    # Every record written before this change lacks the field. Requiring it would
    # flip historically-valid state to invalid (§"Backward compatibility").
    state = _state(tmp_path)
    _create(state)
    r = _run(STATE_WRITE, state, "--feature", "demo", "--set", "current_phase=5")
    assert r.returncode == 0, r.stderr


def test_telemetry_row_carries_substrate_from_state(tmp_path):
    state = _state(tmp_path)
    _create(state)
    _run(STATE_WRITE, state, "--feature", "demo", "--set", f"substrate={SUBSTRATE}")
    out = tmp_path / "telemetry.jsonl"
    r = _run(TELEMETRY, "record", "--feature", "demo", "--state", state,
             "--out", out, "--docs-root", tmp_path)
    assert r.returncode == 0, r.stderr
    row = json.loads(out.read_text().strip().splitlines()[-1])
    assert row["substrate"] == {"name": "orca",
                                "agents": {"codex": "term_abc", "agy": "term_def"}}


def test_telemetry_row_has_substrate_null_when_unrecorded(tmp_path):
    # The key must be PRESENT and null, not absent: a reader distinguishing
    # "dispatched under an unrecorded substrate" from "this schema predates the
    # field" needs the key to exist.
    state = _state(tmp_path)
    _create(state)
    out = tmp_path / "telemetry.jsonl"
    r = _run(TELEMETRY, "record", "--feature", "demo", "--state", state,
             "--out", out, "--docs-root", tmp_path)
    assert r.returncode == 0, r.stderr
    row = json.loads(out.read_text().strip().splitlines()[-1])
    assert "substrate" in row
    assert row["substrate"] is None


def test_skill_no_longer_orders_an_impossible_telemetry_call():
    # The defect was prose ordering a call the script cannot serve. Assert the
    # instruction is gone AND that the executable one replaced it -- deleting the
    # sentence alone would lose the capability rather than fix it.
    text = " ".join(SKILL_MD.read_text(encoding="utf-8").split())
    assert "Record the printed substrate + agent mapping via `scripts/h_mad_telemetry.py`" not in text, (
        "the unexecutable instruction is still present"
    )
    assert "h_mad_state_write.py" in text
    assert "--set substrate=" in text, (
        "the replacement must name the call that actually works"
    )
    assert text.count("--set substrate=") >= 2, (
        "both instruction sites (Phase 5 and audit assembly) must be corrected"
    )
