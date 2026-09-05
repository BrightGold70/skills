# doc-block-exec plan audit v91 — operator override sidecar over plan audit v90 (codex)

## Summary
Operator override sidecar for the round-nineteen gating pass (sheet C8 iii: r19 is the last document
round). Every finding below is carried with its `[key]`; measurement-class findings and deferred
should-fixes are acknowledged by key with their re-run command; build-class musts are NOT acknowledged
here — they are carried as `OPEN-DECISION` lines on the owning impl-plan Task and settled in 5d.
Evidence: the codex report this sidecar answers, re-derived by the orchestrator where stated.

## Must-fix
- [probe-version-line] The composite probe's recorded output carries a `python 3.11.8` line its published heredoc does not print (plan c90 codex must 1; verified: the fence at the `Each of the five probes contributes **two**` passage prints five `composite minus` lines and no version line).
  class: measurement

## Should-fix
- [killer-draft-wording] Measurements still says the design "shipped" the wrong killer; Deliverables distinguishes draft from shipped (plan c90 codex should 1).
  class: measurement
- [register-4.2.0-leg] The verification-status register keeps an expired exclusion of the renderer's 2.2.0 leg and names v1.104 as "this one" (plan c90 codex should 2).
  class: measurement
- [ledger-gap-growth] The ledger gap-growth sentence contradicts its own series (gaps 13 / 72 unchanged between cac6edc and 0021c77) (plan c90 codex should 3).
  class: measurement

## Nit
- [two-live-stamps] "two live stamps" after enumerating six (plan c90 codex nit 1).
- [one-field-moved] "ONE FIELD MOVED ON EACH" names two fields (plan c90 codex nit 2).

## Acknowledged-not-fixed
- [probe-version-line] re-run: `python3.11 -c 'import sys; print("python", sys.version.split()[0])'` → `python 3.11.8`; the stamp was collected separately from the fence's stdout and the plan's stamp accounting counts it — acknowledged, not re-stamped by hand (measurement layer lives in probes; SKILL §"Document-audit round cap").
- [killer-draft-wording] re-run: `grep -n 'The killer is NOT the one the design shipped' docs/01-plan/features/doc-block-exec.plan.md` (1 site) vs design:4293 `killed by` cell → the shipped design names `test_cli_subst_overlap_detail_lines`; wording only.
- [register-4.2.0-leg] re-run: `grep -n 'its \`4.2.0\` leg only' docs/01-plan/features/doc-block-exec.plan.md`; the 2.2.0 leg's last execution is v1.104's; re-entry deferred to the next revision line.
- [ledger-gap-growth] re-run: `git ls-tree -r --name-only <sha> -- docs/01-plan/features/ | grep -cE 'doc-block-exec\.plan\.audit\.v[0-9]+\.codex\.md$'` at cac6edc (75) and 0021c77 (76) against max cycles 88 / 89 → gap 13 unchanged.
- [two-live-stamps] deferred with the document's next revision.
- [one-field-moved] deferred with the document's next revision.
