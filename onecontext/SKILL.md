---
name: onecontext
description: >-
  Search OneContext history for past context, conversations, sessions, and code decisions.
  Use this when the user mentions context, asks about past decisions, references
  existing functions/features/variables, or needs debugging history.
  Always follow broad-to-deep workflow: `onecontext context show` -> regex search
  in session/turn with window checks -> deep dive via `-t content --turns`.
---

# OneContext Skill

Invoke this skill with: `/onecontext`

Use this skill to find reliable historical evidence before answering.

## Response Policy: Synthesize, Don't Dump

When replying to users, prioritize a natural summary over raw search output.

- Answer the user's question first in one sentence.
- Summarize the historical context into 1 concise paragraph or 2-4 thematic bullets.
- Mention only human-friendly evidence (date/title/topic) when needed.
- Do not paste raw `onecontext` output.
- Do not list `session_id` values unless the user explicitly asks for IDs.
- Do not narrate command steps ("I ran X, found Y sessions") unless the user asks for process details.
- Keep uncertainty explicit: if evidence is weak, say what is likely vs. confirmed.
- Match the user's language.

## Core Workflow: Broad to Deep Exploration

Always follow this order:

1. Run `onecontext context show` first.
2. Run `onecontext search` on `-t session` and `-t turn` with regex keywords.
3. Inspect `count`, `limit`, and `window` (`--from/--to`) and adjust windows if needed.
4. Only then run `onecontext search -t content --turns ...` for deep details.

## Usage Strategy

### 1. Start with Context Snapshot
Run this first in every investigation:

```bash
onecontext context show
```

Capture:
- `Context Title`
- `Description`
- each `session_id: session_title`

These are internal investigation notes. Do not copy this list verbatim into the final user reply.

### 2. Broad Search in Session/Turn with Regex
`onecontext search` uses regex mode by default.
Convert the user query into 2-4 regex keyword patterns (synonyms/aliases included), then search `session` and `turn` first.

Always check:
- total matched `count`
- shown `limit`
- current `window` (`--from/--to`)

```bash
onecontext search "auth|token|jwt" -t session --count
onecontext search "auth|token|jwt" -t turn --count
onecontext search "auth|token|jwt" -t turn --from 0 --to 30
onecontext search "auth|token|jwt" -t turn --from 30 --to 60
```

If results are truncated, move/expand window with `--from/--to` or increase `--limit`.

### 3. Deep Dive Only After Turn Selection
Once relevant turn IDs are found, search raw content with `-t content` and `--turns`.
Adjust `--snippet-context` when more local context is needed.

```bash
onecontext search -t content "refresh_token|bearer" --turns t123,t456 --from 0 --to 20
onecontext search -t content "refresh_token|bearer" --turns t123,t456 --from 20 --to 40 --snippet-context 200
```

## Exploration Workflow for Agents

1. **Step 1: Context Snapshot**
   - Run `onecontext context show`.
   - Read `Context Title`, `Description`, and all listed `session_id: session_title`.
2. **Step 2: Build Regex Query Set**
   - Derive regex keywords from the user query (including aliases/synonyms).
3. **Step 3: Session/Turn Broad Search**
   - Run search on `-t session` and `-t turn` first.
   - Inspect `count`, `limit`, and `window`; adjust `--from/--to` or `--limit`.
4. **Step 4: Content Deep Dive**
   - Use `-t content --turns <turn_id_prefixes>` for raw details.
   - Continue adjusting `window` and `--snippet-context` as needed.
5. **Step 5: Return Findings**
   - Return a synthesized answer, not a command log.
   - Default output shape:
     1) One-sentence direct answer ("The history context is mainly about ...")
     2) Short synthesis paragraph (or 2-4 topic bullets) that groups related sessions by theme
     3) Optional evidence line with readable references (date/title), no raw IDs by default
   - If uncertain, state confidence and what is missing; only include search scope/window details when user asks.

## Important Notes
- **ID Prefixes**: You only need the first 8-12 characters of an ID (e.g., `abc12`) for filtering.
- **Pagination**: Output reports total matches and window range; use `--from/--to` (or larger `--limit`) to see more.
