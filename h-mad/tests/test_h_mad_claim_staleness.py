"""`--claim` and the resume router must agree about the same stale claim.

Observed live 2026-08-02: a 19.6h-dead session held a feature.
`h_mad_resume_decision.py` treated the claim as abandoned and returned
`enter_autonomous` — proceed — while `h_mad_state_write.py --claim` refused
outright with "is owned by session ...", because it had no staleness allowance
at all. `--claim --force` was the only way through.

That is worse than an inconvenience. It collapses two different acts into one
verb: taking over a demonstrably abandoned claim (routine, safe) and stealing a
claim from a LIVE session (rare, dangerous) both require `--force`. An operator
who reaches for `--force` every time a crashed session blocks them has been
trained out of the protection it exists to provide.

These tests pin the reconciliation: a stale claim is takeable without `--force`,
a live claim is not, and both halves read ONE window so they cannot drift apart
again.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from h_mad_state_ownership import OWNERSHIP_STALE_AFTER_SECONDS, owner_is_live  # noqa: E402
from h_mad_state_write import StateWriteError, claim  # noqa: E402

STATE_WRITE = SCRIPTS / "h_mad_state_write.py"
RESUME = SCRIPTS / "h_mad_resume_decision.py"

NOW = datetime(2026, 8, 3, 12, 0, 0, tzinfo=timezone.utc)


def _iso(moment: datetime) -> str:
    return moment.isoformat()


def _state(tmp_path: Path, heartbeat: str | None, owner: str | None = "dead-session") -> Path:
    """A strict-v2.2-valid record held by `owner`, last seen at `heartbeat`."""
    record = {
        "feature": "demo",
        "started_ts": "2026-08-01T00:00:00+00:00",
        "last_completed_phase": 4,
        "current_phase": 5,
        "phase": "step5",
        "audit_cycles": {"plan": 0, "design": 0, "impl_plan": 0},
        "iterate_cycles": 0,
        "halt_reason": None,
        "halt_ts": None,
        "owner_session_id": owner,
        "owner_heartbeat_ts": heartbeat,
    }
    path = tmp_path / "state.json"
    path.write_text(json.dumps({"orchestrator_state": {"demo": record}}), encoding="utf-8")
    return path


def _owner_of(path: Path) -> str | None:
    return json.loads(path.read_text())["orchestrator_state"]["demo"]["owner_session_id"]


# --- the reconciliation --------------------------------------------------


def test_a_stale_claim_is_takeable_without_force(tmp_path: Path) -> None:
    stale = _iso(NOW - timedelta(seconds=OWNERSHIP_STALE_AFTER_SECONDS + 60))
    path = _state(tmp_path, stale)
    claim(path, "demo", "new-session", now=_iso(NOW))
    assert _owner_of(path) == "new-session"


def test_a_live_claim_is_still_refused_without_force(tmp_path: Path) -> None:
    # The half that must NOT relax. A refusal test that only ever observes
    # refusals would pass against a claim() that never refuses anything.
    live = _iso(NOW - timedelta(seconds=60))
    path = _state(tmp_path, live)
    with pytest.raises(StateWriteError, match="owned by session"):
        claim(path, "demo", "new-session", now=_iso(NOW))
    assert _owner_of(path) == "dead-session", "the store must be left untouched"


def test_force_still_overrides_a_live_claim(tmp_path: Path) -> None:
    live = _iso(NOW - timedelta(seconds=60))
    path = _state(tmp_path, live)
    claim(path, "demo", "new-session", now=_iso(NOW), force=True)
    assert _owner_of(path) == "new-session"


def test_a_claim_with_no_heartbeat_is_treated_as_live(tmp_path: Path) -> None:
    # Fail closed, and identically to the router: held with no evidence of when
    # is not evidence of abandonment. Otherwise a record predating heartbeats
    # would be silently takeable.
    path = _state(tmp_path, None)
    with pytest.raises(StateWriteError, match="owned by session"):
        claim(path, "demo", "new-session", now=_iso(NOW))


def test_an_unparseable_heartbeat_is_treated_as_live(tmp_path: Path) -> None:
    path = _state(tmp_path, "not-a-timestamp")
    with pytest.raises(StateWriteError, match="owned by session"):
        claim(path, "demo", "new-session", now=_iso(NOW))


def test_taking_a_stale_claim_refreshes_the_heartbeat(tmp_path: Path) -> None:
    stale = _iso(NOW - timedelta(seconds=OWNERSHIP_STALE_AFTER_SECONDS + 60))
    path = _state(tmp_path, stale)
    claim(path, "demo", "new-session", now=_iso(NOW))
    record = json.loads(path.read_text())["orchestrator_state"]["demo"]
    assert record["owner_heartbeat_ts"] == _iso(NOW), (
        "a taken-over claim that keeps the dead session's heartbeat is stale on arrival"
    )


def test_reclaiming_your_own_live_feature_still_works(tmp_path: Path) -> None:
    live = _iso(NOW - timedelta(seconds=60))
    path = _state(tmp_path, live, owner="me")
    claim(path, "demo", "me", now=_iso(NOW))
    assert _owner_of(path) == "me"


# --- the boundary the two halves must share ------------------------------


@pytest.mark.parametrize(
    "offset,live,why",
    [
        (OWNERSHIP_STALE_AFTER_SECONDS - 1, True, "just inside the window"),
        (OWNERSHIP_STALE_AFTER_SECONDS, True, "exactly at the window is still live"),
        (OWNERSHIP_STALE_AFTER_SECONDS + 1, False, "one second past is stale"),
    ],
)
def test_the_liveness_boundary_is_exact(offset: int, live: bool, why: str) -> None:
    heartbeat = _iso(NOW - timedelta(seconds=offset))
    assert owner_is_live(heartbeat, now=_iso(NOW)) is live, why


def test_both_halves_agree_on_every_claim_the_router_would_release(tmp_path: Path) -> None:
    """The actual bug, stated as a property.

    Whenever the router says `enter_autonomous` because the owner went stale,
    `--claim` must succeed without `--force`. Any offset where the router
    releases but the writer refuses is the 2026-08-02 deadlock reproduced.
    """
    for offset in (60, 3599, OWNERSHIP_STALE_AFTER_SECONDS, OWNERSHIP_STALE_AFTER_SECONDS + 1, 19 * 3600):
        heartbeat = _iso(NOW - timedelta(seconds=offset))
        path = _state(tmp_path, heartbeat)
        router = subprocess.run(
            [sys.executable, str(RESUME), "--state", str(path), "--feature", "demo",
             "--session-id", "new-session", "--now", _iso(NOW)],
            capture_output=True, text=True,
        ).stdout.strip()
        released = router != "owned_elsewhere"

        try:
            claim(path, "demo", "new-session", now=_iso(NOW))
            writer_allowed = True
        except StateWriteError:
            writer_allowed = False

        assert released == writer_allowed, (
            f"at age {offset}s the router said {router!r} (released={released}) but the "
            f"writer allowed={writer_allowed} — the two halves disagree about the same claim"
        )


def test_the_window_is_two_hours() -> None:
    # Every other test here derives its offsets FROM the constant, so they all
    # move with it and none of them would notice it changing. The window is a
    # published contract — SKILL.md, the schema description, and an operator's
    # expectation of how long a crashed session holds a feature all assume two
    # hours — so the value itself needs pinning, not just its consistency.
    assert OWNERSHIP_STALE_AFTER_SECONDS == 2 * 60 * 60


def test_the_window_has_a_single_source_of_truth() -> None:
    # Two modules holding their own copy of "2 hours" is how they drifted apart
    # in the first place; a duplicated literal would let them drift again.
    import h_mad_resume_decision as router

    assert router.OWNERSHIP_STALE_AFTER_SECONDS is OWNERSHIP_STALE_AFTER_SECONDS, (
        "the router no longer reads the shared window — a second copy can drift"
    )


# --- the documented half --------------------------------------------------


def test_skill_documents_that_a_released_claim_is_takeable() -> None:
    # The reconciliation is only useful if an operator knows to STOP passing
    # `--force` by reflex. Code that behaves correctly while the guidance still
    # says "force is how you get through" leaves the habit — and the habit is
    # what erodes the live-claim guard. Whitespace-normalised so a markdown
    # reflow cannot break it.
    skill = " ".join((SCRIPTS.parent / "SKILL.md").read_text(encoding="utf-8").split())
    for literal, why in [
        (
            "A non-`owned_elsewhere` token guarantees the claim will be accepted.",
            "the guarantee is the whole point of the fix",
        ),
        (
            "treat needing it on any other route as a bug, not as the usual step",
            "without this, `--force` stays the reflex it became",
        ),
    ]:
        assert " ".join(literal.split()) in skill, f"SKILL.md dropped guidance: {why}"


# --- CLI surface ----------------------------------------------------------


# The CLI has no `--now` injection point, so these anchor on the real clock:
# a heartbeat far enough in the past is stale whenever the test runs, and one
# stamped at call time is live.


def test_cli_claim_takes_a_stale_feature_without_force(tmp_path: Path) -> None:
    real_now = datetime.now(timezone.utc)
    stale = _iso(real_now - timedelta(seconds=OWNERSHIP_STALE_AFTER_SECONDS + 3600))
    path = _state(tmp_path, stale)
    proc = subprocess.run(
        [sys.executable, str(STATE_WRITE), str(path), "--feature", "demo",
         "--claim", "new-session"],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert _owner_of(path) == "new-session"


def test_cli_refusal_of_a_live_claim_names_force_as_the_way_through(tmp_path: Path) -> None:
    real_now = datetime.now(timezone.utc)
    path = _state(tmp_path, _iso(real_now))
    proc = subprocess.run(
        [sys.executable, str(STATE_WRITE), str(path), "--feature", "demo",
         "--claim", "new-session"],
        capture_output=True, text=True,
    )
    assert proc.returncode != 0
    assert "force" in proc.stderr.lower(), proc.stderr
