# PDCA Directory Structure

## Active Phases
| Directory | Purpose |
|-----------|---------|
| `docs/01-plan/features/` | Plan documents for active features |
| `docs/02-design/features/` | Design documents for active features |
| `docs/03-analysis/` | Gap analysis reports |
| `docs/04-report/features/` | Completion reports |
| `docs/plans/` | Working implementation plans and designs |

## Archive
| Directory | Purpose |
|-----------|---------|
| `docs/archive/YYYY-MM/` | Monthly archive folders |
| `docs/archive/YYYY-MM/_INDEX.md` | Monthly archive index |
| `docs/archive/YYYY-MM/{feature}/` | Archived PDCA documents per feature |

## Lifecycle
```
01-plan → 02-design → implementation → 03-analysis → 04-report → archive/
```

Documents move to `docs/archive/YYYY-MM/{feature}/` after report completion.

## Status Tracking
- `.bkit-memory.json` — Current feature and phase
- `.pdca-status.json` — All feature statuses and metrics
