# Implementation Plan: fanout-integrity-and-defects

> Source: docs/02-design/features/fanout-integrity-and-defects.design.md (post-audit, v1.1)
> Branch target: feature/193-fanout-integrity-and-defects

## Executive Summary

Five tasks across three scripts and three docs: the `worktree-rm` guard, the `worktree-create`
task-id marker, the `started_ts` default, the contentless-concern rejection, and the prose — the
four code tasks mutually independent but dispatched **serially**, because the fanout is the
machinery under repair.

## AC coverage map

All 35 ACs are covered by tests. (Spec v1.2 — AC-7.6 was added during this plan's validation; see
the Task 4 note.)

| Task | ACs |
|---|---|
| Task 1 | AC-1.1–1.4, AC-2.1–2.4, AC-3.1–3.3, AC-4.1–4.4 (15) |
| Task 2 | AC-5.1–5.4 (4) |
| Task 3 | AC-6.1–6.4 (4) |
| Task 4 | AC-7.1–7.6 (6) |
| Task 5 | AC-8.1–8.2, AC-9.1–9.4 (6) |

## Correction carried from the design

The design's Test Strategy predicted "at least one existing test asserting the epoch sentinel" would
fail under Task 3. **There is none.** `test_h_mad_state_write.py:30` supplies an explicit
`started_ts` in its `VALID` fixture, and the only `epoch` matches in the suite concern
`autonomous_entry_ts`, an unrelated integer field. Task 3 should therefore expect **zero**
regressions; a test that starts failing there is a real regression, not the anticipated one.

## Task 1: worktree-rm-guard

**Production file**: `h-mad/scripts/hmad-dispatch.sh`
**Test file**: `h-mad/tests/test_hmad_dispatch.py`

**Description**: Add selector→path resolution, work detection, and base-ref resolution, then wire
them into `_cmd_worktree_rm` so a worktree holding uncommitted changes or unmerged commits is not
destroyed. `--force` short-circuits before any resolution. Everything else about the verb is
unchanged.

**Code structure**:
```bash
# Selector -> filesystem path, or empty when it cannot be resolved to exactly one
# existing directory. Empty is "cannot check", never "safe to destroy": the caller
# proceeds, matching _orca_handle_live's rule that only positive evidence blocks.
# Ambiguity returns empty too -- inspecting one worktree and removing a different
# one is worse than not inspecting at all.
_worktree_path() {  # $1 selector -> path on stdout, or empty + rc 1
  local sel="$1" path listing matches
  # Fast path: the fanout's own selectors are `<repoId>::<path>`, so this needs
  # no Orca round trip and is unaffected by listing truncation below.
  case "$sel" in
    *::*) path="${sel#*::}"
          [ -d "$path" ] && { printf '%s\n' "$path"; return 0; } ;;
  esac
  # --limit 200: the default listing is capped and reports `.result.truncated`.
  # A truncated list cannot prove a selector is UNIQUE -- a second match may sit
  # in the part that was cut -- so a still-truncated listing is treated as
  # unresolved rather than trusted. Verified live: this install returns
  # totalCount 5, truncated false.
  listing="$(orca worktree ps --limit 200 --json 2>/dev/null)" || return 1
  printf '%s' "$listing" | jq -e '.result.truncated != true' >/dev/null 2>&1 || return 1
  # `unique` matters: one worktree matches BOTH displayName "main" and the
  # stripped branch "main", and without it that self-double-match would read as
  # ambiguous and bail on the commonest selector there is. Verified live.
  matches="$(printf '%s' "$listing" | jq -r --arg s "$sel" '
    [ .result.worktrees[]?
      | select(.worktreeId==$s or .path==$s or .displayName==$s
               or .branch==$s or ((.branch // "")|sub("^refs/heads/";""))==$s)
      | .path ] | unique' 2>/dev/null)" || return 1
  [ "$(printf '%s' "$matches" | jq -r 'length' 2>/dev/null)" = "1" ] || return 1
  path="$(printf '%s' "$matches" | jq -r '.[0]' 2>/dev/null)"
  [ -n "$path" ] && [ -d "$path" ] || return 1
  printf '%s\n' "$path"
}

# First of origin/HEAD, main, master that this repo actually has. Empty when none
# resolves -- the unmerged check is then SKIPPED, not failed (AC-2.4): h-mad does
# not record a base ref on the worktrees it creates, so this is an ordinary state.
_worktree_default_base() {  # $1 path -> ref on stdout, or empty
  local path="$1" r
  for r in origin/HEAD main master; do
    git -C "$path" rev-parse --verify -q "$r" >/dev/null 2>&1 && { printf '%s\n' "$r"; return 0; }
  done
  return 1
}

# Reason token on stdout + rc 1 when the worktree holds work; rc 0 when it does not.
#
# `git status --porcelain` is the whole uncommitted test: it reports staged,
# unstaged AND untracked-non-ignored entries while honouring .gitignore, so
# AC-1.3 (untracked alone refuses) and AC-1.4 (an ignored file alone does not)
# both fall out with no hand-rolled filtering. Verified empirically: an ignored
# file yields '' and an untracked one yields '?? name'. This boundary is
# load-bearing -- the Wave-3 loss was untracked-and-modified, not staged.
_worktree_holds_work() {  # $1 path, $2 base ref (may be empty)
  local path="$1" base="${2:-}"
  [ -z "$(git -C "$path" status --porcelain 2>/dev/null)" ] || {
    echo "worktree_has_uncommitted_work"; return 1; }
  [ -n "$base" ] || return 0
  [ -z "$(git -C "$path" log --oneline "$base..HEAD" 2>/dev/null)" ] || {
    echo "worktree_has_unmerged_commits"; return 1; }
  return 0
}
```

Wiring in `_cmd_worktree_rm`. The `--force` branch must be decided from the flag scan **before**
`_worktree_path` is called, so the forced path makes exactly one `orca` call:

```bash
_cmd_worktree_rm() {  # <selector> [--force] [--base <ref>]
  _require_orca worktree-rm || return $?
  _need "${1:-}" selector || return $?
  local sel="$1"; shift
  local args=(worktree rm --worktree "$sel") force="" base=""
  # The `*) shift ;;` catch-all is PRE-EXISTING in this verb and is the house
  # idiom at 11 sites across the wrapper. Keep it verbatim. Changing only this
  # verb to forward unknown flags would make argument handling inconsistent
  # across the file for a behaviour no test exercises and no caller relies on,
  # and it is out of this feature's scope. See the note under Task 1 below.
  while [ $# -gt 0 ]; do case "$1" in
    --force) force=1; args+=(--force); shift ;;
    --base) base="$2"; shift 2 ;;
    *) shift ;; esac; done

  if [ -n "$force" ]; then
    echo "[H-MAD] worktree-rm forced selector=$sel — guards skipped" >&2
  else
    local path reason
    if path="$(_worktree_path "$sel")"; then
      [ -n "$base" ] || base="$(_worktree_default_base "$path" || true)"
      if ! reason="$(_worktree_holds_work "$path" "$base")"; then
        echo "hmad-dispatch: $reason — '$sel' still holds work at $path; nothing was removed. Commit or merge it, or pass --force to discard." >&2
        return 1
      fi
    fi
  fi

  args+=(--json)
  local rc=0
  orca "${args[@]}" >/dev/null || rc=$?
  [ $rc -eq 0 ] || { echo "[H-MAD] worktree-rm failed selector=$sel rc=$rc" >&2; return $rc; }
}
```

**Acceptance Criteria**:
- [ ] AC-1.1: A real git repo under `tmp_path` with a modified tracked file, passed as a `<id>::<path>` selector, makes `worktree-rm` return non-zero, and the `HMAD_STUB_CAPTURE` file contains no `worktree rm` call.
- [ ] AC-1.2: That refusal prints `worktree_has_uncommitted_work` on stderr.
- [ ] AC-1.3: A repo whose only change is an untracked, non-ignored file is refused (this is the Wave-3 shape).
- [ ] AC-1.4: A repo whose only change is a file matched by `.gitignore` is **removed** — the guard discriminates.
- [ ] AC-2.1: A clean repo whose branch has a commit not reachable from the base ref is refused, with no `worktree rm` call.
- [ ] AC-2.2: That refusal prints `worktree_has_unmerged_commits`, a different token from AC-1.2's.
- [ ] AC-2.3: A clean repo whose commits are all reachable from the base ref is removed — the guard discriminates.
- [ ] AC-2.4: A clean repo with no `origin/HEAD`, `main` or `master` is removed rather than refused; the unmerged check is skipped, not failed.
- [ ] AC-3.1: `--force` on a repo with uncommitted changes removes it.
- [ ] AC-3.2: `run(["worktree-rm", "wt-7", "--force"])` produces a capture of exactly `orca worktree rm --worktree wt-7 --force --json\n` — the existing assertion, byte for byte, unchanged.
- [ ] AC-3.3: A forced removal prints `[H-MAD] worktree-rm forced selector=<sel>` on stderr.
- [ ] AC-4.1: The bare name `wt-7`, which resolves to no directory, is removed as today — an unresolvable selector never refuses.
- [ ] AC-4.2: A failing `orca worktree rm` still returns rc 1 and prints the existing `[H-MAD] worktree-rm failed selector=wt-7 rc=1` marker.
- [ ] AC-4.3: On substrate cmux, `worktree-rm` returns 2 with "requires orchestration mode" and makes no call.
- [ ] AC-4.4: Removing an already-gone selector logs and no-ops — teardown stays idempotent.

**Note on the unrecognised-argument catch-all.** The cycle-1 audit raised the `*) shift ;;` fallback
as silently dropping unknown flags. The observation is correct, but the change is declined here and
the reasoning is put back rather than the fix applied. Verified against the tree: this catch-all is
**pre-existing** in `_cmd_worktree_rm` and appears at **11 sites** across `hmad-dispatch.sh` — it is
the file's established argument idiom, not something this feature introduces. Changing it in one
verb only would leave argument handling inconsistent across the wrapper, for a behaviour no test
exercises (no test passes an unrecognised argument to `worktree-rm`) and no documented caller relies
on. If it should change, it should change at all 11 sites as its own feature. Base Axis B's
backward-compatibility rule points the same way.

**Dependencies on other tasks**: None

---

## Task 2: worktree-create-task-id

**Production file**: `h-mad/scripts/hmad-dispatch.sh`
**Test file**: `h-mad/tests/test_hmad_dispatch.py`

**Description**: When `--prompt-file` is supplied, register an orchestration task after the worktree
is created and report its id as an `[H-MAD]` stderr marker. **stdout is unchanged in every case** —
exactly the selector, exactly as today.

**Code structure** — the whole function, so `$name` and `$pf` have visible origins. Everything above
the marked block is the existing body unchanged:

```bash
_cmd_worktree_create() {  # <name> [--agent <id>] [--base <ref>] [--prompt-file <path>] [--repo <sel>|--workspace <sel>|--project <id>]
  _require_orca worktree-create || return $?
  _need "${1:-}" name || return $?
  local name="$1"; shift                      # <-- $name defined here (existing)
  local agent="" base="" pf="" repo="" ws="" proj=""
  while [ $# -gt 0 ]; do case "$1" in
    --agent) agent="$2"; shift 2 ;; --base) base="$2"; shift 2 ;;
    --prompt-file) pf="$2"; shift 2 ;;        # <-- $pf defined here (existing)
    --repo) repo="$2"; shift 2 ;; --workspace) ws="$2"; shift 2 ;; --project) proj="$2"; shift 2 ;;
    *) shift ;; esac; done
  local args=(worktree create --name "$name")
  [ -n "$agent" ] && args+=(--agent "$agent")
  [ -n "$base" ] && args+=(--base-branch "$base")
  [ -n "$repo" ] && args+=(--repo "$repo")
  [ -n "$ws" ]   && args+=(--workspace "$ws")
  [ -n "$proj" ] && args+=(--project "$proj")
  if [ -n "$pf" ]; then
    [ -f "$pf" ] || { echo "hmad-dispatch: prompt file not found: $pf" >&2; return 2; }
    args+=(--prompt "$(cat "$pf")")
  fi
  args+=(--json)

  # ---- CHANGED FROM HERE ----
  # Was: _orca_json '<expr>' "${args[@]}"   (streamed straight to stdout)
  # Now: capture it so the marker can name the selector, then re-emit BYTE-FOR-BYTE.
  # `|| return $?` preserves the previous failure passthrough, and an empty
  # selector still prints nothing, keeping the empty-match test's `stdout == ""`.
  local sel rc=0
  sel="$(_orca_json '.result.worktree.id // .result.worktree.selector // .result.worktree.handle' "${args[@]}")" || rc=$?
  [ $rc -eq 0 ] || return $rc
  [ -n "$sel" ] && printf '%s\n' "$sel"

  # Task registration is gated on --prompt-file: that is the fanout path and the
  # only one where await/gate-create are needed. Registering unconditionally would
  # add a second orca call to the BARE argv -- breaking test_worktree_create_argv_orca's
  # exact-capture assertion -- and orphan a task for every non-fanout worktree.
  # Failure is NON-FATAL: a worktree with no task-id is recoverable, a failed
  # creation is not. stdout is untouched on every path; the id goes to stderr as an
  # [H-MAD] marker, the same channel _cmd_pin already uses.
  if [ -n "$pf" ]; then
    local tid
    if tid="$(_cmd_task_create "worktree:$name" "$pf" 2>/dev/null)" && [ -n "$tid" ]; then
      echo "[H-MAD] worktree_task task=$tid selector=$sel" >&2
    else
      echo "[H-MAD] worktree_task_skipped selector=$sel" >&2
    fi
  fi
  return 0
}
```

**Acceptance Criteria**:
- [ ] AC-5.1: With `--prompt-file`, stdout is exactly the selector and stderr carries `[H-MAD] worktree_task task=<id> selector=<sel>`; the two are separately parseable.
- [ ] AC-5.2: The task-id emitted in that marker is accepted by `gate-create` as its `--task` argument (assert the id reaches the `orca … gate-create --task <id>` capture).
- [ ] AC-5.3: Without `--prompt-file`, stdout is byte-identical to today — `test_worktree_create_parses_selector_and_empty_match`'s `stdout == "wt-7\n"` and `test_worktree_create_argv_orca`'s exact single-call capture both still pass unchanged.
- [ ] AC-5.4: When task registration fails, the worktree is still created, the selector is still printed on stdout, the command still returns 0, and `[H-MAD] worktree_task_skipped` appears on stderr.

**Dependencies on other tasks**: None

---

## Task 3: started-ts-default

**Production file**: `h-mad/scripts/h_mad_state_write.py`
**Test file**: `h-mad/tests/test_h_mad_state_write.py`

**Description**: Default `started_ts` to the current UTC time instead of the hardcoded epoch
sentinel. One expression. Existing records are never rewritten.

**Code structure**:
```python
# h_mad_state_write.py — replaces the epoch sentinel at the record-creation site.
#
# The sentinel was itself a VALID timestamp, which is why it read as "the reader
# must be broken" for weeks: nothing downstream could distinguish it from real
# data, and every telemetry row reported elapsed_min ~= 29,744,612 (~56 years).
record["started_ts"] = started_ts or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
```

Import `datetime`/`timezone` if not already imported. Nothing else in the module changes.

**Acceptance Criteria**:
- [ ] AC-6.1: Creating a feature with no `--started-ts` records a `started_ts` parseable as UTC and within 120 seconds of now — and specifically **not** `1970-01-01T00:00:00Z`.
- [ ] AC-6.2: An explicit `--started-ts` is stored verbatim, unchanged by this task.
- [ ] AC-6.3: `h_mad_telemetry.py record` against a record created without `--started-ts` reports an `elapsed_min` under 60, not ~29,744,612.
- [ ] AC-6.4: A pre-existing record whose `started_ts` is the epoch is left byte-identical when an unrelated field on a different feature is written.

**Dependencies on other tasks**: None

---

## Task 4: contentless-concern

**Production file**: `h-mad/scripts/h_mad_extract_verdict.py`
**Test file**: `h-mad/tests/test_h_mad_extract_verdict.py`

**Description**: Reject a `STATUS: DONE_WITH_CONCERNS` whose report names no concern, with the same
exit-2/no-output shape used for a missing verdict. `extract_verdict()` itself is **not** changed —
the check is applied in `main()`, scoped to one key and one value, which keeps it off the `VERDICT:`
and `ASSESSMENT:` paths by construction.

**Code structure** — this implementation was prototyped and validated before being written down: it
passes 14 synthetic cases **and** was replayed against the 13 real `DONE_WITH_CONCERNS` reports on
this machine (see the validation note below). Add to `h_mad_extract_verdict.py`:

```python
# --- contentless DONE_WITH_CONCERNS (J10) -----------------------------------
#
# A verdict that declares doubt without stating it is unactionable and cannot be
# told apart from DONE, so it must fail the way silence does rather than pass as
# nuance. Measured on this machine: 7 of 13 historical DONE_WITH_CONCERNS reports
# name no concern anywhere.

_LABEL_WORD = re.compile(r"\b(?:concerns?|blockers?)\b", re.I)
_SECTION_START = re.compile(r"^(?:#{1,6}[ \t]|STATUS:|VERDICT:|ASSESSMENT:)")
_NEGATIONS = {
    "", "-", "none", "n a", "na", "no", "nil", "nothing",
    "no concern", "no concerns", "no blockers", "not applicable",
}


def _strip_decor(line: str) -> str:
    """Remove list bullets, markdown headings and emphasis from a line."""
    s = line.strip()
    s = re.sub(r"^[-*+][ \t]+", "", s)
    s = re.sub(r"^#{1,6}[ \t]*", "", s)
    return s.strip().strip("*_`").strip()


def _normalise(text: str) -> str:
    """Lowercase, drop punctuation, collapse whitespace — for negation matching."""
    s = _strip_decor(text)
    s = re.sub(r"[^0-9a-z ]+", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def _is_concern_label(head: str) -> bool:
    """True when *head* looks like a concerns section label or heading.

    Matches on CONTAINMENT, not prefix: a real report used the label
    'Working-tree concern:', which a prefix test rejects — wrongly discarding a
    report that did state its concern. Bounded to 60 characters so a prose
    sentence merely mentioning "concerns" is not mistaken for a section label.
    """
    label, sep, _ = head.partition(":")
    target = label if sep else head
    return len(target) <= 60 and bool(_LABEL_WORD.search(target))


def concern_stated(scrape: str) -> bool:
    """True when the report names at least one concern."""
    lines = scrape.splitlines()
    for i, line in enumerate(lines):
        head = _strip_decor(line)
        if not _is_concern_label(head):
            continue
        _, sep, rest = head.partition(":")
        if sep and _normalise(rest):
            return _normalise(rest) not in _NEGATIONS
        for nxt in lines[i + 1:]:
            if not nxt.strip():
                continue
            if _SECTION_START.match(nxt.strip()):
                break
            return _normalise(nxt) not in _NEGATIONS
        return False
    return False
```

And in `main()`, immediately after the existing `extract_verdict` call and before the success print:

```python
    # Scoped to ONE key and ONE value, so the VERDICT: and ASSESSMENT: contracts
    # cannot become collateral damage. extract_verdict() itself is unchanged: it
    # answers "what is the last value of this key", and widening it to read
    # surrounding prose would make its name a lie.
    if (
        args.key == "STATUS"
        and value == "DONE_WITH_CONCERNS"
        and not concern_stated(scrape)
    ):
        print(
            "ERROR: STATUS: DONE_WITH_CONCERNS but the report names no concern "
            "— re-dispatch, or have the agent report DONE",
            file=sys.stderr,
        )
        return 2
```

**Validation already performed** (do not re-derive, but do re-run to confirm): the synthetic set
covers the Wave-3 codex form `Concerns / blockers: none.`, the template form
`Concerns / blockers / context needed:` followed by `- None.`, `None`/`NONE` casing, a markdown
`## Concerns` heading with and without content, an inline `**Concerns:**` with real text, a report
with no section at all, the label `Working-tree concern:`, and the adversarial case
`Concerns: none of the tests cover submodules, which is a real gap` — which must return **True**,
because the negation match is on the normalised whole value, not a substring search.

**Acceptance Criteria**:
- [ ] AC-7.1: A scrape with `STATUS: DONE_WITH_CONCERNS` and a concerns section naming a substantive concern returns the verdict and exits 0. Include the real-world label form `Working-tree concern:` as a case — a prefix-only match rejects it wrongly.
- [ ] AC-7.2: The same verdict with no concerns section anywhere exits 2 and prints no verdict on stdout.
- [ ] AC-7.3: The same verdict whose concerns section contains only a negation exits 2 — asserted for `none`, `None`, `NONE`, `n/a`, `- none`, and `Concerns / blockers / context needed:` followed by `- None.` (the exact template form).
- [ ] AC-7.4: `STATUS: DONE`, `STATUS: BLOCKED`, `STATUS: NEEDS_CONTEXT`, `VERDICT: COMPLIANT`, `VERDICT: DRIFT` and `ASSESSMENT: READY_TO_MERGE` are all unaffected, including when no concerns section exists — the check touches one key and one value only.
- [ ] AC-7.5: The stderr message for a contentless concern is distinguishable from the missing-verdict message, so an operator can tell a mis-formatted report from a silent agent.
- [ ] AC-7.6: `Concerns: none of the tests cover submodules, which is a real gap` returns the verdict — the negation set matches a normalised whole value, never a substring.

**Dependencies on other tasks**: None

---

## Task 5: docs-machinery

**Production file**: `h-mad/SKILL.md`
**Test file**: `h-mad/tests/test_h_mad_preflight_docs.py`

**Description**: Document the `worktree-rm` guards and their tokens, the unified task-id path, and
the concern obligation. Assertions extend the existing doc-mandate module.

**Code structure** — appended to `h-mad/tests/test_h_mad_preflight_docs.py`, reusing its **existing**
module constants `REPO_ROOT`, `SKILL_MD`, `ORCH_MD` (verified present at the top of that file). Only
`CODEX_MD` is new, because no constant for the implementer template exists yet:

```python
# NEW module constant — the other three already exist; do not redefine them.
CODEX_MD = REPO_ROOT / "h-mad" / "references" / "codex-implementer-prompt.md"


def test_skill_documents_worktree_rm_guards() -> None:
    """AC-9.1, AC-9.3: the guard and both reason tokens are documented."""
    text = SKILL_MD.read_text(encoding="utf-8")
    assert "worktree_has_uncommitted_work" in text
    assert "worktree_has_unmerged_commits" in text
    # The verb-behaviour table must say worktree-rm can refuse, not merely that
    # it removes — a reader who only sees the happy path will not pass --force
    # when they mean to discard, and will read a refusal as a bug.
    assert "refuses" in text.lower()
    assert "--force" in text


def test_orchestration_mode_documents_task_id_on_both_paths() -> None:
    """AC-9.2: the two dispatch paths are no longer one sequence."""
    text = ORCH_MD.read_text(encoding="utf-8")
    assert "worktree_task" in text, "the task-id marker must be documented"
    # J14: the old prose ran worktree-create --prompt-file and task-create into a
    # single semicolon-joined instruction. Assert the task-id is described as
    # available from the --prompt-file path, which is what made await/gate-create
    # unusable there.
    assert "--prompt-file" in text
    assert "gate-create" in text


def test_codex_prompt_requires_a_named_concern() -> None:
    """AC-8.1, AC-8.2: the obligation and its consequence are both stated."""
    text = CODEX_MD.read_text(encoding="utf-8")
    assert "DONE_WITH_CONCERNS" in text
    lowered = text.lower()
    assert "at least one concern" in lowered
    assert "report `done`" in lowered or "report done" in lowered
    # The consequence must be visible to the agent, not only to the orchestrator:
    # an obligation with no stated penalty reads as advice.
    assert "reject" in lowered


def test_skill_frontmatter_still_valid() -> None:
    """AC-9.4: project Axis B — skill manifest integrity."""
    lines = SKILL_MD.read_text(encoding="utf-8").splitlines()
    assert lines[0].strip() == "---"
    end = lines.index("---", 1)
    front = "\n".join(lines[1:end])
    for key in ("name:", "description:"):
        assert key in front, f"frontmatter lost {key}"
        value = next(l.split(":", 1)[1].strip()
                     for l in front.splitlines() if l.startswith(key))
        assert value, f"frontmatter {key} is empty"
```

**Acceptance Criteria**:
- [ ] AC-8.1: `references/codex-implementer-prompt.md` states that `DONE_WITH_CONCERNS` requires naming at least one concern, and to report `DONE` otherwise.
- [ ] AC-8.2: That template states the orchestrator will reject a contentless `DONE_WITH_CONCERNS`, so the consequence is visible to the agent.
- [ ] AC-9.1: `SKILL.md` states that `worktree-rm` refuses to destroy a worktree holding work and names both `worktree_has_uncommitted_work` and `worktree_has_unmerged_commits`.
- [ ] AC-9.2: `references/orchestration-mode.md` no longer presents `worktree-create --prompt-file` and `task-create`+`dispatch` as a single sequence, and states a task-id is available from the `--prompt-file` path.
- [ ] AC-9.3: `SKILL.md`'s per-verb behaviour table includes the `worktree-rm` guard.
- [ ] AC-9.4: `SKILL.md` frontmatter still parses with non-empty `name` and `description`.

**Dependencies on other tasks**: Task 1, Task 2, Task 4 (the prose must name the shipped tokens)

---

## Dispatch note

All four code tasks declare `Dependencies on other tasks: None`, and `hmad-dispatch env` reports
`substrate: orca` with `orchestration: on` — so the Phase-5 fanout rule's three conditions are met.
**Fanout is deliberately not engaged.** Its teardown step (`worktree-rm`) is the defect under repair,
and a worker that left work uncommitted would be destroyed by the very bug this feature fixes.
Serial dispatch on the shared feature branch, per the design's cross-cutting decision.

## Version History
- v1.0: Initial implementation plan draft.
- v1.1: Cycle-1 audit response.
  **Must-fix (TBD placeholders, Tasks 4 and 5):** both resolved — Task 4 now carries the complete
  `concern_stated` implementation with its helpers, and Task 5 the four full test bodies. Neither
  was written from imagination: the Task-4 code was prototyped, passed against 14 synthetic cases,
  and then replayed against the 13 real `DONE_WITH_CONCERNS` reports on this machine, which caught a
  false negative the synthetic set missed (the label `Working-tree concern:`) and produced spec
  v1.2's AC-7.6.
  **Should-fix (unrecognised-argument catch-all):** observation accepted, prescribed direction
  declined with reasoning — the catch-all is pre-existing and used at 11 sites, so changing one verb
  would make the wrapper inconsistent. See the note under Task 1.
  **Should-fix (vague `$pf`/`$name` origins):** resolved — Task 2 now shows the whole function with
  the existing argument parsing that defines both, and marks exactly where the change begins.
  **Self-found:** `_worktree_path` now passes `--limit 200` and bails when `.result.truncated` is
  true. A truncated listing cannot prove a selector unique, so the old version could have resolved
  to the wrong worktree and inspected it confidently. Found by running the query live, not by
  review.
- v1.2: Cycle-2 nit — Task 4 carried a duplicated Acceptance Criteria block whose stale copy omitted
  AC-7.6. Removed. Verified afterwards that all 35 ACs appear exactly once and that the spec and
  impl-plan AC sets match with no additions or omissions on either side. A stale duplicate matters
  more than "copy-paste artifact" suggests: the implementer reads this list, and the stale copy was
  the one missing the AC that the historical replay had just added.
