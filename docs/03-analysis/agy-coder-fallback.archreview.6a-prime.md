# Phase 6a-prime Final Architectural Review — `agy-coder-fallback`

**Git Range Reviewed:** `d280af07aefa7921ac39e722933913924d0041c0..ae541fb0c2d2ef8e8cc6f9498d6fbf34005a3f34`  
**Worktree Root:** `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback`  
**Scope:** Pre-merge Phase 5 implementation (Tasks 0–19; FR-1 through FR-7, FR-9, FR-10; post-merge Tasks 20–22 / FR-8 excluded by spec D-13).

---

## 1. Cross-Module Coupling & Architectural Boundaries

- **Single Authorship Resolver (FR-2 / FR-3):**
  - `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/h-mad/scripts/h_mad_tdd_judge.py` (`resolve_implementer`, `format_state_line`, `main_implementer`) is the sole decision point reading `HMAD_CODEX_UNAVAILABLE`, `HMAD_AGY_UNAVAILABLE`, `PATH` (`shutil.which`), and the state record (`implementer`, `codex_status`, `agy_status`, `fallback_agent`).
  - `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/h-mad/hooks/h-mad-tdd-gate.sh` (`STATE_ACTIVE_RE`, `_read_state`, and the top-level refusal precedence block) consumes the 5th comma-delimited field (`codex|agy|peers-out|invalid:<pct>`) on `TDD-STATE: active` lines without re-deriving availability from `PATH` or `HMAD_*` environment variables.
  - Precedence in `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/h-mad/hooks/h-mad-tdd-gate.sh` strictly enforces: (1) `implementer-invalid` across all active records before any peer or fallback check, (2) `codex-authorship` / `agy-authorship` when any active record resolves to a peer, and (3) existing `fallback_agent` gating when all active records resolve to `peers-out`.

- **Shared Policy Extraction & Fail-Closed Import Discipline (FR-6 / FR-4):**
  - `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/h-mad/scripts/h_mad_target_identity.py` hosts the 17 functions and 8 constants (`_POLICY_NAMES`, 25 bindings total) previously private to the Codex gate, referencing `fold_py_suffix` directly in-module.
  - `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/h-mad/hooks/h-mad-codex-tdd-gate.py` imports all 25 symbols by name inside a guarded `try ... except Exception as exc: _POLICY_IMPORT_ERROR = exc` block, re-raises `_POLICY_IMPORT_ERROR` as the first statement of `_main_guarded()` (preserving `# M:G2` and routing through `_deny("judge-error", ...)`), and fails closed in `_self_check()` (`CODEX-TDD-GATE: FAIL policy-import` on stderr, exit 2).
  - `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/h-mad/hooks/h-mad-agy-tdd-gate.py` imports the shared policy from `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/h-mad/scripts/h_mad_target_identity.py` and the judge from `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/h-mad/scripts/h_mad_tdd_judge.py` inside `_evaluate(payload)`, ensuring any import or runtime failure after step 2 is caught by `main()` and emitted as a single JSON object `{"decision": "deny", "reason": "... kind=judge-error"}` with exit code `0`.

- **Hook Wiring & Assembler Gate (FR-5):**
  - `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/h-mad/scripts/h_mad_hook_wiring.py` (`check_agy`, `AGY_GATE_PATH`) validates `<root>/.agents/hooks.json` in exact 7-step precedence (`WIRED`, `UNWIRED` with rc 0, `UNREADABLE` with rc 2).
  - `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/h-mad/scripts/h_mad_assemble_tdd.py` (`TIMEOUT_DEFAULTS`, `_check_agy_wiring`, `main`) gates `--agent agy` before `assemble()` is called, halting with `H-MAD-ASSEMBLE-TDD: HALT reason=agy_tdd_hook_unverified` (exit 0 on `UNWIRED`, exit 2 on `UNREADABLE` or unexpected output) and appending to `implementation_authors` only after a successful write of the assembled prompt.

- **Append-Only State Mutation & Phase 7 Review Independence (FR-1 / FR-7):**
  - `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/h-mad/scripts/h_mad_state_schema.json` appends `implementer`, `agy_status`, `implementer_switch`, `review_independence`, and `implementation_authors` after `fallback_agent` using only `_MiniDraft7`-supported keywords.
  - `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/h-mad/scripts/h_mad_state_validate.py` (`rfc3339_datetime`, `_semantic_ok`, `property_valid`, `classify`) enforces ASCII RFC 3339 validation on `implementer_switch.ts` before either validator tier (`jsonschema` or `_MiniDraft7`), preventing backend divergence.
  - `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/h-mad/scripts/h_mad_state_write.py` (`APPEND_ONLY`, `_parse_append`, `merge_fields`) rejects `--set` on `review_independence` and `implementation_authors`, rejects same-key `--set` + `--append`, and performs locked read-modify-write appends.
  - `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/h-mad/scripts/h_mad_phase7_preconditions.py` (`_review_independence_warnings`) validates `review_independence` and `implementation_authors` entries via `property_valid` and emits `review_independence_malformed`, `review_non_independent`, and `review_independence_unrecorded` across all implementers.

---

## 2. Pattern & Reference Documentation Compliance

- **FR-9 New-Caller Carve-Out:**
  - All six copies of the canonical three-sentence carve-out block are present and verified by `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/h-mad/tests/test_h_mad_new_caller_carveout_copies.py`:
    1. `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/h-mad/references/codex-implementer-prompt.md` (3 copies: `L1` in `### 5d (RED) Procedure`, `L2` in `### Shared Guardrails`, `L6` in `### Output Format`)
    2. `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/h-mad/SKILL.md` (`L3` in `### Phase 5 (Implementation) sub-steps`)
    3. `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/h-mad/references/failure-recovery.md` (`L4` in `step5d:red_wrong_reason:<module>`)
    4. `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/h-mad/scripts/h_mad_assemble_tdd.py` (`L5` in `assemble()`)
- **FR-10 Documentation Alignment:**
  - `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/h-mad/SKILL.md`, `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/h-mad/references/agy-runtime.md`, `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/h-mad/references/state-schema.md`, `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/h-mad/references/failure-recovery.md`, and `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/h-mad/references/codex-implementer-prompt.md` accurately document peer-implementer routing, `.agents/hooks.json` preToolUse wiring, review-independence attribution, and implementer-neutral prompt headings.

---

## 3. Axis B Invariant Compliance

Checked against `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/.h-mad/invariants.md` and `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/h-mad/invariants.base.md`:

- **B1 — Subprocess timeouts:** Every `subprocess.run` call across `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/h-mad/scripts/h_mad_tdd_judge.py` (`timeout=5`), `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/h-mad/hooks/h-mad-agy-tdd-gate.py` (`timeout=5`), and `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/h-mad/scripts/h_mad_assemble_tdd.py` (`timeout=5`) carries an explicit `timeout=`. Stdin read in `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/h-mad/hooks/h-mad-agy-tdd-gate.py` (`_read_stdin_bounded`) uses `select.select` with a bounded 2.0s deadline.
- **B2 — Closed enumerations & fail-closed gates:**
  - `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/h-mad/hooks/h-mad-agy-tdd-gate.py` classifies tools into closed `CLASS_A` (11), `CLASS_B` (5), `run_command` (class c), and routes every other tool name to class (d) (`tool-not-admitted` when active, `judge-error` when unknown).
  - `_deny(kind, detail)` validates `kind in GATE_KINDS | _judge_kinds()` and substitutes `"judge-error"` if outside the closed set, stripping newlines from `detail` and appending `f" kind={kind}"` as the final whitespace-delimited token.
  - `T2a` in `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/h-mad/hooks/h-mad-agy-tdd-gate.py` explicitly checks `os.path.isdir(identity.target)` and denies with `judge-error` before `T3`, preventing `read_chain` from walking a directory's own `docs/.bkit-memory.json`.
- **B3 — Mutation & wire-pin integrity:**
  - `.h-mad/wires.jsonl` at `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/.h-mad/wires.jsonl` records all 6 architectural wires (`WIRE-1` through `WIRE-6`), each backed by dedicated unit and mutation-spec pins.
  - Recorded 5d orchestrator decisions (`/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/docs/03-analysis/agy-coder-fallback.authoring/acf_5d_task0_gate.md`, `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/docs/03-analysis/agy-coder-fallback.authoring/acf_5d_task1_decisions.md`, `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/docs/03-analysis/agy-coder-fallback.authoring/acf_5d_task2_decisions.md`, `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/docs/03-analysis/agy-coder-fallback.authoring/acf_5d_task3_decisions.md`, `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/docs/03-analysis/agy-coder-fallback.authoring/acf_5d_task4_decisions.md`, `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/docs/03-analysis/agy-coder-fallback.authoring/acf_5d_task6_decisions.md`, `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/docs/03-analysis/agy-coder-fallback.authoring/acf_5d_task8_decisions.md`, `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/docs/03-analysis/agy-coder-fallback.authoring/acf_5d_task12_decisions.md`, `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/docs/03-analysis/agy-coder-fallback.authoring/acf_5d_task15_decisions.md`, and `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/docs/03-analysis/agy-coder-fallback.authoring/acf_5d_task18_19_record.md`) are transparent, well-reasoned, and preserve all invariant guarantees.

---

## 4. Dead Code & Debug Artifacts

- None found. All 25 moved symbols were cleanly removed from `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/h-mad/hooks/h-mad-codex-tdd-gate.py` and placed in `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/h-mad/scripts/h_mad_target_identity.py`. No leftover debug prints, commented-out code blocks, or unused imports exist in any modified production script or hook.

---

## 5. Integration Test Coverage

- Comprehensive unit, differential, and integration tests cover every requirement and wire:
  - `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/h-mad/tests/test_h_mad_agy_tdd_gate.py` (contract, activity, tool classes a–d, T1–T7, Cwd resolution, self-check)
  - `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/h-mad/tests/test_h_mad_agy_tdd_gate_differential.py` (51-cell target and shell differential matrix between Codex and agy gates)
  - `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback/h-mad/tests/test_h_mad_new_caller_carveout_copies.py` (6-locator structural + canonical text pin for FR-9)

---

## 6. Issues Found

- **Critical:** None.
- **Important:** None.
- **Minor:** None.

ASSESSMENT: READY_TO_MERGE
