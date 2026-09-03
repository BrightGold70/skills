## Summary
The implementation plan is internally coherent on task ordering, connection-only mutation coverage, and the CLI transport split. The previously critical private-module registration and RunResult construction details are now specified consistently.

## Must-fix
None

## Should-fix
None

## Nit
- Task 4 says `DETAIL_KEYS` lets tests enumerate "all three," but the declared tuple contains ten keys; correct the prose so its count matches the code block.
