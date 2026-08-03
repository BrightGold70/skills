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
