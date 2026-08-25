# Handoff — The `timeout` premise was refuted, and `audit-cycle` had never dispatched

**Date:** 2026-08-25
**Branch:** main
**Project:** /Users/kimhawk/orca/skills (h-mad skill)

## Session Summary

Resumed from `2026-08-25-main__portable-timeout-run-verb` and the reconciliation immediately
refuted that handoff's core premise: coreutils 9.11 was installed on this box at 07:29, **seven
minutes before** the 07:36 commit whose evidence line reads *"`command -v timeout gtimeout` →
nothing, exit 1"*. Regrounded the rule from *absence* to *portability* across six surfaces plus
two new guards (`333e4de`), then worked the four carried Next Steps. Exercising `audit-cycle`
live found it **could never dispatch at `--passes 2`, its default** — fixed in `108eeb6`. All
four carried items are closed, plus a fifth that was evaluated and deliberately not built.
Everything committed and pushed; suite **1804/0**; tree clean, `main` == `origin/main` @ `2f50bff`.

## Key Learnings

- **Installing the missing tool DELETED the forcing function.** Before coreutils, an improvised
  `timeout <n> <cmd>` died at 127 loudly. With it, the same command silently *works* here and
  fails only on a box without it. The error WAS the detector; removing it is a regression, and
  it makes the rule text matter more, not less.
- **A rule whose stated reason a reader can refute in one command is a rule a reader discounts.**
  All four rule surfaces asserted "macOS ships neither", which one `command -v` now falsifies.
- **Exit code cannot police this rule.** Measured A/B: `hmad-dispatch run --timeout 5` and a bare
  `timeout 5` **both returned 124**. Only the command form in the log discriminates — which
  retires the old check ("look for `run_timeout` or a clean exit rather than a 127").
- **Agents reason from a local probe to an exemption.** The unruled control ran `which timeout`
  *first*, found the coreutils copy, and used it. The clause added that morning — *do not reason
  from a successful `command -v` to an exemption* — was written as a guess and an agent did
  exactly that within hours.
- **Mutation coverage proves only the REJECT direction.** `audit-cycle`'s divergence guard was
  fully mutation-covered and still rejected every real prompt. A guard that rejects everything
  kills every mutant. Nothing in 57 tests asserted the ACCEPT direction.
- **Calibrate guards on production output, never a stub.** That guard hardcoded `diff == 2 lines`
  because the fake assembler wrote the report path once; the real one writes it twice
  (`prepend_output_contract` duplicates the contract at the head). And there were **two copies**
  of that fake — the `_cmd_exec` trace harness uses the second, so aligning only the first changed
  nothing and read exactly like the fix having failed.
- **Fixing the seam beat writing a new test.** Once both stubs matched production, reverting the
  guard failed **13 existing tests** that had been green against a verb that could not dispatch.
  The coverage already existed and was aimed at the wrong shape.
- **A doc-lint qualifier must ADJOIN its claim.** A ±90-char proximity window accepted
  `macOS ships neither` because an unrelated `system component` sat 40 chars upstream — it passed
  the exact text it existed to reject. A bare `(?<!stock )` lookbehind failed the other way:
  `non-stock macOS ships neither` ends in `stock ` and satisfied it.
- **Scan doc-lints on whitespace-collapsed, Markdown-stripped text**, or paragraph reflow and
  `**emphasis**` decide whether a guard fires.
- **Measuring the wrong surface produced a false negative FOUR times this session** — grepping
  `stream-json` stdout for a hook's `additionalContext` (it never reaches stdout); searching
  `/tmp` for a stamp when `TMPDIR` is `/var/folders/…`; keying agy's NDJSON on `command` instead
  of `CommandLine`; and counting `.out` files when reports are `.md`. Each looked exactly like
  "the thing never happened".
- **A Claude Code `PreToolUse` hook is structurally blind to dispatched agents.** `exec` launches
  `agy`/`codex` as direct child processes; neither reads `~/.claude/settings.json`.
- **agy audit passes WRITE into the repo** — three `test_*.py` scratch files appeared in `h-mad/`
  after four "read-only" review dispatches. Check `git status --short` before staging.

## Next Steps

1. **Nothing is owed.** `main` == `origin/main` == `2f50bff`, tree clean, suite 1804/0.
2. **[suggested] Re-triage the discarded audit findings, or decide they are noise** — the live
   `audit-cycle` runs produced 4 must-fix + 1 should-fix against
   `docs/01-plan/features/exec-path-hardening.impl-plan.md`. I deleted those reports as
   verb-exercise artifacts without triaging (operator confirmed: nothing to do). Both passes were
   flagged `low-evidence`, and re-auditing a **shipped** feature's plan doc will always look like
   "the plan omits X" when the code has X. Re-derive with
   `hmad-dispatch audit-cycle --feature exec-path-hardening --phase impl-plan --cycle <N> --passes 2 --project-root /Users/kimhawk/orca/skills`.
3. **[suggested] Revisit the runtime forcing function only on a SECOND natural improvisation.**
   Evaluated and rejected this session (see Open Items). If it recurs, scope any scanner to agy
   NDJSON only (structured `CommandLine`), report never gate, never fail-loud on codex.

## Open / Blocked Items

- **Runtime forcing function for an improvised `timeout` — status: evaluated, deliberately NOT
  built.** Nothing at runtime catches an agent improvising `timeout <n>`; the static tree-scan
  covers only h-mad's own checked-in files. Both candidate mechanisms were rejected on evidence:
  a Claude Code `PreToolUse` Bash hook is structurally blind to dispatched agents, and a
  post-dispatch log scan false-positives on quoted text (`echo "timeout <n>" > f`) while any
  fail-loud parse guard would fire on **every** codex dispatch (the codex arg build carries no
  `--json`, so its log is a plain-text transcript). Base rate decided it: **30 real dispatched
  commands this session, zero improvisations** — the only occurrence was an induced control.
  Shipped instead: one line in the `exec` row of `references/agent-substrate.md` (`2f50bff`).
- **The original incident's agent type is unrecorded — status: unresolvable.** A red-team pass
  argued it was the ORCHESTRATOR, not a dispatched agent (it narrated conversationally to the
  operator, and the prior handoff calls it "a snippet from another session"). Plausible and I
  could not refute it; it means my first stated ground for rejecting the hook was partly wrong,
  though the rejection itself stands.
- **`MEMORY.md` over its load limit — status: RESOLVED during closeout, jointly.** It was 25,478 B
  against a ~24,986 B (24.4 KB) ceiling and truncating on load. Mid-session it *grew*, confirming a
  concurrent writer (the `feature/201` sibling), so I deliberately did not trim other features'
  800–1100-char lines — that would have been a read-modify-write race. By closeout the sibling had
  cut ~1.1 KB and my own index edits removed a further 221 B (three pointers rewritten shorter,
  one 456→215). Now **24,139 B / 23.6 KB — under the limit**. Re-measure rather than trusting this
  line: two sessions write that file.
- **Sibling worktree in flight — not this repo, not this lane.**
  `repo: /Users/kimhawk/orca/HemaSuite · branch: feature/201-grounding-evidence-coverage ·
  worktree: (Orca-managed)`. Its stamp reads *"taken over: grounding-evidence-coverage · 12/15
  shipped (Task 10 FR-2 root cause 75c67ebf) · suite 8826/1-known · next: Task 15"*. Two live
  agent PIDs (83059 codex, 83098 agy, both cwd `/Users/kimhawk/orca/HemaSuite`, started 10:38)
  belong to it, **not** to this session. Ownership stays there; nothing to hand over.

## Context for Next Session

**Files touched this session:**
- `h-mad/SKILL.md` — NEVER-list bullet regrounded
- `h-mad/invariants.base.md` — §"Portable time bounds" regrounded
- `h-mad/references/agent-substrate.md` — `run` row, `exec` row (×2: reground + ad-hoc guidance)
- `h-mad/references/codex-implementer-prompt.md` — time-bound paragraph
- `h-mad/scripts/hmad-dispatch.sh` — `_cmd_run` comment; `_cmd_audit_cycle` divergence guard
- `h-mad/tests/test_h_mad_portable_timeout.py` — 2 new guards + 20-row behaviour table
- `h-mad/tests/test_hmad_dispatch_audit_cycle.py` — both stub assemblers aligned to production
- `h-mad/tests/specs/audit_cycle_gating.mutation.json`, `…_connections.mutation.json` — anchors retargeted
- `docs/learnings.md` — 14 entries

**Uncommitted changes:** none — all in `333e4de`, `14a5d26`, `f4bbf55`, `108eeb6`, `e45df89`,
`6b287bb`, `2f50bff`, all pushed.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main
/opt/anaconda3/bin/pytest h-mad/tests/ -q -p no:randomly   # 1804 passed, ~240s
h-mad/scripts/hmad-dispatch.sh run --timeout 2 -- sleep 30 # -> 124 + run_timeout
```

**Verification evidence (so it need not be re-derived):**
- Premise refuted: coreutils 9.11 `installed_on_request: true`, Cellar mtime **07:29**, vs feature
  commit `81dc213` at **07:36**. `command -v timeout gtimeout` now exits 0.
- Suite on final bytes: **1804 passed, 0 failed, 240.96s**.
- Mutations: four rounds over the two new doc-guards, every mutant killed or an intentional
  survival; each round re-baselined green first (one early round's "KILLED" was worthless because
  its baseline was red).
- `audit-cycle` live, `--passes 2`: `AUDITCYCLE: FAIL must=1 should=0 passes=2 p1=1/0 p2=0/0
  delivered=report-file,report-file size_status=verified`, with one `Effort:` line per pass — the
  J49 5th `--pass` field rendering outside a unit test for the first time.
- Context-budget advisory, treatment vs control: `HMAD_CONTEXT_WINDOW=1000` put
  `[H-MAD] Context budget: 6188.8% of a 1000-token window used` into session
  `630d43b2-…`'s transcript twice, plus its emit stamp; the byte-identical control emitted
  nothing and wrote no stamp while still running the Bash tool.
- Time-bound A/B: treatment ran `hmad-dispatch run --timeout 5 -- slow_job.sh` (5.18s); control
  ran `which timeout; which gtimeout` then `timeout 5 slow_job.sh` (5.36s). **Both exit 124.**

**Related docs:**
- `h-mad/references/agent-substrate.md` — the `run` row, and the `exec` row's new ad-hoc-prompt line
- `h-mad/invariants.base.md` §"Portable time bounds" and §"No new external dependency"
- `h-mad/tests/test_h_mad_portable_timeout.py` — `test_absence_detector_behaviour` is the pinned
  contract for the absence-claim detector; read it before touching that regex
- Prior handoff: `docs/handoffs/2026-08-25-main__portable-timeout-run-verb.md` (its "Premise
  confirmed on this box" line is the one this session refuted)
