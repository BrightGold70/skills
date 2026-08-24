# Handoff — J44–J49 closed; the monitoring registry is at 0 open

**Date:** 2026-08-24
**Branch:** main
**Project:** skills (`/Users/kimhawk/orca/skills`)

## Session Summary

Worked an inbound handover brief (three h-mad audit-dispatch defects found while running impl-plan
audit cycles 21–24 on HemaSuite's `grounding-evidence-coverage`), then closed the two remaining
registry entries on request. **Filed J46–J49 and closed all four**, plus the pre-existing J44 —
`docs/skill-monitoring.md` now reports **0 `MONITORING`**. Suite 1668/0. Seven commits landed and **all are pushed** — `origin/main` is at `d974a59`. (An earlier
draft of this doc said four were local-only; that was written before the push.) The through-line: **three of the session's carried or standing premises
were wrong, and each was only caught by re-probing rather than by reading.**

## Key Learnings

- **Two of three handed-over premises did not survive re-probing in the form they arrived.** J46's
  mechanism is *sharper* than reported — with the contract at the tail the reviewer kept the schema
  perfectly and emitted the **literal `<AUDIT_SENTINEL>` placeholder** instead of the substituted
  value the prompt carried 3× (0 literal placeholders in the prompt, verified), so
  `h_mad_extract_report.py` exits 2 and the audit is unscoreable by a narrower route than "the block
  was dropped". J48's stated cause is **refuted outright**: a direct probe showed agy's `.tmp`
  `write_to_file` and the `mv` both reaching `DONE`. The advice was still removed — it is redundant
  with the `.done` marker ordering and costs two tool calls — but on those grounds, not the reported
  one. A confident brief is a claim, not evidence.
- **`result.status: ERROR` came out far more robust than the brief's single mechanism** — confirmed
  three times with three unrelated causes (a refused `.tmp` write; a `find_by_name` timeout plus a
  `view_file` on a nonexistent path, 31 tools / 29 ok / schema-correct report; a `write_to_file`
  rejected for a missing argument that the agent immediately retried successfully). **Any** failed
  tool call sets it, and the cause is usually incidental to the audit.
- **J44's root cause is structural, and the cheap probe was in the live transcript all along.**
  `advisor` is a **`server_tool_use` executed server-side** — it never enters local tool dispatch, so
  **no tool-scoped hook event can attach to it** and no matcher string ever could. The registry's
  planned probe (relaunch + `*`-matcher logger + one billed `advisor()` call) was **subsumed**: the
  2.1.241 binary calls it "the server-side advisor tool", and this session's own JSONL records 3 real
  `advisor()` calls as `server_tool_use` beside **101 `tool_use` blocks** for the tools that do fire
  hooks. **Counting block *types* in the session transcript is the cheap in-situ test for "does the
  harness treat this as an ordinary tool".**
- **"Hooks are snapshotted at session start" is FALSE on 2.1.241** — a standing belief in this repo,
  refuted by accident. I recorded harness invocation as owed to the next session, and the new
  `PostToolUse` hook then **fired at me ~13 minutes later in the same session**, injecting the budget
  line on an ordinary `Bash` call. Not a look-alike: the throttle stamp it left is keyed by this
  session's real id and the percentage tracked the live transcript — which also confirms
  `PostToolUse` payloads carry both `session_id` and `transcript_path`. SKILL.md now says *verify*
  rather than assume, in either direction.
- **A dead registration is worse than no registration.** The `{"matcher": "advisor"}` PreToolUse
  entry could never fire, and its presence is exactly what made the gate read as protection for
  days. Deleting the script (rather than leaving it for an install to re-wire) and teaching
  `h_mad_hook_wiring.py` to report `HOOK_NOT_WIRED` for an advisory under the wrong *event* is the
  part that keeps it closed.
- **The hollow-pass signature is real but is NOT a predictor.** A pass in this repo scored **5,356
  thinking / 2 tool calls** — the exact J49 signature — and still returned a real finding (the D-1
  post-fix dispatch). So `low-evidence` earns a **re-dispatch of that pass**, never a verdict. The
  marker is derived from the **contract** (the report-file path costs 2 successful calls, so `ok<=2`
  means nothing was read), never from tool names — naming tools would re-create J40's first-probe
  defect, where a hardcoded `view_file|grep_search` reported a false zero the moment agy switched to
  `run_command`.
- **My value sweep was the weak step twice in one session.** `a311385` shipped three stale references
  to the file it deletes — I *noted* the context-budget docstrings mid-work, went to the docs pins
  and mutation spec, and never came back (fixed in `291a84a`). Sweep **after** the last edit, not
  during.
- **The mutation harness caught a weak test of mine, twice.** `hostile-session-id-builds-a-path`
  survived because my first version created the wrong parent directory, so the unguarded write failed
  for a reason unrelated to the guard; and an **empty-but-existing** log survived until a
  discriminating test was written. Existence and content are two columns.
- **Two mutants proved genuinely EQUIVALENT and were dropped rather than left as false coverage** —
  `set -euo pipefail` (inert in the advisory because every rc is guarded, though it was the *central*
  defect for the gate, where exit 2 meant block) and the missing-checker guard (no observable
  difference). A spec that keeps them reports coverage it does not have.
- **Two documented calibration guards moved, both deliberately.** The assembler size-band fixture
  re-anchored 3047/3347 → 2850/3150 (the *band* is the assertion; the filler moves), and the
  context-hygiene section's 140-line runaway detector → 160 (it is a boundary-sanity check, not a
  prose budget, and the previous author was squeezing under it at 139).

## Next Steps

1. **Nothing owed on push — done.** `main` == `origin/main` == `d974a59`, tree clean.
2. **Live-fire the advisory in a fresh session** — it already fired in-session, so this is
   confirmation rather than the owed verification: `HMAD_CONTEXT_WINDOW=1000 claude`, then **any**
   tool call; the `[H-MAD] Context budget:` line must appear. It no longer needs an `advisor()` call.
3. **Exercise `audit-cycle` end-to-end once with the new 5th `--pass` field** on a real feature, to
   confirm the `Effort:` block renders from the verb rather than only from a hand-built invocation —
   `hmad-dispatch audit-cycle --feature <f> --phase impl-plan --cycle <N> --passes 2 --project-root <root>`.
   The wire is unit-pinned (`tests/test_hmad_dispatch_audit_cycle.py`) and mutation-covered, but has
   not run against a live dispatch.
4. ~~Decide the fate of the unverified HemaSuite Nit.~~ **DONE — refuted, see Open Items.**
   Verifying it cost three greps; routing it would have cost a brief, a claim check, a worktree
   stamp and a delivery, to transfer something false.

## Open / Blocked Items

- **Unverified HemaSuite finding, produced incidentally — status: not routed, deliberately.** The
  D-1 post-fix verification dispatch (an audit of `grounding-evidence-coverage.impl-plan.md`, run to
  test *my* assembler, not to audit *their* plan) returned one Nit: *"Verify that `project_dir` in
  `cmd_regenerate_section` (Task 14) is a `pathlib.Path` object; if it is a string, the expression
  `project_dir / "guideline_keys.json"` will raise a `TypeError`."* **I did not verify it**, and
  handing an unverified reviewer sentence to another lane as a finding is the exact
  carried-repro-is-not-evidence failure this session spent its time correcting. That lane already
  tracks `cmd_regenerate_section` as an open protocol gap, so this is at most a pointer.
  `repo: /Users/kimhawk/orca/HemaSuite/hematology-paper-writer · branch: feature/201-grounding-evidence-coverage · worktree: none` ·
  report: `<scratchpad>/head_dup.report.md` · log: `<scratchpad>/head_dup.ndjson`.
  **RESOLVED 2026-08-24 — REFUTED, nothing to route.** The operator asked how to solve it; the
  answer was to verify rather than route, and the check was three greps. Inside
  `cmd_regenerate_section` (`cli/_commands.py:3455-3628`) `project_dir` is bound exactly twice and
  **both are Paths by construction**: `:3494` `project_dir = sections_dir.parent` (`.parent` of a
  Path is a Path) and `:3574` `project_dir = Path(sections_dir).parent`. `sections_dir` is itself
  `Path(args.project_dir) / "sections"` at `:3462`, so the raw argparse **str is wrapped at the
  boundary and never survives**. Task 14's planned line lands inside that same function and
  inherits a Path either way, so the `TypeError` cannot occur. The pass confused `args.project_dir`
  (a str, never used bare in a `/` expression) with the local `project_dir`.
  **The general lesson, which is the part worth keeping:** an item parked as "unverified, operator
  call" was cheaper to *falsify* than to route. Verification cost 3 greps; a HANDOVER would have
  cost a brief, a claim check, a worktree stamp and a delivery — to transfer something false. When
  an unrouted item is small and checkable, checking it IS the routing decision.
- **Monitoring registry: 0 open.** `grep -c "Status: \`MONITORING\`" docs/skill-monitoring.md` → `0`.
  Count the word; never the absence of one.
- **`~/.claude/settings.json` was edited** (dead `advisor` PreToolUse matcher removed, `PostToolUse`
  advisory added). Backup at `~/.claude/settings.json.bak.j44-20260824T082243`; verified
  semantically that nothing else in the file changed.

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/h_mad_audit_gate.py`, `h_mad_assemble_audit.py`, `h_mad_audit_cycle.py`,
  `h_mad_review_evidence.py`, `h_mad_hook_wiring.py`, `h_mad_context_budget.py`, `hmad-dispatch.sh`
- `h-mad/hooks/h-mad-advisor-warn.sh` (new) · `h-mad/hooks/h-mad-advisor-gate.sh` (deleted)
- `h-mad/audit-prompt.template.md`, `h-mad/SKILL.md`, `h-mad/references/orchestration-mode.md`
- `h-mad/tests/` — `test_h_mad_audit_gate.py`, `test_h_mad_assemble_audit.py`,
  `test_h_mad_advisor_warn.py` (new), `test_h_mad_advisor_gate.py` (deleted),
  `test_h_mad_hook_wiring.py`, `test_h_mad_context_budget{,_docs}.py`, `test_h_mad_audit_cycle.py`,
  `test_h_mad_review_evidence.py`, `test_hmad_dispatch_audit_cycle.py`
- `h-mad/tests/mutation-specs/` — `advisor_warn.json` (renamed from `advisor_gate.json`),
  `audit_effort.json` (new) · `h-mad/tests/specs/audit_cycle_connections.mutation.json`
- `docs/skill-monitoring.md` (J46–J49 filed; J44 + J49 closed)
- `~/.claude/settings.json` (outside the repo — see Open Items)

**Uncommitted changes:** none — working tree clean.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short --branch                    # expect: main...origin/main [ahead 4], clean
/opt/anaconda3/bin/pytest h-mad/tests/ -q      # expect 1668 passed (~4 min)
grep -c 'Status: `MONITORING`' docs/skill-monitoring.md   # expect 0
```

Suite runtime is ~4 min; run it in the **foreground**. `python3` on PATH here is 3.14 with no
pytest — use `/opt/anaconda3/bin/pytest`.

**Related docs:**
- `docs/handoffs/2026-08-24-main__audit-dispatch-contract-integrity.md` — the inbound brief this
  session worked (J46–J48).
- `docs/handoffs/2026-08-24-main__j30-closed-advisor-gate-never-fires.md` — the sibling session that
  filed J44.
- `docs/skill-monitoring.md` — entries J44, J46, J47, J48, J49 all carry their evidence tables and,
  where a premise was corrected, the correction.
