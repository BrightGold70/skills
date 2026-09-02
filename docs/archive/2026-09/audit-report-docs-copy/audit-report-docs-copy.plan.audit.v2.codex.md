AUDIT-audit-report-docs-copy-plan-v2-BEGIN
## Summary
The plan covers all six functional requirements at plan granularity, but five cross-contract and invariant gaps prevent it from safely reaching implementation. Axis C finds no silent plan/spec divergence: every FR is implemented as written, including defects already present in the source spec.

| Spec item | Classification |
|---|---|
| FR-1 | implemented-as-written |
| FR-2 | implemented-as-written |
| FR-3 | implemented-as-written |
| FR-4 | implemented-as-written |
| FR-5 | implemented-as-written |
| FR-6 | implemented-as-written |

## Must-fix
- FR-3 deliberately changes a historically scoreable, well-formed audit from `GATE: PASS|FAIL` to `GATE: INVALID`, and the plan expressly says the gate “now refuses one path shape it used to score” — this directly breaches the non-overridable Backward compatibility invariant; reconcile the spec and plan so transport enforcement does not change the audit gate's verdict for content that previously passed.
- Conflict protection covers only `_copy_collected_report`, not the `--out` fallback — current `collect()` sends extracted output through `_write_collected_report`, which unlinks and rewrites the docs target, so `<RP>` missing + differing existing docs + valid `--out` silently clobbers the committed report without `--force`. This contradicts “`--force` is the only overwrite path” and the no-clobber goal; thread the conflict policy through both delivery rungs and add the missing differing/identical `delivered=out` cases.
- The claimed 11 “drop/force pairs per connection” are not bidirectional — AC-6.3 provides only a severed CLI→`collect()` mutation `(e)` and only a severed dispatch route `(f)`, with no mutants that force either connection on a fall-through/negative path. Connection enforcement requires both directions for each new call site/route, so name the negative fixtures and add the corresponding force mutations rather than claiming the unpaired set is complete.
- The transport grammar is internally inconsistent and independently reimplemented — the plan says transport names carry `[_<surface>]` and accepts surface tokens under `[A-Za-z0-9][A-Za-z0-9_-]*`, while FR-3's authoritative refusal regex accepts only `[A-Za-z0-9-]+`; thus a valid surface such as `codex_draft` produces a transport-shaped name the gate can score. The proposed grep-based docs test neither supplies one authoritative grammar nor proves behavioral equivalence among `_VERSION_RE`, shell staging, and the gate, violating Single-source contract; the plan must reconcile the grammar in the spec and pin a shared corpus in both directions.
- Runtime mutation verification is absent for the new writes/removal — AC-2.1's test-side `filecmp` and AC-2.8's test assertion do not make the production collector re-read the bytes it wrote or confirm that the docs-path `.done` marker is absent before printing `OK`/`marker: removed`. The Mutation verification invariant binds the mutating step itself, so the plan must require byte-for-byte readback after copy/force and an existence readback after marker deletion, with operational failure if either observation disagrees.
- The load-bearing surface/transport boundary is not tracer-verified in the Assumption table — “Surface grammar is one dot-free token, `p<i>` never co-occurs” cites a comment and `_VERSION_RE`, while “Transport stem is fixed” cites source locations and a summarized corpus count rather than an executed input/output probe. Assumption verification requires throwaway executions with observed output; the missed underscore mismatch demonstrates that static source citations were insufficient.

## Should-fix
- The Success Criteria say “All 32 ACs,” but the spec contains 33 unique criteria (5 + 11 + 6 + 2 + 4 + 5) — correct the count so completion cannot be reported against a short census.

## Nit
- The risk table says the mutation spec and tests are written “in one task,” while the work order assigns tests across tasks 1–5 and the spec to task 6; make the sequencing statement consistent before deriving the impl-plan.
AUDIT-audit-report-docs-copy-plan-v2-END
