## Summary
The plan is highly specific and its task sequencing, wire pins, and type-preserving mutation bodies are consistent with the paired design. One rollback path is still underspecified for the plan's artifact-safety contract, and one scanner comment contains a self-comparison typo.

## Must-fix
None

## Should-fix
- Task 4's failed-second-reservation rollback is not specified as a verified cleanup path — the plan says to close and unlink a first created stream artifact inside the reservation region, but an OSError from that close/unlink is only mapped to StreamPathUnwritable; it does not state a backstop/retry plus read-back that proves the descriptor is closed and the created path is absent. This leaves the stated no-new-artifact-on-refusal guarantee unverified on the very rollback path that mutates it. Specify the state tracking/finally and lexists/fstat checks, with a discriminating fault-injection mutation/test.

## Nit
- In Task 1's _FenceEvent comment, fence_aware_end is said to test start >= start; it should say event.start >= start, as the surrounding prose already does.
