SPEC-AUTHOR: DONE version=v1.0 path=/Users/kimhawk/orca/skills/docs/01-plan/features/agy-coder-fallback.spec.md lines=458 sha256=0403a5469af4bef27da6319eb59b9f9a6fbfa8a411feb82c0bb9ecfecf290662

premises verified (tree at a8d9ba99):
- h-mad/scripts/h_mad_state_schema.json: read with cat. It declares codex_status and fallback_agent(grok|claude|null) and sets "additionalProperties": false, so the new keys must be declared there.
- h-mad/hooks/h-mad-tdd-gate.sh: grep for _refuse kinds. The gate-specific kinds are codex-authorship, fallback-grok and fallback-invalid; the judge's DENY kinds come through BASH_REMATCH; the HMAD_CODEX_UNAVAILABLE / codex-escape / command -v codex condition was read in place.
- h-mad/scripts/h_mad_tdd_judge.py: read in slices. Record(key,codex_status,state_file,fallback); ESCAPE_STATUSES={unavailable,exhausted}; JUDGE_BUDGET_S=40.0; format_state_line produces the TDD-STATE line.
- h-mad/scripts/h_mad_assemble_tdd.py: grep. --agent choices=("codex","grok"); timeout is 1500 for grok, else 900; command_block derives the non-codex first line; the halt token is "ASSEMBLE-TDD: HALT <reason>", exit 2.
- h-mad/tests/test_h_mad_assemble_tdd_agent.py: test_prompt_file_is_agent_independent and test_state_fallback_agent_is_not_read both exist.
- h-mad/hooks/h-mad-codex-tdd-gate.py: read in slices. While step5 is active it refuses any shell command outside _safe_shell_command or the operator allowance (marker M:F2-WIRE). It admits non-.py writes under /tmp (_tmp_report_target) and refuses writes to .h-mad/phase5-shell-allow (M:SA-GUARD).
- ~/.gemini/antigravity-cli/builtin/skills/agy-customizations/docs/hooks.md: read whole (389 lines). The payload carries workspacePaths and artifactDirectoryPath but no cwd field; the handler cwd is the hooks.json directory; the default handler timeout is 30 s; SessionStart is now listed.
- ~/.gemini/config/hooks.json: holds the global orca-status PreToolUse "*" hook, whose script prints {"decision":"ask"} (~/.orca/agent-hooks/antigravity-hook.sh).
- write_to_file arg key TargetFile: seen in docs/03-analysis/probes/multi-host-runtime/rehearsal/agy-G7-tool-write-then-link-read.log. That is stream-json tool_info.parameters, not the hook payload, so the hook-payload key is still unobserved.
- agy tool inventory: 58 distinct tools (python count of init.tools) in live-agy-2026-10-01.log. It includes sed_file, notebook_edit, notebook_execution, send_command_input and call_mcp_tool.
- Codex gate wiring: HemaSuite tracks .codex/hooks.json with "python3 $HOME/.agents/skills/h-mad/hooks/h-mad-codex-tdd-gate.py"; this repo has no .codex (ls).
- This repo excludes /.agents/ in .git/info/exclude (git check-ignore -v).
- `git ls-files h-mad | xargs grep -ln codex-implementer-prompt | wc -l` = 20 files.
- New names (agy_status, HMAD_AGY_UNAVAILABLE, agy-authorship) have zero hits under h-mad (git grep). step5:agy_tdd_hook_unverified appears only in agy-runtime.md (plus brainstorm/archive).
- Brief fix 3 source: HemaSuite notebooklm-integration-interface analysis.v1 F-3 and the handoff 2026-10-16-main__notebooklm-feature-complete. SKILL.md 5d defines halt step5d:red_wrong_reason.

findings applied: none (first draft). Orchestrator scope addition applied: brief fix 3 is FR-9, located structurally ("RED acceptance evidence" item 1, the WIRE-PIN paragraph, the GREEN variant, the SKILL.md 5d halt), with no line numbers.

values swept: `grep -noE '\b(1500|900|40\.0|40|60|30|20)\b'` over the spec. The hits are consistent: 60 is derived as JUDGE_BUDGET_S(40)+20 and is stated as a function, so the wiring check reads it from the module. 1500 is provisional and gets replaced by the FR-8 formula over the tracer readings. A line-pin grep (`:[0-9]+`) found 0.

contradictions found:
1. The brainstorm says run_command is "the stated residual, parity with Codex's shell". The tree says Codex's shell is NOT a residual: it uses a command-shape allowlist during step5. The spec takes the tree (FR-6/D-1) and says so explicitly.
2. The brainstorm risk row says "Every codex-authorship and fallback-grok behaviour stays byte-compatible". Only the message bytes stay identical. With the operator's "fallback only when both peers out" rule, codex_status=exhausted on a machine with agy on PATH now refuses Claude with agy-authorship. FR-3 states this, and notes that existing fixtures keep their outcomes because their PATH excludes agy.
3. The brainstorm and agy-runtime.md list four write-capable tools. The observed inventory has more (sed_file, notebook_edit, send_command_input, notebook_execution, call_mcp_tool), so FR-4 uses matcher "*" with default-deny class (d).
4. Rule-15 extension: FR-7 states the flag as a same-agent rule over every code-review leg, which goes beyond the operator's agy-only wording. This is not decided silently: it is OQ-1 (recommended yes; the revert is narrowing to agy only).

placeholder scan: `h_mad_precheck_doc.py --phase spec`: PRECHECK: PASS issues=0. Three advisories are kept deliberately:
- `h-mad/hooks/h-mad-agy-tdd-gate.py`: a new file this feature creates.
- `.agents/hooks.json`: the new per-project wiring file.
- `.codex/hooks.json`: HemaSuite's file, cited as precedent; it is not in this repo.

owed by other documents:
- h-mad/references/agy-runtime.md §"Hooks" says "There is no SessionStart", but the current agy hooks.md lists SessionStart. Re-check it against agy 1.3.6.
- The plan/design must fix the exact TDD-STATE line shape (FR-3) and the read-only allowlist (FR-4 class a). Mutation specs anchored on STATE_ACTIVE_RE / M: markers in h-mad-tdd-gate.sh will need re-anchoring.
- Operator: OQ-1 (flag Codex-reviews-Codex) and OQ-2 (narrow the .git/info/exclude /.agents/ entry, or force-add .agents/hooks.json).
- Side observation, not in scope: this skills repo has no .codex/hooks.json, so Codex writes here are not gated by h-mad-codex-tdd-gate.py.
