# Handoff — dispatch prompt-size limits reframed by transport; pane frontier 61 KB → 92 KB

**Date:** 2026-07-30
**Branch:** main
**Project:** orca/skills (h-mad + handoff skills)

## Session Summary

Started as a skill-candidate re-evaluation (backlog already drained — nothing actionable), pivoted to a size-limit audit of the h-mad dispatch path. Found the docs conflated two different ceilings (transport vs agent-response) and understated both, then **live-falsified** the pane-path "~61 KB largest confirmed answered" ceiling with a 92,055 B probe that answered cleanly. Reframed every size claim by transport (exec = uncapped/ARG_MAX; pane = 92 KB confirmed), updated both halves (docs + assembler code + doc-tests, mutation-verified), and shipped. All green, committed + pushed (HEAD `e359a58`).

## Key Learnings

- **The "61 KB pane frontier" was false — pane answers ≥92 KB.** Live probe 2026-07-30: a 92,055 B prompt via `hmad-dispatch send` file-indirection to a live agy pane (Gemini 3.1 Pro) returned `PROBE_OK <token>`. Frontier raised 61,493 → 92,055 B.
- **The reflow-not-silence lesson reproduced live.** The reply fragmented across TUI redraw frames (`…VERIF` then a lone `Y`), so my live `tail` poll read `>` for 114 s and looked silent — the `--from-start` full-buffer read recovered the complete token. Never diagnose pane silence from a tail. [[feedback_hmad_agy_gemini_tui_capture]]
- **Two ceilings, not one.** Transport: codex stdin mechanically uncapped; agy `--print` arg bounded by ARG_MAX (measured `getconf ARG_MAX` = 1,048,576). Agent-response: the old "49 KB normal / 53 KB silent" was a delivery-mode artifact (a *paste*, never file indirection) — debunked long ago and now doubly so. `exec` has no transport frontier at all.
- **Orca pane titles lie (confirmed again).** The pane titled "Codex - skills repo" was actually running Antigravity/Gemini (agy); the "skills" pane was the real Codex. Identity by title is unreliable (H4/H5) — resolve by banner/paneKey.
- **A fresh `agy` launch (1.1.8) hung at "not signed in"** while the pre-existing pane (1.1.5) was authenticated. `hmad-dispatch launch agy` does not guarantee a usable REPL — verify the banner reaches an authenticated `>` before dispatching.

## Next Steps

1. **[suggested] Get a second pane datapoint >92 KB** to widen the confirmed frontier beyond a single probe — stage a ~110 KB prompt, `hmad-dispatch send agy <file>`, `read agy --from-start`, grep the sentinel. Only one clean 92 KB point is on record. — `h-mad/references/agent-substrate.md` §"Prompt size".
2. **[suggested] Dogfood 5e verifier full-suite step (new step 4)** on a real `/h-mad` 5e — still deferred from the 2026-07-29 arc. — `h-mad/references/codex-verifier-prompt.md` step 4.

## Open / Blocked Items

- **#2 `wait --not-while-regex 'Waiting for background terminal'` false-idle guard** — status: delegated to a HemaSuite session (2026-07-29), awaiting result. Unit-tested only (`h-mad/tests/test_hmad_dispatch.py`); needs a live pane dispatch that delegates to a background terminal. repo: `/Users/kimhawk/orca/HemaSuite/hematology-paper-writer` · branch: `main` · worktree: main (Orca-managed).
- Second-datapoint + 5e-dogfood (Next Steps 1–2) — status: deferred, not blocking.

## In-Flight Processes

None — all probe dispatches completed; the stuck fresh agy pane (`term_d0032d08`) was closed at end of session.

## Context for Next Session

**Files touched this session (all committed + pushed, `e359a58`):**
- `h-mad/scripts/h_mad_assemble_audit.py` — `CONFIRMED_OK` 61,493 → 92,055; size_status + warning bands rebased
- `h-mad/tests/test_h_mad_assemble_audit.py` — 2 band tests recalibrated (fillers 3200/3500), mutation-verified
- `h-mad/references/agent-substrate.md` — 92,055 B table row + exec-path "no frontier" section + reframe
- `h-mad/SKILL.md` — 4 size-claim sites reframed by transport
- `h-mad/scripts/hmad-dispatch.sh` — transport-scoped comments
- `h-mad/tests/test_hmad_dispatch.py` — comment range fix

**Env side effects (not git):**
- `.h-mad/orca-pins.env` repinned to LIVE handles (agy→`term_0749cce9`, codex→`term_279f609a`); prior pins were dead. Improvement, left in place.
- Probe appended one turn to the agy review pane (`term_0749cce9`); its prior review scrollback backed up to session scratchpad `agy_review_backup.txt`. Nothing lost.

**Uncommitted changes:** none (local `main` = `origin/main` `e359a58`).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main && git pull --ff-only
/opt/anaconda3/bin/python3 -m pytest h-mad/tests/ -q   # 744/0
```

**Related docs:**
- `h-mad/references/agent-substrate.md` §"Prompt size" (the frontier table + exec section)
- Prior handoff: `docs/handoffs/2026-07-29-main__verifier-dogfood-and-handover.md`
