---
title: "Token audit: headless claude -p boots the full harness"
author: Hawk
date: 2026-11-01
branch: main
cost: { minutes: 30, tokens: 216188 }
touches:
  - docs/handoffs/2026-11-01-main__row2729-token-audit-hema-isolation.md
  - docs/learnings.md
  - docs/skill-candidates.md
  - h-mad/scripts/h_mad_failure_diff.py
---

## Decided
Price-weighted per-session/per-hour aggregation of ~/.claude/projects/**/*.jsonl usage (dedupe by message.id+requestId) found the culprit fast: 472 sdk-cli sessions in one hour band, 1 call each, ~600k context. Cause: `claude -p --system-prompt X --tools ""` still loads MCP servers, user plugins/hooks, skill/agent listings and CLAUDE.md. Isolation: --strict-mcp-config --setting-sources "" --disable-slash-commands --no-session-persistence, run from a private 0700 cwd under ~/.cache (349k -> ~700 tokens measured).

## Tried and ruled out
--bare: never reads OAuth, breaks subscription logins. --setting-sources project with tempfile.gettempdir() cwd: a world-writable temp root lets another user plant settings hooks or CLAUDE.md.

## Watch out
Raw token totals are 97% cache reads; weight by price before ranking. The Mac Studio is not reachable from the Mini: hand the user a paste-able read-only script. --setting-sources "" is undocumented in 2.1.316; a future CLI could silently restore the full harness.
