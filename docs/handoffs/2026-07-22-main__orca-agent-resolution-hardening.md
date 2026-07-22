# Handoff — Orca agent-resolution hardening (H1–H5) + report-file `/h-mad`

**Date:** 2026-07-22
**Branch:** main
**Project:** /Users/kimhawk/orca/skills (BrightGold70/skills)

## Session Summary

Started from `/handoff read` of the prior session (orca-skills-hardening) and worked its three optional follow-ons to completion, then chased the agent-resolution problems they surfaced all the way down. **Done and shipped to `main` (12 commits, all pushed):** (1) handoff READ now prefixes restored todos `[repo@branch]`; (2) a full 7-phase `/h-mad` shipped the `hmad-dispatch resolve <agent>` verb and validated **report-file transport** end-to-end (every audit/TDD/review verdict, zero screen-scrape); (3) `_orca_json` ok-guard extended to `dispatch`/`gate-resolve`/`await`; (4) `automation-*` wired into a committed live-e2e flow. Along the way, agent resolution (esp. Codex) was fully reworked: **H1–H5** in `docs/skill-monitoring.md` are all FIXED — worktree-scoped resolution, Codex preview aliases, a standalone report poller (H3), a session pin file + `pin`/`pin-agents` fail-loud (H4), and a **`launch` verb that captures a fresh agent's handle at spawn** (H5 durable fix). The one thing this repo can't fix — auto-identifying an *already-running* Codex pane — is filed as Orca issue #9870. Suite 413/0, git clean, zero open code items.

## Key Learnings

- **`orca terminal rename` is decoupled from resolution.** It sets a tab-UI title layer that `terminal list --json` does NOT surface. The `.title` `_orca_find` reads is the **OSC title the running program emits**: agy emits `agy` (resolvable), Codex emits its **cwd basename** (`skills`, never `codex`). A rename returns `{"ok":true}` while `.title` stays `skills` and `resolve codex` still finds 0 — verified live. This is the root cause of the entire Codex-identity class.
- **`orca terminal create … --json` returns `.result.terminal.handle` at spawn** — the durable identity capture. `hmad-dispatch launch <agent>` uses this: create + capture handle + pin, no title/preview dependence. The only reliable way to auto-identify Codex is to *own its launch*.
- **Codex preview decays**: the `gpt-N`/`OpenAI Codex` banner scrolls out of the Orca preview once the pane does work, so preview-based auto-detect (H2 alias `codex|gpt-[0-9]`) only matches a *fresh* pane. Persona line is "Sol", too generic to match.
- **Dispatching an agent to edit the very wrapper the coordinator polls with is a race** (H3): a `report-wait` fired while Codex was mid-save on `hmad-dispatch.sh` and died on a transient `syntax error near ')'`; `bash -n` was clean seconds later. Fix: the poll loop is now standalone `scripts/h_mad_report_wait.py` — poll it directly, never re-parsing the wrapper.
- **`pin-agents` silent rc=0 on a partial pin was itself a bug** — a run could proceed believing Codex was addressable when it wasn't. Now fails loud (rc=1, names the agent + env var). Caught only because the user challenged "is Codex clearly fixed?" — it wasn't; the honest re-test exposed it.
- **report-file transport is proven end-to-end** in a real `/h-mad`: agent writes `<path>` + `<path>.done`, coordinator polls the marker and reads the clean file — gate scores it directly, no dedent/sentinel/scrape. Used for 4 audit cycles + Codex RED/GREEN + agy 5e + agy 6a-prime.
- **Test-harness gotcha**: `run()` in `test_hmad_dispatch.py` strips all ambient `HMAD_ORCA_*` (F13) but re-applies the explicit `env=` param AFTER the strip, so tests still pass pins/pin-file via `env={...}`.

## Next Steps

Session arc is complete — nothing pending or blocked in-repo. Optional follow-ons:

1. `[suggested]` Wire the new `launch` verb INTO the `/h-mad` Phase-5d flow so an orchestrated run **auto-launches + pins** Codex/agy instead of assuming operator-launched panes — the verb exists (`h-mad/scripts/hmad-dispatch.sh` `_cmd_launch`) but `SKILL.md` §"Phase 5 (Implementation)" still assumes existing panes. This would make Codex identity zero-touch for every run.
2. `[suggested]` Track Orca issue #9870 (https://github.com/stablyai/orca/issues/9870) — if Orca surfaces the custom title OR a running-process field in `terminal list`, add it to `_orca_find` as a first-class signal and retire the preview-alias fallback (H2).
3. `[suggested]` The `automation-*` live-e2e flow (`h-mad/references/e2e-smoke.prompt.md`) is documented + tested but no live recurring job is scheduled — create one with `hmad-dispatch automation-create` if a nightly dispatch-surface health check is wanted.

## Open / Blocked Items

- **Auto-identifying an already-running (operator-launched) Codex pane** — blocked on Orca-side API (issue #9870). Mitigated in-repo: `launch` (owned spawn) needs no auto-detect; `pin`/`pin-agents` handle the adopt-existing case with an explicit handle. Not a blocker for any current flow.

## Context for Next Session

**Files touched this session (see `git log 47ddf05..debcc81`):**
- `h-mad/scripts/hmad-dispatch.sh` — new verbs `resolve`, `pin`, `pin-agents`, `launch`; worktree-scoped `_orca_find` + preview aliases; `_orca_json` guard on dispatch/gate-resolve/await; report-wait delegates to the standalone poller
- `h-mad/scripts/h_mad_report_wait.py` (new) — standalone stdlib report poller (H3)
- `h-mad/tests/test_hmad_dispatch.py`, `h-mad/tests/test_h_mad_report_wait.py` (new) — 413 tests
- `h-mad/references/agent-substrate.md`, `h-mad/references/orchestration-mode.md`, `h-mad/SKILL.md` — resolution precedence, launch/pin docs, automation e2e recipe, rename-decoupling
- `h-mad/references/e2e-smoke.prompt.md` (new) — dispatch-surface self-test prompt
- `docs/skill-monitoring.md` — H1–H5 (all FIXED); H5 links Orca #9870
- `docs/orca-feature-request-terminal-identity.md` (new) — filed issue draft
- `handoff/SKILL.md` — READ mode now prefixes restored todos `[repo@branch]`
- `docs/archive/2026-07/dispatch-resolve-verb/` — the `/h-mad` closure docs (11 artifacts)

**Uncommitted changes:** none (clean, in sync with origin/main).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main
export PATH="$HOME/.claude/skills/h-mad/bin:/opt/anaconda3/bin:$PATH"   # hmad-dispatch + python3 w/ pytest+jsonschema (brew py3.14 lacks jsonschema)
python3 -m pytest handoff/scripts/test_handoff_paths.py h-mad/tests/ -q   # expect 413 passed
# Live Orca dispatch: hmad-dispatch env  (pin codex if it shows UNRESOLVED — H5)
```

**Related docs:**
- `docs/skill-monitoring.md` — standing bug/improvement registry (F1–F14, G1–G6, A1–A2, V1, H1–H5, all resolved)
- `docs/orca-feature-request-terminal-identity.md` — Orca #9870 source
- Memory: `~/.claude/projects/-Users-kimhawk-orca-skills/memory/` (H-MAD Orca dispatch entries)
