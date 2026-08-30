# Handoff — h-mad dispatch inherits the codex/agy CLI model setting

**Date:** 2026-08-31
**Branch:** main
**Project:** /Users/kimhawk/orca/skills

## Session Summary

Started as "pin codex dispatch to gpt-5.6-sol high", ended as the opposite and better change: `hmad-dispatch exec codex` now pins *nothing* and inherits the codex CLI's own configured model and reasoning effort, the same way `exec agy` always has. Along the way `exec codex` gained a working `--effort` (it used to refuse the flag outright), mapped to `-c model_reasoning_effort=<e>` since codex has no such flag. Shipped and merged to `main` at `2a62916`; suite 2278 green on the merged tree, anchors 300/300, `assemble_tdd` mutations ALL_CAUGHT 24/24. Both feature branches deleted, local and remote. Done — no owed work.

## Key Learnings

- **`$CODEX_HOME` is not `~/.codex` under Orca.** It points at `~/Library/Application Support/orca/codex-accounts/<id>/home`, whose `config.toml` said `gpt-5.6-sol` / `high` (edited that morning). `~/.codex/config.toml` said `gpt-5.6-luna` / `medium` and had not been touched since July. Reading the stale one is what made "the config default is broken, so pin a model" look true — a whole correct-looking fix built on the wrong surface. Read `$CODEX_HOME` from the environment before concluding which config governs.
- **Codex has no `--effort` flag.** Reasoning effort is a config override: `-c model_reasoning_effort=high`. `-c` parses the value as TOML and falls back to the raw string, so a bare `high` lands correctly. The key name is confirmed by `config.toml` already carrying `model_reasoning_effort`.
- **A pin in the assembler silently outranks the CLI.** The failure mode is not an error — it is that the model shown in the TUI and the model 5d/5e actually runs drift apart, invisibly, forever. Inherit-by-default makes one setting move both. `--model`/`--effort` survive as per-dispatch overrides, which is also the escape hatch if the configured model is ever one that cannot execute tools.
- **agy's effort is baked into the model label.** Its setting is `model` in `~/.gemini/antigravity-cli/settings.json`, a display label like `Gemini 3.1 Pro (High)`; there is no separate effort knob to inherit. "Change the effort" for agy means picking a different model row.
- **Score a tool-execution probe on the side effect, never the `STATUS:` line.** `gpt-5.6-luna` writes fluent prose while every tool call dies, so it returns a well-formed `STATUS: BLOCKED`; a model that works and a model that cannot execute anything both produce a plausible verdict. The marker file (`printf > marker.txt`, then `cat` it) is the discriminator. The codex session header at the top of `--log` names the resolved `model:` and `reasoning effort:` — that is the cheap check that the run used what you think it did.
- **Current-state resolution is not change-propagation.** Proving "no flags → sol/high" only shows what the config says today. The claim the user actually cared about needed the config flipped to a different model, re-probed, and restored — with sha256 verified identical afterwards. Both agents behaved; neither was assumed.
- **`ls -t <dir>/*.log` is dead under this shell's rtk rewrite** — it errors with `invalid value '<path>' for '--time <FIELD>'`, so newest-file discovery silently yields nothing. Use `sorted(dir.glob(...), key=lambda p: p.stat().st_mtime)` in Python instead.
- **A trap-based restore still fires under the 2-minute tool timeout** (SIGTERM → exit 143), but confirm the file rather than trusting it: the surrounding command reported failure while the restore had in fact completed.

## Next Steps

1. [suggested] Audit the 8 remote-only branches before pruning any — same containment check used this session: `git rev-list --count main..origin/<branch>` must be 0. They are `feat/agent-identity-os-evidence`, `feat/await-surfaces-lifecycle-rejection`, `feat/loop-backlog-orchestration-findings`, `feature/audit-cycle-verb`, `fix/dispatch-injection-and-ack`, `fix/j40-review-evidence-gate`, `fix/reject-lifecycle-rejected-worker-done`.
2. [watch, not an action] If a real 5d/5e dispatch ever exits `rc=124`, suspect the assembler's `--timeout 900` before suspecting the model — high effort lengthens runs and the timeout was calibrated when nothing set effort at all. `h-mad/scripts/h_mad_assemble_tdd.py` (`--timeout` default).

## Open / Blocked Items

None. The feature shipped, merged, and both its branches are deleted; no claim is held and nothing is parked in another repo or worktree.

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/hmad-dispatch.sh` — codex `--effort` → `-c model_reasoning_effort`; exec-pane rejection dropped
- `h-mad/scripts/h_mad_assemble_tdd.py` — `DEFAULT_MODEL`/`DEFAULT_EFFORT` → `None`; flags emitted only when given
- `h-mad/SKILL.md`, `h-mad/references/agent-substrate.md` — overrides-not-defaults; `$CODEX_HOME ≠ ~/.codex` under Orca
- `h-mad/tests/test_h_mad_assemble_tdd.py`, `test_hmad_dispatch_exec.py`, `test_hmad_dispatch_exec_pane.py`
- `h-mad/tests/mutation-specs/assemble_tdd.json` — pin mutations replaced by `hardcode-a-model-into-the-block` + `drop-the-model-and-effort-overrides`

**Uncommitted changes:** none — `main` is clean and level with `origin/main` at `2a62916`.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main
# verify the tree is still green (~5.5 min; python3 here is 3.14 and has no pytest)
/opt/anaconda3/bin/python -m pytest h-mad/tests -q
python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors $(ls h-mad/tests/mutation-specs/*.json)
# what any dispatch will actually run, without pinning anything:
grep -E '^model|^model_reasoning_effort' "$CODEX_HOME/config.toml"
python3 -c "import json;print(json.load(open('$HOME/.gemini/antigravity-cli/settings.json'))['model'])"
```

**Related docs:**
- `h-mad/SKILL.md` §"Exit-code dispatch for 5d/5e" — the recipe now carries no `--model`
- `h-mad/references/agent-substrate.md` — the `exec` row states both config sources
- `docs/learnings.md:100` — a dated 2026-08-20 entry still prescribing `--model gpt-5.5`; historical record, superseded by this session's entry
