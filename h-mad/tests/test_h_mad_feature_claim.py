"""J5: `--claim` cannot create, but SKILL documented it as if it could.

The routing snippet printed `--feature <f> --claim "<session-id>"` for every
token, including `start_fresh` -- which by definition names a feature that does
not exist yet. So every first-time claim failed exactly as documented, with
`ERROR: no such feature`.

Of the two filed directions, "make --claim imply --create" is rejected. The
error is a genuine typo guard on every OTHER route: `resume_manual`,
`enter_autonomous` and `halted` all claim an EXISTING feature, and a misspelled
name there should fail rather than silently fork a second empty record. Verified:
`--feature newfeatt --claim` errors today, and that is worth keeping.

So the snippet is corrected per route, and the tests below pin both halves --
the create-and-claim path the docs now promise, and the refusal that must
survive on the paths where it protects something.
"""
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WRITER = REPO_ROOT / "h-mad" / "scripts" / "h_mad_state_write.py"
SKILL_MD = REPO_ROOT / "h-mad" / "SKILL.md"


def _state(tmp_path):
    p = tmp_path / "s.json"
    p.write_text(json.dumps({"version": 1, "orchestrator_state": {}}))
    return p


def _run(*args):
    return subprocess.run([sys.executable, str(WRITER), *map(str, args)],
                          capture_output=True, text=True)


def test_create_and_claim_together_succeed_on_a_fresh_feature(tmp_path):
    state = _state(tmp_path)
    r = _run(state, "--feature", "newfeat", "--create", "--claim", "sess-1")
    assert r.returncode == 0, r.stderr
    rec = json.loads(state.read_text())["orchestrator_state"]["newfeat"]
    assert rec["owner_session_id"] == "sess-1"
    # J8: --create no longer needs an explicit --started-ts, so the documented
    # one-liner does not have to carry one.
    assert rec["started_ts"] and not rec["started_ts"].startswith("1970")


def test_claim_alone_still_refuses_an_unknown_feature(tmp_path):
    # The typo guard. This is deliberately NOT "fixed" -- on a resume route the
    # feature exists, and a misspelling must not silently fork a second record.
    state = _state(tmp_path)
    _run(state, "--feature", "realfeat", "--create")
    r = _run(state, "--feature", "realfeatt", "--claim", "sess-1")
    assert r.returncode != 0
    assert "no such feature" in r.stderr + r.stdout
    assert "realfeatt" not in state.read_text(), "a typo created a record"


def test_skill_start_fresh_snippet_creates_before_claiming():
    text = " ".join(SKILL_MD.read_text(encoding="utf-8").split())
    assert "--create --claim" in text, (
        "the start_fresh route must create before claiming, or it fails as documented"
    )
    assert "start_fresh" in text


def test_release_also_refuses_an_unknown_feature(tmp_path):
    # Found by mutation while checking J5's claim guard: `set_fields` and `claim`
    # both had their "no such feature" guard enforced by the suite, but
    # `release`'s was not -- deleting it left 653 tests passing. A release
    # against a misspelled name should say so rather than silently no-op, or an
    # operator believes they let go of a feature they still hold.
    state = _state(tmp_path)
    _run(state, "--feature", "realfeat", "--create", "--claim", "sess-1")
    r = _run(state, "--feature", "realfeatt", "--release")
    assert r.returncode != 0
    assert "no such feature" in r.stderr + r.stdout
    rec = json.loads(state.read_text())["orchestrator_state"]["realfeat"]
    assert rec["owner_session_id"] == "sess-1", "the real claim was disturbed"
