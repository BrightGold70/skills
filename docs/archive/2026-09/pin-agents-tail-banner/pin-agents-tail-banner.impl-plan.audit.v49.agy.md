AUDIT-pin-agents-tail-banner-impl-plan-v49-BEGIN
## Summary
The plan is highly rigorous, accurately incorporating lessons from past audits with precise green-at-RED discrimination and robust Bash environment scoping. However, there is a critical logical flaw in Task 4's rival rejection where an empty token results in a degenerate regex, causing all valid candidates to be falsely rejected. Addressing this single logic gap will make the plan safe for implementation.

## Must-fix
- Task 4 rival rejection guard is always true for non-rival tokens — The plan claims `_agent_tail_re ""` safely handles empty `$rival` tokens, but it emits a non-empty regex string (`^[[:space:]]*...`). Consequently, `[ -n "$rival_tail_re" ]` is always true, causing the pass to execute a degenerate regex that matches almost anything. This falsely rejects valid panes for any token outside `codex`/`agy`. Change the guard to check `if [ -n "$rival" ]` (or only assign `rival_tail_re` when `$rival` is non-empty), and update the `find` string of T6's `drop-rival-rejection` mutation to match.

## Should-fix
None

## Nit
None
AUDIT-pin-agents-tail-banner-impl-plan-v49-END
