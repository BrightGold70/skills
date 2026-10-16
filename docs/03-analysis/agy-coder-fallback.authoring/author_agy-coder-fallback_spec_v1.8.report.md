SPEC-AUTHOR: DONE version=v1.8 path=/Users/kimhawk/orca/skills/docs/01-plan/features/agy-coder-fallback.spec.md lines=1124 sha256=1d2a34425f232994cd20246436f7e2fd031814ddf0badd6981d48a81ce8c0564

Ownership check before the first write: sha256 390c4771de0f... and newest VH v1.7, both matched the brief. No other author touched the file; the only changes are mine (git diff: 1 file, +120/-12).

premises verified (tree at cff71b49):
- h-mad/hooks/h-mad-codex-tdd-gate.py `_any_phase5_status`/`_state_status` (sed -n 143,166p): three values. `active` wins over `unknown`. `unknown` = OSError/UnicodeDecodeError/JSONDecodeError or non-dict orchestrator_state.
- Same file, `_deny(` call sites (a python scan of each call's argument text): 13 call sites; 6 have no `kind=` (the shell-unknown, shell-allowance, disallowed-command, no-target, outside-or-unreadable and SA-GUARD denies). This means the design's claim "unknown denies judge-error as the Codex gate does for a shell command" is false (E6).
- Same file, `_main_guarded`: a root that is not canonical but can be entered scans, and `inactive` allows (`return 0`). That confirms design difference 4.
- Same file, the `for raw in targets:  # M:G5` loop: `read_chain` runs whatever the scan reads. Its test `test_unsearchable_docs_on_the_chain_denies_although_the_scan_is_inactive` exists in h-mad/tests/test_h_mad_codex_tdd_gate_judge.py.
- h-mad/scripts/h_mad_tdd_judge.py: `Verdict.kind` exists, so the judge's kind is a real source.
- h-mad/SKILL.md (grep): `5d` is RED and `5e` is GREEN. The heading is "## Phase 5 (Implementation) sub-steps". This confirms E4.
- python3 3.15.0: both leap-second calls raise 'second must be in 0..59, not 60'. S3 keeps only the prefix, as the brief asked.
- Spec §Terms "Active step5" is chain-based. The new activity paragraph is written as two layers (scan, then chain) so that it does not contradict Terms.

findings applied:
- S1/E6: new FR-4 paragraph "Every deny carries a kind". It states the rule over every deny path; the closed list is the design's. The spec names only judge-error, tool-not-admitted and the judge's Verdict kind. It records the Codex gate's 6 of 13 kindless denies as a deliberate difference. AC-4.2 gains one fixture per deny path that asserts one kind from the list.
- E1 (spec side): new FR-4 paragraph "The activity reading". Every step5-gated deny also fires on `unknown`. A class-(b) production .py is still read through read_chain under `inactive`. The workspacePaths and "Tool classes" sentences are reworded to match. The FR-6 intro now states that the unknown-scan shell deny refuses every command. AC-4.1 is rewritten: an inactive exception (the chmod-000 docs/ chain), `unknown` fixtures, and the target differential.
- E5 (spec side): FR-4 "Target keys": a recognised key whose value is not a non-empty string counts as no path key, and "" is never canonicalised. AC-4.1 adds a `""` case.
- S4: ADOPTED. New FR-4 list "Deliberate differences from the Codex gate": the design's 4 items, plus the kind rule as a 5th. Each one either fails toward refusal or is forced by agy's payload, and none weakens a Codex refusal. Residual stated: later Codex rules are not inherited, and the differential catches that.
- S5: ADOPTED. When the reviewer is none of the authors, `implementer` = the author of the latest accepted implementation dispatch. Reason: the schema holds one agent, the choice changes no `independent` value, and "latest" can be decided.
- S2/E2/E4: FR-7 Attribution gains three sub-bullets: GREEN + accepted fixes and never 5d RED; the S5 rule; the complete author set, never a projection, with the unrecoverable case giving no entry and its residual. New AC-7.3 has four fixtures (switch, multi-author recovered, RED-not-author, rejected-not-author), each with its mutant.
- S3: the ValueError quote now ends at "0..59", with a note that the tail depends on the Python version.

values swept:
- "step5 active" wording: grep -n 'During active step5\|during active step5\|step5 inactive' found 3 remaining. FR-6 intro is amended. The subagent-arming note and the FR-8 tracer step are descriptive, not deny rules, and are left as they are.
- "same rules as the Codex gate": grep shows only the class-(b) table cell. The new differences list qualifies it, and the cell is unchanged.
- kind tokens: grep -n -o 'kind=[a-z-]+' gives only judge-error and tool-not-admitted as distinct values, so no design-owned kind is named.
- "not 60": grep gives 0 hits after the edit.
- AC count: h_mad_ac_census went from 19 (v1.7, git show HEAD) to 20 (v1.8): AC-7.3 added.

contradictions found:
- Design v1.1 §FR-7 says "the GREEN dispatch the orchestrator accepted at 5d". The tree says GREEN is 5e. The spec follows the tree (E4); the design owes the fix.
- Design v1.1 step 6 says the Codex gate's `unknown` shell deny is judge-error. The tree says it has no kind (E6).
- E2 vs FR-1: FR-1's `review_independence` entry has no author-set field. If the design's E2 mechanism needs one, FR-1 must change. This revision adds no field (round cap, no new scope). It is flagged in Owed.

placeholder scan: PRECHECK: PASS issues=0. All 13 advisories are already in v1.7 (13 there too, measured on git show HEAD): 12 are PATH advisories for new or not-yet-created files, and 1 is a COUNT advisory inside the v1.6 VH line. All are kept deliberately. ACS: OK count=20 frs=9. VERSION-HISTORY: OK version=v1.8 placement=append. After that I appended one clause ("FR-6 states the unknown-scan shell deny") to my own v1.8 entry, then re-ran the precheck: PASS.

owed by other documents:
- Design: enumerate the closed kind list and assign every deny path a kind (E6). Correct the "as the Codex gate does" kind claim. Name where the complete author set is kept (E2). Change 5d to 5e (E4). If E2 needs an entry field, the spec's FR-1 must gain it in a later revision.
- Impl-plan: give AC-7.3 a code surface; if attribution stays orchestrator prose only, file an OPEN-DECISION. Add the AC-4.1 `unknown` fixtures and the AC-4.2 kind fixtures for each deny path.
- Plan: mirror AC-7.3 (stage 7 already carries the switch fixture; it needs the E2/E4 cases too).
