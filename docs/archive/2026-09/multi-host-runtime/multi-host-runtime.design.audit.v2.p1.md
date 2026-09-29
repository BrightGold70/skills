AUDIT-multi-host-runtime-design-v2-BEGIN
## Summary
Across 51 spec AC IDs, 48 are implemented as written and three have narrower acceptance coverage in the design. The remaining hard gaps concern live-smoke evidence, session-id persistence, source citations, archiving, and the project path invariant.

| Classification | AC IDs |
|---|---|
| implemented-as-written | AC-1.1–1.2; AC-2.1, 2.3–2.5; AC-3.1–3.5; AC-4.1–4.6; AC-5.1–5.7; AC-6.1–6.6; AC-7.1–7.3; AC-8.1–8.5; AC-9.2–9.4; AC-10.1–10.2, 10.4–10.6; AC-12.1–12.2 |
| restated | AC-2.2, AC-9.1, AC-10.3 |
| absent | None |

Evidence: 9 files opened, 12 greps run.
🌱 graft saved ~104,839 tokens (~$0.06) this turn, 1 call.

## Must-fix
- AC-2.2 is restated to permit not-applicable rows without a reason: the design's `tool-search` and `todo-tools-optin` agy cells, and `todo-tools-optin` codex cell, give only evidence tags. The spec requires the mapping cell itself to state why it is not applicable; add those reasons and a discriminating row check or review gate.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.spec.md › `A `not-applicable` row's `mapping` states the reason.`
  quote: docs/02-design/features/multi-host-runtime.design.md › `N: [A3] | N: [observed agy tools]`
- AC-9.1 is restated to a singleton unknown-host test and omits the empty-session-id fixture. The spec requires the unknown value's live-owner and no-owner pair plus `--session-id ""`; a single unknown test cannot discriminate both states or the empty-id route.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.spec.md › `(`HMAD_HOST=zzz`) gets the same pair, and so does `HMAD_HOST=grok` with `--session-id ""`.`
  quote: docs/02-design/features/multi-host-runtime.design.md › `test_decide_unknown_host_without_session_id`
- AC-10.3 is restated to two empty-option tests. The specified two empty-environment cases and two explicit-option-over-environment cases have no named fixtures, so a default resolver that ignores presence or precedence can pass the proposed test plan.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.spec.md › `An explicit option pointing at a `tmp_path` fixture wins over an override variable pointing elsewhere (one fixture per`
  quote: docs/02-design/features/multi-host-runtime.design.md › `test_empty_root_option_is_unreadable[agents|agy]`
- V-11.1 assigns the wrong verdict to codex and agy when no `SKILL.md` read is observed. The spec requires `FAIL` for those two hosts and reserves `UNVERIFIED` for grok's possible inline load; the shared step 4 and R11 instead emit `UNVERIFIED` for all three.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.spec.md › `none observed → `FAIL``
  quote: docs/02-design/features/multi-host-runtime.design.md › `UNVERIFIED V-11.1 no observed SKILL.md read`
- V-11.1 can count a failed shell read as a successful adapter or skill read. The design explicitly treats `cat A || true` as successful when `cat` failed and judges grok/agy tool completion without checking returned file text; the spec requires the read to return the file's text. Add failed-read rehearsals and inspect the read result or halt as unverified.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.spec.md › `returns the file's text`
  quote: docs/02-design/features/multi-host-runtime.design.md › `Success is judged per event, not per simple command. `cat A || true` succeeds even if the`
- V-11.1 misses a Python script run preceded by a file-descriptor redirect. The specified first-non-option-operand rule sees `2` in `python3 2>err h-mad/scripts/h_mad_state_write.py`; a scratch run of the specified shlex settings returned `['python3','2','>','err','h-mad/scripts/h_mad_state_write.py']`. The run can therefore precede the adapter and still pass; model redirection operators and add this negative rehearsal.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.spec.md › `A script run is an **execution** of an `h_mad_*.py` script`
  quote: docs/02-design/features/multi-host-runtime.design.md › `the first operand not starting `-` has a basename`
- V-11.1 knowingly classifies `sed -e 'e python3 h_mad_x.py'` as non-executing even though its `e` command executes. This leaves a documented false PASS path before the adapter read, violating the script-run ordering gate; classify that form as an execution or an unverified command and rehearse it.
  class: build
  quote: docs/02-design/features/multi-host-runtime.design.md › ``sed` is classed as non-executing even though GNU `sed`'s `e` command executes.`
- The Phase-7 smoke never proves that the host actually declared `HMAD_HOST` on a script call. Its prompt asks for inline declaration, but the specified assertions only check status, reads, and file identity; a host can omit the declaration and still pass, contrary to the spec's stated smoke closure for this residual. Add a read-only declared-host script call and assert its input and `host_unsupported` token.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.spec.md › `(FR-11) checks that the adapter's instruction is followed.`
  quote: docs/02-design/features/multi-host-runtime.design.md › `r=$(python3 "$P" v111 --host "$H" --log "$S/log")`
- The minted session id is kept only in shell variable `SID` while the design itself says host shell exports may not persist between calls. Separate tool invocations can expand `"$SID"` to empty, defeating the claim and heartbeat procedure. Specify a durable per-session value carried into each call, and test distinct shell invocations.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.spec.md › `created once at bootstrap and used for the whole session`
  quote: docs/02-design/features/multi-host-runtime.design.md › `SID=$(python3 -c 'import uuid; print(uuid.uuid4())')`
- Codex `source` cells cite binary strings or assumption A2, which are explicitly only leads. FR-2 requires a host-document, inspect/help reading, or observed trace; V-11.1 can show a skill read but cannot substantiate unrelated mappings such as `/new` or `/compact`. Obtain evidence for each mapped capability or mark the row appropriately before claiming parity.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.spec.md › ``source` cites the evidence: a host-doc section, a `grok inspect` / `--help` reading, or an`
  quote: docs/02-design/features/multi-host-runtime.design.md › `M: codex `/new` or `/compact` [DP11: strings `/new`, `/compact`]`
- The live-smoke record has no archive step. The plan promises a committed record in the archive before push; the design writes it under `docs/03-analysis` after 7c and explicitly leaves moving it undecided. Specify the post-smoke archive/commit step or reconcile the plan's record contract before Phase 7.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.plan.md › `docs/archive/<YYYY-MM>/multi-host-runtime/multi-host-runtime.live-smoke.md`
  quote: docs/02-design/features/multi-host-runtime.design.md › `Archiving is not settled.`
- The new hardcoded `~/.agents` and `~/.gemini` install paths conflict with the project invariant's only path exception, documented `~/.claude/...` install locations. The design claims these paths are already allowed, but that is not the invariant's text; reconcile the invariant with the operator-approved new roots before implementation.
  class: build
  quote: .h-mad/invariants.md › `no hardcoded path outside the skill's own directory (except documented`
  quote: docs/02-design/features/multi-host-runtime.design.md › `~/.agents/skills/h-mad`

## Should-fix
- The paired plan's AC census is stale: its published command claims 50 distinct spec AC IDs, while the same anchored-ID census on the current spec yields 51. Correct the measurement and ownership ledger, especially AC-8.5, so later gates do not use the old floor.
  class: measurement
  quote: docs/01-plan/features/multi-host-runtime.plan.md › `50 distinct AC ids`

## Nit
None
AUDIT-multi-host-runtime-design-v2-END
