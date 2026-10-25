## Summary
The design document is largely well-structured and aligned with the shared canonicaliser architecture, but its v1.6 updates were only partially propagated into the normative sections. Specifically, the Test Plan and AC-6.1/AC-3.3 descriptions still state pre-v1.6 unfixed expectations for `M-18`'s `M-14` cell, and the N-1 `.`/`..` walk rules (and D-2/D-3 root-refusal updates) are recorded in Version History or inline notes without updating the corresponding Detailed Design, Error Handling Strategy, Implementation Order, and Test Plan sections. Additionally, the Judge reap section misstates AC-5.1's `2.0 + REAP_GRACE_S + 1.0` s bound as `3.0 s` instead of `4.0 s`.

## Must-fix
- Test Plan and AC-6.1/AC-3.3 prose in `docs/02-design/features/tdd-gate-fail-opens.design.md` contradict `docs/01-plan/features/tdd-gate-fail-opens.spec.md` (v1.6, D-4) and the design's own REPRO softening table on the unfixed behaviour of `M-18`'s `M-14` cell — although lines 709–713 and 820–821 of the design note that the unfixed Codex gate denies `M-18 M-14` under `step3` with `judge-error`, the Test Plan row for ACs 3.1–3.3 still states `M-18 both allow, fixed and unfixed`, and the AC-6.1 Test Plan rows and prose state that the unfixed gate-equality check fails on `exactly M-4, M-5, M-6, M-7, M-8, M-11 and M-12` (and expectation-table on `M-2, M-3, M-9, M-10, M-13 and M-14`), omitting `M-18`'s `M-14` cell which fails both assertions on the unfixed tree per spec AC-3.3 and AC-6.1.
  class: build
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › `M-18 both allow, fixed and unfixed | 3.1–3.3, 3.5 |`
  quote: docs/01-plan/features/tdd-gate-fail-opens.spec.md › `M-18's M-14 cell additionally fails both assertions on the unfixed tree`
- The v1.6 N-1 component-walk rules required by `docs/01-plan/features/tdd-gate-fail-opens.spec.md` (FR-1 step 2 and FR-3) are absent from the normative design sections of `docs/02-design/features/tdd-gate-fail-opens.design.md` — skipping `.` components before walking so `.` never absorbs a subsequent `..`, and taking `os.path.dirname(current)` without opening an existing non-symlink directory on `..` (while still opening a symlink's referent), along with their pins (`test_dot_component_does_not_shift_dotdot`, `test_claude_dot_then_dotdot_into_production_denies`, `test_dotdot_through_unreadable_directory_is_lexical`) and mutations (`TI9`, `TI10`), appear only in the `v1.6` Version History entry and are missing from `### Canonicaliser`, `### Which component is opened, listed, or neither`, `## Components Changed / Added`, `## Implementation Order`, and `## Test Plan`.
  class: build
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › `The walk skips . components (mutation TI10; pins test_dot_component_does_not_shift_dotdot, test_claude_dot_then_dotdot_into_production_denies)`
  quote: docs/01-plan/features/tdd-gate-fail-opens.spec.md › `directory on the way does not make the target unresolvable.`

## Should-fix
- `## Error Handling Strategy`, `## Implementation Order`, and `## Test Plan` in `docs/02-design/features/tdd-gate-fail-opens.design.md` were not updated for the v1.6 D-2/D-3 root-refusal rules in `docs/01-plan/features/tdd-gate-fail-opens.spec.md` FR-3 — while `### Codex call sites` adds a v1.6 note that Codex refuses a non-traversable root (`os.access(root, X_OK)` false) with `judge-error` whatever the phase before any state walk, the preceding paragraph in `### Codex call sites` and the Codex bullet in `## Error Handling Strategy` still state without qualification that Codex root arm-2 results are mapped to `judge-error` only when governed, and `## Components Changed / Added`, `## Implementation Order` (T2, T3, T8), and `## Test Plan` omit `test_mode_000_project_dir_refuses`, `test_codex_mode_000_root_refuses_whatever_the_phase`, and mutations `CG-ROOT-CONJ`, `CG-ROOT-000`, and `CX-ROOT-ENTER`.
  class: build
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › `before any state walk, the Codex gate refuses`
  quote: docs/01-plan/features/tdd-gate-fail-opens.spec.md › `when the root is absent, not a directory, or not traversable`
- `### Judge reap` in `docs/02-design/features/tdd-gate-fail-opens.design.md` miscalculates AC-5.1's elapsed-time bound as `3.0 s` — with `REAP_GRACE_S = 1.0`, the formula `2.0 + REAP_GRACE_S + 1.0` equals `4.0 s`, which is what `docs/01-plan/features/tdd-gate-fail-opens.spec.md` AC-5.1 and the design's own `## Test Plan` state.
  class: build
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › `AC-5.1's bound is 3.0 s, which is`
  quote: docs/01-plan/features/tdd-gate-fail-opens.spec.md › `s = 4.0 s and`

## Nit
- `## Overview` in `docs/02-design/features/tdd-gate-fail-opens.design.md` still cites `Spec v1.4 (644f8bf6)` and `Plan v1.4 (1254595a)` even though later sections of the design incorporate Spec v1.5/v1.6 and Plan v1.5 decisions.
