## Summary
GATING pass (codex-leg stand-in) on design v1.13 at `8a27d264`. The design file is unchanged at HEAD `7e1c48e3`; the diff was checked against spec v1.19 (`d9f25dc2`) and the live code. I read all of D21 (design lines 553-603), the D8 order and cycle block (217-262), the D15 assembler bullet (442), D17's switch bullet (507), the v1.13 mutation rows (844-862), TDD item 12, the version and token entries, and spec AC-3.6, AC-3.8, AC-3.9 and AC-1.9 in full. Against the tree I read `_cmd_audit_cycle` (hmad-dispatch.sh:3559-3855) in full; `assemble`, `prepend_output_contract`, `preflight` and `main` in the assembler; `require` and `main` in the containment module; the D19 exemptions in `h_mad_tool_calls.py`; record-cycle's prompt copy in the probe; the stub assembler; and the D17 tests.

I executed the main property claims rather than reading them:
- **Pinned sha, probe (e).** `7e10f543` is what `git log -1` reports for the two files. Both blob ids (`54e5b4e4…`, `7c93f0bc…`) are identical at `7e10f543`, at `f49f98f1`, at HEAD and in the working tree. `a489031f..f49f98f1` has 0 commits, `7e10f543` is an ancestor of `a489031f`, and the pinned assembler imports only the standard library.
- **Placement, probes (a) and (b).** I monkeypatched the clause in front of the slot-filled text with the current assembler. Preflight found no problems. Removing `clause+"\n\n"` once gave back the switch-off prompt byte for byte. The clause is after `CONTRACT_SEPARATOR` and before `Target document:`. `grep -cxF` on the written prompt printed 1.
- **Test (2) guard premise.** With a symlinked `--project-root`, the report inside the root and `vh_tail=1`, the current assembler leaves 0 given and 0 resolved root occurrences once the report path is removed. The omission note is present.
- **Residual (6).** The three `git grep -c -i -F 'path scope'` measurements reproduce: 0, 0, and 3 files on `f7520e72`.
- **The `--pass-root` caller census** reproduces: 0 non-test callers, 6 matching lines in the wrapper test module, 1 in the probe test module.
- **D18 step 6** matches containment.py:239 (joined, then `casefold()`). Commit `2925febd`, row `canary-denial-case-sensitive` and `test_canary_lowercase_shell_denial_passes` all exist.

Verdict on the four probes:
- (a) Switch off cannot change production output.
- (c) The halt is placed before the divergence check and before the halt-file gate, so AC-3.4 re-dispatch never sees a cycle that is missing the clause.
- (d) `assembler-check` reads the recorded `p<i>.prompt.txt` copies of the dispatched stem prompts (probe:691), so a run missing the clause cannot reach PINNED.
- (b) and (c) are robust in placement. The one real build hazard is how the count is captured under `set -e` (Should-fix 1).

No blocking defect found. Five should-fixes.
Evidence: 16 files opened, 41 greps run.

## Must-fix
None

## Should-fix
- **The design does not say how the count is captured, and the obvious way aborts the wrapper with no token.** Location: design D21 "Fail closed" bullet (line 565), and hmad-dispatch.sh:5 `set -euo pipefail`. `main "$@"` (line 4685) calls `_cmd_audit_cycle` outside any `if`/`||` context, so errexit is live. I ran this in `/bin/bash` 3.2.57: `set -euo pipefail; f(){ n="$(grep -cxF zzqq /etc/hosts)"; echo after; }; f`. It exited rc=1 and printed nothing. With `|| true` it printed `n=0` and continued. A pass with count 0 is exactly the case being checked: the `p2`-alone, `p1`-alone and every-pass knobs of test (6) all reach it. A literal `c=$(grep -cxF …)` implementation therefore exits 1 with no `REQUIRE: STOP`, no halt-file line and no stderr marker. It still fails closed (no `AUDITCYCLE:`), but the token, the halt file and the "exit 0" the design names are lost. Test (6) would catch it as RED, so this is not a gate. Fix: prescribe the capture, using either repair (the wrapper already uses the first, see the `|| true` comment at :3793):
  - `n="$(grep -cxF -e "$_HMAD_PATH_SCOPE_CLAUSE" -- "${prompt[$i]}" || true)"` and halt unless `[ "$n" = 1 ]`. A string compare, so an empty or non-numeric `n` from grep exit 2 also halts.
  - or `if [ "$(grep -cxF …)" != 1 ]`. errexit does not fire inside a test argument.
  - Also pass the pattern with `-e`/`--`.
  instance of: the class "a command whose non-zero exit is a normal outcome, run under `set -e`". The rule is every such capture in `_cmd_audit_cycle` carries `|| true` or sits in a conditional. Residual: none in the existing loop; the divergence loop at :3792-3798 already complies.
  class: build
  quote: docs/02-design/features/grok-audit-surface.design.md › `each pass's prompt must hold exactly one line equal to the wrapper's copy of the clause`

- **The spec asks to record the `$here` that `_cmd_audit_cycle` used. The design records `SELF_DIR` of a different script and infers that the two are equal.** Location: design D21 `assembler-read` bullet (line 568). Spec AC-3.6 says the record holds "the directory `_cmd_audit_cycle` used as `$here`". The design never measures that value. It records `h_mad_grok_containment.py`'s own `SELF_DIR` and argues equality from the runbook's working directory. `here_not_self` compares the readings with the check's own `SELF_DIR`, so it only fires if the reading and the check ran from different checkouts. It cannot detect cycles that ran a different checkout's wrapper. One example: the bare `hmad-dispatch audit-cycle` of the D8 diagram (line 29) resolves through the `~/.claude/skills/h-mad` symlink (`-> /Users/kimhawk/orca/skills/h-mad`, checked) to the main checkout, even when the runbook is driven from a worktree. The pinned cycle block (line 249) uses the relative `h-mad/bin/hmad-dispatch`, which is safe. The diagram does not. The clause check on recorded prompts still holds. Only the published sha can name the wrong commit. Possible repairs, none checked against further constraints:
  - (i) `audit-cycle`, when `scope_arg` is set, writes `here=$here` to stderr or to a per-cycle file, and `assembler-check` requires it to equal the readings' `here`.
  - (ii) Record `pwd -P` plus the command line in `$STEM.command.txt`, and have the check derive `$here` from them.
  - (iii) Keep the inference, but state it as a residual and change the D8 diagram's bare `hmad-dispatch` to `h-mad/bin/hmad-dispatch`.
  class: build
  quote: docs/02-design/features/grok-audit-surface.design.md › `It is the module global `
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `It records three things: the directory`

- **"No test imports the clause from the assembler" contradicts the copy test, which must read the assembler's constant.** Location: D21 Tests (line 579) against the copy-test bullet (line 588). The copy test "requires it to equal both `PATH_SCOPE_CLAUSE` and `STUB_PATH_SCOPE_CLAUSE`", and `PATH_SCOPE_CLAUSE` lives only in the assembler. Spec test (1) forbids importing the clause only for test (1), so that rewording the clause fails it; it does not forbid it for the copy test. Fix, either:
  - narrow the sentence to "No presence test ((1), (3), (5)) imports the clause; the copy test reads `PATH_SCOPE_CLAUSE` from the assembler by import (or `ast` parse)"; or
  - have the copy test parse the constant out of the source text, and say so.
  class: build
  quote: docs/02-design/features/grok-audit-surface.design.md › `No test imports the clause from the assembler.`

- **Residual (2)'s enforcement argument contradicts D15 for the `NO_CLAUSE` case.** Residual (2) says that a run that skips the gate is stopped by the stamp, because without `PINNED` there is no `assembler=<sha40>`. D15 (line 442) publishes `assembler=<sha40>` for `NO_CLAUSE` as well. So a doc with no `PINNED` line can still carry a sha stamp, and the residual's stated stop does not hold for that token. It also does not say which stamp a skipped gate (no `check.txt`) yields. Fix:
  - reword residual (2) to "a doc with no `ASSEMBLER:` token has no stamp; a `NO_CLAUSE` doc carries `assembler=<sha40>` and is unscored by D8 step 6 alone"; or
  - have D15 publish `assembler=<sha40> clause=missing` for `NO_CLAUSE`, so that the stamp alone distinguishes the two.
  class: measurement
  quote: docs/02-design/features/grok-audit-surface.design.md › `a doc with no `
  quote: docs/02-design/features/grok-audit-surface.design.md › `when the token is `

- **Usage errors on the two new verbs fall into an existing branch that prints a `QUARANTINE:` token.** Location: D21 `assembler-read`/`assembler-check` bullets, and h_mad_grok_containment.py:270-277. `_Parser.error` raises `UsageError`, and `main` catches it before any mode dispatch. For every mode other than `canary-plant`, `canary-judge` and `require`, it prints `QUARANTINE: REFUSED reason=internal:UsageError` and exits 2. The design names the internal-error token for each new verb ("An escaping exception prints `ASSEMBLER: UNPINNED reason=internal:<E>`" / `ASSEMBLER-READING: unreadable …`). It says nothing about usage errors, which do not escape. Unless the implementer adds branches, an `assembler-check` with a typo'd flag writes a `QUARANTINE:` line into `check.txt`. That still fails closed through `require --verb assembler`, but under the wrong prefix, and no fixture pins it. Fix: name the usage-error token of each new verb, for example `ASSEMBLER: UNPINNED reason=internal:UsageError` and `ASSEMBLER-READING: unreadable reason=internal:UsageError`, both exit 2. Add a mode branch in the `except UsageError` block and one fixture per verb.
  instance of: the class "every containment verb's usage-error path"; the existing three verbs already have their own branches.
  class: build
  quote: docs/02-design/features/grok-audit-surface.design.md › `An escaping exception prints `

## Nit
- **Header and spec version.** The header says "v1.13 takes spec v1.18 (`f49f98f1`)". Spec v1.19 (`d9f25dc2`) now carries the texts this design asked for. The content agrees with v1.19 (test (2) strips the report path first; D21 is the single source of the reason list), but the next revision should name v1.19.
- **Test (4) wording.** "identical keyword arguments" is not literal: the `template` path differs, and only the current call carries `path_scope=False`. Also, "If a commit to either file lands before Phase 5, the test fails" really means a commit that changes switch-off output. The clause commit itself touches the file and must not fail the test.
- **What counts as a line.** `assembler-check`'s "exactly one line equal to the clause" should say lines are split on `\n` (`split("\n")`), not `splitlines()`. Python's `splitlines` also breaks on `\x0b`, `\x0c`, `\x1c-\x1e`, `\x85` and ` `, so its count can differ from the wrapper's `grep -cxF`.
- **Order of the assembly halt and the clause check.** The `ASSEMBLE: HALT` branch runs before the clause check. A cycle where p2 halts (for example `oversize`) and p1 lacks the clause is recorded as `UNVERIFIED assemble_halt:p2` together with p1's clause-less prompt, and D8 re-dispatches it. `assembler-check` later turns the whole run into `NO_CLAUSE`, so this fails closed, but one sentence in D21 saying so would close the reader's question.
- **Residual (6) and the measurement doc.** D15 now publishes the clause verbatim on a line of its own in a `main` document. The residual's load-bearing reason ("the archived sources and the calibration tree predate the clause") should add that no prompt inlines the measurement doc.
