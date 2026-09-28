## Summary
Plan v1.1 (`85d61ba8`) closes most cycle-1 findings on their own terms. I checked them against the tree:
- All four P0 heredocs hash to their pinned sha256.
- `reproduce.py` prints the 24 `REPRO:` lines P3 claims (current HEAD `6478b8b5`; `h-mad/` and `handoff/` show 0 changed files since `2f262f8a`).
- These figures reproduce: the Claude-gate census (5/5/0/9/1), the assertion census (8 of 8 and 8 of 9), the stale-prose census, P4, ANCHORS (99/907), the stamps (0 of 25), the R2 classified 7-of-16, the wire-registry probe (83/4/16/64) and the 3.9 import floor.

Four blocking gaps remain:
- **V-0 script vs spec v1.1.** The plan's V-0 script and its E1_BLOCKS branch still encode spec v1.0's AC-6.6. Spec v1.1 (`96bf1cd1`) rewrote AC-6.6.
- **Existing tests use the installed hook.** The two Claude-gate test modules run the *installed* (main-tree) hook, so the whole assertion-migration plan executes against the wrong hook in the worktree.
- **"Exactly three populations" is false.** The `_production_claims` rewrite is claimed to change output on exactly three populations; the same corpus has two more (91 matching lines). One of them drops every non-`.py` production claim.
- **Helper rewrite contradicts AC-6.6.** The plan's one-helper rewrite of every existing assertion contradicts spec AC-6.6's "(a) … stand unchanged".

Not verified: the V-1r pre-merge reading (the replay was not run) and the 7-mode fake-`claude` exercise of V-0 (the fake was deleted).
Evidence: 11 files opened, 24 greps run.

## Must-fix
- **V-0's choice rule and the plan's E1_BLOCKS branch disagree with spec v1.1 AC-6.6.**
  - Spec v1.1 says that under `E1_BLOCKS` "`exit 1` is not kept": the form is (b) if `FORM_B=BLOCKS`, else (a) rc 2.
  - The plan still maps E1_BLOCKS to `CHOSEN=rc1` in four places:
    - the embedded script's `case` (plan line 889, `E1_BLOCKS/*) C=rc1`);
    - the run-gate grep, which accepts `CHOSEN=\(a\|b\|rc1\)` (line 1044);
    - the Choice bullet (line 1066) and the offline-mode reading (line 1076);
    - the Success Criteria `(1, '', '[H-MAD-TDD-GATE] BLOCK: …')` under `rc1` row (line 1164), and the census pass condition (lines 207-209).
  - An implementer following the script on an E1_BLOCKS reading would keep `exit 1` at every site, which is exactly what spec v1.1 forbids.
  - instance of: every plan site that states the E1_BLOCKS outcome. The six sites listed above are all the members I found with `grep -n 'rc1\|AC-6\.6\|E1_BLOCKS'`.
  - Repair: change the `case` so that `E1_*/*/BLOCKS → b`, and `E1_*/BLOCKS/* → a`; drop `rc1` from the run-gate grep, the Choice bullet, the offline-mode list and the Success-Criteria reading; make the census pass condition AC-6.5's grep → 0 on both branches. Then re-pin the sha256 of `v0-blocking-contract.sh` (the current `b8a3400d…` reproduces for the old bytes) and re-run the offline fake-claude modes.
  - Plan S-3 offered "keep rc 1 … or move to the proven JSON form"; the spec chose a third wording ((b) else (a) rc 2), and the plan must follow it.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `AC-6.6 applies as spec v1.0 says`
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `or AC-6.6's (every site asserted rc 1 and the`
  quote: docs/01-plan/features/codex-tdd-gate-defects.spec.md › `is **not** kept. Every refusal site uses one form`
- **The existing Claude-gate test modules run the installed main-tree hook, not the worktree's hook.**
  - Both modules hard-wire `HOOK = Path.home() / ".claude" / "hooks" / "h-mad-tdd-gate.sh"`. That is `h-mad/tests/test_h_mad_tdd_gate_codex.py:20` and `h-mad/tests/test_h_mad_tdd_gate_state_resolution.py:27`, both opened.
  - `readlink ~/.claude/hooks/h-mad-tdd-gate.sh` → `/Users/kimhawk/orca/skills/h-mad/hooks/h-mad-tdd-gate.sh`, the main checkout.
  - v1.1 closed the hook→judge member of this class (a hook-relative judge path, W6). It did not close the test→hook member.
  - In the worktree, all 13 tests the Success Criteria migrate would execute the unmodified main-tree hook. So:
    - the "after: deny through the judge, with the `kind` named" assertions fail;
    - any unmigrated rc/stderr assertion passes for the wrong reason (R5's failure shape, one edge further out).
  - instance of: worktree artifacts reached through `$HOME/.claude`. Members found by `grep -n 'Path.home() / ".claude"' h-mad/tests/*.py`:
    - these two `HOOK` constants (open);
    - `test_h_mad_install_check.py:246,255`, which intentionally asserts the installed default and is not a member;
    - `test_h_mad_resume_decision.py:136`, which targets `handoff/`, not this feature's files.
  - Repairs, any one:
    - (a) resolve `HOOK` from `Path(__file__).resolve().parents[1] / "hooks" / "h-mad-tdd-gate.sh"`;
    - (b) run the hook through a symlink placed outside the tree, pointing at the worktree file, as the W6 test does.
  - Either way the change is a module-level edit outside any `def test_*`, so it must also be listed under §"Regression provenance" (see the function-body-diff Should-fix).
  - Unchecked: whether (a) changes any currently green reading on main; it should not, because main's hook is the same file.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `A worktree's hook would therefore call the **main tree's** judge, which does not exist until`
- **The "exactly three populations" claim for the `_production_claims` rewrite is false on the plan's own corpus.**
  - Spec FR-2's value axis admits only backtick-quoted tokens ending in `.py`. `_production_claims` today keys any singular `Production file` value, of any extension (`h-mad/scripts/h_mad_wire_registry.py:370-380`, opened; the regex has `re.I`).
  - I ran the registry's own `REG_LABEL` over the same 83 tracked non-archive impl-plans. Corpus reads at skills `6478b8b5` / HemaSuite `3f0c9f3a`; the plan's probe reproduces its published 83/4/16/64 there. Two populations exist outside the plan's three (unit: matching lines):
    - **68 singular-label values with zero `.py` tokens.** 55 of them are backticked non-`.py` paths across 26 files, e.g. `h-mad/scripts/hmad-dispatch.sh`, `h-mad/SKILL.md`, `h-mad/hooks/h-mad-tdd-gate.sh`. 9 are `none …` values, and 4 are other.
    - **23 values with one `.py` token plus trailing prose**, e.g. `` `…/column_mapper.py` (modify) ``, read today as a malformed key.
  - After the rewrite, every non-`.py` production claim disappears from the registry, so those changed heads become `unattributed`. That is a wire-registry behaviour regression the spec does not authorize, and the plan's 5g differential would flag every such entry as "a defect".
  - Repairs, any one, each needing spec S-10 wording:
    - (a) `_parse_tasks` records all backticked tokens (or a raw list), and the judge filters to `.py`;
    - (b) list both populations as expected changes, with an operator decision that the registry stops attributing non-`.py` files;
    - (c) leave `_production_claims` on its grammar and state the second parser as a residual (the teammate's option (b)).
  - Also extend `wire-registry-grammar.py` to count both populations, so the accounting derives from the probe and is not asserted.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `Moving the registry to the shared grammar changes its output on`
  quote: docs/01-plan/features/codex-tdd-gate-defects.spec.md › `An entry is a backtick-quoted token ending in`
- **The plan's single-helper rewrite of every existing Claude-gate assertion contradicts spec v1.1 AC-6.6/AC-6.2 under form (a).**
  - Spec AC-6.6 says that under (a) only the `returncode == 1` assertions change (to rc 2), and that "the stderr and `returncode == 0` assertions stand unchanged". AC-6.2 limits changes to what AC-6.5/AC-6.6 require.
  - The plan's Success Criteria route **every** assertion through one helper regardless of form. The function-body diff then requires the changed-test set to equal the impl-plan's list. So under (a) the plan changes about 9 tests the spec says stay unchanged:
    - the 3 "must be authored by codex" absent tests;
    - the 6 `returncode == 0` tests;
    - the stderr halves of the 2 stderr-asserting tests.
  - Repairs, either:
    - (a) make the helper migration form-conditional: under (a), edit only the 4 rc-1 assertions;
    - (b) route an amendment to spec AC-6.2/AC-6.6 (a new S-n) saying all existing assertions move to the helper on either form.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `through one helper that returns (allow|deny, reason) from rc, stdout JSON and stderr together;`
  quote: docs/01-plan/features/codex-tdd-gate-defects.spec.md › `assertions stand unchanged.`

## Should-fix
- **The plan's "pending spec v1.1 S-1…S-6" markers and its spec-version pointer are now stale.** Spec v1.1 applied S-1..S-6. The plan still says:
  - "The per-form readings are pending S-1, since spec FR-0 has no EJ arm" (line 1062);
  - "pending S-4, because spec AC-6.7 lets AC-6.1–AC-6.4 ship without it" (lines 73-74);
  - "pending S-2 / S-3", "pending S-5" (lines 1063, 1088, 1109) and "S-6" (line 372);
  - "FR-0 through FR-8 of … spec.md v1.0 apply" (line 68).

  Sweep them to cite spec v1.1 as settled (S-1..S-6) and v1.0→v1.1 where the text is stated.
  class: measurement
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `The per-form readings are pending S-1, since spec FR-0 has no EJ arm.`
- **S-7..S-12 were not applied in spec v1.1, yet the plan still labels them "pending spec v1.1" and builds layers on them.** The layers:
  - S-8: the `state` verb, the Claude-side governance read, the fail-closed unreadable chain and the multi-ACTIVE escape;
  - S-9: an rc-1 ALLOW stub expecting DENY;
  - S-10: the `_production_claims` rewrite;
  - S-11: the SKILL.md, agy-runtime.md and codex-implementer-prompt.md edits.

  Spec FR-6 still says "not step5" is unchanged, while plan layer 6.3 replaces it with the `state` verb. That is a live cross-document contradiction on the one path the teammate's Must-fix 1 was about.

  Retarget the markers to a named next spec revision, and state which layers are blocked on it before Phase 4 starts. Otherwise a design built from this plan adopts unsanctioned spec changes.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.spec.md › `S-7..S-12 not applied (2026-09-28).`
  quote: docs/01-plan/features/codex-tdd-gate-defects.spec.md › `The non-blocking paths are unchanged: no state, no`
- **V-0 scores a different path from the one whose Write it proves.** This only partly closes codex Must-fix 2.
  - The arm hook logs `HIT` when the Write's `file_path` merely ends in the sentinel basename (`case "$f" in */%s|%s)`).
  - Presence is then scored at the fixed path `$S/$a/$n` (`p()`, line 877).
  - A session that Writes the sentinel basename into any other directory passes the HIT check, and then reads `absent`: a false BLOCKS for E1, E2 or EJ.
  - The HIT line already records `$f`. Have `p()` test the logged path (normalised with `realpath`, since `$TMPDIR` is under `/private/var` on macOS), or have the hook match the exact absolute sentinel path. Add an offline fake-claude mode for "same basename, other directory".
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `case "$f" in */%s|%s) ;; *) exit 0;; esac`
- **The V-0 script is stricter than spec v1.1's per-form reading.**
  - Spec: an `UNMEASURED` EJ arm makes `FORM_B=INCONCLUSIVE`, and `READING` stays conclusive, since `INCONCLUSIVE` is triggered only by E1, E2 or E0 `UNMEASURED`. Under E1_DOES_NOT_BLOCK, (a) is then still chosen.
  - The script `exit 1`s on any arm's `UNMEASURED` (the replay check at lines 869-872 and `attempt`), including EJ's, so no reading is printed at all.

  Either make the script record `EJ UNMEASURED` → `FORM_B=INCONCLUSIVE` and continue, or state the stricter halt as a deliberate deviation routed to the spec.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.spec.md › `E0's sentinel is absent, or E0 or the arm is`
- **The function-body diff (the R6 fix for codex's Should-fix) cannot see an assertion weakened through a shared helper, fixture or module constant.**
  - It compares only `def test_*` bodies. The plan itself prescribes "one helper … a single definition shared by both modules", and the `HOOK`-constant repair above is module-level too.
  - A weakened helper (e.g. one mapping any rc to allow) changes no `def test_*` segment.
  - Extend the diff to every top-level `def`, class and assignment in the changed test files, plus any `conftest.py`/helper module the two gate modules import. The whole set must equal the §"Regression provenance" list.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `the helper is a single definition shared by both modules`
- **Spec v1.1 lists the changed existing assertions only under AC-6.6 (branch E1_BLOCKS).**
  - Under AC-6.5 (branch E1_DOES_NOT_BLOCK) with form (b), the same three negative tests go vacuous and the same rc/stderr assertions move. But AC-6.5 carries no list, and AC-6.2 only points at both ACs.
  - Route to the spec, so that the list is stated once and cited by both branches. The plan's Success Criteria list is form-keyed and already covers both.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.spec.md › `**Existing assertions that change** (the plan's census, re-read in this revision by test`
- **The R2 command, copied from the plan source, prints 0, not 7.**
  - The table cell escapes the pipes as `\|` inside `grep -cE '…'`. `\|` is needed in the markdown table, but copied raw into ERE it matches a literal `|`.
  - Measured at `2f262f8a` in `bash --noprofile --norc`: `\|` form → 0 matching lines; `|` form → 7 (the 3 case arms, 2 AC lines and G1/G2, all printed and classified). The v1.0 command → 16, of which 9 are verification-script `exit 1` lines. So the published 7/16 are correct, but only for the rendered text.
  - Move the command out of the table into a fenced block, or add a note that the escapes are table escaping only.
  class: measurement
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `grep -cE 'exit 1 ;;$\|BLOCK-\|test_gate_matrix'`

## Nit
- The embedded `reproduce.py` uses `str | None` in a `def` signature without `from __future__ import annotations`, so it needs Python ≥ 3.10. Step P0 runs bare `python3`, which is Homebrew 3.14 here but `/usr/bin/python3` 3.9.6 in the hook-test PATH the plan discusses. Pin the interpreter in the P0 command, or add the future import.
- The Version History says the teammate report had "6 shoulds"; it has 6 bullets, and they are answered. But the "Owed by the spec" heading still says "(pending spec v1.1)" after v1.1 shipped. It is covered by the stale-marker Should-fix and restated here only so the heading is not missed in the sweep.
