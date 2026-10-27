# bkit G-004 — ask only when a protected branch is rewritten or removed

**Status:** APPLIED locally to bkit `2.1.38` and `2.1.40` on 2026-10-27 (Hawk-MacStudio).
**Why:** operator, 2026-10-27: "Git push, merge, pull, sync is not tasks for each permission."
Upstream G-004 asked for confirmation on every `git commit|merge|rebase|push` whose text named
`main|master|release|production`. That included every routine fast-forward push to main, every
`git merge --ff-only origin/main`, and any commit whose message contained the word "main". The
session runs in `auto` permission mode, and bkit does not suppress asks there
(`ASK_SUPPRESSING_MODES` = acceptEdits, dontAsk, bypassPermissions). bkit has no config off-switch,
by design (`bkit.config.json` `_comment_destructiveDetection`: relief comes from rule precision), so
this is a precision patch.
**Target file:** `~/.claude/plugins/cache/bkit-marketplace/bkit/<version>/lib/control/destructive-detector.js`
**Coexists with:** `../bkit-g001-bare-heredoc-substitution/` (different hunk).

## What changes

| command | upstream | patched |
|---|---|---|
| `git push origin main`, `HEAD:main`, `refs/heads/main:refs/heads/main` | G-004 ask | clean |
| `git merge … main`, `git merge --ff-only origin/main` | G-004 ask | clean |
| `git commit -m "…main…"` | G-004 ask | clean |
| `git pull … main`, `git fetch … main` | clean | clean |
| `git rebase origin/main`, `git rebase -i main` | G-004 ask | **G-004 ask** |
| `git push origin +main`, `+HEAD:main` (refspec force) | G-004 ask | **G-004 ask** |
| `git push origin :main`, `--delete main`, `-d origin release` | G-004 ask | **G-004 ask** |
| a `--force`/`-f` push to a protected branch | G-002 deny | **G-002 deny** (unchanged) |

A `+refspec` force push is kept under G-004 on purpose: G-002 only matches `-f`, `--force` and
`--force-with-lease`, so without this branch a `+main` push would become unguarded.

## Re-applying after a bkit update

```bash
# 1. Did the update drop the patch?
node /Users/kimhawk/orca/skills/docs/patches/bkit-g004-protected-branch-precision/verify.js
#    exit 1 + "patch MISSING" => re-apply. Check upstream's G-004 first: if it has changed,
#    re-derive the change instead of forcing this hunk.

# 2. Re-apply (adjust <version>)
cd ~/.claude/plugins/cache/bkit-marketplace/bkit/<version>
patch -p1 --dry-run < /Users/kimhawk/orca/skills/docs/patches/bkit-g004-protected-branch-precision/destructive-detector.patch
patch -p1           < /Users/kimhawk/orca/skills/docs/patches/bkit-g004-protected-branch-precision/destructive-detector.patch

# 3. Confirm
node /Users/kimhawk/orca/skills/docs/patches/bkit-g004-protected-branch-precision/verify.js
```

The hook spawns a fresh `node` per Bash call, so the change takes effect without a restart.
**Each Mac needs it separately.** The plugin cache is machine-local.

## Verification evidence (2026-10-27)

- `verify.js` red-green: before the patch, `8/16 cases correct` (exit 1); after it, `16/16`
  (exit 0) on both 2.1.38 and 2.1.40. Its trigger strings are assembled at runtime, so the file
  does not trip the hook it tests when it is passed through a shell.
- `patch -p1 --dry-run` applies cleanly to an untouched 2.1.40 source (the marketplace clone).
- bkit's own suites on patched 2.1.40:
  - unchanged: destructive-bypass 32/32, QA heredoc 53/53, sinclair-seo-148 precision 12/12,
    integrity-verification 11/11 (its IV-09 "detection cannot be switched off" holds);
  - **3 expected failures**, each asserting exactly the behaviour removed:
    `DT-004` ("protected branch push detected"), `GP-19` (`git merge master`) and
    bash-pre-decision `MUST_ASK git merge main`. They are vendor tests and are not edited.
