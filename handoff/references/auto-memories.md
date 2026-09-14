## Update persistent auto-memories

`docs/learnings.md` is **project-scoped** (lives in the repo, grepped on demand). It is NOT the same
as the **persistent auto-memory** store at `~/.claude/projects/<project-dir-slug>/memory/`, which is
**user-global** and whose `MEMORY.md` index is loaded into context at the start of *every* session.
A learning written only to `docs/learnings.md` will not surface automatically next session; a
memory written to the auto-memory store will. Wrapping up is the moment to reconcile the store with
what this session proved — skip it and the next session starts with stale guidance. (Skip this phase
only if `--skip-memories` was set, or the memory dir does not exist.)

**When to write/update a memory** (distinct from a `docs/learnings.md` entry):
- The session produced **feedback on how to work** — a correction the user gave, or a confirmed
  approach (e.g. "tool X is reliable when invoked via Y", "always run a real end-to-end check").
- A **fact contradicts an existing memory** — flip/correct it; a stale memory is worse than none.
- A durable **user / project / reference** fact not derivable from the repo (who the user is, an
  ongoing constraint, an external dashboard/ticket).
Skip anything already captured in the code, git history, CLAUDE.md, or that only mattered this
session — those belong in the handoff doc or `docs/learnings.md`, not the auto-memory store.

**PRE-CHECK THE INDEX BEFORE YOU WRITE TO IT — the failure is silent and happens at LOAD, not at
write.** Claude Code caps the index at **25000 bytes / 200 lines**; past that, quoting the binary,
*"the write succeeded, but everything past the limit is silently dropped each time the index is
loaded — entries at the end are already invisible to readers."* So the built-in warning fires on the
write that crosses the line, which is one write too late, and it lands in a hook message that no
later session reads. `wc -c` cannot tell you the tail is being dropped; only a comparison against
the cap can.

```bash
python3 ~/.claude/skills/h-mad/scripts/h_mad_check_memory_index.py --show-dropped
```

`OK` → write normally. `WARN` (≥80% of the worse dimension) → **compact first**; this is the last
point at which compaction is cheap, and a memory appended now may be pushing an older one off the
end. `OVER` → content is **already** invisible: `--show-dropped` prints exactly which entries, and
appending without compacting silently deletes more of them. Exit 1 on WARN/OVER, 2 on unreadable —
an index you cannot read is never treated as fine.

Compact to **70% of the cap** (17500 bytes / 140 lines), which is the target the binary itself
names. Both dimensions are scored and the **worse** one binds: an index at 40% of its byte cap can
still be over on lines, so a byte-only eyeball reports healthy on a broken index.

**How to apply:**
1. Read the store's `MEMORY.md` index first. For each candidate, find an existing memory file it
   updates and **edit that file** (correct/flip stale claims, append a dated reinforcement) rather
   than creating a duplicate. Only create a new file when nothing covers it.
2. Each memory is one file with frontmatter (`name`, `description`, `metadata.type:
   user|feedback|project|reference`) and a body; for `feedback`/`project`, include **Why:** and
   **How to apply:** lines. Link related memories with `[[their-name]]`. Convert relative dates to
   absolute.
3. **Update the one-line pointer in `MEMORY.md`** when a memory's hook changes (e.g. a flipped
   conclusion) — the index is what the next session actually reads first.
4. The auto-memory dir is **not a git repo** — there is nothing to commit or push there. It is
   user-global local state. (The §"Commit and push" finale pushes only the project handoff +
   learnings to the project remote; it does not touch the memory store.)

If the project uses a different memory mechanism (no `~/.claude/projects/.../memory/` dir), skip
silently — do not invent one.
