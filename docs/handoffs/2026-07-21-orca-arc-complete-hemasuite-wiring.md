# Handoff — Orca adaptation arc COMPLETE (Tier-3/M1/M2 + live-e2e + auto-detect + HemaSuite wiring)

**Date:** 2026-07-21
**Branch:** main (both `Coding/skills` and `Coding/HemaSuite`)
**Project:** BrightGold70/skills (h-mad skill) + BrightGold70/HemaSuite (HPW)

## Session Summary
Cleared the **entire Orca adaptation backlog** in one session via an autonomous `/h-mad` loop, then closed the standing live-Orca gap and the last carries. Shipped to `skills` main: **Tier-3 worktree-parallel-multi-module-tdd** (`bba5123`), **M1 orca-file-diff-review-gates** (`8148db8`), **M2 orca-automations-scheduled-e2e** (`061c43c`), a **live-Orca e2e bugfix** (`33fedf8`), and **cmux pane title auto-detect** (`ba79898`). Shipped to `HemaSuite` main: **orca-review-and-e2e-scheduling** (M1 desk-check diff surfacing + M2 `hpw schedule-e2e`, `74f32601`, 7250/0, live smoke PASS). Also compacted the user-global `MEMORY.md` (20.4→11.0 KB). Everything merged + pushed; both repos in sync with origin; nothing in flight.

## Key Learnings
- **Live-Orca e2e caught 3 stub-masked bugs that 5 agy audits + 3 6a-prime reviews all missed.** The create-verbs (`worktree-create`, `automation-create`) extracted the response *envelope* `.id` instead of `.result.<resource>.id`, because the stub JSON *guessed* the shape (`.result.worktree.selector`). Rule: Orca create-verbs return the resource id at `.result.<resource>.id`; **never** fall through to the envelope `.id`. Update stubs to the real envelope+result shape so they guard reality.
- **Orca runtime facts (live-verified):** automations are agent-driven — valid `--provider` is `claude|codex|gemini` (NOT `agent`; Orca rejects unknown). `worktree create` requires `--repo`/targeting. `--trigger` and `--schedule`/`--cron` are mutually exclusive. Tier-2 orchestration (`dispatch`/`await`/`gate`) is **un-exercisable** — 0 Orca-hosted agents (`agents:[]`); transport (`read`/`send`/`wait`) works.
- **HPW gates Orca on `launcher_helpers.detect_profile()`, which returns `"cmux"` inside a cmux session** (cmux marker wins over `ORCA_*` env). To force the orca path for a live smoke: `HPW_PROFILE_OVERRIDE=orca` (highest precedence) + `orca` on PATH.
- **Operator decision:** HemaSuite reaches Orca via **direct `orca` CLI calls**, NOT `hmad-dispatch` — no cross-repo dependency on the h-mad skill; mirrors the §37 launch-profile precedent. All `orca` I/O behind one mocked `_run_orca` seam (B10).
- **cmux `hmad-dispatch` agent defaults were stale** (`codex→surface:5`, `agy→surface:2`) and silently misrouted. Replaced with `_cmux_find` — matches the single surface whose title's **leading word** is the agent token (`[terminal] "${token}[^A-Za-z]`, mirrors `_orca_find`); env pins still override; 0/2+ matches → UNRESOLVED (loud). agy flagged the first (unanchored) attempt as false-matching `vim codex_result` — leading-word anchor fixed it.
- **agy IS the Antigravity CLI** (v1.1.4, `/Users/kimhawk/.local/bin/agy`, surface:5) running a Gemini model — verified it was the intended auditor throughout, not raw Gemini (Antigravity is a Gemini-CLI fork by design).
- **MEMORY.md compaction:** the index is a pointer-only file — all detail belongs in topic files; trimming index hooks loses nothing. `[[wikilinks]]` reference topic files without the `.md` suffix (a `grep <file>.md` check false-flags them).

## Next Steps
1. **[BLOCKED] Tier-2 orchestration live e2e** — validate `task-create→dispatch→await→gate` end-to-end. Needs an Orca runtime with **hosted agents** (currently `agents:[]`). Not actionable until such agents exist.
2. **Re-run anemia-jmj live e2e** (carry from session start, never acted) — `hpw launch --project anemia_jmj --prompt "Anemia in hematological malignancies" --llm-provider agent --yes --status-json` on a cmux surface (daemon backend=claude + NLM up; `hpw doctor` first). Confirms the earlier launch-path-canonical fix.
3. **[suggested] review-pipeline-correctness feature** — next HemaSuite e2e-backlog cluster (A-P1-1/2/4) in `HemaSuite/.../docs/HemaSuite_improvement_backlog_2026-06.md`; via HPW `/h-mad`.
4. **[suggested] dose-token PubMed noise** → #37 topic-hygiene follow-on (E-P1-1, same backlog doc).

## Open / Blocked Items
- **Tier-2 orchestration e2e** — status: blocked on Orca-hosted agents (external prereq).
- **HemaSuite Orca wiring carries** — status: deferred, non-blocking. (a) full live desk-check visually opening the manuscript diff in Orca's editor (needs NLM + real manuscript); (b) a cron automation actually *firing* (needs a scheduling cycle). The create/list/remove lifecycle is live-proven.
- **anemia-jmj e2e / review-pipeline-correctness / dose-token** — status: deferred (pre-existing HemaSuite carries, not touched this session).
- **Low/speculative Orca candidates** — status: dropped as unnecessary (`linear` N/A, `computer`/`tab`, `status`, `automations show/runs/edit`).
- **`h_mad_derive_test_path.sh`** (skills repo) — pre-existing uncommitted dirty file, NOT ours; leave it.

## HemaSuite Backlog & Todos (not touched this session — carried)

The Orca arc was skills-repo work; the HemaSuite feature backlog sat untouched. Authoritative sources:
- `HemaSuite/docs/HemaSuite_improvement_backlog_2026-06.md` — the P0–P3 program (18 items).
- `HemaSuite/hematology-paper-writer/docs/03-analysis/e2e-findings-2026-07-17.md` — F1–F7 (SAPPHIRE-G synopsis) + G1–G5 / A-series (anemia-jmj review) live findings.

**Restored todos #7–#10 (from session-start READ, never acted):**
1. **#7 — Re-run anemia-jmj live e2e** to confirm the launch-path-canonical fix (`d2f8af0f`) closed **A-P0-1** (output-dir split across `anemia_in_hematological_malignancies/` + `anemia_jmj/`) and **A-P1-3** (KO grounded wrong notebook `9ec98cb7` not `3817ead8`). `hpw launch --project anemia_jmj --prompt "Anemia in hematological malignancies" --llm-provider agent --yes --status-json` (cmux surface; `hpw doctor` first).
2. **#8 — review-pipeline-correctness feature** (`/h-mad`): the A-series cluster from the anemia e2e —
   - **A-P1-2** `manuscript-review` doctype never resolves (`resolve doctype_missing`) → wrong quality rubric (root cause).
   - **A-P1-1** 0/13 sections accepted yet **exit 0** — quality-gate soft-fail masked as success.
   - **A-P1-4** 16 irrelevant references reach post-assembly audit; `01_introduction` grounding 0.00.
3. **#9 — dose-token PubMed noise** (F2 / E-P1-1): topic-hygiene follow-on to #37.
4. **#10 — watch** `_ko_notebooks` interactive fuzzy-match removal (behavior change from launch-path-canonical GREEN — a slug-less KO caller that relied on the `input()` path).

**Other open F/E-series (e2e-findings):** F1/F4 title-slug + registry fragmentation → capstone was `unified-project-store` (verify closed by the anemia re-run); F3 fold into #4 resource-parse; F6 synopsis-PostProcessor KO-wiring follow-on; F7 no-action.

**P0–P3 program (backlog doc, higher-level, un-scheduled):** P0-1 edition-anachronism citation guard · P0-2 manuscript path must not assert classification/risk/nomenclature · P0-3 EndNote PMID auto-resolution can bind the wrong paper · P1-1 `hpw doctor` hard-warn on dead LightRAG daemon · P1-2 NLM grounding for manuscript *editing* · P1-3 auto reference+nomenclature verify in revision flow · P1-4 version-filtered corpus query helper · P2-1..6 (first-class revise command, DocumentRevisor engagement, stats-figure PNG+EPS contract, DOCX figure embed, RecNum↔[N] alignment, CSA `.sav` ingest) · P3-1..6 (quality-checker numbered-heading detection, hardcoded abstract limit, pandoc numbering, `pyreadstat` missing, auto-register project, B4 heading matcher).

**Candidate-unimplemented plan features (no report doc — verify before picking up):** `antigravity-role-7-pilot`, `launcher-imperative-prompt-guard`, `protocol-quality-analyzer`, `r-api-index-real-package-verification`, `slide-guidance-section-slicing`.

## Context for Next Session

**Files touched this session (all merged + pushed):**
- skills (`main`): `h-mad/scripts/hmad-dispatch.sh` (Tier-3 worktree verbs + M1 file verbs + M2 automation verbs + `_json_extract` + `_cmux_find`), `h-mad/tests/test_hmad_dispatch.py` (30→114 tests), `h-mad/SKILL.md`, `h-mad/references/{orchestration-mode,agent-substrate}.md`, `docs/archive/2026-07/{worktree-parallel-multi-module-tdd,orca-file-diff-review-gates,orca-automations-scheduled-e2e}/`.
- HemaSuite (`main`): `hematology-paper-writer/tools/orca_integration.py` (new), `cli/{_commands,_parser,_main}.py`, `tests/{test_orca_integration,test_schedule_e2e_command}.py`, `HemaSuite_Project_Document.md` §38, `docs/archive/2026-07/orca-review-and-e2e-scheduling/`.
- Auto-memory (user-global, not a repo): `MEMORY.md` (compacted 20.4→11.0 KB) + `project_orca_adaptation_backlog.md`.

**Shipped commits:**
- skills: `bba5123` (Tier-3) → `8148db8` (M1) → `061c43c` (M2) → `33fedf8` (live-e2e fix) → `ba79898` (cmux auto-detect).
- HemaSuite: `74f32601` (orca-review-and-e2e-scheduling merge).

**Uncommitted changes:** none of substance — skills: only the pre-existing `h_mad_derive_test_path.sh`; HemaSuite: operational cruft only (`*.bak`, `.lock`, `telemetry.jsonl`, stray `docs/orca_vs_cmux_comparison.md`).

**To resume:**
```bash
cd /Users/kimhawk/Coding/skills        # h-mad skill (symlinked ~/.claude/skills/h-mad); main, in sync
# or: cd /Users/kimhawk/Coding/HemaSuite  # HPW; main, in sync
# Live Orca IS up (app running, runtime+graph ready): drive verbs via HMAD_SUBSTRATE=orca (h-mad) or HPW_PROFILE_OVERRIDE=orca (hpw)
# cmux panes: Codex=surface:4, agy=surface:5 (now auto-detected; env-pin no longer required)
```

**Related docs:**
- `Coding/skills/docs/archive/2026-07/*/` — full H-MAD trails for Tier-3/M1/M2.
- `Coding/HemaSuite/hematology-paper-writer/docs/archive/2026-07/orca-review-and-e2e-scheduling/` — HPW feature trail; `HemaSuite_Project_Document.md` §37/§38 (Orca substrate origination records).
- Auto-memory: `project_orca_adaptation_backlog.md` (full arc record).
