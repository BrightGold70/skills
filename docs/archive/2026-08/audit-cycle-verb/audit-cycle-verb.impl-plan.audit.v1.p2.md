## Summary
The implementation plan is exceptionally thorough and adheres tightly to the design document, successfully translating complex requirements into clear, verifiable tasks. Two issues need correction: a direct contradiction in the dispatch code block (`hmad_exec` vs `exec`), and the use of bash array syntax which violates the design's strict "POSIX shell only" invariant.

## Must-fix
- Task 6 code block contradicts text and design — The description states "Launches all K passes concurrently as `exec agy...`", but the code block uses `hmad_exec agy`. This violates the impl-plan writing quality requirement for code blocks to match referenced functions/text.
- Array syntax in Tasks 6 and 7 contradicts "POSIX shell only" invariant — The shell code blocks use bash array syntax (`pids[i]=$!`, `rc[i]=$?`, `${rc[1]}`). The design explicitly claims compliance with the "No-plugin-dependency" base invariant as "POSIX shell only". Strict POSIX `sh` does not support arrays; this must be rewritten using POSIX-compliant variable assignments (e.g., dynamically evaluated scalar variables) or the invariant compliance claim must be clarified if `hmad-dispatch.sh` is strictly a `bash` script.

## Should-fix
None

## Nit
None
