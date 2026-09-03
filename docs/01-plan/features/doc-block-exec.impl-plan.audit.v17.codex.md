## Summary
The task ordering, exact paths, and mutation rows are largely implementation-ready, but the paired design and this plan still disagree on the authoritative fault-injection/transport taxonomy. That disagreement reaches the tests that establish CLI exit-code coverage, so it is not safely left as prose drift.

## Must-fix
- The paired design's Test Strategy still says that only six module-level seam injections require in-process `main(argv)` and describes the instance wrapper only for `communicate`/`wait`; this plan defines eight injections (seven module seams, including `os.unlink`, plus the one instance wrapper also used for `poll`) — the source design can therefore direct an implementer to send the unlink/poll fault cases through the wrong transport or omit them from the canonical taxonomy. Make the design and plan use one identical eight-item list, explicitly covering `os.unlink` and all three wrapped instance methods (`communicate`, `wait`, `poll`), and correct the plan's "seventh injection form" wording to "eighth".

## Should-fix
None

## Nit
None
