## Summary
The design is remarkably thorough, precise, and robust, particularly in its handling of process group lifecycle (zombie leader reaping, escapee bounds) and atomic stream artifact reservations. A minor factual error exists regarding how POSIX `open()` handles directories and sockets under `O_WRONLY`, but the resulting refusal behavior is correct.

## Must-fix
- A directory (or socket) opened with `O_WRONLY` never returns a descriptor to check — the `open` syscall itself raises `EISDIR` (or `ENXIO`/`EOPNOTSUPP`), meaning the refusal happens at the syscall level and never reaches the `fstat` check.
  quote: docs/02-design/features/doc-block-exec.design.md › `a FIFO, socket, device or directory is closed and refused as StreamPathUnwritable (UNREADABLE reason=stream_path_unwritable), checked on the descriptor rather than the path`

## Should-fix
None

## Nit
None
