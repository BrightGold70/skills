## Automation scout

Scan this session's work for repeated patterns worth capturing as skills. Runs after learnings are persisted, before committing. Skip entirely if `--skip-scout` was set.

### How to run

Run this analysis inline (no external agent or plugin required). If a read-only subagent is available, spawn one for isolation — but the inline path is the default.

Review `git diff HEAD~10..HEAD` and the conversation. Find: command pipelines the user retyped multiple times, multi-step workflows done manually without a shortcut, patterns that recurred ≥2 times, or any sequence that felt like "there should be a skill for this." For each candidate: pattern name, recurrence count, one-line description. Cap at 5 candidates.

### Reconcile the open rows FIRST

Do this **before** appending, and do not skip it because the appending is the part that feels like
the work. `docs/skill-candidates.md` says its status "is only useful if it is current" — and this
scout is the only thing that ever writes the file, so a status nobody reconciles decays until the
whole backlog has to be re-derived by hand. Measured 2026-08-03: five rows stood at `candidate: yes`
and **four described work that had already shipped**, two of them for over a week.

List what is still open. **Ask the census, not a line grep** — it is the reader with tests, and a
row's terminal marker is written on the *continuation* line beneath it (`  — **LANDED 2026-08-25**
…`), so any single-line pattern sees the `candidate: yes` and never the `LANDED` that closed it:

```bash
python3 handoff/scripts/skill_candidates_census.py docs/skill-candidates.md   # OPEN(yes+maybe)=N
```

**Need the rows in code rather than a printed count? Import it — do not write a parser.**
The module is import-safe (nothing runs at import), and four symbols are the whole API:
`rows(path)` → `[(lineno, [lines])]` per row, `ROW`/`TERM`/`CAND` for the row, terminal-marker
and verdict patterns, and `main(argv)` if you want the printed census in-process. Every
hand-written substitute has been wrong — one returned 270 rows / 101 open where the census read
316 / 125, because rows **wrap** and not all of them use a colon; two more miscounted on
2026-08-28. Writing your own is not the cheap option, it is the one that produces the number
nobody re-checks.

Measured 2026-08-26: the old line-scoped grep below returned **7 rows, all 7 already terminal** —
a 100% false-positive rate against a file the census correctly read as zero open `yes`. It is kept
only as a fallback for a store the census cannot parse, and its output must be re-checked against
the line *after* each hit before you believe it:

```bash
# FALLBACK ONLY — see above. Anchored on the row shape (`- **name**: …`), because prose
# that merely quotes the phrase "candidate: yes" matches too. `\**` tolerates a bolded
# verdict: bold is this file's convention for the TERMINAL states, so a `candidate: **yes**`
# slip would otherwise be invisible to this very check — which happened the first time the
# step was run. Neither trick helps with the continuation-line problem, which is why the
# census is the primary.
grep -nE '^- \*\*.*candidate: \**yes' docs/skill-candidates.md | grep -vE 'LANDED|SUPERSEDED|DECLINED'
```

Keep `yes`/`maybe` **unbolded** when you write a row; reserve bold for `LANDED` / `SUPERSEDED` /
`DECLINED`, which is what the rest of the file does.

That is the actionable set. `candidate: maybe` rows are mostly parked provenance ("this IS the
/h-mad skill") — swap `yes` for `maybe` and skim them only when the `yes` set is empty, or you will
re-litigate twenty parked rows every session.

For each row it returns, verify the claim **against source, not against the label** — the row is a
claim about the world made by a past session:

```bash
git log --oneline -S'<distinctive symbol or phrase>' -- .   # did it ship, and where?
grep -rn '<the rule or verb the row asks for>' <skill-dir>  # is it already in the skill?
```

Then flip it, naming where it landed: `**LANDED** — <file> §<section>` · `**SUPERSEDED** — <what
removed the need>` · `**DECLINED** — <reason>`. Leave it as-is only when it is genuinely still open.
Update the summary table at the top of the file in the same pass; a flipped row and a stale table
disagree, and the table is what the next reader trusts.

Two traps worth naming, both hit on 2026-08-03:

- **A different tool can already do the job.** One row asked for a script whose exact contract
  (exact-string replace, refuse unless the anchor matched once, restore and verify) the bundled
  mutation harness already had. That is `SUPERSEDED`, not open.
- **A `no` can still name an upgrade.** The verdict answers "is this a new skill?", which is not
  "should an existing skill change?". Read the *reason* on `no` and `maybe` rows too — one sat inert
  while its own reason named the exact insertion point ("belongs in the handoff skill's READ
  reconciliation").

### Where to write

Append to `docs/skill-candidates.md` (create with `# Skill Candidates` header if absent):

```markdown
## YYYY-MM-DD — <session-slug>

- **<pattern>**: <description> — recurrence: N — candidate: yes/maybe/no
```

If zero candidates found, write: `## YYYY-MM-DD — <slug> — no candidates`.

### Evolution bridge (opt-in)

After writing to `docs/skill-candidates.md`, check whether
`~/.claude/homunculus/evolved/skills/` exists. If it does **and** any candidate
has `recurrence: N` where N ≥ 3 **and** `candidate: yes`, write a minimal stub
there so the pattern is visible to continuous-learning-v2 if installed:

For each qualifying candidate, create
`~/.claude/homunculus/evolved/skills/<pattern-slug>.md`:

```markdown
---
name: <pattern-slug>
description: <one-line description from candidate>
source: handoff-scout
recurrence: N
session: YYYY-MM-DD
---

# <Pattern Name>

Candidate graduated from `docs/skill-candidates.md` via handoff automation scout.
Recurrence: N sessions. Promote to a full skill when the pattern stabilises further.
```

Skip silently if `~/.claude/homunculus/evolved/` does not exist — this bridge
is opt-in for users who have continuous-learning-v2 installed. Do not create
the directory; just skip.
