AUDIT-codex-tdd-gate-defects-design-v2-BEGIN
## Summary
All 49 named acceptance criteria have an implementation or test path in the design, but six contract and safety gaps remain. The highest-risk gaps are a newly exempted production path and two state-file cases that do not reach a reliable refusal.

Evidence: 13 files opened, 4 greps run; the current hooks and parser imports were inspected, and two read-only inline probes checked Bash path matching and the timeout behavior. 🌱 graft saved ~53,319 tokens (~$0.03) this turn, 1 call.

| Spec ACs | implemented-as-written | restated | absent |
|---|---|---|---|
| FR-0 | 0.1–0.2 | None | None |
| FR-1 | 1.1–1.3 | None | None |
| FR-2 | 2.1–2.9 | None | None |
| FR-3 | 3.1–3.6 | None | None |
| FR-4 | 4.1–4.7 | None | None |
| FR-5 | 5.1–5.4 | None | None |
| FR-6 | 6.1–6.15 | None | None |
| FR-7 | 7.1–7.2 | None | None |
| FR-8 | 8.1 | None | None |

## Must-fix
- DD-7's relative-path relaxation also exempts `tests/../x.py`, a production target outside `tests/` — the old gate treats that relative spelling as production, while the new root-prefixed string matches `*/tests/*` before canonicalization. The published differential omits traversal spellings and its claimed softened set is incomplete, breaching Guard narrowing. A read-only Bash probe classified `tests/../x.py` as gated and `/repo/tests/../x.py` as exempt; canonicalize before exemption or explicitly reject ambiguous paths, then extend the old/new corpus.
  class: build
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `**Expected softened set:** exactly the two active cells relative `tests/x.py` and relative`
- A FIFO state file can block the Codex hook before `read_chain` runs — D8 retains `_any_phase5_status` on every payload, and the current function calls `read_text` through `_state_status` on files found by `rglob`. The host timeout then decides the write rather than returning the FR-5 unreadable-state refusal. Keep the shell-policy scan from blocking the per-target path, or make the scan nonblocking, and test the real Codex entry point with a FIFO.
  class: build
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `A FIFO there blocks the Codex gate before this reader runs, and the host's hook timeout then decides.`
  quote: docs/01-plan/features/codex-tdd-gate-defects.spec.md › `a dangling symlink, a directory or a FIFO — is unreadable, never absent.`
- A state file behind an unsearchable directory is treated as absent by both readers — `lexists` cannot distinguish absence from a permission failure, so the design explicitly permits an unmeasured write even when that state file is present. FR-5 requires any unreadable file on the chain to deny; distinguish `ENOENT` from `EACCES` in the shared reader and make the fast path defer when it cannot prove absence.
  class: build
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `A state file inside a directory the process cannot search reads as absent to both`
  quote: docs/01-plan/features/codex-tdd-gate-defects.spec.md › `Any unreadable file on the chain means `unknown`, which denies fail-closed, as today.`
- The `fallback` wire field has incompatible encoding rules — D13 builds an `invalid:` tag with percent-encoded JSON, while D10 says every variable field is quoted again; quoting the full tag changes `invalid:%22null%22` to `invalid%3A%2522null%2522`. The active-line ERE requires a literal `invalid:`, so an invalid fallback value becomes a Claude `judge-error` although D13 says the tag is data only. Specify exactly one encoding boundary and test the actual formatter output against the gate ERE.
  class: build
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `Every variable field value is `urllib.parse.quote(value, safe="/._-")``
- The name-map process is outside the process-group timeout contract — D3 uses `subprocess.run(timeout=…)` for its Bash script, although D6 promises one bounded budget and uses `Popen` plus `killpg` for candidate runs because `run` leaves child processes behind. The name-map script invokes `basename`; a child retaining captured pipe descriptors can make post-timeout cleanup exceed the budget. A read-only controlled probe with `sleep 2 & wait` and a 0.2-second timeout took 2.01 seconds. Apply the same bounded group cleanup to the name map and pin that branch.
  class: build
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `subprocess.run(["bash", <scripts>/h_mad_derive_test_path.sh, rel], cwd=root, capture_output=True, text=True, timeout=<remaining budget>)`.
- Plan G5 still directs both gates to resolve relative targets against payload `cwd`, while the design and current spec direct the Claude gate to resolve them against the project root — these produce different target and exemption decisions for a nested cwd. Correct the paired plan's implementation contract so the Claude task and tests have one base rule.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `G5: Both gates resolve a relative target against the payload `cwd`.`
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `A non-empty relative `TARGET_PATH` becomes `$ROOT_ABS/$TARGET_PATH` when `ROOT_ABS` is`
  quote: docs/01-plan/features/codex-tdd-gate-defects.spec.md › `A relative target is made absolute against the project root before any check`

## Should-fix
- The exemption path's “no Python process” claim is false — D9's target reader starts `python3` before the exemptions, so the statement could misdirect latency estimates or an entry-point test. State only that the `state` and `judge` verbs are skipped.
  class: measurement
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `No `python3` process is started for an exempt`

## Nit
None
AUDIT-codex-tdd-gate-defects-design-v2-END
