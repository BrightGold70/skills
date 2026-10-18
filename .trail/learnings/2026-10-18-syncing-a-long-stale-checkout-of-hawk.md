---
title: "Syncing a long-stale checkout of this repo, and the J56 --out fix"
author: Hawk
date: 2026-10-18
branch: main
cost: { minutes: 1, tokens: 1606 }
touches:
  - "h-mad/scripts/hmad-dispatch.sh#_out_write_failed"
  - docs/skill-monitoring.md
  - docs/patches/claude-security-guidance-bare-exec/verify.py
  - docs/patches/bkit-enh310-quoted-heredoc-body/verify.js
---

## Decided
- Re-porting local commits onto a far-moved origin beats rebasing them: back up to a branch, `git reset --keep origin/main`, then cherry-pick what still applies and re-do the rest test-first against upstream's code.
- An unwritable `--out` fails soft (J56): every exec write site is `{ write || _out_write_failed "$out"; }`, rc untouched, same contract as J29.
- Plugin patches are retired once upstream ships a partial fix; verifiers list the accepted misses in `KNOWN_GAPS` (J54 bkit, J55 security-guidance) and print `GAP CLOSED` when upstream catches up.

## Tried and ruled out
- Cherry-picking the old `--out` fix: upstream had rewritten every write site to `_write_out_atomic`, so it was redone instead. The bug survived the rewrite (`mktemp` in the missing dir fails first).
- Reusing J30–J32 for new entries: upstream already used them. Check the highest J id on origin before numbering.

## Watch out
- On this Mac, 30 h-mad tests fail for environmental reasons: audit-cycle tests hardcode `/opt/anaconda3/bin/python3.11`, one reads the stale `bkit/2.1.19` cache, and Python 3.14's return-in-finally SyntaxWarning leaks into compared stderr. Compare failing *sets* against an unmodified baseline, not counts.
- `python3` here is Homebrew 3.15 without pytest; use `/opt/homebrew/opt/python@3.14/bin/python3.14`.
- A second pytest run is refused while `.h-mad/mutation.lock` is held; don't start one alongside a background suite.
- `sed` on a `Status:` line in skill-monitoring.md matches other entries too; anchor on the last line or edit by exact block.
- zsh: `echo =====` and unmatched globs (`--include=*.sh`) abort the command; wrap in `bash -c`.
