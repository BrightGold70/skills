# doc-block-exec — Phase 5d decisions

Decisions settled during 5d, per `h-mad/SKILL.md` §"Document-audit round cap — Phase 5 is
the gate": an open design-logic question surfaces at 5d as a blocked or failing RED and is
settled here, where a wrong choice costs minutes rather than a document round.

The five `OPEN-DECISION (r19, 5d)` lines carried on the impl-plan (Tasks 2/3/4, at
`:2635 :2871 :2873 :3374 :3376`) are NOT settled here. They are reached at their own Tasks.

---

## D1 — `_FenceEvent` field values on non-`open` events (Task 1)

**Raised by**: the Task 1 RED dispatch (`STATUS: NEEDS_CONTEXT`, 5d, session `93d3d858`),
which declined to invent them rather than guessing.

**The gap, exactly.** The impl-plan's `Code structure` block gives neutral-outside-their-kind
values for three of the kind-scoped fields —

    level: int      # heading events only (1-6, the opening-run length); 0 otherwise
    text: str       # heading events only: the compared text (closing-run stripped)
    candidate: bool # scanner-derived: True only for a BACKTICK opener whose first info word is "bash"

— and says nothing about `marker`, `run`, `indent` and `info` on a `close`, `body`, `prose`
or `heading` event. The design describes those four as "the opener's marker character, run
length, indentation and info string", which fixes their meaning on an `open` event and leaves
the other four kinds unstated. AC-1.8's `test_fence_events_trace_on_every_hostile_fixture`
pins **every** field of every event on LF and CRLF copies of each hostile fixture, so the test
cannot be written until this is decided. It is build-class: the 5e production code and that
test differ depending on the answer.

**Decision (operator, 2026-09-06): neutral on every non-`open` event.**

    open   : marker='`'  run=3 indent=<opener indent> info=<raw info string>
    close  : marker=None run=0 indent=0 info=''
    body   : marker=None run=0 indent=0 info=''
    prose  : marker=None run=0 indent=0 info=''
    heading: marker=None run=0 indent=0 info=''   (level and text carry the heading's own values)

**Why this and not the alternatives.**

1. It is the pattern the document already states for every other kind-scoped field: `level`
   is "0 otherwise", `text` is "heading events only", `candidate` is "True only for a
   backtick opener". Three fields neutral outside their kind and four inheriting would be two
   rules where the document reads as one.
2. `marker: str | None` is typed optional. Nothing but a non-opener needs the `None` arm.
3. No consumer reads any of the four on a non-`open` event. `extract` selects on `.candidate`
   and holds the `open` event it de-indents against; `fence_aware_end` reads `.kind`,
   `.level`, `.start` and `.end`; `find_heading` reads `.text`, `.level` and `.end`.
4. Carrying the opener's values onto `body`/`close` would make fence geometry readable off a
   body line, which is the property the design's single-scanner rule exists to prevent
   ("no consumer re-recognises a fence or a heading"). A future consumer could then branch on
   fence state without going through `_fence_events`, which is the shape
   `scanner-duplicated-in-consumer` and `test_extract_has_no_fence_state_of_its_own` guard.

**Residual, stated exactly.** A `close` event does not report the closer's own run length or
indentation, so nothing downstream can distinguish a 3-backtick closer from a 5-backtick one,
or a 0-space closer from a 3-space one. That information is used inside `_fence_events` to
decide closure and is deliberately not exported. If a later task needs it, it is a DESIGN
change and gains its own field and its own mutation row — it is not to be recovered by
re-scanning in a consumer.

**No mutation row follows.** The row list in the impl-plan MIRRORS the design's matrix and
the total is 87 at this batch; adding a row here would put the impl-plan one above the design.
A row for the neutral-fields rule, if the design wants one, is the design's to add. What
stands in for it is the fixture: the AC-1.8 trace test asserts the neutral values on every
non-`open` event of every hostile fixture, on LF and CRLF, so an implementation that carries
opener metadata through fails outright.
