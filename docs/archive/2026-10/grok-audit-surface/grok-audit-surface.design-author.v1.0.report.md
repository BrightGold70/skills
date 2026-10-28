DESIGN-AUTHOR: DONE version=v1.0 path=docs/02-design/features/grok-audit-surface.design.md lines=516 sha256=cb0c5cf70f133ba4b5e6a00c42d05b10b40fd56c141378dae16a4fe9f5a335f3

# Report: grok-audit-surface design v1.0 (first draft)

File: /Users/kimhawk/orca/skills/docs/02-design/features/grok-audit-surface.design.md (new, untracked, not committed).
Precheck: `PRECHECK: PASS issues=0`. DOC-SHAPE: PASS. VERSION-HISTORY: OK v1.0 (tool, append).
Advisories kept on purpose:
- PATH "does not exist yet": every one is a file this feature creates, or a harness path relative to `h-mad/` (`scripts/…`).
- COUNT on the ledger-fields line: it lists nine fields and says nine; the checker misreads it.

## Obligation → design section
Derived from the plan's lines with "design pins / names / enumerates / confirms" (grep run), spec AC-1.7 and AC-2.6, and the brief's seven items.
- MISS-branch test of §Never gate (plan Ordering) → D14 (DECISION: yes, a content pin), Doc pins
- Test module names, FR-8/9/10 placement, fixture layout and must-not-refuse fixtures → Components, Test Plan
- Final consumed-verdict list, with the token or function per member → D10 (M1–M6, plus the excluded items with reasons)
- Prompt retention under HMAD_AUDIT_STEM_DIR, token-line recording, per-member pairs → D3, D8, D10 (brief item 3)
- Vocabulary injection, smoke command line, truncated vs vocab_missing:end → D2, D11
- Mode names and command lines, fetch_failed vs ref_absent, ancestry, calibration layout → D2, D3, D9 (brief items 1, 2)
- Mutation rows' find strings and tests → Test Plan, "Mutation spec" (W1–W8, G1–G5, C1–C3, K1–K3, P-rows)
- Interpreter and the place Phase 5e runs → mutation spec (brief item 5)
- Exclusion-list path, and list version → D5
- Root parent directory → D5 ($TMPDIR mkdtemp); the reach check is the evidence
- AC-3.4 stands rule → D12 (the whole v2 stands for every surface); AC-10.1 maps by pass index → Wrapper pins (brief item 4)
- git ls-files command for fixture names → Test Plan, Fixture names; Readings
- Root builder, list format, normaliser, mutation-spec file (Next Steps 2) → D5, D6, Test Plan
- SMOKE component (spec AC-1.7) → D11
- Own-source exemption (spec AC-2.6) → D5 step 4, D6
- Delta-review should-fixes (brief item 6):
  - R12 per branch → W7/W8 plus a new identical-prompts test and a stub knob
  - `_leg_key` → G1 (`dict.fromkeys`, deterministic)
  - S1 by-products → D8 kept dir, D9 smoke commit
  - S0b work tree → D9 `commit-data` (plumbing, temp index, no checkout)
  - kept-pin stages → K1–K3
  - list-version refusal → D5 (recorded `list_blob` and a `LIST:` line; no refusal, because the spec is closed)
- Opposed-fixture rule for every token-read check (brief item 7) → D10. Each pair is checked against its authority when the fixture is built.

## Decisions (design-author), all marked in the document
1. The source list is the `SOURCES` constant plus a `--sources` CLI override for fixtures, because the probe dir allows only the probe and the list.
2. Every non-smoke refusal is spelled `SEEDSCORE: UNREADABLE reason=…`, in every mode.
3. AC-2.3 placement violations refuse as `seed_rebuild`.
4. One fresh root per cycle; S1 shares one root (`d1`, cycles 1/2/3). That means ten or more roots, not the plan's "9 + smoke root".
5. The exclusion list is fail-closed on its own grammar. An unknown directive refuses `leak:exclusions.txt`.
6. `name-contains grok-audit-surface` is a superset of "begins with"; it also removes 2 handoffs that "begins with" misses.
7. The smoke commit carries the S1 by-products on PASS and on FAIL.
8. `delivered=out` (extracted from the final message) counts as `no_delivery`.
9. Extra cycle-record failures share `cycle_token`: v2 missing, unexpected v2, v3, bad `--surfaces`, a missing collected report.
10. A HIT naming a seed of another document is `label:<id>`.
11. `seeds_undetected` outranks PASS and MISS.
12. MISS uses `reason=bar_missed`.
13. There is no catch-all UNREADABLE reason. An unmapped exception exits 2 with no token.
14. The new test modules go in new files and import the existing helpers.
15. G4 force is "the refusal always fires", because the plan's force row duplicated its remove row.
16. The K3 (AC-7.3 kept pin) row is written at S0 over today's text.
17. The interpreter is the absolute `/opt/anaconda3/bin/python3.11`.

## Premises verified (command → result)
- `command -v python3.11` → `/opt/anaconda3/bin/python3.11`. Then `python3.11 -m pytest --version` → pytest 9.1.1. The binary is dated Aug 2024.
- `python3.14 -m pytest --version` → No module named pytest. `python3` (3.15) has pytest 9.1.1.
- R13 re-derived over the spec JSONs: 166 bare `python3.11`, 9 `/opt/anaconda3/bin/python3`, 2 `/opt/anaconda3/bin/python3.11`, of 177. Every root is `../..`.
- `ORIGINS`: 8 members (sed on `h_mad_audit_origins.py`). `_GROK_TYPES` and `_GROK_TYPES_RE`: the same 7 types (grep).
- `_cmd_audit_cycle`, from sed/grep over the function:
  - stem dir is `${HMAD_AUDIT_STEM_DIR:-/tmp}` and must be an absolute existing dir without ':'
  - `--project-root` is required; default `timeout="900"`
  - the agent map is `agent[$i]="${_surf[$((i - 1))]}"`; legs default is `legs=("${_surf[@]}")`
  - the divergence check is `if [ -z "$div" ] || [ "$foreign" -ne 0 ]`, with foreign = `grep -c '^[<>]'`, so an empty diff gives foreign=0
  - passes run in the background (`) &` then `pids[$i]=$!`); `exit 4` follows the assemble checks
- `h_mad_audit_cycle.py`:
  - the collected path is `<root>/docs/0X/features/<f>.<phase>.audit.v<N>.p<i>.md`, with `.effort.json` beside it and logs copied to `<root>/.h-mad/pass-logs/`
  - `delivered` takes the values `report-file`, `out`, `none`, `unscorable:…`
  - the Effort item spells `format=grok`, or the "grok log truncated" text
  - the anchors for `combine` and the floor loop were grep-checked
- No `COLLECT:` print in `h_mad_audit_cycle.py` (2 hits, a docstring and a comment); it is printed by `h_mad_collect_report.py`.
- Gate:
  - `_leg_key`, `exit_check` (`legs_disagree`, `legs_changed`), `round_check` (`grouped.add(key)`) read via sed
  - `--exit-check` and `--round-cap` exist
  - `h_mad_audit_gate.py <report>` prints `GATE: PASS must=0 should=0` (scratch report, deleted)
- Every mutation `find` anchor gives `grep -cF` = 1. The whole Readings block of the design was executed and reproduced.
- `probe_readers` needle and boundary (sed). The harness accepts `file: ../…` (precedent `host_runtime_docs.json` → `../handoff/SKILL.md`), and `target_command` is optional.
- `git ls-remote --exit-code`: missing ref 2, missing remote 128, missing URL 128 (scratch bare repo, deleted).
- A mktemp dir and `$HOME/.local/state` are both outside any work tree (rev-parse fails). Note: `mkdir -p $HOME/.local/state` ran, which is a no-op if the dir already exists.
- Fixture-named files under `h-mad/tests/`: 0. R10: 1 occurrence over 32 files.
- `--surfaces agy,grok` in SKILL.md: 2 occurrences. The K2 and K3 anchors are unique.
- Extractor vs `classify`: a scratch probe of 5 shapes found no disagreement, so the `must_count_mismatch` fixture injects the counter (D12).

Sweep, for the stated counts "eight modes / five new test modules / six entries / three key decisions / 11 committed": `grep -n -o` over the design; each spelling agrees with its list. Probes deleted: the scratchpad is empty and `git status` shows only the design.

## Tree contradicts brief or plan
- Brief and plan R13 say `python3.11` is absent. It is present at `/opt/anaconda3/bin/python3.11` in this shell; the earlier "absent" was a PATH condition.
- Plan Convention Prerequisites name python3.14 as the test interpreter, but it has no pytest. `python3` (3.15) now has pytest. The plan's claim is the reverse of the tree.
- The memory file `python-interpreters-this-mac.md` named by the brief does not exist.
- The delta review said `/opt/anaconda3/bin/python3.11` is absent ("ls failed"). It exists now.
- The plan's AC-3.2 observation of "byte-identical prompts" through `install_audit_cycle_stubs` cannot be reproduced with the shipped stub: it always writes the report path, and it has no knob for that. The design adds `HMAD_ASSEMBLE_SAME_REPORT_P<i>`.
- `COLLECT:` is never printed by audit-cycle, so spec AC-1.7's input list names a line that path cannot produce. The design reads `delivered=` instead.

## Owed elsewhere (not edited)
- Spec author:
  - AC-5.4 should name placement violations (AC-2.3); the list-version refusal (e.g. `list_changed:<oid>`); and the extra cycle-record cases under `cycle_token`.
  - AC-3.6 should cite the list commit.
  - AC-1.8 should admit the smoke-commit citation.
  - AC-5.3 should state that `seeds_undetected` takes precedence.
  - AC-2.7 should list the reports, logs and prompts explicitly.
  - AC-1.7 should not list `COLLECT:` as an input on the audit-cycle path.
  - Optional restamp to the new shas.
- Plan author:
  - Convention Prerequisites interpreter (python3.14 has no pytest).
  - R13 "absent".
  - The S0b root count (now ten or more roots).
  - G4's force wording.
  - Old shas (see the sha-remap).
- Impl-plan: confirm the `_cmd_exec` stub delivers a report for all three surfaces, so that AC-10.2 stamps exist (a stated residual).

## Declines
None. Not committed (per brief).
