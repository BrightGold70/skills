import atexit
import json
import os
import shutil
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
WRAPPER = SKILL / "scripts" / "hmad-dispatch.sh"
STUBS = SKILL / "tests" / "stubs"

# J7: the pin file is the second leak channel into this harness. F13 stripped the
# HMAD_ORCA_* env vars, but _pin_file() falls back to a CWD-RELATIVE
# ".h-mad/orca-pins.env" and pytest's cwd is the repo, so the repo's own session
# pin file was read by every test that set no explicit value. Measured: 17 failed
# with a pin file present, 153 passed with it absent.
#
# This path is deliberately NEVER CREATED: _pin_file() only reads it via
# `[ -f "$pf" ]`, so a non-existent path IS the "no pin file" state and there is
# nothing to clean up. tempfile. mkdtemp() would be wrong here — it registers no
# cleanup and would leak an empty directory on every pytest collection (rejected
# by design audit v1). PID-scoped so two concurrent suite runs cannot collide.
_NO_PIN_BASE = Path(tempfile.gettempdir())
_NO_PIN_STEM = f"hmad-tests-absent-orca-pins-{os.getpid()}"
# The canonical never-created path, kept as a module symbol for the guards below.
_NO_PIN_FILE = _NO_PIN_BASE / f"{_NO_PIN_STEM}.env"


def _absent_pin_file() -> str:
    """A DISTINCT never-created pin path for each run() invocation.

    A single module-scoped path would be shared by every test in the worker: if
    one ever forgets to pass an explicit HMAD_ORCA_PIN_FILE to a pin-WRITING
    verb, it writes there and silently contaminates every later test. Per
    invocation, that same mistake can only affect the one call that made it, so
    it surfaces as a local failure instead of spooky action at a distance.
    (6a-prime architectural review.)
    """
    return str(_NO_PIN_BASE / f"{_NO_PIN_STEM}-{uuid.uuid4().hex}.env")


@atexit.register
def _remove_stray_pin_file() -> None:
    """Defensive only: every pin-writing test passes its own HMAD_ORCA_PIN_FILE,
    so nothing should create this path. If a future test forgets, `pin` would
    mkdir -p and write here, contaminating later tests and leaving a file behind."""
    for stray in [_NO_PIN_FILE, *_NO_PIN_BASE.glob(f"{_NO_PIN_STEM}-*.env")]:
        try:
            stray.unlink()
        except FileNotFoundError:
            pass

# --- Real Orca response envelopes ------------------------------------------
#
# Captured from a live Orca runtime during the 2026-07-21 Tier-2 e2e. Every
# response is {"id": <per-request uuid>, "ok": true, "result": {...}} and every
# create-verb returns the resource id at .result.<resource>.id -- NEVER at the
# envelope .id, which is a per-request correlation uuid that always exists.
#
# These fixtures deliberately keep a decoy envelope id: an extraction that
# falls through to .id yields "req_<uuid>_NOT_THE_RESOURCE_ID" and the assert
# fails loudly instead of silently returning a plausible-looking uuid. Earlier
# stubs guessed flat shapes ({"result":{"taskId":...}}) and so guarded a
# fiction -- the wrapper passed here while failing against a real runtime.
_ENVELOPE_DECOY_ID = "req_11111111-2222-3333-4444-555555555555_NOT_THE_RESOURCE_ID"

_ENV_TASK_CREATE = (
    '{"id":"' + _ENVELOPE_DECOY_ID + '","ok":true,'
    '"result":{"task":{"id":"task_1","parent_id":null,"task_title":"implement-module",'
    '"status":"ready","deps":"[]","result":null,"completed_at":null}}}'
)

_ENV_GATE_CREATE = (
    '{"id":"' + _ENVELOPE_DECOY_ID + '","ok":true,'
    '"result":{"gate":{"id":"gate_1","task_id":"task_1","question":"Continue?",'
    '"options":"[\\"yes\\",\\"no\\"]","status":"pending","resolution":null}}}'
)

# worker_done carries taskId/dispatchId inside a JSON *string* payload, not a
# nested object -- indexing it directly is a jq hard error, so the filter must
# fromjson it first.
_ENV_CHECK_WAIT = (
    '{"id":"' + _ENVELOPE_DECOY_ID + '","ok":true,"result":{"messages":['
    '{"id":"msg_other","type":"worker_done","from_handle":"term_w",'
    '"payload":"{\\"taskId\\":\\"other\\",\\"dispatchId\\":\\"ctx_other\\"}"},'
    '{"id":"msg_match","type":"worker_done","from_handle":"term_w","report-path":"/r",'
    '"payload":"{\\"taskId\\":\\"task_1\\",\\"dispatchId\\":\\"ctx_1\\"}"}'
    '],"count":2}}'
)


def run(args, *, substrate=None, env=None, capture=None, cwd=None):
    """Invoke the wrapper with only the named stub binaries on PATH."""
    bindir = Path(env["_BINDIR"]) if env and "_BINDIR" in env else None
    e = dict(os.environ)
    e.pop("HMAD_SUBSTRATE", None)
    # Session-marker env vars checked by _detect_substrate() ABOVE binary
    # presence; must be stripped so an ambient cmux/orca host session doesn't
    # false-resolve substrate detection for stub-only tests.
    e.pop("CMUX", None)
    e.pop("CMUX_PANE", None)
    e.pop("ORCA_SESSION", None)
    e.pop("ORCA_TERMINAL_ID", None)
    # ORCA_PANE_KEY drives coordinator auto-detect; strip the ambient one so a
    # host Orca session can't leak into stub-only tests (tests set it explicitly).
    e.pop("ORCA_PANE_KEY", None)
    # F13: strip every HMAD_ORCA_* pin (coordinator + agent terminal handles).
    # A live h-mad Orca session exports these, and the identity/coordinator tests
    # assume an unpinned environment — leaked pins made 8 tests fail spuriously
    # exactly when the suite is run from inside a running orchestration.
    for _k in [k for k in e if k.startswith("HMAD_ORCA_")]:
        e.pop(_k, None)
    # The receipt override is likewise caller state: lifecycle tests must start
    # from the pin-file-derived default unless they explicitly set an override.
    e.pop("HMAD_PREFLIGHT_RECEIPT_FILE", None)
    if substrate:
        e["HMAD_SUBSTRATE"] = substrate
    if capture:
        e["HMAD_STUB_CAPTURE"] = str(capture)
    if env:
        e.update({k: v for k, v in env.items() if k != "_BINDIR"})
    # AFTER the update, so a test that passes its own HMAD_ORCA_PIN_FILE keeps it.
    # env values must be str, hence the cast.
    e.setdefault("HMAD_ORCA_PIN_FILE", _absent_pin_file())
    # Build an isolated PATH containing only the requested stubs (+ real jq/coreutils).
    # Deliberately excludes the ambient PATH: dev/CI machines may have real
    # cmux/orca binaries installed (e.g. under /opt/homebrew/bin), which would
    # leak into `command -v` lookups and defeat the bindir-only isolation this
    # helper exists to provide.
    e["PATH"] = f"{bindir}:/usr/bin:/bin" if bindir else os.environ["PATH"]
    return subprocess.run(["bash", str(WRAPPER), *args], capture_output=True,
                          text=True, env=e, cwd=cwd)


def _bindir(tmp_path, names):
    """Create a bin dir symlinking only the requested stub names."""
    b = tmp_path / "bin"
    b.mkdir()
    for n in names:
        (b / n).symlink_to(STUBS / n)
    # Later-task wrappers (identity resolve-from-json, alive) pipe stub
    # output through jq. Provide the real jq under the isolated PATH without
    # widening it to the ambient PATH (which would leak real cmux/orca).
    jq = shutil.which("jq")
    if jq:
        (b / "jq").symlink_to(jq)
    return b


def _git_repo(tmp_path, *, branch="main"):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.com"],
                   check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test User"], check=True)
    (repo / "tracked.txt").write_text("initial\n")
    subprocess.run(["git", "-C", str(repo), "add", "tracked.txt"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", "initial"],
                   check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo), "branch", "-M", branch], check=True)
    return repo


def _rm(repo, *, base=None, force=False, tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    args = ["worktree-rm", f"repo::{repo}"]
    if force:
        args.append("--force")
    if base is not None:
        args.extend(["--base", base])
    result = run(args, substrate="orca", env={"_BINDIR": b}, capture=cap)
    return result, cap


def test_env_reports_override(tmp_path):
    b = _bindir(tmp_path, ["cmux", "orca"])
    r = run(["env"], substrate="orca", env={"_BINDIR": b})
    assert r.returncode == 0
    assert "orca" in r.stdout


def test_detect_cmux_only_is_cmux(tmp_path):
    b = _bindir(tmp_path, ["cmux"])
    r = run(["env"], env={"_BINDIR": b})
    assert r.returncode == 0
    assert "cmux" in r.stdout


def test_detect_orca_only_is_orca(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    r = run(["env"], env={"_BINDIR": b})
    assert r.returncode == 0
    assert "orca" in r.stdout


def test_detect_default_both_present_is_orca(tmp_path):
    b = _bindir(tmp_path, ["cmux", "orca"])
    r = run(["env"], env={"_BINDIR": b})
    assert r.returncode == 0
    assert "substrate: orca" in r.stdout


def test_detect_override_forces_cmux(tmp_path):
    b = _bindir(tmp_path, ["cmux", "orca"])
    r = run(["env"], substrate="cmux", env={"_BINDIR": b})
    assert r.returncode == 0
    assert "substrate: cmux" in r.stdout


def test_detect_marker_forces_cmux(tmp_path):
    b = _bindir(tmp_path, ["cmux", "orca"])
    r = run(["env"], env={"_BINDIR": b, "CMUX": "1"})
    assert r.returncode == 0
    assert "substrate: cmux" in r.stdout


def test_no_substrate_errors(tmp_path):
    b = _bindir(tmp_path, [])
    r = run(["env"], env={"_BINDIR": b})
    assert r.returncode == 1


def test_cmux_identity_autodetect_by_title(tmp_path):
    # No env pins: resolve each agent by matching its cmux pane title (mirrors _orca_find).
    b = _bindir(tmp_path, ["cmux"])
    tree = ('surface surface:1 [terminal] "Claude Code"\n'
            'surface surface:4 [terminal] "Codex - HemaSuite"\n'
            'surface surface:5 [terminal] "agy --dangerously-skip-permissions"\n')
    r = run(["env"], substrate="cmux", env={"_BINDIR": b, "HMAD_STUB_CMUX_STDOUT": tree})
    assert "codex -> surface:4" in r.stdout
    assert "agy -> surface:5" in r.stdout


def test_cmux_identity_autodetect_ambiguous_and_missing(tmp_path):
    b = _bindir(tmp_path, ["cmux"])
    # 0 matches -> UNRESOLVED (loud, not a stale default)
    r0 = run(["env"], substrate="cmux",
             env={"_BINDIR": b, "HMAD_STUB_CMUX_STDOUT": 'surface surface:1 [terminal] "Claude Code"\n'})
    assert "codex -> UNRESOLVED" in r0.stdout
    assert "agy -> UNRESOLVED" in r0.stdout
    # 2 codex matches -> ambiguous -> UNRESOLVED
    r2 = run(["env"], substrate="cmux",
             env={"_BINDIR": b, "HMAD_STUB_CMUX_STDOUT":
                  'surface surface:4 [terminal] "Codex - A"\nsurface surface:6 [terminal] "Codex - B"\n'})
    assert "codex -> UNRESOLVED" in r2.stdout


def test_cmux_identity_autodetect_rejects_false_matches(tmp_path):
    # Token must be the LEADING title word; unrelated panes whose title merely
    # contains the token as a substring must NOT match.
    b = _bindir(tmp_path, ["cmux"])
    tree = ('surface surface:3 [terminal] "vim codex_result.py"\n'
            'surface surface:7 [terminal] "less agy-notes.md"\n'
            'surface surface:4 [terminal] "Codex - HemaSuite"\n'
            'surface surface:5 [terminal] "agy --dangerously-skip-permissions"\n')
    r = run(["env"], substrate="cmux", env={"_BINDIR": b, "HMAD_STUB_CMUX_STDOUT": tree})
    # Only the real leading-token panes resolve (not the vim/less substring panes).
    assert "codex -> surface:4" in r.stdout
    assert "agy -> surface:5" in r.stdout


def _orca_terms(*pairs):
    """Build an `orca terminal list --json` envelope from (handle, title, preview)."""
    items = ",".join(
        '{"handle":"%s","title":"%s","preview":"%s"}' % p for p in pairs
    )
    return '{"ok":true,"result":{"terminals":[' + items + ']}}'


def test_orca_identity_autodetect_by_title(tmp_path):
    # Mirror of the cmux auto-detect: resolve by the LEADING word of the title.
    b = _bindir(tmp_path, ["orca"])
    listing = _orca_terms(
        ("term_claude", "Claude Code", "claude --dangerously-skip-permissions"),
        ("term_codex", "Codex - HemaSuite", "gpt-5.6-terra high"),
        ("term_agy", "agy --dangerously-skip-permissions", "Gemini 3.1 Pro"),
    )
    r = run(["env"], substrate="orca", env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": listing})
    assert "codex -> term_codex" in r.stdout
    assert "agy -> term_agy" in r.stdout


def test_orca_identity_autodetect_ambiguous_and_missing(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    r0 = run(["env"], substrate="orca",
             env={"_BINDIR": b,
                  "HMAD_STUB_ORCA_STDOUT": _orca_terms(("term_c", "Claude Code", "claude"))})
    assert "codex -> UNRESOLVED" in r0.stdout
    assert "agy -> UNRESOLVED" in r0.stdout
    r2 = run(["env"], substrate="orca",
             env={"_BINDIR": b,
                  "HMAD_STUB_ORCA_STDOUT": _orca_terms(("term_a", "Codex - A", ""),
                                                       ("term_b", "Codex - B", ""))})
    assert "codex -> UNRESOLVED" in r2.stdout


def test_orca_identity_autodetect_ignores_preview_and_substring_titles(tmp_path):
    # Regression: the matcher used to test an unanchored regex against
    # (preview + title). Preview is live scrollback, so a coordinator pane that
    # merely *rendered* the word "codex" would match and the coordinator could
    # dispatch a task to itself. Identity must come from the title alone, and
    # only as its leading word.
    b = _bindir(tmp_path, ["orca"])
    listing = _orca_terms(
        # Coordinator rendering the word in its scrollback -- must NOT match.
        ("term_coord", "Claude Code", "discussing codex and agy dispatch targets"),
        # Title contains the token but not as the leading word -- must NOT match.
        ("term_vim", "vim codex_result.py", ""),
        ("term_less", "less agy-notes.md", ""),
        ("term_codex", "Codex - HemaSuite", ""),
        ("term_agy", "agy --dangerously-skip-permissions", ""),
    )
    r = run(["env"], substrate="orca", env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": listing})
    # agy sets its own OSC title, so its title IS identity and resolves.
    assert "agy -> term_agy" in r.stdout
    # Codex sets no OSC title: "Codex - HemaSuite" can only have been inherited
    # from the tab (or the worktree basename), so it says nothing about what runs
    # in that pane -- an agy pane in a tab named "Codex - …" carries the same
    # string. With no preview banner either, the honest answer is UNRESOLVED,
    # which forces a pin. Resolving it here is what let Codex work reach agy.
    assert "codex -> UNRESOLVED" in r.stdout
    # And the coordinator, which merely *rendered* both words, is never a match.
    assert "term_coord" not in r.stdout
    assert "term_vim" not in r.stdout and "term_less" not in r.stdout


def test_orca_identity_preview_fallback_skips_coordinator_own_pane(tmp_path):
    # Title match yields 0, so the preview fallback runs. The coordinator's own
    # preview renders this conversation and therefore contains "codex" whenever
    # the token is merely discussed -- it must be excluded, or the coordinator
    # dispatches to itself. The real agent pane (generic title, banner in the
    # preview) is the correct target.
    b = _bindir(tmp_path, ["orca"])
    listing = _orca_terms(
        ("term_coord", "Claude Code", "weighing codex vs agy as dispatch targets"),
        ("term_real", "HemaSuite", "OpenAI Codex (v0.144.6)  model: gpt-5.6-terra"),
    )
    r = run(["env"], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": listing,
                 "HMAD_ORCA_COORDINATOR_TERMINAL": "term_coord"})
    assert "codex -> term_real" in r.stdout
    assert "codex -> term_coord" not in r.stdout


def test_orca_identity_preview_fallback_refuses_when_only_coordinator_matches(tmp_path):
    # Excluding the coordinator leaves 0 candidates -> loud UNRESOLVED rather
    # than a self-dispatch.
    b = _bindir(tmp_path, ["orca"])
    listing = _orca_terms(("term_coord", "Claude Code", "talking about codex again"))
    r = run(["env"], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": listing,
                 "HMAD_ORCA_COORDINATOR_TERMINAL": "term_coord"})
    assert "codex -> UNRESOLVED" in r.stdout


def test_cmux_identity_env_override(tmp_path):
    b = _bindir(tmp_path, ["cmux"])
    r = run(["env"], substrate="cmux",
            env={"_BINDIR": b, "HMAD_CMUX_CODEX_SURFACE": "surface:9"})
    assert "codex -> surface:9" in r.stdout


def test_resolve_reads_pin_file_when_env_unset(tmp_path):
    # H4: a session pin file (written by `pin-agents`) survives Codex/agy preview
    # decay — resolution consults it before falling back to auto-detect, so a
    # long autonomous run doesn't lose a pane when its banner scrolls off.
    b = _bindir(tmp_path, ["orca"])
    pins = tmp_path / "pins.env"
    pins.write_text("agy=term_pinned_agy\ncodex=term_pinned_codex\n")
    # No env pin, no ORCA_PANE_KEY, empty terminal list → auto-detect would find
    # nothing; the pin file must supply the handle.
    r = run(["resolve", "agy"], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_PIN_FILE": str(pins),
                 "HMAD_STUB_ORCA_STDOUT": _orca_terms()})
    assert r.returncode == 0
    assert r.stdout.strip() == "term_pinned_agy"


def test_env_var_pin_beats_pin_file(tmp_path):
    # H4 precedence: an explicit operator env pin always wins over the session
    # pin file, which in turn wins over auto-detect.
    b = _bindir(tmp_path, ["orca"])
    pins = tmp_path / "pins.env"
    pins.write_text("agy=term_from_file\n")
    r = run(["resolve", "agy"], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_PIN_FILE": str(pins),
                 "HMAD_ORCA_AGY_TERMINAL": "term_from_env"})
    assert r.returncode == 0
    assert r.stdout.strip() == "term_from_env"


def test_pin_agents_writes_resolved_handles(tmp_path):
    # H4: `pin-agents` resolves both agents once and persists them to the pin
    # file, so subsequent dispatches are deterministic regardless of preview decay.
    b = _bindir(tmp_path, ["orca"])
    pins = tmp_path / "pins.env"
    r = run(["pin-agents"], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_PIN_FILE": str(pins),
                 "HMAD_ORCA_CODEX_TERMINAL": "t-codex",
                 "HMAD_ORCA_AGY_TERMINAL": "t-agy"})
    assert r.returncode == 0
    written = pins.read_text()
    assert "codex=t-codex" in written
    assert "agy=t-agy" in written


def test_pin_agents_fails_loud_on_unresolved(tmp_path):
    # H4 follow-up: Codex has no reliable auto-identity (title = worktree, preview
    # decays). pin-agents must NOT return 0 when an agent is unresolved — a silent
    # partial pin let a run proceed believing both agents were addressable. It
    # still persists the agent that DID resolve, but exits non-zero and names the
    # missing agent + the exact env var to pin.
    b = _bindir(tmp_path, ["orca"])
    pins = tmp_path / "pins.env"
    # agy resolves via env pin (and that pane is live); codex has no pin and no
    # pane in the listing → auto-detect finds nothing → UNRESOLVED.
    r = run(["pin-agents"], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_PIN_FILE": str(pins),
                 "HMAD_ORCA_AGY_TERMINAL": "t-agy",
                 "HMAD_STUB_ORCA_STDOUT": _orca_terms(("t-agy", "agy", ""))})
    assert r.returncode != 0
    assert "codex" in r.stderr
    assert "HMAD_ORCA_CODEX_TERMINAL" in r.stderr
    assert "agy=t-agy" in pins.read_text()   # the resolved agent is still frozen


def test_launch_creates_pins_and_echoes_handle(tmp_path):
    # H5 durable path: h-mad owns the Codex launch, so identity is captured at
    # spawn from the create response (`.result.terminal.handle`) — no title/preview
    # dependence, no manual pin. launch resolves the handle, pins it, echoes it.
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    pins = tmp_path / "pins.env"
    canned = '{"ok":true,"result":{"terminal":{"handle":"term_new_codex"}}}'
    r = run(["launch", "codex"], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_PIN_FILE": str(pins),
                 "HMAD_STUB_ORCA_STDOUT": canned}, capture=cap)
    assert r.returncode == 0
    assert r.stdout.strip() == "term_new_codex"
    assert "codex=term_new_codex" in pins.read_text()      # pinned at spawn
    cmd = cap.read_text()
    assert "terminal create --worktree active --command codex --title codex --json" in cmd
    # resolve then reads the freshly-pinned handle
    r2 = run(["resolve", "codex"], substrate="orca",
             env={"_BINDIR": b, "HMAD_ORCA_PIN_FILE": str(pins)})
    assert r2.stdout.strip() == "term_new_codex"


def test_launch_honors_worktree_and_rejects_unknown_agent(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    pins = tmp_path / "pins.env"
    canned = '{"ok":true,"result":{"terminal":{"handle":"h1"}}}'
    r = run(["launch", "agy", "--worktree", "path:/x"], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_PIN_FILE": str(pins),
                 "HMAD_STUB_ORCA_STDOUT": canned}, capture=cap)
    assert r.returncode == 0
    assert "--worktree path:/x" in cap.read_text()
    bad = run(["launch", "bogus"], substrate="orca", env={"_BINDIR": b})
    assert bad.returncode == 2
    assert "unknown agent" in bad.stderr


def test_pin_writes_single_agent_and_resolve_reads_it(tmp_path):
    # H5 follow-up: the durable path for Codex is capturing its handle at a known
    # moment. `pin <agent> <handle>` records one agent without disturbing the
    # other, and resolution reads it back.
    b = _bindir(tmp_path, ["orca"])
    pins = tmp_path / "pins.env"
    pins.write_text("agy=t-agy\n")
    r = run(["pin", "codex", "term_xyz"], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_PIN_FILE": str(pins)})
    assert r.returncode == 0
    text = pins.read_text()
    assert "codex=term_xyz" in text
    assert "agy=t-agy" in text            # sibling preserved
    r2 = run(["resolve", "codex"], substrate="orca",
             env={"_BINDIR": b, "HMAD_ORCA_PIN_FILE": str(pins)})
    assert r2.stdout.strip() == "term_xyz"


def test_pin_replaces_existing_and_rejects_unknown_agent(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    pins = tmp_path / "pins.env"
    pins.write_text("codex=old\n")
    r = run(["pin", "codex", "new_handle"], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_PIN_FILE": str(pins)})
    assert r.returncode == 0
    text = pins.read_text()
    assert "codex=new_handle" in text and "codex=old" not in text   # replaced, not duplicated
    bad = run(["pin", "bogus", "h"], substrate="orca",
              env={"_BINDIR": b, "HMAD_ORCA_PIN_FILE": str(pins)})
    assert bad.returncode == 2
    assert "unknown agent" in bad.stderr


def test_pin_agents_clear_removes_file(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    pins = tmp_path / "pins.env"
    pins.write_text("agy=stale\n")
    r = run(["pin-agents", "--clear"], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_PIN_FILE": str(pins)})
    assert r.returncode == 0
    assert not pins.exists()


def test_orca_identity_explicit_pin(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    r = run(["env"], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_CODEX_TERMINAL": "t-abc",
                 "HMAD_ORCA_AGY_TERMINAL": "t-def"})
    assert "codex -> t-abc" in r.stdout
    assert "agy -> t-def" in r.stdout


def test_orca_identity_resolves_from_list_json(tmp_path):
    # Previews carry the agents' launch banners, not the bare words "codex"/"agy":
    # a bare token is something any pane can render while merely discussing
    # dispatch, which is how the coordinator once resolved as Codex.
    b = _bindir(tmp_path, ["orca"])
    canned = ('{"result":{"terminals":['
              '{"handle":"term_c","preview":"gpt-5.6-terra high"},'
              '{"handle":"term_a","preview":"Antigravity CLI 1.1.5"}]}}')
    r = run(["env"], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": canned})
    assert "codex -> term_c" in r.stdout
    assert "agy -> term_a" in r.stdout


def _orca_terms_full(*terms):
    """Build an `orca terminal list --json` envelope from full term dicts
    (handle/title/preview/worktreePath/leafId)."""
    return json.dumps({"ok": True, "result": {"terminals": list(terms)}})


def test_orca_identity_scopes_to_coordinator_worktree(tmp_path):
    # Multi-worktree Orca: two panes titled "agy", one per worktree. The
    # coordinator (ORCA_PANE_KEY leafId) lives in worktree A; only A's agy may
    # resolve. Without worktree scoping the global title match sees 2 "agy"
    # panes -> ambiguous -> UNRESOLVED (the live 2026-07-22 bug: a HemaSuite agy
    # made the skills agy unresolvable).
    b = _bindir(tmp_path, ["orca"])
    listing = _orca_terms_full(
        {"handle": "term_coordA", "title": "coordinator", "preview": "driving h-mad",
         "worktreePath": "/repo/A", "leafId": "leaf-A"},
        {"handle": "term_agyA", "title": "agy", "preview": "",
         "worktreePath": "/repo/A", "leafId": "leaf-A2"},
        {"handle": "term_agyB", "title": "agy", "preview": "",
         "worktreePath": "/repo/B", "leafId": "leaf-B2"},
        # Codex panes carry no OSC title, so they are identified by their launch
        # banner, not by the tab-inherited "Codex - X" string. The banner is what
        # makes this test still exercise Codex scoping rather than title parsing.
        {"handle": "term_codexA", "title": "Codex - A", "preview": "gpt-5.6-terra high",
         "worktreePath": "/repo/A", "leafId": "leaf-A3"},
        {"handle": "term_codexB", "title": "Codex - B", "preview": "gpt-5.6-terra high",
         "worktreePath": "/repo/B", "leafId": "leaf-B3"},
    )
    r = run(["env"], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": listing,
                 "ORCA_PANE_KEY": "tab-1:leaf-A"})
    assert "agy -> term_agyA" in r.stdout
    assert "codex -> term_codexA" in r.stdout
    assert "term_agyB" not in r.stdout
    assert "term_codexB" not in r.stdout


def test_orca_identity_excludes_coordinator_own_pane_by_autodetect(tmp_path):
    # The coordinator's own pane can carry the agent token in its title/preview
    # (it renders this conversation). Auto-detect via ORCA_PANE_KEY must exclude
    # it WITHOUT needing HMAD_ORCA_COORDINATOR_TERMINAL pinned — the live gap
    # where $self was empty so the coordinator could match itself.
    b = _bindir(tmp_path, ["orca"])
    listing = _orca_terms_full(
        {"handle": "term_self", "title": "agy notes", "preview": "codex and agy",
         "worktreePath": "/repo/A", "leafId": "leaf-A"},
        {"handle": "term_agyA", "title": "agy", "preview": "",
         "worktreePath": "/repo/A", "leafId": "leaf-A2"},
    )
    r = run(["env"], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": listing,
                 "ORCA_PANE_KEY": "tab-1:leaf-A"})
    assert "agy -> term_agyA" in r.stdout
    assert "agy -> term_self" not in r.stdout


def test_orca_identity_codex_by_model_banner(tmp_path):
    # Live 2026-07-22: a user-launched Codex pane is titled after its worktree
    # ("skills") and its preview banner carries NO "codex" literal -- only the
    # model id ("gpt-5.6-terra") and persona text. Title Pass-1 misses; the
    # preview fallback must recognise the Codex model-id signature. agy is
    # unaffected (its title resolves directly).
    b = _bindir(tmp_path, ["orca"])
    listing = _orca_terms_full(
        {"handle": "term_coord", "title": "coordinator", "preview": "driving h-mad",
         "worktreePath": "/repo/A", "leafId": "leaf-A"},
        {"handle": "term_codex", "title": "skills",
         "preview": "Sol is highly capable. Explain this codebase gpt-5.6-terra high",
         "worktreePath": "/repo/A", "leafId": "leaf-A2"},
        {"handle": "term_agy", "title": "agy", "preview": "",
         "worktreePath": "/repo/A", "leafId": "leaf-A3"},
    )
    r = run(["env"], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": listing,
                 "ORCA_PANE_KEY": "tab-1:leaf-A"})
    assert "codex -> term_codex" in r.stdout
    assert "agy -> term_agy" in r.stdout


def test_resolve_agy_autodetects_in_coordinator_worktree(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    listing = _orca_terms_full(
        {"handle": "term_coordA", "title": "coordinator", "preview": "",
         "worktreePath": "/repo/A", "leafId": "leaf-A"},
        {"handle": "term_agyA", "title": "agy", "preview": "",
         "worktreePath": "/repo/A", "leafId": "leaf-A2"},
        {"handle": "term_agyB", "title": "agy", "preview": "",
         "worktreePath": "/repo/B", "leafId": "leaf-B2"},
    )
    r = run(["resolve", "agy"], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": listing,
                 "ORCA_PANE_KEY": "tab-1:leaf-A"})
    assert r.returncode == 0
    assert r.stdout == "term_agyA\n"
    assert r.stderr == ""


def test_resolve_codex_uses_explicit_orca_pin(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    r = run(["resolve", "codex"], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_CODEX_TERMINAL": "t-x"})
    assert r.returncode == 0
    assert r.stdout == "t-x\n"
    assert r.stderr == ""


def test_resolve_agy_reports_unresolved_orca_candidates(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    r = run(["resolve", "agy"], substrate="orca",
            env={"_BINDIR": b,
                 "HMAD_STUB_ORCA_STDOUT": _orca_terms(("term_codex", "codex", ""))})
    assert r.returncode == 1
    assert r.stdout == ""
    assert "pin HMAD_ORCA_AGY_TERMINAL" in r.stderr


def test_resolve_rejects_unknown_agent_with_agent_diagnostic(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    r = run(["resolve", "bogus"], substrate="orca", env={"_BINDIR": b})
    assert r.returncode == 2
    assert r.stdout == ""
    assert "unknown agent" in r.stderr


def test_resolve_requires_agent_arg_without_unknown_verb(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    r = run(["resolve"], substrate="orca", env={"_BINDIR": b})
    assert r.returncode == 2
    assert r.stdout == ""
    assert "unknown verb" not in r.stderr


def test_resolve_agy_matches_env_handle(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    listing = _orca_terms(
        ("term_codex", "Codex - HemaSuite", ""),
        ("term_agy", "agy --dangerously-skip-permissions", ""),
    )
    env = {"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": listing}
    env_result = run(["env"], substrate="orca", env=env)
    handle = next(line for line in env_result.stdout.splitlines() if line.startswith("agy -> "))
    handle = handle.removeprefix("agy -> ")

    r = run(["resolve", "agy"], substrate="orca", env=env)
    assert r.returncode == 0
    assert r.stdout == f"{handle}\n"
    assert r.stderr == ""


def test_resolve_is_known_verb_while_other_unknown_verbs_remain_unknown(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    resolve = run(["resolve", "agy"], substrate="orca",
                  env={"_BINDIR": b, "HMAD_ORCA_AGY_TERMINAL": "term_agy"})
    unknown = run(["frobnicate"], substrate="orca", env={"_BINDIR": b})

    assert resolve.returncode == 0
    assert "unknown verb" not in resolve.stderr
    assert unknown.returncode == 2
    assert "unknown verb" in unknown.stderr


def test_send_cmux_uses_file_contents(tmp_path):
    b = _bindir(tmp_path, ["cmux"])
    cap = tmp_path / "cap.txt"
    pf = tmp_path / "prompt.txt"; pf.write_text("HELLO-PROMPT")
    r = _enforced_send(["send", "codex", str(pf)], substrate="cmux",
                       env={"_BINDIR": b, "HMAD_CMUX_CODEX_SURFACE": "surface:5"}, capture=cap)
    assert r.returncode == 0
    text = cap.read_text()
    assert "cmux send --surface surface:5 HELLO-PROMPT" in text
    assert "send-key --surface surface:5 Enter" in text


def test_send_orca_uses_file_contents(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    pf = tmp_path / "prompt.txt"; pf.write_text("HELLO-ORCA")
    r = _enforced_send(["send", "codex", str(pf)], substrate="orca",
                       env={"_BINDIR": b, "HMAD_ORCA_CODEX_TERMINAL": "t-1"}, capture=cap)
    assert r.returncode == 0
    text = cap.read_text()
    assert "orca terminal send --terminal t-1 --text HELLO-ORCA --enter" in text


def test_clear_sends_slash_clear(tmp_path):
    b = _bindir(tmp_path, ["cmux"])
    cap = tmp_path / "cap.txt"
    r = run(["clear", "agy"], substrate="cmux",
            env={"_BINDIR": b, "HMAD_CMUX_AGY_SURFACE": "surface:2"}, capture=cap)
    assert r.returncode == 0
    assert "cmux send --surface surface:2 /clear" in cap.read_text()


def test_read_cmux_passes_lines(tmp_path):
    b = _bindir(tmp_path, ["cmux"])
    cap = tmp_path / "cap.txt"
    r = run(["read", "codex", "--lines", "50"], substrate="cmux",
            env={"_BINDIR": b, "HMAD_CMUX_CODEX_SURFACE": "surface:5"}, capture=cap)
    assert r.returncode == 0
    assert "cmux read-screen --surface surface:5 --lines 50" in cap.read_text()


def test_read_orca_uses_native_limit(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    r = run(["read", "codex"], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_CODEX_TERMINAL": "term_read"}, capture=cap)
    assert r.returncode == 0
    assert cap.read_text() == "orca terminal read --terminal term_read --limit 50\n"


def test_read_orca_passes_explicit_line_limit(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    r = run(["read", "codex", "--lines", "50"], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_CODEX_TERMINAL": "term_read"}, capture=cap)
    assert r.returncode == 0
    assert cap.read_text() == "orca terminal read --terminal term_read --limit 50\n"


def test_read_orca_from_start_reads_whole_buffer(tmp_path):
    # F5: --from-start recovers a report longer than the retained tail viewport.
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    r = run(["read", "codex", "--from-start"], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_CODEX_TERMINAL": "term_read"}, capture=cap)
    assert r.returncode == 0
    assert cap.read_text() == "orca terminal read --terminal term_read --cursor 0 --limit 4000\n"


def test_read_orca_explicit_cursor(tmp_path):
    # F5: --cursor <n> reads from an absolute offset.
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    r = run(["read", "codex", "--cursor", "1200", "--lines", "300"], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_CODEX_TERMINAL": "term_read"}, capture=cap)
    assert r.returncode == 0
    assert cap.read_text() == "orca terminal read --terminal term_read --cursor 1200 --limit 300\n"


def test_interrupt_orca_sends_ctrl_c(tmp_path):
    # F4: interrupt cancels a wedged agent turn with Ctrl-C (0x03), never a bare Enter.
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    r = run(["interrupt", "agy"], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_AGY_TERMINAL": "term_int"}, capture=cap)
    assert r.returncode == 0
    out = cap.read_text()
    assert "orca terminal send --terminal term_int --text" in out
    assert "--enter" not in out  # a blank-Enter submit would be the bug


def test_interrupt_cmux_sends_ctrl_c(tmp_path):
    # F4: cmux path sends the C-c key.
    b = _bindir(tmp_path, ["cmux"])
    cap = tmp_path / "cap.txt"
    r = run(["interrupt", "codex"], substrate="cmux",
            env={"_BINDIR": b, "HMAD_CMUX_CODEX_SURFACE": "surface:3"}, capture=cap)
    assert r.returncode == 0
    assert "cmux send-key --surface surface:3 C-c" in cap.read_text()


def test_worktree_ps_rejects_ok_false_envelope(tmp_path):
    # F11: an exit-0 `"ok":false` error envelope must NOT pass through as data —
    # the whole point of routing verbs through _orca_json.
    b = _bindir(tmp_path, ["orca"])
    r = run(["worktree-ps"], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_FAIL": "1"})
    assert r.returncode != 0
    assert "boom" in r.stderr
    assert r.stdout == ""


def test_task_create_rejects_ok_false_envelope(tmp_path):
    # F11: same guard on an id-extracting verb.
    b = _bindir(tmp_path, ["orca"])
    spec = tmp_path / "spec.txt"; spec.write_text("do the thing")
    r = run(["task-create", "label", str(spec)], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_FAIL": "1",
                 "HMAD_ORCA_COORDINATOR_TERMINAL": "term_coord"})
    assert r.returncode != 0
    assert r.stdout == ""


def test_dispatch_rejects_ok_false_envelope(tmp_path):
    # F11 extension: the raw-JSON `dispatch` verb must not swallow an exit-0
    # `"ok":false` envelope. Without the guard it echoes the error as stdout and
    # returns 0 → the coordinator believes the task was delivered and `await`
    # then times out with no diagnostic. The codex pin makes _resolve_target
    # succeed without an orca call, so the failure is the dispatch call itself.
    b = _bindir(tmp_path, ["orca"])
    r = run(["dispatch", "codex", "task_1"], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_FAIL": "1",
                 "HMAD_ORCA_CODEX_TERMINAL": "term_codex"})
    assert r.returncode != 0
    assert "boom" in r.stderr
    assert r.stdout == ""


def test_gate_resolve_rejects_ok_false_envelope(tmp_path):
    # F11 extension: `gate-resolve` must surface an error envelope, not report a
    # phantom successful resolution (exit 0 + error JSON on stdout).
    b = _bindir(tmp_path, ["orca"])
    r = run(["gate-resolve", "gate_1", "approved"], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_FAIL": "1"})
    assert r.returncode != 0
    assert "boom" in r.stderr
    assert r.stdout == ""


def test_await_rejects_ok_false_envelope(tmp_path):
    # F11 extension: `await` piped a raw `check` response into jq; an `"ok":false`
    # envelope yielded `[]` → empty match → looked like "no worker_done yet" and
    # timed out silently. The guard must surface it instead. Coordinator pin makes
    # _coordinator succeed without an orca call.
    b = _bindir(tmp_path, ["orca"])
    r = run(["await", "task_1", "--timeout", "5"], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_FAIL": "1",
                 "HMAD_ORCA_COORDINATOR_TERMINAL": "term_coord"})
    assert r.returncode != 0
    assert "boom" in r.stderr
    assert r.stdout == ""


_TERMS_WITH_LEAF = '{"ok":true,"result":{"terminals":[{"handle":"term_coord","leafId":"leaf-1"}]}}'


def test_coordinator_autodetect_makes_orchestration_on(tmp_path):
    # G5: with codex/agy pinned and ORCA_PANE_KEY matching a terminal's leafId,
    # the coordinator resolves WITHOUT HMAD_ORCA_COORDINATOR_TERMINAL → orchestration on.
    b = _bindir(tmp_path, ["orca"])
    r = run(["env"], substrate="orca",
            env={"_BINDIR": b, "ORCA_PANE_KEY": "tab-9:leaf-1",
                 "HMAD_ORCA_CODEX_TERMINAL": "t-c", "HMAD_ORCA_AGY_TERMINAL": "t-a",
                 "HMAD_STUB_ORCA_STDOUT": _TERMS_WITH_LEAF})
    assert r.returncode == 0
    assert "orchestration: on" in r.stdout


def test_coordinator_autodetect_absent_pane_key_is_off(tmp_path):
    # G5: no pin and no ORCA_PANE_KEY → coordinator unresolved → orchestration off.
    b = _bindir(tmp_path, ["orca"])
    r = run(["env"], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_CODEX_TERMINAL": "t-c", "HMAD_ORCA_AGY_TERMINAL": "t-a"})
    assert r.returncode == 0
    assert "orchestration: off" in r.stdout


def test_coordinator_pin_wins_over_autodetect(tmp_path):
    # G5: an explicit pin is authoritative even when auto-detect could resolve.
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    spec = tmp_path / "spec.txt"; spec.write_text("do the thing")
    r = run(["task-create", "label", str(spec)], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_COORDINATOR_TERMINAL": "term_pinned",
                 "ORCA_PANE_KEY": "tab-9:leaf-1",
                 "HMAD_STUB_ORCA_STDOUT": '{"ok":true,"result":{"task":{"id":"task_1"}}}'},
            capture=cap)
    assert r.returncode == 0
    # the pinned handle must appear as the worker_done --to line in the task spec
    assert "term_pinned" in cap.read_text()


def test_gate_wait_returns_resolution(tmp_path):
    # G4: a resolved gate → gate-wait echoes its resolution, exit 0.
    b = _bindir(tmp_path, ["orca"])
    resolved = '{"ok":true,"result":{"gates":[{"id":"g1","status":"resolved","resolution":"yes"}]}}'
    r = run(["gate-wait", "g1", "--timeout", "2", "--interval", "0"], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": resolved})
    assert r.returncode == 0
    assert r.stdout.strip() == "yes"


def test_gate_wait_times_out_on_pending(tmp_path):
    # G4: gate still pending (empty list) → clean non-zero timeout, no hang.
    b = _bindir(tmp_path, ["orca"])
    r = run(["gate-wait", "g1", "--timeout", "0", "--interval", "0"], substrate="orca",
            env={"_BINDIR": b})
    assert r.returncode != 0
    assert "timed out" in r.stderr


def test_gate_wait_fails_closed_on_non_resolved_status(tmp_path):
    # G4 hardening: a gate with a non-"resolved" status (open/created/waiting) and
    # no resolution must NOT be treated as resolved — a blocking merge gate must
    # fail closed (keep polling → timeout), never proceed on an ambiguous state.
    b = _bindir(tmp_path, ["orca"])
    openish = '{"ok":true,"result":{"gates":[{"id":"g1","status":"open","resolution":null}]}}'
    r = run(["gate-wait", "g1", "--timeout", "0", "--interval", "0"], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": openish})
    assert r.returncode != 0
    assert "timed out" in r.stderr


def test_gate_wait_requires_orca(tmp_path):
    b = _bindir(tmp_path, ["cmux"])
    r = run(["gate-wait", "g1"], substrate="cmux", env={"_BINDIR": b})
    assert r.returncode == 2


def test_report_wait_returns_file_when_marker_present(tmp_path):
    # File-drop transport: agent wrote the report + a .done marker → report-wait
    # emits the file, exit 0. No substrate/scrape/sentinel involved.
    b = _bindir(tmp_path, ["orca"])
    report = tmp_path / "audit.md"
    report.write_text("## Must-fix\nNone\n")
    (tmp_path / "audit.md.done").write_text("")
    r = run(["report-wait", str(report), "--timeout", "2", "--interval", "0"],
            substrate="orca", env={"_BINDIR": b})
    assert r.returncode == 0
    assert "## Must-fix" in r.stdout


def test_report_wait_times_out_without_marker(tmp_path):
    # Report present but no .done marker → still generating → keep polling → timeout.
    b = _bindir(tmp_path, ["orca"])
    report = tmp_path / "audit.md"
    report.write_text("partial...")
    r = run(["report-wait", str(report), "--timeout", "0", "--interval", "0"],
            substrate="orca", env={"_BINDIR": b})
    assert r.returncode != 0
    assert "timed out" in r.stderr


def test_report_wait_ignores_marker_when_report_empty(tmp_path):
    # Race guard: .done landed before content → empty file must NOT be read.
    b = _bindir(tmp_path, ["orca"])
    report = tmp_path / "audit.md"
    report.write_text("")
    (tmp_path / "audit.md.done").write_text("")
    r = run(["report-wait", str(report), "--timeout", "0", "--interval", "0"],
            substrate="orca", env={"_BINDIR": b})
    assert r.returncode != 0


def test_report_wait_is_substrate_agnostic(tmp_path):
    # No _require_orca: file-drop works on cmux too (shared filesystem).
    b = _bindir(tmp_path, ["cmux"])
    report = tmp_path / "r.md"
    report.write_text("hello")
    (tmp_path / "r.md.done").write_text("")
    r = run(["report-wait", str(report), "--timeout", "2", "--interval", "0"],
            substrate="cmux", env={"_BINDIR": b})
    assert r.returncode == 0
    assert r.stdout.strip() == "hello"


def test_report_wait_missing_path_arg(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    r = run(["report-wait"], substrate="orca", env={"_BINDIR": b})
    assert r.returncode == 2


def test_report_wait_rejects_flag_in_path_slot(tmp_path):
    # A flag where the path should be must fail fast (exit 2), not poll 300s for a
    # file named "--timeout".
    b = _bindir(tmp_path, ["orca"])
    r = run(["report-wait", "--timeout", "600"], substrate="orca", env={"_BINDIR": b})
    assert r.returncode == 2
    assert "looks like a flag" in r.stderr


def test_wait_orca_uses_native_idle(tmp_path):
    """Native tui-idle is still called — but as a first gate, not as proof.

    This test used to assert the capture equalled the native wait line alone.
    That equality encoded "native idle is sufficient", which is the defect:
    the call was observed returning satisfied while an agent was still
    generating. The assertion is now containment, and the companion test
    below pins the confirming read that must follow it.
    """
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    r = run(["wait", "agy"], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_AGY_TERMINAL": "term_wait",
                 "HMAD_STUB_ORCA_STDOUT": "steady", "HMAD_WAIT_POLL_INTERVAL": "0"},
            capture=cap)
    assert r.returncode == 0
    assert ("orca terminal wait --terminal term_wait --for tui-idle "
            "--timeout-ms 300000") in cap.read_text()


def test_wait_orca_converts_timeout_seconds_to_milliseconds(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    r = run(["wait", "agy", "--timeout", "30"], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_AGY_TERMINAL": "term_wait",
                 "HMAD_STUB_ORCA_STDOUT": "steady", "HMAD_WAIT_POLL_INTERVAL": "0"},
            capture=cap)
    assert r.returncode == 0
    assert "--timeout-ms 30000" in cap.read_text()


def test_orca_explicit_pin_bypasses_list_resolution(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    r = run(["read", "codex"], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_CODEX_TERMINAL": "term_pin"}, capture=cap)
    assert r.returncode == 0
    assert cap.read_text() == "orca terminal read --terminal term_pin --limit 50\n"


def test_alive_cmux_true(tmp_path):
    b = _bindir(tmp_path, ["cmux"])
    r = run(["alive", "codex"], substrate="cmux",
            env={"_BINDIR": b, "HMAD_CMUX_CODEX_SURFACE": "surface:5",
                 "HMAD_STUB_CMUX_STDOUT": "surface:5 codex\nsurface:2 agy\n"})
    assert r.returncode == 0


def test_alive_cmux_false(tmp_path):
    b = _bindir(tmp_path, ["cmux"])
    r = run(["alive", "codex"], substrate="cmux",
            env={"_BINDIR": b, "HMAD_STUB_CMUX_STDOUT": "surface:2 agy\n"})
    assert r.returncode == 1


def test_notify_cmux(tmp_path):
    b = _bindir(tmp_path, ["cmux"])
    cap = tmp_path / "cap.txt"
    r = run(["notify", "halted", "reason-x"], substrate="cmux",
            env={"_BINDIR": b}, capture=cap)
    assert r.returncode == 0
    assert "cmux notify --title halted --body reason-x" in cap.read_text()


def test_alive_orca_true(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    canned = '{"result":{"terminals":[{"handle":"term_x"}]}}'
    r = run(["alive", "codex"], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_CODEX_TERMINAL": "term_x",
                 "HMAD_STUB_ORCA_STDOUT": canned})
    assert r.returncode == 0


def test_alive_orca_false(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    canned = '{"result":{"terminals":[{"handle":"term_x"}]}}'
    r = run(["alive", "codex"], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_CODEX_TERMINAL": "term_y",
                 "HMAD_STUB_ORCA_STDOUT": canned})
    assert r.returncode == 1


def test_task_create_registers_pinned_coordinator_and_parses_task_id(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    spec = tmp_path / "task.md"; spec.write_text("Implement the module.\n")
    r = run(["task-create", "implement-module", str(spec)], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_COORDINATOR_TERMINAL": "term_coord",
                 "HMAD_STUB_ORCA_STDOUT": _ENV_TASK_CREATE},
            capture=cap)
    assert r.returncode == 0
    assert r.stdout == "task_1\n"
    text = cap.read_text()
    assert "orca orchestration task-create --spec [H-MAD] worker_done coordinator handle (use as --to): term_coord" in text
    assert "Implement the module." in text
    assert "--task-title implement-module --json" in text


def test_task_create_requires_coordinator_and_existing_spec_file(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    spec = tmp_path / "task.md"; spec.write_text("spec")
    missing_pin = run(["task-create", "label", str(spec)], substrate="orca", env={"_BINDIR": b})
    assert missing_pin.returncode == 1
    assert "HMAD_ORCA_COORDINATOR_TERMINAL" in missing_pin.stderr
    missing_file = run(["task-create", "label", str(tmp_path / "missing.md")], substrate="orca",
                       env={"_BINDIR": b, "HMAD_ORCA_COORDINATOR_TERMINAL": "term_coord"})
    assert missing_file.returncode == 2
    assert "spec file not found" in missing_file.stderr


def test_dispatch_orchestration_uses_resolved_target(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    r = run(["dispatch", "codex", "task_1"], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_CODEX_TERMINAL": "term_codex"}, capture=cap)
    assert r.returncode == 0
    # --inject is load-bearing: without it Orca returns the preamble text but
    # delivers nothing to the worker, so worker_done never fires and await
    # always times out. The reference doc says dispatch *sends* the task.
    assert cap.read_text() == (
        "orca orchestration dispatch --task task_1 --to term_codex "
        "--inject --return-preamble --json\n"
    )


def test_await_filters_worker_done_and_converts_timeout(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    r = run(["await", "task_1", "--timeout", "60"], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_COORDINATOR_TERMINAL": "term_coord",
                 "HMAD_STUB_ORCA_STDOUT": _ENV_CHECK_WAIT}, capture=cap)
    assert r.returncode == 0
    # Real worker_done carries the ids inside a JSON *string* payload, so the
    # filter must fromjson it; matching selects msg_match and drops msg_other.
    assert "msg_match" in r.stdout
    assert "msg_other" not in r.stdout
    assert cap.read_text() == "orca orchestration check --terminal term_coord --wait --types worker_done --timeout-ms 60000 --json\n"


def test_await_defaults_timeout_and_requires_coordinator(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    r = run(["await", "task_1"], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_COORDINATOR_TERMINAL": "term_coord",
                 "HMAD_STUB_ORCA_STDOUT": '{"messages":[]}'}, capture=cap)
    assert r.returncode == 0
    assert "--timeout-ms 600000 --json" in cap.read_text()
    no_pin = run(["await", "task_1"], substrate="orca", env={"_BINDIR": b})
    assert no_pin.returncode == 1
    assert "HMAD_ORCA_COORDINATOR_TERMINAL" in no_pin.stderr


def test_gate_create_with_and_without_options_and_gate_resolve(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    canned = _ENV_GATE_CREATE
    r = run(["gate-create", "task_1", "Continue?", '["yes","no"]'], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": canned}, capture=cap)
    assert r.returncode == 0
    assert r.stdout == "gate_1\n"
    assert cap.read_text() == 'orca orchestration gate-create --task task_1 --question Continue? --options ["yes","no"] --json\n'
    r = run(["gate-create", "task_1", "Continue?"], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": canned}, capture=cap)
    assert r.returncode == 0
    assert cap.read_text().endswith("orca orchestration gate-create --task task_1 --question Continue? --json\n")
    r = run(["gate-resolve", "gate_1", "approved"], substrate="orca", env={"_BINDIR": b}, capture=cap)
    assert r.returncode == 0
    assert cap.read_text().endswith("orca orchestration gate-resolve --id gate_1 --resolution approved --json\n")


def test_orchestration_verbs_require_orca_on_cmux(tmp_path):
    b = _bindir(tmp_path, ["cmux", "orca"])
    spec = tmp_path / "task.md"; spec.write_text("spec")
    verbs = [
        ["task-create", "label", str(spec)], ["dispatch", "codex", "task_1"],
        ["await", "task_1"], ["gate-create", "task_1", "q?"],
        ["gate-resolve", "gate_1", "approved"],
    ]
    for args in verbs:
        r = run(args, substrate="cmux", env={"_BINDIR": b})
        assert r.returncode == 2
        assert "requires orchestration mode (substrate=orca)" in r.stderr


def test_orchestration_verbs_validate_required_arguments(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    for args in (["task-create"], ["dispatch", "codex"], ["await"], ["gate-create", "task_1"],
                 ["gate-resolve"], ["gate-resolve", "gate_1"]):
        r = run(args, substrate="orca", env={"_BINDIR": b})
        assert r.returncode == 2
        assert "missing required argument" in r.stderr


def test_env_reports_orchestration_indicator(tmp_path):
    b = _bindir(tmp_path, ["cmux", "orca"])
    on = run(["env"], substrate="orca",
             env={"_BINDIR": b, "HMAD_ORCA_COORDINATOR_TERMINAL": "term_coord"})
    assert on.returncode == 0
    assert "orchestration: on" in on.stdout
    off = run(["env"], substrate="cmux", env={"_BINDIR": b})
    assert off.returncode == 0
    assert "orchestration: off" in off.stdout


def test_orchestration_worker_done_prompt_blocks_and_docs():
    required_prompt_strings = ["worker_done", "--task-id", "--report-path",
                               "[H-MAD] worker_done coordinator handle"]
    for filename in ["codex-implementer-prompt.md", "agy-spec-reviewer-prompt.md"]:
        text = (SKILL / "references" / filename).read_text()
        for required in required_prompt_strings:
            assert required in text
    mode_doc = SKILL / "references" / "orchestration-mode.md"
    assert mode_doc.exists()
    mode_text = mode_doc.read_text()
    for required in ["task-create", "dispatch", "await", "gate-create", "gate-resolve",
                     "HMAD_ORCA_COORDINATOR_TERMINAL", "worker_done"]:
        assert required in mode_text
    assert "references/orchestration-mode.md" in (SKILL / "SKILL.md").read_text()


def test_worktree_create_argv_orca(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    r = run(["worktree-create", "m", "--agent", "a1", "--base", "main"], substrate="orca",
            env={"_BINDIR": b}, capture=cap)
    assert r.returncode == 0
    assert cap.read_text() == "orca worktree create --name m --agent a1 --base-branch main --json\n"


def test_worktree_create_parses_selector_and_empty_match(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    selected = run(["worktree-create", "m"], substrate="orca",
                   env={"_BINDIR": b,
                        "HMAD_STUB_ORCA_STDOUT": '{"id":"envelope-xyz","result":{"worktree":{"id":"wt-7"}}}'})
    assert selected.returncode == 0
    assert selected.stdout == "wt-7\n"
    empty = run(["worktree-create", "m"], substrate="orca",
                env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": '{"result":{}}'})
    assert empty.returncode == 0
    assert empty.stdout == ""


def test_worktree_create_repo_targeting(tmp_path):
    # Live Orca requires a repo target: `orca worktree create` without --repo
    # fails "Missing repo selector". Verify targeting flags pass through.
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    r = run(["worktree-create", "m", "--repo", "HemaSuite"], substrate="orca",
            env={"_BINDIR": b}, capture=cap)
    assert r.returncode == 0
    assert cap.read_text() == "orca worktree create --name m --repo HemaSuite --json\n"


def test_worktree_create_prompt_file_and_missing_file(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("X")
    r = run(["worktree-create", "m", "--prompt-file", str(prompt)], substrate="orca",
            env={"_BINDIR": b}, capture=cap)
    assert r.returncode == 0
    assert "--prompt X --json" in cap.read_text()

    missing_cap = tmp_path / "missing-cap.txt"
    missing = run(["worktree-create", "m", "--prompt-file", str(tmp_path / "missing.txt")],
                  substrate="orca", env={"_BINDIR": b}, capture=missing_cap)
    assert missing.returncode == 2
    assert "prompt file not found" in missing.stderr
    assert not missing_cap.exists()


def test_worktree_create_prompt_registers_task_on_stderr(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("fanout prompt")
    canned = ('{"result":{"worktree":{"id":"wt-fanout"},'
              '"task":{"id":"task-fanout"},"gate":{"id":"gate-fanout"}}}')
    r = run(["worktree-create", "fanout", "--prompt-file", str(prompt)], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_COORDINATOR_TERMINAL": "term_coord",
                 "HMAD_STUB_ORCA_STDOUT": canned}, capture=cap)
    assert r.returncode == 0
    assert r.stdout == "wt-fanout\n"
    assert r.stderr == "[H-MAD] worktree_task task=task-fanout selector=wt-fanout\n"
    assert "orca worktree create --name fanout --prompt fanout prompt --json\n" in cap.read_text()
    assert "--task-title worktree:fanout --json" in cap.read_text()


def test_worktree_create_without_prompt_registers_no_task(tmp_path):
    """AC-5.1/AC-5.3: the --prompt-file gate must DISCRIMINATE.

    The pre-existing argv test passes whether or not the gate exists, because
    run() strips HMAD_ORCA_*, so _coordinator() fails and task-create bails
    before it ever calls orca — leaving the capture clean for the wrong reason.
    Pinning a coordinator here removes that accident, so registering
    unconditionally becomes observable. Verified by mutation: replacing the
    `[ -n "$pf" ]` gate with `true` fails this test and nothing else.
    """
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    canned = ('{"result":{"worktree":{"id":"wt-bare"},'
              '"task":{"id":"task-should-not-exist"}}}')
    r = run(["worktree-create", "bare"], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_COORDINATOR_TERMINAL": "term_coord",
                 "HMAD_STUB_ORCA_STDOUT": canned}, capture=cap)
    assert r.returncode == 0
    assert r.stdout == "wt-bare\n"
    calls = cap.read_text()
    assert "task-create" not in calls, "no task may be registered without --prompt-file"
    assert "worktree_task" not in r.stderr


def test_worktree_create_task_id_can_open_gate(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("fanout prompt")
    canned = ('{"result":{"worktree":{"id":"wt-fanout"},'
              '"task":{"id":"task-fanout"},"gate":{"id":"gate-fanout"}}}')
    created = run(["worktree-create", "fanout", "--prompt-file", str(prompt)], substrate="orca",
                  env={"_BINDIR": b, "HMAD_ORCA_COORDINATOR_TERMINAL": "term_coord",
                       "HMAD_STUB_ORCA_STDOUT": canned}, capture=cap)
    assert created.returncode == 0
    gate = run(["gate-create", "task-fanout", "Approve?"], substrate="orca",
               env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": canned}, capture=cap)
    assert gate.returncode == 0
    assert gate.stdout == "gate-fanout\n"
    assert "orca orchestration gate-create --task task-fanout --question Approve? --json\n" in cap.read_text()


def test_worktree_create_task_registration_failure_is_nonfatal(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("fanout prompt")
    created = run(["worktree-create", "fanout", "--prompt-file", str(prompt)], substrate="orca",
                  env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT":
                       '{"result":{"worktree":{"id":"wt-fanout"}}}'}, capture=cap)
    assert created.returncode == 0
    assert created.stdout == "wt-fanout\n"
    assert "[H-MAD] worktree_task_skipped selector=wt-fanout" in created.stderr
    assert cap.read_text() == "orca worktree create --name fanout --prompt fanout prompt --json\n"


def test_worktree_create_refuses_cmux(tmp_path):
    b = _bindir(tmp_path, ["cmux", "orca"])
    cap = tmp_path / "cap.txt"
    r = run(["worktree-create", "m"], substrate="cmux", env={"_BINDIR": b}, capture=cap)
    assert r.returncode == 2
    assert "requires orchestration mode (substrate=orca)" in r.stderr
    assert not cap.exists()


def test_worktree_ps_argv_and_passthrough(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    canned = '{"result":{"a":1}}'
    r = run(["worktree-ps", "--limit", "3"], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": canned}, capture=cap)
    assert r.returncode == 0
    assert cap.read_text() == "orca worktree ps --limit 3 --json\n"
    assert r.stdout == '{"a":1}\n'

    default_cap = tmp_path / "default-cap.txt"
    default = run(["worktree-ps"], substrate="orca", env={"_BINDIR": b}, capture=default_cap)
    assert default.returncode == 0
    assert default_cap.read_text() == "orca worktree ps --json\n"


def test_worktree_rm_argv_force_and_failure(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    r = run(["worktree-rm", "wt-7", "--force"], substrate="orca", env={"_BINDIR": b}, capture=cap)
    assert r.returncode == 0
    assert cap.read_text() == "orca worktree rm --worktree wt-7 --force --json\n"

    failed = run(["worktree-rm", "wt-7"], substrate="orca",
                 env={"_BINDIR": b, "HMAD_STUB_ORCA_EXIT": "1"})
    assert failed.returncode == 1
    assert "[H-MAD] worktree-rm failed selector=wt-7 rc=1" in failed.stderr


def test_worktree_rm_refuses_modified_tracked_repo(tmp_path):
    repo = _git_repo(tmp_path)
    (repo / "tracked.txt").write_text("modified\n")
    result, cap = _rm(repo, tmp_path=tmp_path)
    assert result.returncode != 0
    assert "worktree_has_uncommitted_work" in result.stderr
    assert not cap.exists()


def test_worktree_rm_refuses_untracked_repo(tmp_path):
    repo = _git_repo(tmp_path)
    (repo / "untracked.txt").write_text("untracked\n")
    result, cap = _rm(repo, tmp_path=tmp_path)
    assert result.returncode != 0
    assert "worktree_has_uncommitted_work" in result.stderr
    assert not cap.exists()


def test_worktree_rm_ignores_ignored_only_change(tmp_path):
    repo = _git_repo(tmp_path)
    (repo / ".gitignore").write_text("ignored.txt\n")
    subprocess.run(["git", "-C", str(repo), "add", ".gitignore"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", "ignore"],
                   check=True, capture_output=True, text=True)
    (repo / "ignored.txt").write_text("ignored\n")
    result, cap = _rm(repo, tmp_path=tmp_path)
    assert result.returncode == 0
    assert cap.read_text() == f"orca worktree rm --worktree repo::{repo} --json\n"


def test_worktree_rm_refuses_unmerged_commit(tmp_path):
    repo = _git_repo(tmp_path)
    (repo / "tracked.txt").write_text("committed\n")
    subprocess.run(["git", "-C", str(repo), "add", "tracked.txt"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", "unmerged"],
                   check=True, capture_output=True, text=True)
    result, cap = _rm(repo, base="HEAD~1", tmp_path=tmp_path)
    assert result.returncode != 0
    assert "worktree_has_unmerged_commits" in result.stderr
    assert not cap.exists()


def test_worktree_rm_allows_commits_reachable_from_base(tmp_path):
    repo = _git_repo(tmp_path)
    result, cap = _rm(repo, base="HEAD", tmp_path=tmp_path)
    assert result.returncode == 0
    assert cap.read_text() == f"orca worktree rm --worktree repo::{repo} --json\n"


def test_worktree_rm_skips_unmerged_check_without_default_base(tmp_path):
    repo = _git_repo(tmp_path, branch="feature")
    result, cap = _rm(repo, tmp_path=tmp_path)
    assert result.returncode == 0
    assert cap.read_text() == f"orca worktree rm --worktree repo::{repo} --json\n"


def test_worktree_rm_force_short_circuits_dirty_repo(tmp_path):
    repo = _git_repo(tmp_path)
    (repo / "tracked.txt").write_text("modified\n")
    result, cap = _rm(repo, force=True, tmp_path=tmp_path)
    assert result.returncode == 0
    assert cap.read_text() == f"orca worktree rm --worktree repo::{repo} --force --json\n"
    assert "[H-MAD] worktree-rm forced selector=repo::" in result.stderr


def test_worktree_rm_unresolvable_selector_is_removed(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    result = run(["worktree-rm", "wt-7"], substrate="orca", env={"_BINDIR": b}, capture=cap)
    assert result.returncode == 0
    assert "orca worktree rm --worktree wt-7 --json\n" in cap.read_text()


def test_worktree_ps_and_rm_refuse_cmux(tmp_path):
    b = _bindir(tmp_path, ["cmux", "orca"])
    for args in (["worktree-ps"], ["worktree-rm", "wt-7"]):
        cap = tmp_path / f"{'-'.join(args)}.txt"
        r = run(args, substrate="cmux", env={"_BINDIR": b}, capture=cap)
        assert r.returncode == 2
        assert "requires orchestration mode (substrate=orca)" in r.stderr
        assert not cap.exists()


def test_worktree_comment_orca_sets_comment(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    r = run(["worktree-comment", "id:w1", "hi"], substrate="orca",
            env={"_BINDIR": b}, capture=cap)
    assert r.returncode == 0
    assert cap.read_text() == "orca worktree set --worktree id:w1 --comment hi --json\n"


def test_worktree_comment_default_selector_active(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    r = run(["worktree-comment", "hi"], substrate="orca",
            env={"_BINDIR": b}, capture=cap)
    assert r.returncode == 0
    assert cap.read_text() == "orca worktree set --worktree active --comment hi --json\n"


def test_worktree_comment_missing_text_exit2(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    r = run(["worktree-comment"], substrate="orca", env={"_BINDIR": b}, capture=cap)
    assert r.returncode == 2
    assert "missing required argument: text" in r.stderr
    assert not cap.exists()


def test_worktree_comment_requires_orca(tmp_path):
    b = _bindir(tmp_path, ["cmux", "orca"])
    cap = tmp_path / "cap.txt"
    r = run(["worktree-comment", "id:w1", "hi"], substrate="cmux",
            env={"_BINDIR": b}, capture=cap)
    assert r.returncode == 2
    assert "requires orchestration mode (substrate=orca)" in r.stderr
    assert not cap.exists()


def test_worktree_comment_propagates_ok_false(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    r = run(["worktree-comment", "id:w1", "hi"], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_FAIL": "1"})
    assert r.returncode != 0
    assert "boom" in r.stderr
    assert "OK" not in r.stdout


def test_worktree_current_orca_reads(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    r = run(["worktree-current"], substrate="orca", env={"_BINDIR": b}, capture=cap)
    assert r.returncode == 0
    assert cap.read_text() == "orca worktree current --json\n"
    assert r.stdout == '{"worktree":{"branch":"refs/heads/main","path":"/x","comment":"c"}}\n'
    assert " set " not in cap.read_text()
    assert " create " not in cap.read_text()
    assert " rm " not in cap.read_text()


def test_worktree_current_requires_orca(tmp_path):
    b = _bindir(tmp_path, ["cmux", "orca"])
    cap = tmp_path / "cap.txt"
    r = run(["worktree-current"], substrate="cmux", env={"_BINDIR": b}, capture=cap)
    assert r.returncode == 2
    assert "requires orchestration mode (substrate=orca)" in r.stderr
    assert not cap.exists()


def test_worktree_current_propagates_ok_false(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    r = run(["worktree-current"], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_FAIL": "1"})
    assert r.returncode != 0
    assert "boom" in r.stderr


def test_skill_documents_fanout_conjunction():
    text = (SKILL / "SKILL.md").read_text()
    fanout = text[text.index("## Phase 5 parallel fanout"):]
    for required in ["substrate=orca", "orchestration: on", "≥2 independent",
                     "HMAD_ORCA_MAX_WORKTREES", "default 4", "worktree-create",
                     "worktree-ps", "worktree-rm", "serial fallback"]:
        assert required in fanout


def test_file_diff_argv(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    r = run(["file-diff", "foo.py"], substrate="orca", env={"_BINDIR": b}, capture=cap)
    assert r.returncode == 0
    assert cap.read_text() == "orca file diff foo.py --json\n"


def test_file_diff_flags(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    r = run(["file-diff", "foo.py", "--staged", "--worktree", "wt-3"], substrate="orca",
            env={"_BINDIR": b}, capture=cap)
    assert r.returncode == 0
    assert cap.read_text() == "orca file diff foo.py --staged --worktree wt-3 --json\n"


def test_file_diff_passthrough(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    r = run(["file-diff", "foo.py"], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": '{"result":{"d":1}}'})
    assert r.returncode == 0
    assert r.stdout == '{"d":1}\n'


def test_file_diff_refuses_cmux(tmp_path):
    b = _bindir(tmp_path, ["cmux", "orca"])
    cap = tmp_path / "cap.txt"
    r = run(["file-diff", "foo.py"], substrate="cmux", env={"_BINDIR": b}, capture=cap)
    assert r.returncode == 2
    assert "requires orchestration mode (substrate=orca)" in r.stderr
    assert not cap.exists()


def test_file_diff_requires_path(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    r = run(["file-diff"], substrate="orca", env={"_BINDIR": b}, capture=cap)
    assert r.returncode == 2
    assert "missing required argument: path" in r.stderr
    assert not cap.exists()


def test_file_open_changed_argv(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    r = run(["file-open-changed"], substrate="orca", env={"_BINDIR": b}, capture=cap)
    assert r.returncode == 0
    assert cap.read_text() == "orca file open-changed --json\n"

    r = run(["file-open-changed", "--mode", "diff", "--worktree", "wt-3"], substrate="orca",
            env={"_BINDIR": b}, capture=cap)
    assert r.returncode == 0
    assert cap.read_text().endswith("orca file open-changed --mode diff --worktree wt-3 --json\n")


def test_file_open_changed_passthrough(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    r = run(["file-open-changed"], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": '{"result":{"opened":2}}'})
    assert r.returncode == 0
    assert r.stdout == '{"opened":2}\n'


def test_file_open_changed_refuses_cmux(tmp_path):
    b = _bindir(tmp_path, ["cmux", "orca"])
    cap = tmp_path / "cap.txt"
    r = run(["file-open-changed"], substrate="cmux", env={"_BINDIR": b}, capture=cap)
    assert r.returncode == 2
    assert "requires orchestration mode (substrate=orca)" in r.stderr
    assert not cap.exists()


def test_skill_documents_diff_surface_gate():
    text = (SKILL / "SKILL.md").read_text()
    for required in ["file-open-changed", "file-diff", "best-effort", "non-blocking"]:
        assert required in text


def test_automation_create_argv(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("RUN E2E")
    r = run(["automation-create", "--name", "nightly", "--trigger", "cron",
             "--prompt-file", str(prompt), "--provider", "agent"], substrate="orca",
            env={"_BINDIR": b}, capture=cap)
    assert r.returncode == 0
    assert cap.read_text() == (
        "orca automations create --name nightly --trigger cron --prompt RUN E2E "
        "--provider agent --json\n"
    )


def test_automation_create_targeting_and_precheck(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("RUN E2E")
    r = run(["automation-create", "--name", "nightly", "--trigger", "cron",
             "--prompt-file", str(prompt), "--precheck", "hpw doctor", "--repo", "r1"],
            substrate="orca", env={"_BINDIR": b}, capture=cap)
    assert r.returncode == 0
    assert cap.read_text() == (
        "orca automations create --name nightly --trigger cron --prompt RUN E2E "
        "--precheck hpw doctor --repo r1 --json\n"
    )


def test_automation_create_parses_id(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("RUN E2E")
    r = run(["automation-create", "--name", "nightly", "--trigger", "cron",
             "--prompt-file", str(prompt)], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": '{"id":"envelope-xyz","result":{"automation":{"id":"auto_9"}}}'})
    assert r.returncode == 0
    assert r.stdout == "auto_9\n"


def test_automation_create_missing_prompt_file(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    r = run(["automation-create", "--name", "nightly", "--trigger", "cron",
             "--prompt-file", str(tmp_path / "missing.txt")], substrate="orca",
            env={"_BINDIR": b}, capture=cap)
    assert r.returncode == 2
    assert "prompt file not found" in r.stderr
    assert not cap.exists()


def test_e2e_smoke_prompt_artifact_covers_surface():
    # The dispatch-surface live-e2e flow (orchestration-mode.md §"Scheduling an
    # h-mad dispatch-surface live-e2e") points a scheduled automation at a
    # COMMITTED prompt artifact so the job and the repo cannot drift. Guard the
    # artifact: it must exist and exercise the core surface, or the scheduled
    # smoke silently stops testing anything.
    prompt = SKILL / "references" / "e2e-smoke.prompt.md"
    assert prompt.is_file(), "e2e-smoke.prompt.md missing — the scheduled flow has no prompt"
    text = prompt.read_text()
    for token in ("hmad-dispatch env", "resolve agy", "resolve codex",
                  "report-wait", "pytest", "E2E: PASS"):
        assert token in text, f"e2e smoke prompt no longer covers {token!r}"


def test_e2e_smoke_flow_wires_automation_create(tmp_path):
    # End-to-end wiring of the flow against the stub (no live job): staging the
    # real committed prompt through automation-create must produce the documented
    # argv — daily preset trigger (no --schedule), provider claude, --repo skills.
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    prompt = SKILL / "references" / "e2e-smoke.prompt.md"
    r = run(["automation-create", "--name", "hmad-dispatch-e2e", "--trigger", "daily",
             "--prompt-file", str(prompt), "--provider", "claude",
             "--precheck", "hmad-dispatch env", "--repo", "skills"],
            substrate="orca", env={"_BINDIR": b}, capture=cap)
    assert r.returncode == 0
    cmd = cap.read_text()
    assert "automations create --name hmad-dispatch-e2e --trigger daily" in cmd
    assert " --schedule " not in cmd          # preset trigger takes no --schedule
    assert "--provider claude" in cmd
    assert "--precheck hmad-dispatch env" in cmd
    assert "--repo skills" in cmd
    assert cmd.rstrip().endswith("--json")
    assert "E2E: PASS" in cmd                 # the real prompt body was inlined


def test_automation_create_requires_name_and_trigger(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("RUN E2E")
    for args in (
        ["automation-create", "--trigger", "cron", "--prompt-file", str(prompt)],
        ["automation-create", "--name", "nightly", "--prompt-file", str(prompt)],
    ):
        cap = tmp_path / f"{'-'.join(args[1:3])}.txt"
        r = run(args, substrate="orca", env={"_BINDIR": b}, capture=cap)
        assert r.returncode == 2
        assert "missing required argument" in r.stderr
        assert not cap.exists()


def test_automation_create_refuses_cmux(tmp_path):
    b = _bindir(tmp_path, ["cmux", "orca"])
    cap = tmp_path / "cap.txt"
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("RUN E2E")
    r = run(["automation-create", "--name", "nightly", "--trigger", "cron",
             "--prompt-file", str(prompt)], substrate="cmux", env={"_BINDIR": b}, capture=cap)
    assert r.returncode == 2
    assert "requires orchestration mode (substrate=orca)" in r.stderr
    assert not cap.exists()


def test_automation_run_argv_and_requires_id(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    r = run(["automation-run", "auto_9"], substrate="orca", env={"_BINDIR": b}, capture=cap)
    assert r.returncode == 0
    assert cap.read_text() == "orca automations run auto_9 --json\n"

    missing_cap = tmp_path / "missing-cap.txt"
    missing = run(["automation-run"], substrate="orca", env={"_BINDIR": b}, capture=missing_cap)
    assert missing.returncode == 2
    assert "missing required argument: id" in missing.stderr
    assert not missing_cap.exists()


def test_automation_list_argv_and_passthrough(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    r = run(["automation-list"], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": '{"result":{"x":1}}'}, capture=cap)
    assert r.returncode == 0
    assert cap.read_text() == "orca automations list --json\n"
    assert r.stdout == '{"x":1}\n'


def test_automation_remove_argv_and_requires_id(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    r = run(["automation-remove", "auto_9"], substrate="orca", env={"_BINDIR": b}, capture=cap)
    assert r.returncode == 0
    assert cap.read_text() == "orca automations remove auto_9 --json\n"

    missing_cap = tmp_path / "missing-cap.txt"
    missing = run(["automation-remove"], substrate="orca", env={"_BINDIR": b}, capture=missing_cap)
    assert missing.returncode == 2
    assert "missing required argument: id" in missing.stderr
    assert not missing_cap.exists()


def test_automation_verbs_refuse_cmux(tmp_path):
    b = _bindir(tmp_path, ["cmux", "orca"])
    for args in (["automation-run", "auto_9"], ["automation-list"], ["automation-remove", "auto_9"]):
        cap = tmp_path / f"{'-'.join(args)}.txt"
        r = run(args, substrate="cmux", env={"_BINDIR": b}, capture=cap)
        assert r.returncode == 2
        assert "requires orchestration mode (substrate=orca)" in r.stderr
        assert not cap.exists()


def test_skill_documents_automation_usage():
    text = (SKILL / "SKILL.md").read_text()
    for required in ["automation-create", "automation-run", "automation-list", "automation-remove", "hpw doctor"]:
        assert required in text


# --- send: inline vs file-indirection --------------------------------------
#
# `send` used to inline the prompt unconditionally (`$(cat "$2")`), which
# contradicted the file-indirection rule for large prompts at exactly the
# sizes that occur in practice: audit prompts run 32-61 KB. Above
# HMAD_SEND_INLINE_MAX (default 8192 bytes) the wrapper now sends a short
# instruction naming the staged file instead of its contents.

_INLINE_MAX_DEFAULT = 8192


def _prompt_file(tmp_path, size, name="prompt.txt"):
    pf = tmp_path / name
    pf.write_text("X" * size)
    return pf


def test_send_inlines_a_small_prompt(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    pf = tmp_path / "small.txt"; pf.write_text("SMALL-PROMPT")
    r = _enforced_send(["send", "codex", str(pf)], substrate="orca",
                       env={"_BINDIR": b, "HMAD_ORCA_CODEX_TERMINAL": "t-1"}, capture=cap)
    assert r.returncode == 0
    text = cap.read_text()
    assert "SMALL-PROMPT" in text
    assert str(pf) not in text, "small prompts must still be inlined"


def test_send_switches_to_indirection_for_a_large_prompt(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    pf = _prompt_file(tmp_path, _INLINE_MAX_DEFAULT + 1, "big.txt")
    r = _enforced_send(["send", "codex", str(pf)], substrate="orca",
                       env={"_BINDIR": b, "HMAD_ORCA_CODEX_TERMINAL": "t-1"}, capture=cap)
    assert r.returncode == 0
    text = cap.read_text()
    assert str(pf) in text, "must name the staged file"
    assert "XXXXXXXXXXXX" not in text, "must not inline the contents"


def test_indirection_canonicalises_the_path(tmp_path):
    """The agent resolves the path from its own cwd, so send a canonical one."""
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    sub = tmp_path / "sub"; sub.mkdir()
    pf = _prompt_file(tmp_path, _INLINE_MAX_DEFAULT + 1, "big.txt")
    noncanonical = sub / ".." / "big.txt"   # valid, absolute, not canonical

    r = _enforced_send(["send", "codex", str(noncanonical)], substrate="orca",
                       env={"_BINDIR": b, "HMAD_ORCA_CODEX_TERMINAL": "t-1"}, capture=cap)
    assert r.returncode == 0
    text = cap.read_text()
    assert str(pf.resolve()) in text
    assert "/.." not in text


def test_threshold_boundary_is_inclusive(tmp_path):
    """Exactly at the limit still inlines; one byte over does not."""
    b = _bindir(tmp_path, ["orca"])
    at = tmp_path / "cap_at.txt"
    pf_at = _prompt_file(tmp_path, _INLINE_MAX_DEFAULT, "at.txt")
    _enforced_send(["send", "codex", str(pf_at)], substrate="orca",
                   env={"_BINDIR": b, "HMAD_ORCA_CODEX_TERMINAL": "t-1"}, capture=at)
    assert "XXXXXXXXXXXX" in at.read_text()

    over = tmp_path / "cap_over.txt"
    pf_over = _prompt_file(tmp_path, _INLINE_MAX_DEFAULT + 1, "over.txt")
    _enforced_send(["send", "codex", str(pf_over)], substrate="orca",
                   env={"_BINDIR": b, "HMAD_ORCA_CODEX_TERMINAL": "t-1"}, capture=over)
    assert "XXXXXXXXXXXX" not in over.read_text()


def test_threshold_is_tunable(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    pf = _prompt_file(tmp_path, 100, "medium.txt")
    r = _enforced_send(["send", "codex", str(pf)], substrate="orca",
                       env={"_BINDIR": b, "HMAD_ORCA_CODEX_TERMINAL": "t-1",
                            "HMAD_SEND_INLINE_MAX": "50"}, capture=cap)
    assert r.returncode == 0
    text = cap.read_text()
    assert str(pf) in text
    assert "XXXXXXXXXXXX" not in text


def test_send_cmux_indirection_too(tmp_path):
    """The threshold is substrate-independent."""
    b = _bindir(tmp_path, ["cmux"])
    cap = tmp_path / "cap.txt"
    pf = _prompt_file(tmp_path, _INLINE_MAX_DEFAULT + 1, "big.txt")
    r = _enforced_send(["send", "codex", str(pf)], substrate="cmux",
                       env={"_BINDIR": b, "HMAD_CMUX_CODEX_SURFACE": "surface:5"}, capture=cap)
    assert r.returncode == 0
    text = cap.read_text()
    assert str(pf) in text
    assert "XXXXXXXXXXXX" not in text


def test_send_missing_file_fails_loudly(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    r = run(["send", "codex", str(tmp_path / "nope.txt")], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_CODEX_TERMINAL": "t-1"})
    assert r.returncode != 0


# --- send: resolved-agent conflict guard ------------------------------------


def test_send_refuses_when_both_agents_resolve_to_one_handle(tmp_path):
    """AC-7.1/7.2: never deliver into a pane claimed by both agents."""
    b = _bindir(tmp_path, ["orca"])
    prompt = tmp_path / "prompt.txt"; prompt.write_text("do the thing")
    shared = _preflight_listing("term_shared")

    for agent in ("codex", "agy"):
        cap = tmp_path / f"{agent}.txt"
        r = run(["send", agent, str(prompt)], substrate="orca",
                env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": shared,
                     "HMAD_ORCA_CODEX_TERMINAL": "term_shared",
                     "HMAD_ORCA_AGY_TERMINAL": "term_shared"}, capture=cap)

        assert r.returncode != 0
        assert "preflight_agent_conflict" in r.stderr
        assert not cap.exists() or "terminal send" not in cap.read_text(), \
            "conflict must prevent delivery"


def test_send_allows_distinct_agent_resolutions(tmp_path):
    """AC-7.3: the conflict guard distinguishes two separate live panes."""
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    prompt = tmp_path / "prompt.txt"; prompt.write_text("do the thing")
    live = _preflight_listing("term_codex", "term_agy")

    r = _enforced_send(["send", "codex", str(prompt)], substrate="orca",
                       env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": live,
                            "HMAD_ORCA_CODEX_TERMINAL": "term_codex",
                            "HMAD_ORCA_AGY_TERMINAL": "term_agy"}, capture=cap)

    assert r.returncode == 0
    assert "preflight_agent_conflict" not in r.stderr
    assert "terminal send --terminal term_codex" in cap.read_text()


def test_send_unresolved_agents_is_not_refused_as_a_conflict(tmp_path):
    """AC-7.4: two unresolved agents do not establish a shared pane."""
    b = _bindir(tmp_path, ["orca"])
    prompt = tmp_path / "prompt.txt"; prompt.write_text("do the thing")

    r = run(["send", "codex", str(prompt)], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": _preflight_listing()})

    assert r.returncode != 0
    assert "preflight_agent_conflict" not in r.stderr
    assert "orca terminal for 'codex' resolved" in r.stderr


# --- wait: idle must be confirmed, not taken on trust ------------------------
#
# Orca's native `--for tui-idle` was observed returning satisfied:true twice
# while agy was still generating, so downstream read a partial pane. cmux never
# had a native idle and has always confirmed with two consecutive identical
# snapshots; the orca arm now does the same, using the native call as a fast
# first gate rather than as proof.
#
# LIMITATION: these tests pin the wrapper's control flow against stubs. The
# underlying defect only manifests against a live Orca runtime with a genuinely
# mid-response agent, which no stub can reproduce — a stub that returns two
# identical reads is idle by construction. Live confirmation is outstanding.

_FAST = {"HMAD_WAIT_POLL_INTERVAL": "0"}


def test_wait_orca_gates_on_native_idle_then_confirms_by_reading(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    r = run(["wait", "agy"], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_AGY_TERMINAL": "term_wait",
                 "HMAD_STUB_ORCA_STDOUT": "steady screen", **_FAST},
            capture=cap)
    assert r.returncode == 0
    text = cap.read_text()
    assert "orca terminal wait --terminal term_wait --for tui-idle" in text
    assert "orca terminal read --terminal term_wait" in text, (
        "native idle alone is not proof; it must be confirmed by reading"
    )


def test_wait_orca_still_converts_timeout_to_milliseconds(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    r = run(["wait", "agy", "--timeout", "30"], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_AGY_TERMINAL": "term_wait",
                 "HMAD_STUB_ORCA_STDOUT": "steady screen", **_FAST},
            capture=cap)
    assert r.returncode == 0
    assert "--timeout-ms 30000" in cap.read_text()


def test_wait_orca_fails_when_native_gate_fails(tmp_path):
    """A native timeout is authoritative for 'not idle' — do not poll past it."""
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    r = run(["wait", "agy"], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_AGY_TERMINAL": "term_wait",
                 "HMAD_STUB_ORCA_EXIT": "1", **_FAST}, capture=cap)
    assert r.returncode != 0


def test_wait_cmux_still_polls_for_stability(tmp_path):
    b = _bindir(tmp_path, ["cmux"])
    cap = tmp_path / "cap.txt"
    r = run(["wait", "agy"], substrate="cmux",
            env={"_BINDIR": b, "HMAD_CMUX_AGY_SURFACE": "surface:2",
                 "HMAD_STUB_CMUX_STDOUT": "steady screen", **_FAST}, capture=cap)
    assert r.returncode == 0
    text = cap.read_text()
    assert "cmux read-screen --surface surface:2" in text
    assert text.count("read-screen") >= 2, "stability needs two reads, not one"


def test_wait_requires_two_reads_on_both_substrates(tmp_path):
    """One read can catch a pane mid-write; two identical ones cannot."""
    for sub, pin, binname, needle in [
        ("orca", {"HMAD_ORCA_AGY_TERMINAL": "t"}, "orca", "terminal read"),
        ("cmux", {"HMAD_CMUX_AGY_SURFACE": "s"}, "cmux", "read-screen"),
    ]:
        d = tmp_path / sub; d.mkdir()
        b = _bindir(d, [binname])
        cap = d / "cap.txt"
        stdout_var = f"HMAD_STUB_{binname.upper()}_STDOUT"
        r = run(["wait", "agy"], substrate=sub,
                env={"_BINDIR": b, stdout_var: "steady", **pin, **_FAST},
                capture=cap)
        assert r.returncode == 0, sub
        assert cap.read_text().count(needle) >= 2, sub


def test_wait_poll_interval_is_tunable(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    r = run(["wait", "agy", "--timeout", "1"], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_AGY_TERMINAL": "t",
                 "HMAD_STUB_ORCA_STDOUT": "steady",
                 "HMAD_WAIT_POLL_INTERVAL": "0"}, capture=cap)
    assert r.returncode == 0


def test_empty_reads_are_not_treated_as_idle(tmp_path):
    """A blank pane is absence of evidence, not evidence of idleness.

    Two empty reads are trivially 'identical'; accepting them would make a
    dead or still-starting pane look settled.
    """
    b = _bindir(tmp_path, ["orca"])
    r = run(["wait", "agy", "--timeout", "2"], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_AGY_TERMINAL": "t",
                 "HMAD_WAIT_POLL_INTERVAL": "0"})
    assert r.returncode != 0, "empty snapshots must time out, not report idle"


# --- Orca tab-title inheritance (stablyai/orca#9870) --------------------------
# Orca's `.title` is the pane program's OSC title when it emits one, and the
# enclosing TAB's title otherwise. A tab title is shared by every leaf in the
# tab, so it names a tab, not a pane. Codex emits no OSC title; agy does.


def test_codex_never_resolves_from_an_inherited_title(tmp_path):
    """The live 2026-07-22 mis-dispatch: an *agy* pane sat in a tab titled
    "Codex - skills repo" and matched "^codex". Both agents emit a well-formed
    sentinel report, so handing Codex's work to agy is silent -- the wrong model
    answers and the gate scores it. Codex has no title-based identity at all."""
    b = _bindir(tmp_path, ["orca"])
    listing = _orca_terms_full(
        {"handle": "term_agy_in_codex_tab", "title": "Codex - skills repo",
         "preview": "the generated report has been written to:",
         "worktreePath": "/repo/A", "tabId": "tab-1", "leafId": "l1"},
    )
    r = run(["env"], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": listing})
    assert "codex -> UNRESOLVED" in r.stdout
    assert "term_agy_in_codex_tab" not in r.stdout


def test_agy_title_shared_across_leaves_of_one_tab_is_rejected(tmp_path):
    """A title on two leaves of the SAME tab is provably the tab's, not either
    pane's, so it cannot be identity -- even for an agent that does emit OSC."""
    b = _bindir(tmp_path, ["orca"])
    shared = _orca_terms_full(
        {"handle": "term_x", "title": "agy - worker", "preview": "",
         "worktreePath": "/repo/A", "tabId": "tab-1", "leafId": "l1"},
        {"handle": "term_y", "title": "agy - worker", "preview": "",
         "worktreePath": "/repo/A", "tabId": "tab-1", "leafId": "l2"},
    )
    r = run(["env"], substrate="orca", env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": shared})
    assert "agy -> UNRESOLVED" in r.stdout

    # Same title, but one leaf per tab: nothing proves inheritance, and a real
    # OSC title must still resolve. Guards against over-rejecting.
    distinct = _orca_terms_full(
        {"handle": "term_x", "title": "agy - worker", "preview": "",
         "worktreePath": "/repo/A", "tabId": "tab-1", "leafId": "l1"},
    )
    r2 = run(["env"], substrate="orca", env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": distinct})
    assert "agy -> term_x" in r2.stdout


def test_agent_signatures_reject_words_a_pane_merely_rendered(tmp_path):
    """Preview signatures must be program output. The bare tokens "codex"/"agy"
    are not: a coordinator discussing dispatch prints both, and with Pass 1 no
    longer covering Codex, a bare-token signature made the coordinator resolve
    as Codex and dispatch to itself."""
    b = _bindir(tmp_path, ["orca"])
    listing = _orca_terms_full(
        {"handle": "term_coord", "title": "Claude Code",
         "preview": "dispatching to codex and agy panes; codex handles TDD",
         "worktreePath": "/repo/A", "tabId": "tab-1", "leafId": "l1"},
    )
    r = run(["env"], substrate="orca", env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": listing})
    assert "codex -> UNRESOLVED" in r.stdout
    assert "agy -> UNRESOLVED" in r.stdout
    assert "term_coord" not in r.stdout


# --- verify: pin liveness without making resolution depend on the listing -----


def test_verify_reports_a_stale_pin_that_resolve_accepts(tmp_path):
    """`resolve` echoes a pinned handle it never checked, so a dead pin from a
    crashed run prints happily with exit 0. `verify` is the opt-in check."""
    b = _bindir(tmp_path, ["orca"])
    live = _orca_terms_full(
        {"handle": "term_live", "title": "agy", "preview": "",
         "worktreePath": "/repo/A", "tabId": "tab-1", "leafId": "l1"},
    )
    env = {"_BINDIR": b, "HMAD_ORCA_AGY_TERMINAL": "term_dead",
           "HMAD_STUB_ORCA_STDOUT": live}

    r = run(["resolve", "agy"], substrate="orca", env=env)
    assert r.returncode == 0 and r.stdout.strip() == "term_dead"

    v = run(["verify", "agy"], substrate="orca", env=env)
    assert v.returncode == 1
    assert "stale_pin" in v.stderr
    assert "term_dead" in v.stderr


def test_verify_passes_for_a_live_pin(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    live = _orca_terms_full(
        {"handle": "term_live", "title": "agy", "preview": "",
         "worktreePath": "/repo/A", "tabId": "tab-1", "leafId": "l1"},
    )
    v = run(["verify", "agy"], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_AGY_TERMINAL": "term_live",
                 "HMAD_STUB_ORCA_STDOUT": live})
    assert v.returncode == 0
    assert v.stdout.strip() == "term_live"


def test_verify_rejects_unknown_agent(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    v = run(["verify", "bogus"], substrate="orca", env={"_BINDIR": b})
    assert v.returncode == 2
    assert "unknown agent" in v.stderr


def test_resolve_stays_independent_of_the_terminal_listing(tmp_path):
    """Regression guard on the fix itself: a pin must keep resolving when the
    listing is empty or `orca` is failing outright. That independence is the
    reason pins survive the auto-detect decay they exist to replace -- moving
    the liveness check into `resolve` would put the fallback back under the
    failure it is meant to survive."""
    b = _bindir(tmp_path, ["orca"])
    r = run(["resolve", "agy"], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_AGY_TERMINAL": "term_pinned",
                 "HMAD_STUB_ORCA_STDOUT": _orca_terms()})
    assert r.returncode == 0
    assert r.stdout.strip() == "term_pinned"


# --- a pin file records intent, not state -------------------------------------
# Observed 2026-07-22 (clinical-abbreviation-hygiene Phase 5): every Orca handle
# rotated, `env` still printed the dead pins, and a RED dispatch reported
# "Sent 7293 bytes" into a stale handle and vanished -- no error, no report file,
# no tests written. "Sent N bytes" is not delivery, and a resolvable pin is not a
# live pane.


def test_send_refuses_a_handle_the_listing_proves_is_gone(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    prompt = tmp_path / "p.txt"; prompt.write_text("do the thing")
    live = _orca_terms_full(
        {"handle": "term_live", "title": "agy", "preview": "",
         "worktreePath": "/repo/A", "tabId": "tab-1", "leafId": "l1"},
    )
    r = run(["send", "agy", str(prompt)], substrate="orca",
        env={"_BINDIR": b, "HMAD_ORCA_AGY_TERMINAL": "term_dead",
                 "HMAD_STUB_ORCA_STDOUT": live,
                 "HMAD_SKIP_PREFLIGHT": "1"}, capture=cap)
    assert r.returncode == 1
    assert "terminal_handle_stale" in r.stderr
    assert "nothing was sent" in r.stderr
    assert "terminal send" not in cap.read_text(), "must not reach the send call"


def test_send_still_works_when_the_listing_cannot_be_read(tmp_path):
    """Only positive evidence blocks a send. A pin exists so dispatch survives
    when the listing is unavailable; treating 'could not check' as 'dead' would
    put the pin back under the failure it exists to survive."""
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    prompt = tmp_path / "p.txt"; prompt.write_text("do the thing")
    r = _enforced_send(["send", "agy", str(prompt)], substrate="orca",
                       env={"_BINDIR": b, "HMAD_ORCA_AGY_TERMINAL": "term_x",
                            "HMAD_STUB_ORCA_STDOUT": "not json at all"}, capture=cap)
    assert r.returncode == 0
    assert "terminal send" in cap.read_text()


def test_env_marks_a_stale_pin_instead_of_printing_it_as_addressable(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    live = _orca_terms_full(
        {"handle": "term_live", "title": "agy", "preview": "",
         "worktreePath": "/repo/A", "tabId": "tab-1", "leafId": "l1"},
    )
    r = run(["env"], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_CODEX_TERMINAL": "term_dead",
                 "HMAD_STUB_ORCA_STDOUT": live})
    assert "STALE" in r.stdout
    assert "stale pins: codex" in r.stdout


def test_pin_refuses_a_handle_absent_from_the_listing(tmp_path):
    """Pinning is when identity is supposedly known -- the cheapest place to
    catch a wrong handle, rather than discovering it as a vanished dispatch."""
    b = _bindir(tmp_path, ["orca"])
    pins = tmp_path / "pins.env"
    live = _orca_terms_full(
        {"handle": "term_live", "title": "agy", "preview": "",
         "worktreePath": "/repo/A", "tabId": "tab-1", "leafId": "l1"},
    )
    env = {"_BINDIR": b, "HMAD_ORCA_PIN_FILE": str(pins), "HMAD_STUB_ORCA_STDOUT": live}

    r = run(["pin", "codex", "term_dead"], substrate="orca", env=env)
    assert r.returncode == 1
    assert "refusing to pin" in r.stderr
    assert not pins.exists()

    # --force covers pinning a pane that does not exist yet.
    f = run(["pin", "--force", "codex", "term_dead"], substrate="orca", env=env)
    assert f.returncode == 0
    assert "codex=term_dead" in pins.read_text()

    # A live handle pins normally.
    ok = run(["pin", "agy", "term_live"], substrate="orca", env=env)
    assert ok.returncode == 0
    assert "agy=term_live" in pins.read_text()


def test_pin_agents_ignores_a_dead_env_pin_rather_than_freezing_it(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    pins = tmp_path / "pins.env"
    live = _orca_terms_full(
        {"handle": "term_live_agy", "title": "agy", "preview": "",
         "worktreePath": "/repo/A", "tabId": "tab-1", "leafId": "l1"},
    )
    r = run(["pin-agents"], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_PIN_FILE": str(pins),
                 "HMAD_ORCA_CODEX_TERMINAL": "term_dead",
                 "HMAD_STUB_ORCA_STDOUT": live})
    assert r.returncode != 0, "a dead pin must not read as a resolved agent"
    assert "not a live terminal" in r.stderr
    assert "term_dead" not in pins.read_text()
    assert "agy=term_live_agy" in pins.read_text(), "the live agent is still frozen"


# --- title inheritance, round 2: the single-leaf hole and prose model ids ------


def test_agy_does_not_take_a_pane_running_codex(tmp_path):
    """A SINGLE-leaf tab proves nothing about inheritance, so the shared-title
    check cannot fire -- a Codex pane in a one-leaf tab named "agy - worker"
    resolved as agy (verified before the fix). The rival's program banner is
    strong evidence of what actually runs there and outranks a weak title."""
    b = _bindir(tmp_path, ["orca"])
    listing = _orca_terms_full(
        {"handle": "term_actually_codex", "title": "agy - worker",
         "preview": "gpt-5.6-terra high · ~/repo", "worktreePath": "/repo/A",
         "tabId": "tab-1", "leafId": "l1"},
    )
    r = run(["env"], substrate="orca", env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": listing})
    assert "agy -> UNRESOLVED" in r.stdout
    assert "codex -> term_actually_codex" in r.stdout, "it IS the Codex pane"
    assert "CONFLICT" not in r.stdout


def test_codex_signature_ignores_a_model_id_in_prose(tmp_path):
    """`gpt-[0-9]` alone matched "comparing gpt-5 output with ours". Codex prints
    a product line or a model id paired with a reasoning effort; prose does not."""
    b = _bindir(tmp_path, ["orca"])
    prose = _orca_terms_full(
        {"handle": "term_some_agent", "title": "worker",
         "preview": "comparing gpt-5 output with ours", "worktreePath": "/repo/A",
         "tabId": "tab-1", "leafId": "l1"},
    )
    r = run(["env"], substrate="orca", env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": prose})
    assert "codex -> UNRESOLVED" in r.stdout

    # The forms Codex actually prints must still resolve.
    for banner in ("OpenAI Codex (v0.145.0)  model: gpt-5.6-terra",
                   "gpt-5.6-terra high · ~/orca/HemaSuite"):
        listing = _orca_terms_full(
            {"handle": "term_codex", "title": "worker", "preview": banner,
             "worktreePath": "/repo/A", "tabId": "tab-1", "leafId": "l1"},
        )
        rr = run(["env"], substrate="orca",
                 env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": listing})
        assert "codex -> term_codex" in rr.stdout, banner


def test_env_flags_two_agents_resolving_to_one_pane(tmp_path):
    """Two agents cannot be the same pane, so identical handles prove at least one
    resolution is wrong -- the exact shape tab-title inheritance produces."""
    b = _bindir(tmp_path, ["orca"])
    listing = _orca_terms_full(
        {"handle": "term_one", "title": "shared", "preview": "",
         "worktreePath": "/repo/A", "tabId": "tab-1", "leafId": "l1"},
    )
    r = run(["env"], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": listing,
                 "HMAD_ORCA_CODEX_TERMINAL": "term_one",
                 "HMAD_ORCA_AGY_TERMINAL": "term_one"})
    assert "CONFLICT" in r.stdout
    assert "term_one" in r.stdout


def test_autodetect_scopes_to_the_worktree_enclosing_cwd(tmp_path):
    """Without ORCA_PANE_KEY the matcher used to search EVERY worktree, so a pane
    in an unrelated checkout competed for the token. cwd is weaker evidence than
    the coordinator's own pane but far better than none."""
    b = _bindir(tmp_path, ["orca"])
    here = str(tmp_path)
    listing = _orca_terms_full(
        {"handle": "term_agy_here", "title": "agy", "preview": "",
         "worktreePath": here, "tabId": "tab-1", "leafId": "l1"},
        {"handle": "term_agy_elsewhere", "title": "agy", "preview": "",
         "worktreePath": "/some/other/checkout", "tabId": "tab-2", "leafId": "l2"},
    )
    r = run(["env"], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": listing}, cwd=str(tmp_path))
    assert "agy -> term_agy_here" in r.stdout
    assert "term_agy_elsewhere" not in r.stdout


def test_resolve_verify_flag_matches_the_verify_verb(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    live = _orca_terms_full(
        {"handle": "term_live", "title": "agy", "preview": "",
         "worktreePath": "/repo/A", "tabId": "tab-1", "leafId": "l1"},
    )
    dead = {"_BINDIR": b, "HMAD_ORCA_AGY_TERMINAL": "term_dead",
            "HMAD_STUB_ORCA_STDOUT": live}
    bad = run(["resolve", "agy", "--verify"], substrate="orca", env=dead)
    assert bad.returncode == 1 and "stale_pin" in bad.stderr
    # Default stays unverified.
    plain = run(["resolve", "agy"], substrate="orca", env=dead)
    assert plain.returncode == 0 and plain.stdout.strip() == "term_dead"

    ok = run(["resolve", "agy", "--verify"], substrate="orca",
             env={"_BINDIR": b, "HMAD_ORCA_AGY_TERMINAL": "term_live",
                  "HMAD_STUB_ORCA_STDOUT": live})
    assert ok.returncode == 0 and ok.stdout.strip() == "term_live"


# --- J7: default pin-file isolation must not leak session state ------------
#
# The production default is intentionally cwd-relative. Tests must not let the
# real repository session pin file affect isolated harness invocations.


def test_default_pin_file_is_ignored_without_explicit_env(tmp_path):
    """AC-6.1-mechanism: the repo-relative default pin file is not read by tests."""
    b = _bindir(tmp_path, ["orca"])
    repo_default = tmp_path / ".h-mad" / "orca-pins.env"
    repo_default.parent.mkdir()
    repo_default.write_text("agy=term_from_repo_default\n")
    r = run(["resolve", "agy"], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": _orca_terms()},
            cwd=str(tmp_path))
    assert r.returncode == 1
    assert r.stdout == ""
    # Assert WHY it failed. rc=1 + empty stdout is also what a crashing wrapper
    # produces (bad substrate detection, missing jq, a shell syntax error), so
    # without this the test would pass for a reason unrelated to the pin file.
    assert "pin HMAD_ORCA_AGY_TERMINAL" in r.stderr
    assert "term_from_repo_default" not in r.stdout + r.stderr


def test_explicit_pin_file_path_still_wins(tmp_path):
    """AC-6.3: an explicit HMAD_ORCA_PIN_FILE remains the pin destination."""
    b = _bindir(tmp_path, ["orca"])
    pins = tmp_path / "explicit-pins.env"
    r = run(["pin", "agy", "term_explicit"], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_PIN_FILE": str(pins)})
    assert r.returncode == 0
    assert pins.read_text() == "agy=term_explicit\n"


def test_no_pin_file_path_is_defined_outside_repo():
    """AC-6.4: _NO_PIN_FILE is module-scoped and outside the repository root."""
    no_pin_file = _NO_PIN_FILE
    repo_root = SKILL.parent
    assert no_pin_file.is_absolute()
    assert repo_root not in no_pin_file.parents


def test_no_mkdtemp_and_no_pin_file_leak_guard():
    """AC-mkdtemp-guard: no mkdtemp leak pattern exists and the guard path is absent."""
    source = Path(__file__).read_text()
    assert "tempfile." + "mkdtemp(" not in source
    assert not _NO_PIN_FILE.exists()


def test_production_pin_file_resolution_literal_unchanged():
    """AC-6.5: production still contains the cwd-relative pin-file fallback."""
    script = WRAPPER.read_text()
    assert "${HMAD_ORCA_PIN_FILE:-.h-mad/orca-pins.env}" in script


# --- preflight verdict: consumable form of the STALE/CONFLICT lines ---------
#
# The human-readable agent diagnostics remain useful, but PREFLIGHT: is the
# single machine-consumable verdict that follows them and the orchestration
# status line.


def _preflight_listing(*handles):
    return _orca_terms_full(*[
        {"handle": handle, "title": "worker", "preview": "",
         "worktreePath": "/repo/A", "tabId": "tab-1", "leafId": f"leaf-{handle}"}
        for handle in handles
    ])


def test_preflight_passes_when_pins_are_live_and_distinct(tmp_path):
    """AC-1.1: a healthy session emits PREFLIGHT: PASS."""
    b = _bindir(tmp_path, ["orca"])
    r = run(["env"], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": _preflight_listing("term_codex", "term_agy"),
                 "HMAD_ORCA_CODEX_TERMINAL": "term_codex",
                 "HMAD_ORCA_AGY_TERMINAL": "term_agy"})
    assert "PREFLIGHT: PASS" in r.stdout.splitlines()


def test_preflight_reports_one_stale_codex_pin(tmp_path):
    """AC-1.2a: a pinned handle absent from the listing reports stale=codex."""
    b = _bindir(tmp_path, ["orca"])
    r = run(["env"], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": _preflight_listing("term_agy"),
                 "HMAD_ORCA_CODEX_TERMINAL": "term_dead",
                 "HMAD_ORCA_AGY_TERMINAL": "term_agy"})
    line = next(line for line in r.stdout.splitlines() if line.startswith("PREFLIGHT:"))
    assert line.startswith("PREFLIGHT: FAIL")
    assert "stale=codex" in line


def test_preflight_reports_both_stale_pins(tmp_path):
    """AC-1.2b: both pinned handles absent from the listing report stale=codex,agy."""
    b = _bindir(tmp_path, ["orca"])
    r = run(["env"], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": _preflight_listing("term_other"),
                 "HMAD_ORCA_CODEX_TERMINAL": "term_dead_codex",
                 "HMAD_ORCA_AGY_TERMINAL": "term_dead_agy"})
    line = next(line for line in r.stdout.splitlines() if line.startswith("PREFLIGHT:"))
    assert "stale=codex,agy" in line


def test_preflight_reports_handle_conflict(tmp_path):
    """AC-1.3: two agents pinned to one live handle report its conflict."""
    b = _bindir(tmp_path, ["orca"])
    r = run(["env"], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": _preflight_listing("term_shared"),
                 "HMAD_ORCA_CODEX_TERMINAL": "term_shared",
                 "HMAD_ORCA_AGY_TERMINAL": "term_shared"})
    line = next(line for line in r.stdout.splitlines() if line.startswith("PREFLIGHT:"))
    assert "conflict=term_shared" in line


def test_preflight_combines_stale_and_conflict_in_one_verdict(tmp_path):
    """AC-1.4: stale and conflict findings share one PREFLIGHT: FAIL line."""
    b = _bindir(tmp_path, ["orca"])
    r = run(["env"], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": _preflight_listing(),
                 "HMAD_ORCA_CODEX_TERMINAL": "term_dead",
                 "HMAD_ORCA_AGY_TERMINAL": "term_dead"})
    lines = [line for line in r.stdout.splitlines() if line.startswith("PREFLIGHT:")]
    assert len(lines) == 1
    assert lines[0].startswith("PREFLIGHT: FAIL")
    assert "stale=" in lines[0]
    assert "conflict=" in lines[0]


def test_preflight_is_last_after_orchestration_status(tmp_path):
    """AC-1.5: PREFLIGHT: is the last non-empty stdout line after orchestration:."""
    b = _bindir(tmp_path, ["orca"])
    r = run(["env"], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": _preflight_listing("term_codex", "term_agy"),
                 "HMAD_ORCA_CODEX_TERMINAL": "term_codex",
                 "HMAD_ORCA_AGY_TERMINAL": "term_agy"})
    lines = [line for line in r.stdout.splitlines() if line.strip()]
    assert lines[-1].startswith("PREFLIGHT:")
    assert any(line.startswith("orchestration:") for line in lines[:-1])


def test_preflight_emits_exactly_one_verdict_line(tmp_path):
    """AC-1.6: each env invocation emits exactly one PREFLIGHT: line."""
    b = _bindir(tmp_path, ["orca"])
    r = run(["env"], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": _preflight_listing("term_codex", "term_agy"),
                 "HMAD_ORCA_CODEX_TERMINAL": "term_codex",
                 "HMAD_ORCA_AGY_TERMINAL": "term_agy"})
    assert sum(line.startswith("PREFLIGHT:") for line in r.stdout.splitlines()) == 1


def test_preflight_pass_keeps_zero_exit_status(tmp_path):
    """AC-2.1: PASS is a verdict and exits successfully."""
    b = _bindir(tmp_path, ["orca"])
    r = run(["env"], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": _preflight_listing("term_codex", "term_agy"),
                 "HMAD_ORCA_CODEX_TERMINAL": "term_codex",
                 "HMAD_ORCA_AGY_TERMINAL": "term_agy"})
    assert "PREFLIGHT: PASS" in r.stdout
    assert r.returncode == 0


def test_preflight_fail_keeps_zero_exit_status(tmp_path):
    """AC-2.2: FAIL is a verdict and still exits successfully."""
    b = _bindir(tmp_path, ["orca"])
    r = run(["env"], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": _preflight_listing("term_agy"),
                 "HMAD_ORCA_CODEX_TERMINAL": "term_dead",
                 "HMAD_ORCA_AGY_TERMINAL": "term_agy"})
    assert "PREFLIGHT: FAIL" in r.stdout
    assert r.returncode == 0


def test_no_substrate_has_no_preflight_verdict(tmp_path):
    """AC-2.3 guard: operational substrate failure remains non-zero and unadorned."""
    b = _bindir(tmp_path, [])
    r = run(["env"], env={"_BINDIR": b})
    assert r.returncode != 0
    assert "PREFLIGHT:" not in r.stdout


def test_preflight_source_documents_nonzero_and_posttool_failure_contract():
    """AC-2.4: the verdict source documents no non-zero exit and PostToolUseFailure."""
    lines = WRAPPER.read_text().splitlines()
    indices = [i for i, line in enumerate(lines) if 'echo "PREFLIGHT:' in line]
    assert len(indices) == 1
    window = lines[max(0, indices[0] - 15):indices[0]]
    text = "\n".join(window)
    assert "non-zero" in text
    assert "PostToolUseFailure" in text


def test_preflight_passes_when_both_agents_are_unresolved(tmp_path):
    """AC-3.1: unresolved agents are ordinary and do not fail preflight."""
    b = _bindir(tmp_path, ["orca"])
    r = run(["env"], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": _preflight_listing()})
    assert "codex -> UNRESOLVED" in r.stdout
    assert "agy -> UNRESOLVED" in r.stdout
    assert "PREFLIGHT: PASS" in r.stdout


def test_preflight_keeps_unresolved_agents_visible_in_env_output(tmp_path):
    """AC-3.2 guard: unresolved agent diagnostics continue to be printed."""
    b = _bindir(tmp_path, ["orca"])
    r = run(["env"], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": _preflight_listing()})
    assert "codex -> UNRESOLVED" in r.stdout
    assert "agy -> UNRESOLVED" in r.stdout


def test_preflight_fail_never_reports_unresolved_field(tmp_path):
    """AC-3.3 guard: a FAIL verdict has no unresolved= failure category."""
    b = _bindir(tmp_path, ["orca"])
    r = run(["env"], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": _preflight_listing("term_agy"),
                 "HMAD_ORCA_CODEX_TERMINAL": "term_dead",
                 "HMAD_ORCA_AGY_TERMINAL": "term_agy"})
    fail_lines = [ln for ln in r.stdout.splitlines() if ln.startswith("PREFLIGHT: FAIL")]
    # Assert the FAIL line EXISTS before asserting what it lacks. The loop-only
    # form passes vacuously when no verdict is emitted at all, so it would keep
    # passing if the implementation ever stopped emitting FAIL — the same shape
    # as the AC-6.1 weak assertion caught by the 5d coverage review.
    assert len(fail_lines) == 1, r.stdout
    assert "unresolved=" not in fail_lines[0]


def test_preflight_passes_when_terminal_listing_is_unreadable(tmp_path):
    """AC-edge: unknown liveness from an unreadable listing does not fail."""
    b = _bindir(tmp_path, ["orca"])
    r = run(["env"], substrate="orca",
            env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": "not json at all",
                 "HMAD_ORCA_CODEX_TERMINAL": "term_codex",
                 "HMAD_ORCA_AGY_TERMINAL": "term_agy"})
    assert "PREFLIGHT: PASS" in r.stdout


# --- preflight receipt lifecycle --------------------------------------------


def _receipt_env(b, pin_file, listing, *, receipt_file=None):
    """Environment for a deterministic, healthy preflight invocation."""
    env = {
        "_BINDIR": b,
        "HMAD_ORCA_PIN_FILE": str(pin_file),
        "HMAD_STUB_ORCA_STDOUT": listing,
        "HMAD_ORCA_CODEX_TERMINAL": "term_codex",
        "HMAD_ORCA_AGY_TERMINAL": "term_agy",
    }
    if receipt_file is not None:
        env["HMAD_PREFLIGHT_RECEIPT_FILE"] = str(receipt_file)
    return env


def _receipt_values(receipt_file):
    return dict(line.split("=", 1) for line in receipt_file.read_text().splitlines())


def _env_then_send(args, *, substrate, env, capture):
    """Run the enforced preflight and dispatch using one receipt path."""
    preflight = run(["env"], substrate=substrate, env=env)
    sent = run(args, substrate=substrate, env=env, capture=capture)
    return preflight, sent


def _enforced_send(args, *, substrate, env, capture):
    env = dict(env)
    env.setdefault("HMAD_PREFLIGHT_RECEIPT_FILE", str(Path(capture).with_suffix(".receipt")))
    preflight, sent = _env_then_send(args, substrate=substrate, env=env, capture=capture)
    assert "PREFLIGHT: PASS" in preflight.stdout, preflight.stdout
    return sent


def test_send_without_receipt_refuses_before_delivery(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("do the thing")
    receipt = tmp_path / "receipt"
    r = run(["send", "codex", str(prompt)], substrate="orca", capture=cap,
            env={"_BINDIR": b, "HMAD_PREFLIGHT_RECEIPT_FILE": str(receipt),
                 "HMAD_ORCA_CODEX_TERMINAL": "term_codex",
                 "HMAD_ORCA_AGY_TERMINAL": "term_agy",
                 "HMAD_STUB_ORCA_STDOUT": _preflight_listing("term_codex", "term_agy")})
    assert r.returncode != 0
    assert "preflight_not_run" in r.stderr
    assert not cap.exists() or "terminal send" not in cap.read_text()


def test_send_after_passing_env_delivers_on_enforced_path(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("do the thing")
    env = {"_BINDIR": b, "HMAD_PREFLIGHT_RECEIPT_FILE": str(tmp_path / "receipt"),
           "HMAD_ORCA_CODEX_TERMINAL": "term_codex",
           "HMAD_ORCA_AGY_TERMINAL": "term_agy",
           "HMAD_STUB_ORCA_STDOUT": _preflight_listing("term_codex", "term_agy")}
    preflight, sent = _env_then_send(["send", "codex", str(prompt)],
                                     substrate="orca", env=env, capture=cap)
    assert "PREFLIGHT: PASS" in preflight.stdout
    assert sent.returncode == 0
    assert "terminal send --terminal term_codex" in cap.read_text()


def test_send_bypass_is_explicit_and_enforced_when_empty(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("do the thing")
    cap = tmp_path / "cap.txt"
    base = {"_BINDIR": b, "HMAD_ORCA_CODEX_TERMINAL": "term_codex",
            "HMAD_ORCA_AGY_TERMINAL": "term_agy",
            "HMAD_STUB_ORCA_STDOUT": _preflight_listing("term_codex", "term_agy"),
            "HMAD_PREFLIGHT_RECEIPT_FILE": str(tmp_path / "missing.receipt")}
    bypass = dict(base, HMAD_SKIP_PREFLIGHT="1")
    allowed = run(["send", "codex", str(prompt)], substrate="orca", env=bypass, capture=cap)
    assert allowed.returncode == 0
    assert "HMAD_SKIP_PREFLIGHT" in allowed.stderr
    cap.unlink()
    enforced = run(["send", "codex", str(prompt)], substrate="orca",
                    env=dict(base, HMAD_SKIP_PREFLIGHT=""), capture=cap)
    assert enforced.returncode != 0
    assert "preflight_not_run" in enforced.stderr
    assert not cap.exists() or "terminal send" not in cap.read_text()


def test_send_rejects_expired_and_rotated_receipts_with_distinct_reasons(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    prompt = tmp_path / "prompt.txt"; prompt.write_text("do the thing")
    receipt = tmp_path / "receipt"
    env = {"_BINDIR": b, "HMAD_PREFLIGHT_RECEIPT_FILE": str(receipt),
           "HMAD_ORCA_CODEX_TERMINAL": "term_codex",
           "HMAD_ORCA_AGY_TERMINAL": "term_agy",
           "HMAD_STUB_ORCA_STDOUT": _preflight_listing("term_codex", "term_agy")}
    preflight = run(["env"], substrate="orca", env=env)
    assert "PREFLIGHT: PASS" in preflight.stdout
    values = _receipt_values(receipt)
    values["ts"] = str(int(time.time()) - 10)
    receipt.write_text("\n".join(f"{k}={v}" for k, v in values.items()) + "\n")
    expired = run(["send", "codex", str(prompt)], substrate="orca",
                  env=dict(env, HMAD_PREFLIGHT_TTL_SEC="1"), capture=tmp_path / "expired.cap")
    assert "preflight_expired" in expired.stderr

    values["ts"] = str(int(time.time()))
    receipt.write_text("\n".join(f"{k}={v}" for k, v in values.items()) + "\n")
    rotated = run(["send", "codex", str(prompt)], substrate="orca",
                  env=dict(env, HMAD_ORCA_CODEX_TERMINAL="term_rotated"),
                  capture=tmp_path / "rotated.cap")
    assert "preflight_handles_rotated" in rotated.stderr


def test_receipt_for_unresolved_agent_is_invalid_after_pinning(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    receipt = tmp_path / "receipt"
    prompt = tmp_path / "prompt.txt"; prompt.write_text("do the thing")
    unresolved = {"_BINDIR": b, "HMAD_PREFLIGHT_RECEIPT_FILE": str(receipt),
                  "HMAD_STUB_ORCA_STDOUT": _preflight_listing("term_codex"),
                  "HMAD_ORCA_CODEX_TERMINAL": "term_codex"}
    preflight = run(["env"], substrate="orca", env=unresolved)
    assert "PREFLIGHT: PASS" in preflight.stdout
    pinned = dict(unresolved, HMAD_ORCA_AGY_TERMINAL="term_agy")
    refused = run(["send", "agy", str(prompt)], substrate="orca", env=pinned,
                  capture=tmp_path / "cap.txt")
    assert "preflight_handles_rotated" in refused.stderr


def test_unset_ttl_uses_the_documented_3600_default(tmp_path):
    """AC-5.4: with HMAD_PREFLIGHT_TTL_SEC unset the window is 3600s exactly —
    not an error, and not unbounded. 3500s old is accepted, 3700s old is not."""
    b = _bindir(tmp_path, ["orca"])
    receipt = tmp_path / "receipt"
    prompt = tmp_path / "prompt.txt"; prompt.write_text("do the thing")
    env = {"_BINDIR": b, "HMAD_PREFLIGHT_RECEIPT_FILE": str(receipt),
           "HMAD_ORCA_CODEX_TERMINAL": "term_codex",
           "HMAD_ORCA_AGY_TERMINAL": "term_agy",
           "HMAD_STUB_ORCA_STDOUT": _preflight_listing("term_codex", "term_agy")}
    preflight = run(["env"], substrate="orca", env=env)
    assert "PREFLIGHT: PASS" in preflight.stdout
    values = _receipt_values(receipt)

    def _send_with_age(seconds, cap_name):
        values["ts"] = str(int(time.time()) - seconds)
        receipt.write_text("\n".join(f"{k}={v}" for k, v in values.items()) + "\n")
        # HMAD_PREFLIGHT_TTL_SEC deliberately NOT set: this asserts the default.
        return run(["send", "codex", str(prompt)], substrate="orca", env=env,
                   capture=tmp_path / cap_name)

    fresh_enough = _send_with_age(3500, "within.cap")
    assert fresh_enough.returncode == 0, fresh_enough.stderr
    assert "preflight_expired" not in fresh_enough.stderr

    too_old = _send_with_age(3700, "beyond.cap")
    assert too_old.returncode == 1
    assert "preflight_expired" in too_old.stderr


def test_bypass_does_not_suppress_the_agent_conflict_guard(tmp_path):
    """AC-6.4: HMAD_SKIP_PREFLIGHT waives the *receipt* requirement only. It must
    never permit a dispatch into a pane two agents both resolve to — that bypass
    exists to allow dispatching without a preflight, not into a provably wrong pane."""
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    prompt = tmp_path / "prompt.txt"; prompt.write_text("do the thing")
    both_on_one = {"_BINDIR": b, "HMAD_SKIP_PREFLIGHT": "1",
                   "HMAD_ORCA_CODEX_TERMINAL": "term_shared",
                   "HMAD_ORCA_AGY_TERMINAL": "term_shared",
                   "HMAD_STUB_ORCA_STDOUT": _preflight_listing("term_shared")}
    r = run(["send", "codex", str(prompt)], substrate="orca", env=both_on_one, capture=cap)
    assert r.returncode == 1
    assert "preflight_agent_conflict" in r.stderr
    assert not cap.exists() or "terminal send" not in cap.read_text(), \
        "the bypass must not let a conflicted dispatch reach the send call"


def test_preflight_pass_writes_default_receipt_with_timestamp_and_fingerprint(tmp_path):
    """AC-1.1, AC-1.2, AC-1.5, AC-8.2: PASS writes beside its pin file."""
    b = _bindir(tmp_path, ["orca"])
    pins = tmp_path / "session" / "pins.env"
    receipt = pins.parent / "preflight.receipt"
    r = run(["env"], substrate="orca", env=_receipt_env(
        b, pins, _preflight_listing("term_codex", "term_agy")))

    assert r.returncode == 0
    assert "PREFLIGHT: PASS" in r.stdout.splitlines()
    assert receipt.is_file()
    values = _receipt_values(receipt)
    assert values["verdict"] == "PASS"
    assert values["fingerprint"]
    assert int(values["ts"]) >= 0


def test_preflight_receipt_fingerprint_is_stable_and_tracks_resolved_handles(tmp_path):
    """AC-1.3, AC-1.4: fingerprint is stable for identity and changes with it."""
    b = _bindir(tmp_path, ["orca"])
    pins = tmp_path / "pins.env"
    receipt = pins.parent / "preflight.receipt"
    first_env = _receipt_env(b, pins, _preflight_listing("term_codex", "term_agy"))

    first = run(["env"], substrate="orca", env=first_env)
    assert first.returncode == 0
    first_fingerprint = _receipt_values(receipt)["fingerprint"]

    second = run(["env"], substrate="orca", env=first_env)
    assert second.returncode == 0
    assert _receipt_values(receipt)["fingerprint"] == first_fingerprint

    changed_env = _receipt_env(
        b, pins, _preflight_listing("term_codex_changed", "term_agy"))
    changed_env["HMAD_ORCA_CODEX_TERMINAL"] = "term_codex_changed"
    changed = run(["env"], substrate="orca", env=changed_env)
    assert changed.returncode == 0
    assert _receipt_values(receipt)["fingerprint"] != first_fingerprint


def test_preflight_fail_without_receipt_leaves_no_receipt_and_preserves_verdict(tmp_path):
    """AC-2.1, AC-2.3: FAIL clears absent default receipt without changing stdout."""
    b = _bindir(tmp_path, ["orca"])
    pins = tmp_path / "pins.env"
    receipt = pins.parent / "preflight.receipt"
    env = _receipt_env(b, pins, _preflight_listing("term_agy"))
    env["HMAD_ORCA_CODEX_TERMINAL"] = "term_dead"
    r = run(["env"], substrate="orca", env=env)

    assert r.returncode == 0
    line = next(line for line in r.stdout.splitlines() if line.startswith("PREFLIGHT:"))
    assert line.startswith("PREFLIGHT: FAIL")
    assert "stale=codex" in line
    assert not receipt.exists()


def test_preflight_fail_removes_existing_receipt(tmp_path):
    """AC-2.2: FAIL removes a receipt written by a prior PASS."""
    b = _bindir(tmp_path, ["orca"])
    pins = tmp_path / "pins.env"
    receipt = pins.parent / "preflight.receipt"
    passed = run(["env"], substrate="orca", env=_receipt_env(
        b, pins, _preflight_listing("term_codex", "term_agy")))
    assert passed.returncode == 0
    assert receipt.is_file()

    failing_env = _receipt_env(b, pins, _preflight_listing("term_agy"))
    failing_env["HMAD_ORCA_CODEX_TERMINAL"] = "term_dead"
    failed = run(["env"], substrate="orca", env=failing_env)
    assert "PREFLIGHT: FAIL" in failed.stdout
    assert not receipt.exists()


def test_preflight_receipt_override_wins_over_pin_file_directory(tmp_path):
    """AC-8.1: explicit receipt override wins and default receipt remains absent."""
    b = _bindir(tmp_path, ["orca"])
    pins = tmp_path / "pins" / "session.env"
    default_receipt = pins.parent / "preflight.receipt"
    override_receipt = tmp_path / "override" / "receipt.env"
    r = run(["env"], substrate="orca", env=_receipt_env(
        b, pins, _preflight_listing("term_codex", "term_agy"),
        receipt_file=override_receipt))

    assert r.returncode == 0
    assert "PREFLIGHT: PASS" in r.stdout
    assert override_receipt.is_file()
    assert not default_receipt.exists()


def test_default_preflight_receipt_is_gitignored():
    """AC-8.4: the repository ignores the unconfigured default receipt path."""
    r = subprocess.run(
        ["git", "check-ignore", "-v", ".h-mad/preflight.receipt"],
        capture_output=True, text=True, cwd=SKILL.parent,
    )
    assert r.returncode == 0
    assert ".h-mad/" in r.stdout


def test_absent_pin_paths_are_unique_per_invocation():
    """6a-prime: a shared module-scoped path lets one forgetful test poison the rest."""
    a, b = _absent_pin_file(), _absent_pin_file()
    assert a != b
    for p in (Path(a), Path(b)):
        assert p.is_absolute()
        assert SKILL.parent not in p.parents
        assert not p.exists()


def test_forgotten_pin_file_cannot_contaminate_a_later_invocation(tmp_path):
    """6a-prime finding 1, the property that matters: a pin-WRITING verb invoked
    without an explicit HMAD_ORCA_PIN_FILE must not be visible to any later call.

    With one shared default this passed silently and broke the next test; with a
    per-invocation path the mistake stays local to the call that made it."""
    b = _bindir(tmp_path, ["orca"])
    live = _orca_terms_full(
        {"handle": "term_live", "title": "worker", "preview": "",
         "worktreePath": "/repo/A", "tabId": "tab-1", "leafId": "l1"},
    )
    wrote = run(["pin", "codex", "term_live"], substrate="orca",
                env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": live})
    assert wrote.returncode == 0, wrote.stderr

    later = run(["resolve", "codex"], substrate="orca",
                env={"_BINDIR": b, "HMAD_STUB_ORCA_STDOUT": _orca_terms()})
    assert later.returncode == 1
    assert "term_live" not in later.stdout
