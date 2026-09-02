AUDIT-doc-block-exec-design-v3-BEGIN
## Summary
The design provides a robust, well-justified implementation that thoroughly satisfies the spec requirements, cleanly addressing edge cases like isolated cwds and overlapping substitutions. Axis C reconciliation shows one API shape restatement where the design deliberately splits extraction and selection to resolve an ambiguity in the spec's contract.

| AC | Classification |
|---|---|
| AC-1.1 | restated |
| AC-1.2 - 1.7 | implemented-as-written |
| AC-2.1 - 2.7 | implemented-as-written |
| AC-3.1 - 3.9 | implemented-as-written |
| AC-4.1 - 4.5 | implemented-as-written |
| AC-5.1 - 5.4 | implemented-as-written |
| AC-6.1 - 6.6 | implemented-as-written |

## Must-fix
- AC-1.1 restated — The Spec states: `extract(doc, heading="## H") returns exactly one block`. The Design restates this by splitting the logic: `def extract(...) -> list[Block]` and `def select(...) -> Block`. The design's choice is a necessary architectural narrowing (it resolves a contradiction between returning one block and handling 0/>1 candidates cleanly), but this API divergence must be explicitly pushed back to the Spec so the implementation is verified against the separated architecture.

## Should-fix
- Process group reaping risk — The design specifies `os.killpg(os.getpgid(proc.pid), signal.SIGKILL)` for timeouts. If the direct child process has already died but a grandchild holds the pipe open, `os.getpgid` can raise `ProcessLookupError`, aborting the reaping and leaving the grandchild alive. Since `start_new_session=True` guarantees the process group ID is numerically equal to the child's PID, `os.killpg(proc.pid, signal.SIGKILL)` is the robust, race-free pattern to reap the entire group.

## Nit
None
AUDIT-doc-block-exec-design-v3-END
