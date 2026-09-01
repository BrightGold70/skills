# Handoff — h-mad audit dispatch: three contract-integrity defects

**Date:** 2026-08-24
**Branch:** main
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Handover-From:** HemaSuite · feature/201-grounding-evidence-coverage · session a7f5968f-2f3a-4659-b527-e074a50edeea
**Taken-Over-By:** skills · main · session unknown · backfilled 2026-09-01 — all three shipped -- D-1 `assemble_audit` step 6.7 emits the output contract at the head; D-2 `_is_none_sentinel` normalises trailing punctuation; D-3 no `.tmp` advice remains and the `result.status` caveat is in SKILL.md and orchestration-mode.md

## Session Summary

Ran impl-plan audit cycles 21–24 on HemaSuite's `grounding-evidence-coverage` (8 `exec agy` passes
total). The feature work is done and stays there; **these three defects are h-mad's, not HemaSuite's**,
and all three were load-bearing on whether an audit could be scored at all. Nothing here is claimed —
`h_mad_resume_decision.py` returns `start_fresh` for `audit-dispatch-contract-integrity` against
`/Users/kimhawk/orca/skills/docs/.bkit-memory.json`, so take it with a plain `--claim`.

Two of the three caused a **wrong verdict**, in opposite directions: D-1 made two real audits
unscoreable, and D-2 manufactured findings that did not exist. D-3 makes `result.status` unusable as a
success signal.

## Key Learnings

- **D-1 — the output contract at the tail of a long prompt is dropped, and head-duplication fixes it.**
  Cycle 21: both passes ignored the entire output-framing block — no `-BEGIN`/`-END` sentinels, no
  `## Summary`/`## Must-fix`/`## Should-fix`/`## Nit` schema, no `.report.md`, no `.done`. Pass A
  invented its own `GATE: PASS must=0 should=0 nit=0` header; pass B invented `GATE: FAIL must=1`.
  `h_mad_audit_gate.py` returned `GATE: INVALID` on both. **Both passes did real work** (A: 100 s /
  11,230 thinking; B: 193 s / 15,786 thinking / 34 tool calls) and pass B's content contained a genuine
  must-fix — it was simply unscoreable.
  **Do not read this as a size limit.** I first recorded it as a J30 size effect and withdrew that: J30
  is closed and its size premise was refuted 8/8 on re-probing. The measurement is
  **placement**, not size — with the contract at the tail it was lost 2 of 2 passes at 206.4 KB; with the
  contract duplicated at the head it was kept **4 of 4** passes at *larger* sizes (219.8 KB, 224.5 KB,
  229.4 KB). Larger prompts succeeding is what rules size out.
  Fix belongs in `h_mad_assemble_audit.py` — emit the framing block at the head as well as the tail.
  Working prototype (a wrapper over the assembler, not a patch to it) is inlined under "Reproduce" below.
- **D-2 — `h_mad_audit_gate.py`'s empty-section sentinel is punctuation-intolerant, and it false-FAILs.**
  `_count_section_findings` tests `p.lower() == "none"`. A reviewer that writes `None.` — with a trailing
  period, which agy does — misses the sentinel, falls through to the fail-safe branch ("non-`None`
  content with no countable bullet → count 1") and **manufactures one phantom finding per section**.
  Observed live: cycle 23 pass B wrote "Must-fix: None." / "Should-fix: None." and scored
  `GATE: FAIL must=1 should=1` with nothing behind it.
  The fail-safe *direction* is right — a false FAIL beats a false PASS — so the fix is narrow: normalise
  trailing punctuation before the sentinel comparison (`p.lower().rstrip(" .") == "none"` or similar).
  Do **not** loosen the fail-safe branch itself.
- **D-3 — the `<path>.tmp` + `mv` atomicity advice is refused by agy's artifact sandbox, and the run
  then reports `status: ERROR` on a correctly written report.** The assembled prompt's report-file
  section advises "for a hard atomicity guarantee, write to `<path>.tmp` and `mv` it into place". Under
  `exec agy` that path is rejected: `declaring permissions: cortex tool write_to_file: … <path>.report.md.tmp
  is not a valid artifact path; artifacts must be in /Users/kimhawk/.gemini/antigravity-cli/brain/<conversation-id>`.
  agy then completes the job via `run_command`, so **the report and its `.done` marker are correct while
  `result.status` is `ERROR`**. Observed: cycle 22 pass B — `status: ERROR`, and its report scored
  `GATE: FAIL must=2` on two findings I independently verified as real.
  Two consequences: the `.tmp`+`mv` advice is counterproductive on the agy surface and should be dropped
  or made surface-conditional; and **`result.status` must never gate an audit** — read the `.report.md`
  and the `.done` marker.
- **An audit pass that made no tool calls audited the prompt, not the codebase.** Not a defect, a
  scoring caveat worth a line in the skill: across 8 passes, *every* substantive finding came from a pass
  with either high thinking tokens or ~34 tool calls. Cycle 21 pass A ran **0** tool calls and returned
  "CLEAN PASS" on a plan that pass B proved defective. Cycle 24 returned a double-clean with thinking
  collapsed to 6.2 k / 4.4 k (vs 11–23 k in all six earlier passes) and 2 tool calls each — exactly the
  `write_to_file` and the `.done` marker, i.e. no reads. Consider surfacing thinking-tokens and
  tool-call count next to the gate verdict so a hollow pass is visible without opening the NDJSON.

## Next Steps

1. **Claim it** — `python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py /Users/kimhawk/orca/skills/docs/.bkit-memory.json --feature audit-dispatch-contract-integrity --claim "<your-session-id>"`. Plain `--claim`; nothing is held.
2. **D-2 first — it is a two-line fix with a direct unit test.** `scripts/h_mad_audit_gate.py`, `_count_section_findings`: normalise trailing punctuation before the `== "none"` comparison. Test with a report whose sections read `None.`, `None`, `- None`, and `None .` — the first three must score 0 and the fail-safe must still count a real prose finding.
3. **D-3 next — drop or condition the `.tmp` + `mv` advice** in the report-file section emitted by `scripts/h_mad_assemble_audit.py`, and add the `result.status` caveat wherever the skill tells an orchestrator how to verify a dispatch.
4. **D-1 last — it is the largest.** Emit the output-framing block at the head of the assembled prompt as well as the tail. Prototype below; the real fix should live in the assembler so every caller gets it.
5. **Optional (the caveat above)** — surface thinking-tokens + tool-call count alongside the gate verdict.

## Open / Blocked Items

- **All three defects — status: not started, unclaimed.** `repo: /Users/kimhawk/orca/skills · branch: main · worktree: none (main worktree)`. State file: `/Users/kimhawk/orca/skills/docs/.bkit-memory.json`.
- **Evidence is in a volatile scratchpad.** `/private/tmp/claude-501/-Users-kimhawk-orca-HemaSuite/a7f5968f-2f3a-4659-b527-e074a50edeea/scratchpad/audit_gec_implplan_cycle2{1,2,3,4}_{A,B}.{txt,out,ndjson,report.md}`. `/private/tmp` does not survive indefinitely — everything needed to act is inlined in this brief, and the reproduce steps below regenerate it from scratch.
- **Not verified by me**: that the D-1 fix belongs in `h_mad_assemble_audit.py` rather than the prompt template. I used a wrapper because the assembler exposes no contract-position knob (`--help` shows only `--template`, which is the shared rubric and not something I would change from a consuming repo).

## Context for Next Session

**Files this work will touch (in `/Users/kimhawk/orca/skills`):**
- `h-mad/scripts/h_mad_audit_gate.py` — D-2, `_count_section_findings`
- `h-mad/scripts/h_mad_assemble_audit.py` — D-1 (head-emit) and D-3 (report-file advice)
- `h-mad/SKILL.md` and/or `h-mad/references/` — D-3's `result.status` caveat, and the hollow-pass caveat

**Reproduce (from HemaSuite, which is where the large prompts exist):**
```bash
cd /Users/kimhawk/orca/HemaSuite/hematology-paper-writer
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
SP=<some scratch dir>

# baseline — assemble WITHOUT head-duplication and dispatch; expect the contract to be dropped
python3 ~/.claude/skills/h-mad/scripts/h_mad_assemble_audit.py \
  --feature grounding-evidence-coverage --phase impl-plan --cycle 99 --project-root "$PWD" \
  --out "$SP/tail_only.txt" --report-file "$SP/tail_only.report.md"
hmad-dispatch exec agy "$SP/tail_only.txt" --cd "$PWD" \
  --out "$SP/tail_only.out" --log "$SP/tail_only.ndjson" --timeout 1800
python3 ~/.claude/skills/h-mad/scripts/h_mad_audit_gate.py "$SP/tail_only.out"   # expect GATE: INVALID

# D-2, no dispatch needed — a two-line repro
printf '## Summary\nx\n\n## Must-fix\nNone.\n\n## Should-fix\nNone.\n\n## Nit\nNone.\n' > "$SP/dot.md"
python3 ~/.claude/skills/h-mad/scripts/h_mad_audit_gate.py "$SP/dot.md"   # BUG: FAIL must=1 should=1
printf '## Summary\nx\n\n## Must-fix\nNone\n\n## Should-fix\nNone\n\n## Nit\nNone\n' > "$SP/plain.md"
python3 ~/.claude/skills/h-mad/scripts/h_mad_audit_gate.py "$SP/plain.md"  # PASS — same content, no period
```

**D-1 prototype** (what I ran; lift the head-emit into the assembler rather than shipping this wrapper):
```python
ANCHOR = "Output framing (mandatory"
BANNER = (
    "!!! READ THIS BLOCK FIRST AND OBEY IT LAST !!!\n"
    "This is the OUTPUT CONTRACT. It is repeated verbatim at the end of this prompt.\n"
    "Your reply is machine-scored: a report that omits the sentinels or the exact\n"
    "`## Summary` / `## Must-fix` / `## Should-fix` / `## Nit` headings is scored\n"
    "INVALID and discarded no matter what it says. Do NOT invent your own verdict\n"
    "line. Re-read this block before you write a single word of your report.\n\n"
)
body = raw.read_text()
i = body.find(ANCHOR)
assert i != -1, "anchor not found — assembler changed"
contract = body[i:]                      # lifted verbatim, so the per-pass report path stays correct
assert f"{stem}.report.md" in contract, "report path missing from contract slice"
out.write_text(BANNER + contract +
               "\n\n====== END OUTPUT CONTRACT — the audit prompt begins below ======\n\n" + body)
```
Both asserts are load-bearing: hand-writing the contract instead of slicing it would hardcode a stale
report path, and the anchor is the only thing tying the slice to the assembler's current output.

**Evidence table (8 passes, cycles 21–24):**

| cycle | pass | duration | thinking | tool calls | gate |
|---|---|---|---|---|---|
| 21 | A | 100 s | 11,230 | 0 | INVALID (contract dropped) |
| 21 | B | 193 s | 15,786 | 34 | INVALID (contract dropped) |
| 22 | A | 189 s | 22,956 | 2 | FAIL should=1 |
| 22 | B | 131 s | 14,555 | 4 | FAIL must=2 — `result.status: ERROR`, report correct (D-3) |
| 23 | A | 126 s | 15,315 | 2 | PASS |
| 23 | B | 190 s | 15,289 | 34 | FAIL must=1 should=1 — **false**, the `None.` artifact (D-2) |
| 24 | A | 62 s | 6,248 | 2 | PASS (hollow — no reads) |
| 24 | B | 47 s | 4,429 | 2 | PASS (hollow — no reads) |

**Uncommitted changes in the target repo at handover:** `hooks/h-mad-advisor-gate.sh` (modified, pre-existing — not mine, not touched).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short --branch
python3 ~/.claude/skills/h-mad/scripts/h_mad_resume_decision.py \
  --state docs/.bkit-memory.json --feature audit-dispatch-contract-integrity \
  --session-id "<your-session-id>"        # expect start_fresh
```

**Related docs:**
- HemaSuite plan `docs/01-plan/features/grounding-evidence-coverage.impl-plan.md` v1.34–v1.37 — the full narrative, including the withdrawal of the size/J30 attribution at v1.36 and the effort table at v1.37. Commits `1c616e60`, `6443abed`, `4aa1ad25`, `f520d43c` on `feature/201-grounding-evidence-coverage`.
