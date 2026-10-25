# Upstream follow-up

- **Filed:** 2026-10-25 as [ww-w-ai/bkit-claude-code#161](https://github.com/ww-w-ai/bkit-claude-code/issues/161).
  The body is `UPSTREAM-REPORT.md`, verbatim.
- **Repo moved:** `gh issue create -R popup-studio-ai/bkit-claude-code` landed on
  `ww-w-ai/bkit-claude-code`, so the repo was transferred or renamed. Earlier links (#145, #155)
  still use the old owner and redirect.
- **Channel:** public issue. The repo has no `SECURITY.md`, and private vulnerability reporting is
  disabled (`gh api repos/…/private-vulnerability-reporting` → `enabled: false`), checked 2026-10-25.

## When it closes

Run `verify.js` on the bkit release that claims the fix, with the local patch NOT applied. Exit 0
with "patch MISSING" means upstream fixed it: retire this directory the way
`bkit-enh310-quoted-heredoc-body/` was retired. Also check whether `sub-broad-delete-grades-critical`
reports `GAP CLOSED`.
