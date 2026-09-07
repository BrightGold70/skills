# Handoff — the H1–H9 fold shipped, five prose gates became code, and TAKEOVER mode

**Date:** 2026-09-07
**Branch:** `main` — clean, `0/0`, HEAD `f4be931`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-09-07-main__tooling-backlog-drained-7f-and-91.md (branch predecessor, resumed from at session start; every open item walked below), 2026-09-07-main__subagent-report-truncation.md (inbound brief, taken over and **SHIPPED**), 2026-09-07-main__audit-loop-cycle-count-evidence.md (inbound brief, taken over; its five items are OPEN below)

## Session Summary

Resumed from the tooling-backlog handoff and worked the `#11` H1–H9 fold to completion: **H3**
(leg-set stability), **H5** (shared-sentence adoption), **H4** (delta self-review as a script) and
**H2** (the round cap, *enforced*) all shipped, leaving **H7 the only unbuilt hypothesis**. Two
inbound briefs were adopted mid-session; one of them shipped the same day. **21 commits, all
pushed.** The spine of the session is one repeated finding: **five h-mad rules that were correct,
documented and argued from measurement existed only as prose** — the two-consecutive-clean streak,
the suite gate, the leg set, the author REPORT contract, and the round cap. Each was skippable, and
each is now code. A sixth gap produced a new `handoff` mode: **TAKEOVER**, because adopting an
inbound brief was reachable only through READ, which halts on a loaded session.

Final gates: h-mad **3011 passed**, handoff **304 passed**, `ANCHORS_OK specs=62 mutations=681`,
every mutation battery `ALL_CAUGHT`.

## Key Learnings

- **A rule that is correct, measured and documented is still skippable if nothing executes it.** Five
  found this session, each shipped with its own argument and none enforced. The pattern is not
  carelessness — it is that writing the rule *feels* like shipping it. `grep` for the enforcement,
  not for the rule.
- **An instrument built around the happy path proves only the happy path.** `exit_check` certified a
  two-cycle streak from **one cycle's two legs**; neither the 2936-test suite nor my own field tracer
  could see it, because both used fixtures that were distinct cycles *by construction*
  (`v1.gated.json`/`v2.gated.json`, and v43/v44). The fixtures now carry the real filename grammar,
  which is what lets them express the failure at all.
- **Tracer a new detector on REAL commits before trusting it.** v1 of the delta review called every
  backticked span a claim and returned `claims=15 executed=0` on a real commit — every one an
  identifier (`doc-auditor`, `DIVERGED`, `[H-MAD]`). An alert that is always wrong gets ignored.
  Filtered to verb+argument it returns `claims=2` on `a90c365`, both genuine.
- **The mutation battery keeps catching my TESTS, not my code.** Six times this session a row
  SURVIVED or was REFUSED because the assertion named the *topic* rather than the prescription, or
  the mutation was aimed at a line that never carried the property. `-s` on a file read is an
  optimisation, not a guard; `shlex.split` means a canary for an executed redirect can never fire;
  "names no feature" appears in the mutant's own replacement text.
- **A count is only comparable at the same collection root.** The handoff suite read 155 from the
  repo root and 295 from `handoff/` — the root-level run misses `handoff/scripts/`, where a real test
  lives. Same commit, same tree, two numbers.
- **A positional shell arg in a skill body is REWRITTEN before the agent sees it.** Measured twice on
  one line: it arrived as `…": "read}` under `/handoff read` and `…": "takeover}` under
  `/handoff takeover`, while disk held awk's whole-record variable. The documented command printed
  the argument instead of the matching line — invisible to anyone reading the rendered text.
- **A carried label can be wrong for days.** `exec agy lingers` sat as "related lane, NOT owned here"
  for four days; the brief says `Project: skills`, was already `Taken-Over-By: skills`, and states
  "Ownership moves to this lane". I inherited the mislabel from the handoff and repeated it until I
  re-read the brief itself.

## Next Steps

1. **Build H7 — per-must origin tagging.** The only unshipped hypothesis, and the instrument that
   would measure whether the other eight worked. Schema already specified — read it, do not
   re-derive: `/Users/kimhawk/orca/HemaSuite/hematology-paper-writer/docs/03-analysis/gateway-consolidation.audit-ledger.md`
   lines 88–106. Working sidecar at `…/gateway-consolidation.audit-origins.jsonl` (64 KB).
2. **Decide the two-round cap's exit terms and write them into `h-mad/SKILL.md`** §"Document-audit
   round cap". The cap forbids a third *gating round*, not a final corrective revision — the text
   does not say which it means, and HemaSuite `#18` Phase 5b is hitting it right now with a provably
   unsatisfiable AC (88-vs-94) that would otherwise ship as an `OPEN-DECISION`.
3. **Exercise the new gates on a live feature cycle.** `--project-tests`/`--gated`/`--legs` on
   `h_mad_audit_cycle.py`, then `--round-cap 2 <stamps>` and `--exit-check <stamps>`. None of the
   five has run inside a real H-MAD cycle in this repo; the tracers used real artifacts, not a real
   loop.
4. **Investigate the second surface-disagreement mechanism** — H6 ships and does not explain agy
   `must=0` at `tools=41` beside codex `must=3`, zero overlap, on one prompt.
5. `[suggested]` **Probe hygiene for the four author agents** (`h-mad/agents/*-author.md`), mirroring
   SKILL §"Confirming a suspected defect". An author left an executable `test_env_sleep.py` at a
   sub-project root; the agents inherit no delete-your-probes rule.

## Open / Blocked Items

**This lane — `repo: /Users/kimhawk/orca/skills · branch: main · worktree: none (main is canonical)`**

- **H7 origin tagging — OPEN.** Absence re-verified across **ten spellings**; the only hits are prose
  written today. Inherited via **Handover-From:** HemaSuite · main · session `6a09584b`. Claimed by
  this session as feature `audit-loop-cycle-count-evidence`.
- **The two-round cap's exit terms are ambiguous — OPEN, blocking a live lane.** See Next Step 2.
  Inherited via the same brief.
- **Second surface-disagreement mechanism — OPEN.** Inherited via the same brief. n=1, and the round
  that produced it is still in flight.
- **Two H8 extensions and probe hygiene — OPEN.** Vacuous pins (a criterion that cannot discriminate
  in either direction: AC-2.5b, AC-7.5c); H8 one level out (a *contract* elsewhere in the document
  pinning a count the revision moved — two independent arithmetic checks missed it the same way);
  and the author probe-hygiene rule. Inherited via the same brief.
- **The code-phase ledger does not exist — OPEN.** Phase 4 measured documents only; nothing measures
  corruption of *code* by an audit fix. Candidates with recorded evidence: `#46
  grounding-evidence-coverage` (62 cycles, a Critical missed), `manuscript-model-provenance` (a clean
  cycle falsified four times). Inherited via the same brief. Largest and lowest-priority of the five.
- **#112 GATE-CLASS reviewer half — OPEN, unchanged since 2026-09-07 morning.** The mechanism is
  field-measured with controls; no reviewer has ever emitted a `class:` line (833 of 1001 legs carry
  zero). Blocked on a live phase 3/4 cycle — there is none in this repo.
- **#2 Phase 7f on the next feature closure — OPEN, unchanged.** `h_mad_phase7_integrate.py` exists
  and is documented; it has never run on a real closure.
- **#30 · #32 · #49w — CANNOT RESOLVE.** They are an earlier session's orchestrator labels, not keys
  in `docs/skill-candidates.md`, which has no `#N` numbering. Their definitions did not survive the
  chain. Either recover them from the session that assigned them, or drop them — carrying three
  opaque tokens forward as "unchanged" asserts a status nobody can check.
- **`docs/skill-candidates.md` open-row census — NOT PUBLISHED, deliberately.** Three hand
  derivations disagreed (51 flat occurrences / 45 in-row / 44 rows; open reads 16 or 18 depending
  only on whether the terminal marker must be bold). Route it through
  `references/automation-scout.md`; do not hand-parse.
- **The automation scout did NOT run this session — OPEN, and it is owed.** `--skip-scout` was not
  passed; the phase was skipped on the context ceiling (`CTXBUDGET: OK used=787080 pct=78.7
  ceiling=80` at the moment of the decision — the scout needs its 120-line reference plus a
  reconciliation pass over a ~1500-line `docs/skill-candidates.md`, which does not fit in the
  remaining budget). A degraded scout is worse than a declared skip: it is the only thing that writes
  that file, and a status nobody flips decays until the backlog must be re-derived by hand. Run it
  first thing next session — and note that this session ALSO found the open-row census cannot be
  hand-parsed (three derivations disagreed), so the scout is the only correct route.
- **Time Machine destination does not mount** (`tmutil latestbackup` → error 18) while
  `/Users/kimhawk/.h-mad-corpora` is `[Included]`. Nothing under `$HOME` is verifiably backed up.
  Operator action; the evidence-gate corpus is only where it surfaced.
- **Evidence-gate corpus** — outside the repo, now **manifest-pinned** (`52972e7`, 66 files, 66/66
  `OK`). Loss is detectable and the corpus re-derivable; it is still not backed up.
- **The sender's lane is LIVE and mid-run.** HemaSuite `#18` Phase 5b is executing Task-1 mutations
  right now (`repo: /Users/kimhawk/orca/HemaSuite/hematology-paper-writer · branch: main`). Not this
  session's processes, and not this session's to touch — but the H7, cap-ambiguity and
  second-mechanism items above all come from it, and its answers may move while they sit here.

**Closed this session, so the next reader does not re-check them**

- **#11 H1–H9 fold — COMPLETE.** H3 `9a31357`+`6f2f227`, H5 `8af16d9`, H4 `e7b97db`, H2 enforced
  `85fe94a`. H1/H6 were already enforced code, H9 is `AGENT_TOOL_WARN_BYTES`. **H7 alone remains**,
  and H8 stays doctrine-only by decision, not oversight.
- **The streak counted STAMPS, not cycles** — `e54f920`. 8 of 17 archived cycles carry two stamps;
  the real pair `design.audit.v20.codex`+`…v20.p1` returned `EXIT: READY`.
- **The cycle driver fed neither gate** — `7b5cb2f`. Every cycle recorded `suite: null` and no leg
  set. Suite now runs once per cycle, forwarded per leg as `--suite-result`.
- **Author agents had no REPORT path** — `96fca5f` + `6e1554a`. Inbound brief, adopted and shipped
  the same day; the orchestrator now reads `$RP` rather than only staging it.
- **`exec agy` lingered after its `result`** — `be0a490`. Waits on the signal, not the pid. The
  carried "not owned here" label was FALSE.
- **TAKEOVER mode** — `88cea92`, upgraded `f4be931`. First live run adopted a brief that arrived
  mid-session; it exposed a claim gap (a brief naming no feature left five items unowned) which is
  now fixed and applied.
- **#61 `COLLECT: MISSING`** — carried premise FALSE, already landed; re-verified by reproducing the
  incident. **#66** — all three defects confirmed resolved. **#36** — re-derived at 88 markers with
  its rationale re-verified at source.

## Context for Next Session

**Files touched this session:** `h-mad/scripts/h_mad_audit_gate.py` · `h_mad_audit_cycle.py` ·
`hmad-dispatch.sh` · `h_mad_adoption_check.py` (new) · `h_mad_delta_review.py` (new) ·
`h-mad/SKILL.md` · `h-mad/agents/{design,plan,spec,implplan}-author.md` ·
`h-mad/references/failure-recovery.md` · `handoff/SKILL.md` ·
`handoff/scripts/test_handover_docs.py` · 6 new test files · 6 new mutation specs ·
`docs/03-analysis/hmad-gate-field-verification.md` (new) ·
`docs/03-analysis/hmad-audit-evidence-gate.corpus-manifest.md` (new) · `docs/learnings.md`

**Uncommitted changes:** none, besides the 88 untracked `.done` markers. **Do not commit or
gitignore them** — `hmad-dispatch.sh:2955-2956` counts them (`^?? .*\.done$`) to exclude them from
its tree delta, so hiding them blinds that measurement.

**Claims held by this session:** `audit-loop-cycle-count-evidence` → `e07f76b9`. Release it if you
are not continuing that work. `pin-agents-tail-banner` → `f70b9d62` is NOT this session's and the
inbound brief says to leave it alone.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main                      # f4be931, clean, 0/0
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"; hmad-dispatch env
# the H7 dataset is in the OTHER repo — read it in place, do not hand-edit its tables
sed -n '88,106p' /Users/kimhawk/orca/HemaSuite/hematology-paper-writer/docs/03-analysis/gateway-consolidation.audit-ledger.md
```

**Verification state at closure**, all re-derived at `f4be931`: h-mad `3011 passed / 0 failed` ·
handoff `304 passed / 0 failed` (measured from `handoff/`, **not** the repo root — that reads 155 and
misses `handoff/scripts/`) · `ANCHORS_OK specs=62 mutations=681 drifted=0` · every mutation spec
`ALL_CAUGHT`.

**Related docs:**
- `docs/03-analysis/hmad-gate-field-verification.md` — the tracer run, its predictions recorded
  before the result, and the defect the tracer's own method could not see.
- `h-mad/SKILL.md` §"Document-audit round cap" (H2, with the 6.6%-new-mechanism evidence),
  §"Shared sentences are single-sourced" (H5), §"Run the delta self-review as a SCRIPT" (H4).
- `handoff/SKILL.md` §"TAKEOVER mode" — including why it may skip READ's fresh-context halt.
