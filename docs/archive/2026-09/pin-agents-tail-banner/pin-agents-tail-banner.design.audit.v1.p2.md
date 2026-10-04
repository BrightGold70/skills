## Summary
The design cleanly maps to the spec, translating the tail-signature pass into a clear architectural placement between Pass 2 and the OS-evidence Pass 4, and accurately capturing all candidate filtering logic. However, the design silently drops a load-bearing argument (`--cursor 0`) explicitly warned about in the plan, which is critical for reading the correct end of the terminal buffer.

| Spec AC | Classification |
|---|---|
| AC-1.1 | `implemented-as-written` |
| AC-1.2 | `implemented-as-written` |
| AC-1.3 | `implemented-as-written` |
| AC-2.1 | `implemented-as-written` |
| AC-2.2 | `implemented-as-written` |
| AC-2.3 | `implemented-as-written` |
| AC-3.1 | `implemented-as-written` |
| AC-3.2 | `implemented-as-written` |
| AC-3.3 | `implemented-as-written` |
| AC-4.1 | `implemented-as-written` |
| AC-4.2 | `implemented-as-written` |
| AC-4.3 | `implemented-as-written` |
| AC-5.1 | `implemented-as-written` |

## Must-fix
- Dropped load-bearing implementation detail (Cross-doc consistency) — The plan explicitly mandated the exact read command (`orca terminal read --terminal <handle> --cursor 0 --limit <n> --json`) and warned that `--cursor 0` is load-bearing to read the correct end of the scrollback. The design drops the command specification and `--cursor 0` entirely. This silent drift would result in the implementation reading the wrong end of the terminal buffer on panes with history.

## Should-fix
None

## Nit
None
