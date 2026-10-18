# grok-audit-surface: commit sha remap (2026-10-18 rebase)

The session's last five local commits were rebased onto `origin/main` `db630c01` before they were ever pushed. That rewrote their shas, so phase documents and audit artifacts written before the rebase cite commits that `main` does not contain. File contents are byte-identical across the rebase; only the commit ids changed.

| old (cited in docs) | new (on `main`) | content |
|---|---|---|
| `946ffc5a` | `a0b41697` | spec v1.4 + plan audit cycle 2 reports |
| `5b2df07b` | `bfb6960a` | plan v1.2 |
| `611c299d` | `2f7bf7ae` | spec v1.5 + plan gating round 2 reports |
| `b085ad7a` | `ab3c9f32` | plan v1.3 (Phase 3 exit) |
| `5920f704` | `218ee791` | handoff 2026-10-18 grok-audit-surface-phase3-exit |

Documents that cite an old sha:
- `docs/01-plan/features/grok-audit-surface.plan.md` cites `946ffc5a`, `5b2df07b` and `611c299d`.
- `docs/01-plan/features/grok-audit-surface.spec.md` cites `5b2df07b`.
- `docs/03-analysis/grok-audit-surface.plan.delta-review.5b2df07-20261018T130440Z.md` names `5b2df07` in its filename and body.

Read the documents through this table. Their next revision (spec-author or plan-author) may restamp to the new shas. A doc's own sha256 is unaffected, so the DONE-gate digests in session records still verify.

Re-derive this table:
```bash
for s in 946ffc5a 5b2df07b 611c299d b085ad7a; do git log -1 --format='%h %s' "$s" 2>/dev/null || echo "$s: not reachable"; done
git log --oneline db630c01..218ee791
```
