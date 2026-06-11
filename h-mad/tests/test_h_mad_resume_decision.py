import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = REPO_ROOT / "h-mad" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from h_mad_resume_decision import _phase_num, decide  # noqa: E402


def _write_state(tmp_path: Path, feature: str, feat_state: dict) -> Path:
    state_file = tmp_path / ".bkit-memory.json"
    state_file.write_text(
        json.dumps({"version": 1, "orchestrator_state": {feature: feat_state}}),
        encoding="utf-8",
    )
    return state_file


@pytest.mark.parametrize(
    "value,expected",
    [
        (7, 7),          # schema int form
        (4, 4),
        (0, 0),
        ("step7", 7),    # orchestrator "stepN" string form actually written to state
        ("phase7", 7),   # alternate "phaseN" form also seen in real state
        ("step4", 4),
        ("STEP5", 5),    # case-insensitive
        ("complete", 7), # sentinel
        ("5", 5),        # bare digit string
        (None, 0),       # absent/unknown degrades, never raises
        (True, 0),       # bool is an int subclass — must NOT count as 1
        ("garbage", 0),
    ],
)
def test_phase_num_coerces_every_state_form(value, expected) -> None:
    assert _phase_num(value) == expected


def test_decide_complete_from_stepN_string_does_not_crash(tmp_path: Path) -> None:
    # Regression: state stored "step7" (string) while decide() compared `>= 7`
    # (int) -> TypeError on every completed feature. Must return "complete".
    state = _write_state(tmp_path, "feat", {"last_completed_phase": "step7"})
    assert decide(state, "feat") == "complete"


def test_decide_honors_explicit_complete_flag(tmp_path: Path) -> None:
    state = _write_state(
        tmp_path, "feat", {"complete": True, "last_completed_phase": "step5"}
    )
    assert decide(state, "feat") == "complete"


def test_decide_complete_sentinel_phase(tmp_path: Path) -> None:
    state = _write_state(tmp_path, "feat", {"last_completed_phase": "complete"})
    assert decide(state, "feat") == "complete"


def test_decide_current_phase_complete_with_phase7_last(tmp_path: Path) -> None:
    # Real synopsis-manifest-source-ingestion shape: current_phase sentinel
    # plus the "phaseN" (not "stepN") last_completed_phase variant.
    state = _write_state(
        tmp_path,
        "feat",
        {"current_phase": "complete", "last_completed_phase": "phase7"},
    )
    assert decide(state, "feat") == "complete"


def test_decide_routing_thresholds(tmp_path: Path) -> None:
    assert decide(_write_state(tmp_path, "f", {"last_completed_phase": "step4"}), "f") == "enter_autonomous"
    assert decide(_write_state(tmp_path, "f", {"last_completed_phase": "step2"}), "f") == "resume_manual"
    assert decide(_write_state(tmp_path, "f", {"halt_reason": "step5d:no_codex_pane"}), "f") == "halted"


def test_decide_missing_feature_or_state_starts_fresh(tmp_path: Path) -> None:
    state = _write_state(tmp_path, "other", {"last_completed_phase": "step7"})
    assert decide(state, "absent") == "start_fresh"
    assert decide(tmp_path / "nonexistent.json", "feat") == "start_fresh"
