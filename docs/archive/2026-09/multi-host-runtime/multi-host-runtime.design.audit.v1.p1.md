AUDIT-multi-host-runtime-design-v1-BEGIN
## Summary
The design covers most of the 50 acceptance criteria, but four are restated against the spec and the live-smoke checks can report V-11.1 without proving the required reads. The tree review also found a host-declaration documentation guard that accepts an unusable placeholder. Evidence: 16 files opened, 8 greps run. 🌱 graft saved ~21,043 tokens (~$0.01) this turn, 1 call.

| Classification | Acceptance criteria |
|---|---|
| implemented-as-written | AC-1.1–1.2, AC-2.1–2.5, AC-3.1–3.2, AC-3.4–3.5, AC-4.1–4.6, AC-5.1, AC-5.3–5.7, AC-6.1–6.6, AC-7.1–7.3, AC-8.1–8.2, AC-9.1–9.4, AC-10.1–10.6, AC-12.1–12.2 |
| restated | AC-3.3, AC-5.2, AC-8.3, AC-8.4 |
| absent | None |

## Must-fix
- AC-3.3 is restated from fourteen kind fixtures to 42 disjunct and split fixtures — the added coverage is sensible, but the spec's explicit fixture count still conflicts with the design's RED/GREEN inventory; reconcile the spec before implementation.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.spec.md › `Fourteen kinds means fourteen fixtures.`
  quote: docs/02-design/features/multi-host-runtime.design.md › `Fixture count: 36 disjunct fixtures plus 6 splits, 42 in total.`
- AC-5.2's first TDD-gate reason becomes branch-dependent — the spec requires the concrete exit-1 reason, while the design may write a different reason after the sibling feature lands; update the spec from the measured base or keep its reason, and pin the chosen reason in the doc test.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.spec.md › ``- (i) `h-mad/hooks/h-mad-tdd-gate.sh` refuses by `exit 1`, which grok treats as fail-open``
  quote: docs/02-design/features/multi-host-runtime.design.md › `Reason (i) takes the branch's wording.`
- AC-8.3 is narrowed from running every existing context-budget test twice to comparing a selected probe case set under the two host values — regressions in existing tests outside that set can pass the designed gate. Retain the probe and run the full existing test module once with HMAD_HOST unset and once with claude.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.spec.md › ``With `HMAD_HOST` unset, and again with it set to `claude`, every existing``
  quote: docs/02-design/features/multi-host-runtime.design.md › ``Each budget and decision case runs with `HMAD_HOST` unset, and again with `claude`.``
- AC-8.4 is narrowed for grok to an operator-only indicator that the orchestrator cannot reach — the spec requires an indicator the orchestrator uses, or an explicit statement that none exists. State that grok has no model-accessible substitute and give the operator's /context check as a separate manual action.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.spec.md › `adapter names what the orchestrator uses instead (the host's own context indicator), or states that there is none.`
  quote: docs/02-design/features/multi-host-runtime.design.md › ``grok: the operator's `/context` (`04-slash-commands.md`; interactive only, and not reachable by the model);``
- V-11.1's adapter-read predicate accepts any tool input containing the adapter filename, including a test -f, echo, or search that never reads its contents — a positive smoke can falsely certify the required read. Require an observed successful content read before the first script run and rehearse a filename-only negative case.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.spec.md › ``The transcript shows the host loaded h-mad's `SKILL.md` and read``
  quote: docs/02-design/features/multi-host-runtime.design.md › ``a` is the first event whose `input_text` contains `<H>-runtime.md`.``
- V-11.1's grok skill-load predicate proves only that h-mad was advertised in available_commands, not that grok loaded SKILL.md; the spec still names an init event that the design has measured absent. Define an observable of an actual skill load, or mark this part unverified and halt, and reconcile the V-11.1 wording in the spec.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.spec.md › ``For grok, the stream-json `init` line's `skills` list contains `h-mad` (F11).``
  quote: docs/02-design/features/multi-host-runtime.design.md › ``For grok, some `available_commands` event's `commands[].name` must include``
- The FR-8 unknown-host stdout contract changes from the supplied value to JSON-quoted text even for simple values such as zzz — callers consuming host=<value> get different bytes. Specify that encoding in the spec and test it, or preserve bare safe values while escaping unsafe ones.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.spec.md › ``| any other value | `CTXBUDGET: UNKNOWN reason=unknown_host host=<value>` | 2 |``
  quote: docs/02-design/features/multi-host-runtime.design.md › ``print(f"CTXBUDGET: UNKNOWN reason=unknown_host host={json.dumps(host_value)}")``
- The AC-9.3 documentation test checks only uuid.uuid4() and owned_elsewhere — deleting the required same-id arguments on --claim, --beat, --set, and --release would leave the test green. Pin each argument and the once-at-bootstrap rule in the located row; similarly pin the grok shell-presence condition.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.spec.md › ``created once at bootstrap and passed on every `--claim`, `--beat`, `--set` and `--release` in that session.``
  quote: docs/02-design/features/multi-host-runtime.design.md › ``all: `uuid.uuid4()` and `owned_elsewhere`; grok also `GROK_SESSION_ID` and `hook processes``
- The FR-8 documentation guard requires the literal HMAD_HOST=<host> placeholder, so a per-host adapter can pass while never giving a runnable inline declaration such as HMAD_HOST=grok. Pin the concrete value in each host's adapter and an executable call shape.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.spec.md › ``on each h-mad script call: `HMAD_HOST=<codex|agy|grok> python3 …`.``
  quote: docs/02-design/features/multi-host-runtime.design.md › ```HMAD_HOST=<host>`, `CTXBUDGET: UNKNOWN`, `80%`, and `/context` (grok) or `none` (codex, agy)``

## Should-fix
None

## Nit
None
AUDIT-multi-host-runtime-design-v1-END
