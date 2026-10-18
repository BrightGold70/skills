# Plan: hpw-duplicate-copy-retirement

**Status:** Draft, awaiting user approval. Nothing has been moved or deleted.
**Written:** 2026-10-18 (handoff Next Step 4 from `2026-08-09-main__j29-out-clobber-guard.md`)

## Executive Summary
This repo tracks a 195-file copy (239 before upstream `df4a0664` untracked its bytecode) of `hematology-paper-writer/` that HemaSuite has since developed
far past (1767 commits on that directory there vs 8 here; last change here 2026-03-12). The
investigation found that the copy here is **almost entirely a stale snapshot, not a fork**: HemaSuite
deliberately deleted, split or moved nearly everything that exists only here. Exactly one piece of
work is unique to this copy and has to be rescued before anything is removed: the **HBV
reactivation project scaffold** from `a6950ef`. The plan is to rescue that, then retire the copy.

## Findings (measured 2026-10-18)

**Lineage.** Added here 2026-02-23 (`3e07c9a` "Consolidate skills"). HemaSuite began tracking
its copy 2026-03-07. Only two commits here touched it after that date:

| Commit | Date | Content | Still unique? |
|---|---|---|---|
| `0792725` | 03-09 | 52 `__pycache__` files, 0 line changes | No (build artefacts) |
| `a6950ef` | 03-12 | HBV project scaffold: `HBV_reactivation_in_hematological_diseases_202603121315.md` (142 lines), `project_notebooks/HBV reactivation in hematological diseases.skills_context.json`, `research_topic.json`, `literature_seed.json`, and a 10-line `research_workflow.py` change | **Yes** for the `.md`, the `skills_context.json` and `research_topic.json`. `literature_seed.json` is already in HemaSuite byte-identical, and HemaSuite deleted `research_workflow.py` outright in `ae9fc028` ("terminal deletion of ResearchWorkflow") |

**"Only here" files (~80 tracked): HemaSuite removed them on purpose.**

| Path(s) | Fate in HemaSuite |
|---|---|
| `cli.py` | split into packages, `d1262b0a` (2026-03-18) |
| `journal_loader.py` | deleted as "dead+broken journal_loader shadow", `8daa8acc` (2026-07-09) |
| `ui/`, `hpw-ui/` | moved in the Dual IPC architecture change, `8bb4bd2c` (2026-04-05) |
| `tools/draft_generator/` (unique parts) | ResearchWorkflow terminally deleted, `ae9fc028` (2026-07-16) |
| `phases/phase10_resubmission`, other `phases/*` extras | dead-code cleanup, `e3cc4732` (2026-04-03) |
| `docs/01-04` plan/design/analysis/report for `hpw-recipe3-upgrade`, `hpw-skill-improvements`, `hpw-improvements-batch2` | archived under HemaSuite `docs/archive/2026-04/` (`4311c8e4`) |
| `Asciminib_CML_Review_Blood_Research.docx`, `Asciminib_CML_Systematic_Review_HPW-202602121021.docx`, `asciminib_cml.docx`, `sr_asciminib_…leukemia.json` | removed in HemaSuite; **verified byte-identical** (`cmp`) in HemaSuite history at `6301a7bd^`, `80b70097^` (both docx), `cfab2792^` respectively, plus a vendored copy under `hemasuite/src-tauri/sidecar/vendor/hpw/` at `8bb4bd2c^`. No rescue needed |
| `HBV_reactivation_…_202603121315.md`, HBV `skills_context.json` | **never in HemaSuite, on disk or in git** |

**42 tracked files differ** (`SKILL.md`, `CLAUDE.md`, `phase_manager.py`, most of `tools/`, …).
None of the differences come from changes made here after 2026-03-07 except `research_topic.json`
(the HBV topic, part of the rescue set). HemaSuite's side is the maintained one.

**Nothing consumes this copy.** `~/.claude/skills/` has no `hematology-paper-writer` link.
h-mad's references are path patterns for the HemaSuite layout
(`h_mad_derive_test_path.sh:21`) or comments, not reads of this directory. It holds no
`tests/test_h_mad_*.py` (established 2026-08-09).

## Plan

1. **Rescue the HBV scaffold into HemaSuite** (in HemaSuite, on its own branch):
   - copy `HBV_reactivation_in_hematological_diseases_202603121315.md` and
     `project_notebooks/HBV reactivation in hematological diseases.skills_context.json`
   - for `research_topic.json`: **decide with the user** whether the HBV topic should become
     HemaSuite's active topic or live under a per-project path. HemaSuite's current
     `research_topic.json` holds a different topic, so a straight copy would overwrite it.
     (`literature_seed.json` needs nothing: HemaSuite already has it byte-identical.)
   - commit there with a message citing `orca/skills@a6950ef`.
2. **Asciminib manuscripts: already done.** All four were `cmp`-verified byte-identical in
   HemaSuite history on 2026-10-18 (see the Findings table), so they need no rescue.
3. **Retire the copy here:** `git rm -r hematology-paper-writer` in this repo, on a branch, with the
   commit body citing the step 1 rescue commit and the step 2 verification. Git history keeps every byte, so this can
   be undone with `git revert`.
4. **Verify:** the h-mad suite's failing set is unchanged
   (`/opt/homebrew/opt/python@3.14/bin/python3.14 -m pytest h-mad/tests/ -q`; on this Mac
   2026-10-18: 6611 passed, 9 skipped, 30 failed, all 30 environmental, see J56's commit), and `git grep -n hematology-paper-writer` here shows only path
   patterns and prose, with no reads of the removed directory.

## Out of scope
- Reconciling the 42 differing files. HemaSuite's side is authoritative and nothing here postdates
  the import except the rescue set.
- The untracked noise in HemaSuite's copy (`.venv`, `.serena`, `.omc`, …).

## Open questions for the user
1. Where should the HBV topic live in HemaSuite (active `research_topic.json` vs a per-project file)?
2. Should step 3 delete the directory, or keep a short README in its place pointing at HemaSuite?
