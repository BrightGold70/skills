SPEC-AUTHOR: DONE version=v1.10 path=/Users/kimhawk/orca/skills/docs/01-plan/features/agy-coder-fallback.spec.md lines=1251 sha256=4102cf3214d631a287c99e58fc2c1df43018a11dab69a129c7f63a3bc436acac

Pre-write assertion: sha256 ebc20f730eec…, newest VH `- v1.9`, HEAD 84ec2133 (the spec was last changed at 4bef0e76). It had not moved, so I wrote.

premises verified:
- h-mad/hooks/h-mad-codex-tdd-gate.py:main `--self-check`. `sed -n 530,555p` at 84ec2133 shows two FAIL branches, `FAIL parser` and `FAIL shell-policy`. Both print to stderr and `return 2`. PASS prints to stdout and returns 0.
- h-mad/tests/test_h_mad_tdd_gate_docs.py::test_hook_line_names_both_gates exists (grep `def test_hook_line_names_both_gates`). It requires the tokens h-mad-codex-tdd-gate.py, apply_patch, shell, h-mad-tdd-gate.sh, Write and Edit.
- h-mad/references/codex-implementer-prompt.md has a `Hook:` line that names Claude's h-mad-tdd-gate.sh guarding Write/Edit (grep -n 'Hook:').
- No existing test pins exit 2 for the Codex `FAIL shell-policy` path. Ran `git ls-files h-mad/tests | xargs grep -n 'self-check|self_check|FAIL shell-policy' | grep -i codex`. It returned only test_codex_hook_self_check_reports_machine_readable_pass, a PASS test, and a mutation-spec `_mechanism` string.
- Impl-plan v1.1 halt names come from Task 16 (grep 'implementer_unresolved\|implementer_invalid'). The OD-2 T2a text comes from Task 6 and §OD-2. The agy self-check tokens and exits come from the Task 5 self-check bullets.

findings applied:
- P1: added D-16 (OD-2, operator). Added FR-4 §"Deliberate differences" item 6: a directory target denies kind=judge-error under active/unknown and is allowed under inactive. The residual is a trailing-/ path that names no existing directory. The header now says "item 6 added v1.10, D-16". AC-4.1 gains an active-scan directory fixture and an inactive-scan allow fixture, and "directory target" is added to its unknown-scan deny list. §Open questions now notes OD-2 settled.
- P2: the FR-2 token table "caller does" column now names the halts. A new **Halts** paragraph lists step5:implementer_invalid (for invalid), step5:implementer_unresolved (for no-record and unreadable) and step5:implementer_switch_unrecorded (for record=failed), adopted from impl-plan Task 16. Residual: failure-recovery.md gets no rows for them.
- P3: FR-5 gains a bullet: the gate's --self-check prints one stdout token. A verdict FAIL exits 0, and only an operational error exits nonzero. The wiring check still reads anything but PASS with exit 0 as self-check-failed. The bullet also records the Codex `FAIL shell-policy` correction in impl-plan Task 4. AC-5.2 gains a forced self-check FAIL fixture and a return-2 mutant.
- P4: the FR-9 Hook-line bullet adds Claude's h-mad-tdd-gate.sh (Write/Edit), pinned by test_hook_line_names_both_gates.
- Owed section: added a "Design (spec v1.10)" item (Q1–Q3).

values swept (grep -c, matching lines, in the spec after the edit; prose, tables and fenced blocks are all included because grep reads the whole file):
- implementer_invalid 4, implementer_unresolved 5, implementer_switch_unrecorded 3: each one is in the FR-2 table/Halts paragraph or the VH/owed lines. No other halt spelling is left for these rows.
- D-16 7, OD-2 4. Checked the count wording with `grep -n -i 'five|deliberate difference|differences from the Codex'`. Nothing states "five differences". AC-4.1's differential refers to §"Deliberate differences" by name, so item 6 is picked up there.
- self-check 12. Checked `nonzero` for any stale "self-check FAIL exits nonzero" claim. The remaining hits are the FR-5 verdict rule, the no-token row and unrelated FR-9/AC lines. None is stale.
- h-mad-tdd-gate.sh 7.
- AC census: `h_mad_ac_census.py` gives `ACS: OK count=21 frs=9` on v1.10 and on HEAD's v1.9 (via git show, in a scratch copy that is now deleted). No AC was added or dropped; only the bullets of AC-4.1 and AC-5.2 grew.

contradictions found:
- Not a contradiction but a gap: decision I4/P3 covers only the Codex `FAIL shell-policy` branch. `FAIL parser` (stderr, return 2) is the same kind of self-test verdict. I left it as a stated residual in FR-5 ("unchanged and unclassified") and did not classify it. The orchestrator may want Task 4 to cover it too.
- Not added, because it would be new scope: FR-2 does not say what the caller does when the verb prints no `TDD-IMPLEMENTER:` token (a crash). The impl-plan names no halt for it either. I drafted a sentence mapping it to implementer_unresolved and removed it.
- While I worked, `git status` showed docs/02-design/features/agy-coder-fallback.design.md modified. I did not touch it; presumably the design author is running in parallel.

placeholder scan: `h_mad_precheck_doc.py --phase spec` returned PRECHECK: PASS issues=0. There are 13 advisories, all from before this revision: 12 PATH advisories for not-yet-created files, and 1 COUNT advisory on an older VH line (L1247). I did not pass any --allow.

owed by other documents:
- Design (Q1–Q3): FR-4 needs a T2a directory check before T6, plus a sixth §"Deliberate differences" item to match the spec's item 6. FR-4 --self-check should say a verdict FAIL exits 0 (it currently says "a nonzero exit") and note the Codex gate fix in Task 4. FR-2 should adopt step5:implementer_invalid and step5:implementer_unresolved.
- Impl-plan: remove the "residual, not changed" text about Codex `FAIL shell-policy` (that is I4, which the implplan-author owns). The new AC-5.2 bullet (a self-check verdict FAIL is read as UNWIRED reason=self-check-failed, plus the return-2 mutant) should be traced to Task 5's test_self_check_policy_fail_is_a_verdict_with_exit_0, its mutation row, and Task 9's check. The new AC-4.1 directory fixtures map to Task 6 item 10. Check that item 10 also has an inactive-scan allow id and an unknown-scan deny id.
- Later feature: failure-recovery.md rows for the three FR-2 halts; classification of the Codex `FAIL parser` self-check exit.
