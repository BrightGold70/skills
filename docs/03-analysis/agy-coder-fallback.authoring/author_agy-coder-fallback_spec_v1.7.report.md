SPEC-AUTHOR: DONE version=v1.7 path=/Users/kimhawk/orca/skills/docs/01-plan/features/agy-coder-fallback.spec.md lines=1016 sha256=390c4771de0fad45363c485845b3aef554fbb86ebf7b39b54f35edc1ab95d901

Pre-write assertion: sha256 e65dd606… and newest VH `- v1.6` matched at start (mtime 1792134328). No concurrent writer was seen on the spec.

premises verified:
- h_mad_state_write.py `_utc_now`: `grep -n -A4 'def _utc_now'` -> `datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")`. `started_ts` uses the same form.
- Python datetime refuses second 60: `datetime(2016,12,31,23,59,60)` and `fromisoformat('2016-12-31T23:59:60+00:00')` -> `ValueError: second must be in 0..59, not 60` (run, python3).
- `agy --version` -> 1.4.0, run at HEAD 200ffd52.
- h-mad/scripts/h_mad_target_identity.py exists. The Codex gate imports it (`grep -n target_identity hooks/h-mad-codex-tdd-gate.py`: lines with `from h_mad_target_identity import Identity` and `import_module("h_mad_target_identity")`).
- test_codex_gate_judge_timeout_reason copies only the gate, a judge stub and h_mad_target_identity.py into tmp tree B (checked with sed on the test). This confirms D-12's reason.
- codex_status schema description says "blocked when Codex is available" and "permitting Claude to write the fallback". state-schema.md row says "permits a Phase-5 authoring fallback". Both read with grep.
- No test pins the codex_status text: `git ls-files h-mad/tests | xargs grep -l '<4 phrases>'` -> 0 files (rc=1).
- Order pin: test_fallback_agent_description_states_the_four_facts asserts `index(fallback_agent) == index(codex_status)+1`. This is now stated in FR-1.
- SessionStart: `grep -n SessionStart h-mad/references/agy-runtime.md` at 200ffd52 -> 2 matching lines (§Hooks, §Construct mapping). Unchanged.
- S2 premise: the spec did NOT say the author comes from implementer_switch. `grep -n implementer_switch` hits only FR-1 fields, FR-2 --record, FR-7 unrecorded-fixture scope and AC-7.2. Only the design (v1.0) attributed from `implementer_switch.to`. So FR-7 got a clarifying Attribution bullet that closes the ambiguity. The rule itself did not change.

findings applied:
- S1 (C1) -> FR-1 field bullet ("narrowed to seconds 00–59"), a new FR-1 sub-bullet "A leap second is refused too (D-14)" with its reason and residual, AC-1.2 gains fixture `2016-12-31T23:59:60Z` on both paths, AC-1.1 notes the narrowed profile, and the decision D-14 was added. Note: the .ts fixtures live in AC-1.2, not AC-1.1, so both were amended.
- S2 (C6) -> new FR-7 bullet "Attribution". An entry's implementer is the author of the reviewed code, taken from its successful implementation dispatch. It is never taken from implementer_switch.to or from `implementer`. A worked example is given. For multi-author code the entry is non-independent if the reviewer is any of the authors.
- S3a -> FR-1 gains a codex_status description bullet (both surfaces, Pinned subsection). FR-10 state-schema bullet now names all four rewritten surfaces. AC-1.1 checks the codex_status rewrite.
- S3b -> FR-8 "Version" bullet: 1.4.0 at 200ffd52, every reading stamps its version, and a reading from a different version is re-taken. The Owed SessionStart item was re-stamped from 1.3.6 / 17d73037 to 1.4.0 / 200ffd52.
- S3c -> FR-6 and AC-6.1: "shared module" = h_mad_target_identity.py (D-12).
- S3d / OQ-B -> FR-8 "When it runs (D-13)" and AC-8.1: post-merge stage, with COMPLETE only after AC-8.1 and AC-8.2 pass.
- OQ-A and OQ-B are recorded as D-12 and D-13 (operator, 2026-10-16). The Open questions line now says they are settled.

values swept:
- `grep -n 'shared module\|1\.3\.6\|1\.4\.0\|leap\|:60\|D-1[234]\|OQ-[AB]\|description'` over the whole spec, including fences, tables and VH. Results: every "shared module" site is bound by the FR-6 definition sentence. The only remaining 1.3.6 is the deliberate "earlier readings saw 1.3.6" in FR-8. 17d73037 stays in FR-3 (a separate measurement, not touched).
- No measured value changed, so there are no derived figures to move.

contradictions found: none between the spec and the decision sheet. Design C6/AC-7: the spec does not choose where attribution is computed (code or procedure).

placeholder scan: `h_mad_precheck_doc.py --phase spec` -> PRECHECK: PASS issues=0. Advisories were kept on purpose. The PATH advisories point to files this feature creates (`h-mad-agy-tdd-gate.py`, `.agents/hooks.json`), to `.codex/hooks.json` (the spec says this repo has none), and to a HemaSuite archive path. The COUNT advisory is on L1015, which is the pre-existing v1.6 VH line. `h_mad_ac_census.py` -> ACS: OK count=19 frs=9.

owed by other documents:
- Design: cite FR-1/D-14 for the leap-second refusal and drop the "Residual" framing (C1). FR-7 attribution must follow the spec's Attribution bullet, not `implementer_switch.to` (C6). If the design computes attribution in code, the plan needs a fixture: a stored switch.to=agy with a Codex-authored review target gives implementer=codex, and a Codex reviewer gives independent=false. FR-1 schema edits must keep fallback_agent directly after codex_status.
- Plan: mirror D-12, D-13, D-14 and agy 1.4.0 (P3/P4). Add the leap-second fixture to the AC-1.2 task. Add codex_status description/row rewrite tasks.
- Impl-plan (later): the AC-1.2 leap-second fixture runs on both validator paths.
