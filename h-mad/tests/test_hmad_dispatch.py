import json
import os
import shutil
import subprocess
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
WRAPPER = SKILL / "scripts" / "hmad-dispatch.sh"
STUBS = SKILL / "tests" / "stubs"

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


def run(args, *, substrate=None, env=None, capture=None):
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
    if substrate:
        e["HMAD_SUBSTRATE"] = substrate
    if capture:
        e["HMAD_STUB_CAPTURE"] = str(capture)
    if env:
        e.update({k: v for k, v in env.items() if k != "_BINDIR"})
    # Build an isolated PATH containing only the requested stubs (+ real jq/coreutils).
    # Deliberately excludes the ambient PATH: dev/CI machines may have real
    # cmux/orca binaries installed (e.g. under /opt/homebrew/bin), which would
    # leak into `command -v` lookups and defeat the bindir-only isolation this
    # helper exists to provide.
    e["PATH"] = f"{bindir}:/usr/bin:/bin" if bindir else os.environ["PATH"]
    return subprocess.run(["bash", str(WRAPPER), *args], capture_output=True, text=True, env=e)


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
    assert "codex -> term_codex" in r.stdout
    assert "agy -> term_agy" in r.stdout


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


def test_orca_identity_explicit_pin(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    r = run(["env"], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_CODEX_TERMINAL": "t-abc",
                 "HMAD_ORCA_AGY_TERMINAL": "t-def"})
    assert "codex -> t-abc" in r.stdout
    assert "agy -> t-def" in r.stdout


def test_orca_identity_resolves_from_list_json(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    canned = '{"result":{"terminals":[{"handle":"term_c","preview":"codex ..."},{"handle":"term_a","preview":"agy ..."}]}}'
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
        {"handle": "term_codexA", "title": "Codex - A", "preview": "",
         "worktreePath": "/repo/A", "leafId": "leaf-A3"},
        {"handle": "term_codexB", "title": "Codex - B", "preview": "",
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
    r = run(["send", "codex", str(pf)], substrate="cmux",
            env={"_BINDIR": b, "HMAD_CMUX_CODEX_SURFACE": "surface:5"}, capture=cap)
    assert r.returncode == 0
    text = cap.read_text()
    assert "cmux send --surface surface:5 HELLO-PROMPT" in text
    assert "send-key --surface surface:5 Enter" in text


def test_send_orca_uses_file_contents(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    pf = tmp_path / "prompt.txt"; pf.write_text("HELLO-ORCA")
    r = run(["send", "codex", str(pf)], substrate="orca",
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
    r = run(["send", "codex", str(pf)], substrate="orca",
            env={"_BINDIR": b, "HMAD_ORCA_CODEX_TERMINAL": "t-1"}, capture=cap)
    assert r.returncode == 0
    text = cap.read_text()
    assert "SMALL-PROMPT" in text
    assert str(pf) not in text, "small prompts must still be inlined"


def test_send_switches_to_indirection_for_a_large_prompt(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    pf = _prompt_file(tmp_path, _INLINE_MAX_DEFAULT + 1, "big.txt")
    r = run(["send", "codex", str(pf)], substrate="orca",
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

    r = run(["send", "codex", str(noncanonical)], substrate="orca",
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
    run(["send", "codex", str(pf_at)], substrate="orca",
        env={"_BINDIR": b, "HMAD_ORCA_CODEX_TERMINAL": "t-1"}, capture=at)
    assert "XXXXXXXXXXXX" in at.read_text()

    over = tmp_path / "cap_over.txt"
    pf_over = _prompt_file(tmp_path, _INLINE_MAX_DEFAULT + 1, "over.txt")
    run(["send", "codex", str(pf_over)], substrate="orca",
        env={"_BINDIR": b, "HMAD_ORCA_CODEX_TERMINAL": "t-1"}, capture=over)
    assert "XXXXXXXXXXXX" not in over.read_text()


def test_threshold_is_tunable(tmp_path):
    b = _bindir(tmp_path, ["orca"])
    cap = tmp_path / "cap.txt"
    pf = _prompt_file(tmp_path, 100, "medium.txt")
    r = run(["send", "codex", str(pf)], substrate="orca",
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
    r = run(["send", "codex", str(pf)], substrate="cmux",
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
