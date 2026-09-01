## Summary
The plan is highly detailed and structurally sound, covering the necessary tests, mutations, and implementation steps for the tail-evidence pass. However, there is a discrepancy in Task 5 where a required code edit mentioned in the description is omitted from the code block, and a minor performance optimization was missed in Task 4 regarding subshell execution inside a loop.

## Must-fix
- Task 5's Code structure block omits the change for `hmad-dispatch.sh:1046` — The description explicitly states a value sweep finds a second site needing the number update, and AC-5.1 asserts it, but the code block only provides the fix for the first site. Provide the exact code block for this second site to ensure exact file paths and no vague requirements.

## Should-fix
- Task 4 injects `rival_tail_re="$(_agent_tail_re "$rival")"` inside the `while` candidate loop — Since `$rival` is determined above the loop and remains constant, computing it inside spawns an unnecessary subshell for every matched candidate. Hoist it outside the loop alongside `tail_re` to evaluate it exactly once.

## Nit
- In Task 6, several regex mutations (`tail-re-unanchored`, `tail-re-unanchored-agy`, `tail-re-widened-to-launch-line-agy`, `tail-re-widened-to-launch-line`) have an extra two spaces of indentation in their `replace` strings compared to their `find` strings.
