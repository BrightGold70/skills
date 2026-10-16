SPEC-AUTHOR: DONE version=v1.1 path=/Users/kimhawk/orca/skills/docs/01-plan/features/agy-coder-fallback.spec.md lines=470 sha256=d92cfe3cbea4639f6dbc715e636685c2828b76738009c8bfbee37ea00bf8d0c5

premises verified:
- pre-write ownership: shasum = 0403a5469af4…0662 (matches d65374e9); newest `- v1.` line was v1.0. Proceeded.
- `.git/info/exclude`: `grep -n agents` -> one entry `/.agents/skills/` (no bare `/.agents/` left).
- `git check-ignore -v .agents/hooks.json` -> no output, rc=1 (not ignored).
- `git check-ignore -v .agents/skills` -> `.git/info/exclude:…:/.agents/skills/  .agents/skills`, rc=0 (still ignored).
- HEAD = d65374e9 (the sha the D-10 evidence is stamped at).
- FR-1 `review_independence` fields `{leg, module, reviewer, implementer, independent}` with reviewer/implementer in `codex|agy|grok|claude`: the Codex-on-Codex case is representable with no schema change.
- Linked worktrees share `info/exclude` via git's common dir: taken from git's documented repository layout, NOT probed (this checkout is the main clone: `git rev-parse --git-common-dir --git-dir` -> `.git .git`).

findings applied (orchestrator decisions; no audit reports this cycle):
- Decision 1 (OQ-1 YES): FR-7 "Rule over the axis" now says the rule covers every implementer, Codex included, with the 5e anti-gaming verifier example, warning only. Added D-9 to the decisions list as an operator decision.
- Decision 2 (OQ-2 narrow): added D-10, with the check-ignore evidence at d65374e9, "no `git add -f`", and a residual saying `.git/info/exclude` is per-clone, so other clones and other projects adopting the gate need the same narrowing. Where the file is missing, FR-5 halts `UNWIRED reason=no-hooks-file`.
- Decision 3: "Open questions for the operator" now reads "None — OQ-1/OQ-2 settled 2026-10-16."
- Version History v1.1 via h_mad_version_history.py -> `VERSION-HISTORY: OK … version=v1.1 placement=append`.

values swept:
- `grep -n 'OQ-\|git add -f\|/\.agents/'`: the remaining OQ-1/OQ-2 mentions are only in D-9/D-10 ("was OQ-n"), the empty-OQ line and Version History. The old FR-7 line "OQ-1 asks the operator…" is gone.
- `grep -n 'D-8\|eight\|8 open\|D-1\.\.'`: the only count, "8 open questions (D-1..D-8)", is in the v1.0 history entry. It is historical and correct as of v1.0, so I left it. No other surface states a decision count.

contradictions found: none.
- Open, for the orchestrator: FR-7's `review_independence_unrecorded` warning still fires only when the feature's implementer was agy. D-9 widens the flag, but not the unrecorded check. So a Codex-implemented feature with no 6a-prime entry gets no "unrecorded" warning, and no flag either. I did not change this because it was outside the decisions given. If D-9 should also widen the unrecorded trigger, that is a further operator or orchestrator call.

placeholder scan: clean. `PRECHECK: PASS issues=0` (--phase spec), re-run after the last write. There are 8 PATH advisories, all kept on purpose: `h-mad/hooks/h-mad-agy-tdd-gate.py` and `.agents/hooks.json` are files this feature creates; `.codex/hooks.json` is HemaSuite's file, named as precedent.

owed by other documents: none new. The v1.0 item (agy-runtime.md §"Hooks" SessionStart re-check) stands. The plan, design and impl-plan should mirror D-9 (Codex-on-Codex flag) and the D-10 per-clone prerequisite when they are written.
