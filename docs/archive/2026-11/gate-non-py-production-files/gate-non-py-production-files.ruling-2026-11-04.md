# Operator ruling of 2026-11-04 — the ninth FR-9 driver refusal (primary record)

Located 2026-11-08. Every analysis from v1 to v5, and the report, carried this as `unverified: primary record not found`. Their greps searched the spec, but the ruling was never in a document. It was a typed prompt.

**The ruling (verbatim):**

> Add the ninth refusal for a missing plan path to the impl-plan

- **When:** 2026-11-04T07:04:43.434Z (16:04 KST)
- **Where:** Claude Code session `29681318-7f86-45ed-b6e4-d1528da3d634`, cwd `/Users/kimhawk/orca/skills`, transcript line 2986 of `~/.claude/projects/-Users-kimhawk-orca-skills/29681318-7f86-45ed-b6e4-d1528da3d634.jsonl`. The transcript is local to this machine and not in git, so this file is the durable copy.

**What it answered.** The assistant message at 2026-11-04T06:11:19Z (line 2972) asked, as question 1 of 3, none of them blocking:

> **Plan path missing at the base commit (`OPEN-DECISION`, Task 8):** today the driver crashes with no token. The plan counts the design's stated residual, and `implplan-author` recommends a ninth refusal, which takes it to 9 refusals and 89 mutation rows. I agree with the ninth refusal, because a crash with no token is what these refusals are meant to prevent.

**Where it was applied:**
- `gate-non-py-production-files.impl-plan.md:29`, departure 9: `FR9-DRIVE: UNREADABLE plan-absent-at-base`, exit 2, `# M:D-PLAN-ABSENT`.
- `gate-non-py-production-files.impl-plan.rejections.md:7`.

The spec's Assumptions (R-A to R-D) never recorded it, which is why the spec greps found nothing. AC-9.5 does not depend on it.
