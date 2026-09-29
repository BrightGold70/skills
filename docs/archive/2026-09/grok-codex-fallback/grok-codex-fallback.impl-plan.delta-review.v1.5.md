## Summary
ADVISORY delta review of impl-plan v1.4 → v1.5.1 (`aaf796eb..c0ab18e2`). I checked it against the committed Task 12 code at `0d6088bc`; the plan is byte-identical between `c0ab18e2` and `0d6088bc` (`git diff --quiet` rc 0). Everything was run in a scratch `git clone --shared` at `…/scratchpad/wr1`; the worktree was never edited.

Answers to the four dispatch questions:
- **(1) The registry move runs as written.** Output: `WIREPIN: PASS tasks=17 wiring=8 unpinned=0 mislabeled=0`, `registration: registered=14 skipped=0`, `TOMBSTONE: OK`. The registry then holds 40 records, 15 of them grok. The 12 records of Tasks 3–11 changed only `registered_ts`. `Task 12` gained exactly `status`/`removal_provenance`/`removed_by_feature`/`successor_pin`. `(WIRE 1)` and `(WIRE 2)` were added.
  - `verify --base 8ef6009f` does **not** pass, either before or after the move. It read `FAIL registered=38 verified=34 … missing=4` before and `FAIL registered=40 verified=36 … missing=4` after. All 4 are `multi-host-runtime` records whose test files do not exist; they were inherited from `8ef6009f`. The move itself adds no driver.
  - The move was never committed. Neither `b190f01d` nor `0d6088bc` touches `.h-mad/wires.jsonl`, even though the plan requires it in the RED commit.
- **(2) The Task 16 bounds match the committed state.** `numstat` against `8ef6009f` reads `5 0` / `5 0` / `1 1` / `1 1` / `3 3`. I extracted steps 3 and 3b verbatim and ran them under both bash and zsh: every arm printed `count=N/N rest_equals_base=True`, then PASS.
  - `grokfixtures.py` is not tracked at base, so it is outside the allowlist; only 3b bounds it, and 3b passes.
  - Migration 3 changes only the three `replace` strings.
- **(3) Every find in the G1–G12, WR12-1 and WR12-2 rows occurs exactly once** in the committed files (14 of 14; unit: occurrences via `str.count`, with `⏎`→newline and `\|`→`|`). Every replace occurs 0 times. All 19 test names the plan cites for this test file exist exactly once as `def`.
- **(4) Four of the five v1.4 shoulds closed as classes. The registry should did not close:** the plan now carries a correct procedure, but it has not been executed.

I also re-ran the RED and GREEN results in the scratch clone:
- RED (`b190f01d`): `64 failed, 128 passed`.
- GREEN (`0d6088bc`), the fallback-agent test file together with both migrated test files: `385 passed`.

Evidence: 14 files opened, 24 greps run (plus 1 scratch registry move, 2 `verify` runs, 2 Task 16 step-3/3b runs under bash and zsh, 2 pytest runs, 1 find-count script).

## Must-fix
- [must] Task 12's registry AC is unmet, and as written it cannot be met: its commit slot is already in the past. The plan says Task 12 runs the move "as its first step" and commits `.h-mad/wires.jsonl` "in its RED commit". Both RED (`b190f01d`) and GREEN (`0d6088bc`) are committed and neither touches the file (`git diff --stat c0ab18e2 0d6088bc -- .h-mad` is empty). The worktree registry still has 38 lines, 13 of them grok, and line 38 is the stale v1.3 `Task 12` record naming a gate block that no longer exists. So Task 12 is not "implemented" in full. WIRE 1 (`format_state_line` → `_fallback_fold`) is still unregistered, and 5f will not re-verify it. The procedure itself is sound (dry-run above). Only its placement is wrong. Two repairs would work, and neither was executed on the tree:
  - (a) amend §"Wire registry move" and the AC to "a follow-up commit after GREEN, before Task 14", then run the two blocks verbatim; or
  - (b) fold the move into Task 14's first step.

  Under either repair, record the expected post-move `verify` token (next item).
  class: build
  quote: docs/01-plan/features/grok-codex-fallback.impl-plan.md › `` `renamed`. Task 12 runs both steps from the worktree root, as its first step, and commits ``

## Should-fix
- [should] `h_mad_wire_registry.py verify` reads FAIL before and after the move, and the plan never states this. The failures are inherited, not caused by this feature. Measured in the scratch clone at `0d6088bc` with `--python /opt/anaconda3/bin/python`: `WIREREG: FAIL registered=40 verified=36 broken=0 missing=4 ambiguous=0 unverified_renames=0 undeclared_removals=0`. The drivers are `step5f:wire_pin_missing:multi-host-runtime::Task 5`, `::Task 6`, `::Task 7 (WIRE 1)` and `::Task 7 (WIRE 2)`. Their pins are `h-mad/tests/test_h_mad_host_declaration.py` and `test_h_mad_install_check_roots.py`, and neither file exists at `0d6088bc` or in the main checkout. The records came from `6156a2dc`, an ancestor of `8ef6009f`. All 15 grok records verify (unit: records; 36 verified = the 34 verified before the move + 2 new).
  - A 5f operator who reads that FAIL will attribute it to this feature.
  - Prescription: name the inherited FAIL and its 4 drivers as the expected 5f result. Or state that 5f judges the `grok-codex-fallback::*` records only.
  - `verify` needs a pytest interpreter. Bare `python3` here is homebrew 3.14 without pytest, and gives `UNREADABLE: pytest collection failed`.
  - Unverified: whether the multi-host records should be repaired upstream. That is outside this plan.
  class: measurement
- [should] The test census was not updated by the v1.5.1 erratum. The Version History entry then says nothing else changed.
  - Task 12's split is now 64 / 128 (line 1830), and I reproduced it: `64 failed, 128 passed` at `b190f01d`. The census still sums Task 12 as `63` failing and `129` passing, and totals `187` / `186`.
  - Correct totals: 188 failing, 185 passing (unit: collected items; 373 unchanged).
  class: measurement
  quote: docs/01-plan/features/grok-codex-fallback.impl-plan.md › `Task 13 23, Task 15 7 — total 373, of which 187 fail at RED and 186 are regression guards or`
- [should] The plan's commit placement for migrations 3 and 4 disagrees with what was committed. The plan says all migration edits "land in the RED commit". Migration 3 (`claude_gate_judge_wiring.json`, `3 3`) and migration 4 (`grokfixtures.BASE_SHA`) landed in GREEN `0d6088bc`; RED `b190f01d` carries migrations 1–2 only (its subject line says so).
  - GREEN is arguably the correct slot for migration 3. It moves together with the ERE, which is merged §D13 item 5's "in the same commit".
  - The line 1725 note "Not yet done at `6277d703`" is now also stale.
  - Prescription: record the executed placement (1–2 RED, 3–4 GREEN) and why.
  class: measurement
  quote: docs/01-plan/features/grok-codex-fallback.impl-plan.md › `**Migration edits** (committed files outside the test file; all land in the RED commit, because`

## Nit
- [nit] "landed literally" does not hold for the gate block's comment. The plan's code block has a 5-line comment above `if [ "$FALLBACK" != none ]` ("…this block checks only that the fold's kind agrees with that record's tag, and applies no rule over the records of its own."). The committed hook has a single line instead: `# fallback_agent (FR-2): codex-authorship has already refused every case where codex is available.` The code, all `# M:` markers and every anchored line match byte for byte. Either sync the plan to the tree, or say the comment is not literal.
- [nit] The tag-agreement paragraph calls the check "the third member of the class 'a line-level summary field that names a record', beside … `codex-escape`-against-`blocker`". The closest literal sibling is not checked: `blocker=N` names a record, but the gate never checks that record's status subfield against `ESCAPE_STATUSES`. `BLOCKER_RECORD` is used only for its key and file (`h-mad-tdd-gate.sh:196–197` at `0d6088bc`). That code belongs to the merged feature and is out of this plan's scope. Stating the member as a residual would keep the class claim honest.
- [nit] Task 16's narrowed arm checks the stated text, its count, and that the rest of the file equals base. It does not check *where* the text sits. For example, it would accept ` fallback=none` inserted into a `find` rather than a `replace` of `claude_gate_judge_wiring.json`. Spec AC-11.1 says "only the `replace` strings". In practice `--check-anchors` or the suite would catch any such misplacement, but the arm itself does not. A one-line residual would be enough.
