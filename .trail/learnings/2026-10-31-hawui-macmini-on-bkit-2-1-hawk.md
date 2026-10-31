---
title: Hawui-Macmini on bkit 2.1.41 with patch-verify hook and patches
author: Hawk
date: 2026-10-31
branch: main
cost: { minutes: 4, tokens: 23917 }
---

## Decided
- Hawui-Macmini (2026-10-31): bkit upgraded 2.1.40 → 2.1.41 with `claude plugin marketplace update bkit-marketplace` + `claude plugin update bkit@bkit-marketplace`. Copied the patch-verify-on-update.sh hook to ~/.claude/hooks/ and registered it in SessionStart (timeout 120). The hook reports OK.
- On 2.1.41, 4 of 6 carried patches pass verify as-is, because upstream covers them or the hunk survived: enh310, g001, subagentstop, claude-security-guidance.
- Only bkit-g004-protected-branch-precision and bkit-sprint-stop-hook-active needed re-applying. Both applied cleanly with `patch -p1` against cache/bkit-marketplace/bkit/2.1.41 with no fuzz. verify.js: 16/16 and 2/2.

## Tried and ruled out
- Re-applying all 6 patches after the upgrade is not needed. Run the hook (or each verify.js) first and re-apply only the ones that FAIL.

## Watch out
- This supersedes the "hook not installed on Hawui-Macmini" note in the 2026-10-31 resume learning.
- Mac Studio still needs the same steps: upgrade to 2.1.41, run the hook, re-apply g004 + sprint-stop-hook-active.
- To force the hook to re-check, delete ~/.claude/state/patch-verify.state. It only re-runs when the plugin fingerprint changes.
