## Summary
The plan is highly specific, but its prescribed tail matcher fails on the long retained tails the feature explicitly targets. One verification command also remains underspecified for dispatch.

## Must-fix
- T3 mandates `printf '%s' "$tout" | grep -Eiq ...` under the wrapper's global `set -o pipefail` — when a banner occurs early in a large tail, `grep -q` exits immediately, the upstream `printf` receives SIGPIPE, and the pipeline returns 141 even though the regex matched. A producer-shaped 200,013-byte probe reproduced rc 141, and the documented 2,000-line cap can exceed the pipe buffer at ordinary terminal widths; the own-signature check then skips a valid pane (breaking spec AC-1.1), while the rival check can fail to reject a rival-bearing pane (breaking spec AC-2.3). Replace both early-closing pipelines with a form that consumes all input (for example, `printf ... | grep -Ei ... >/dev/null`) or a non-pipeline input form, update the exact mutation anchor, and add long-tail tests that put the wanted signature early and separately put the rival signature early after ensuring the wanted-signature check succeeds.

## Should-fix
- AC-6.10 does not give the exact anchor-sweep command — the harness requires one or more positional spec paths, yet the plan only says to run `--check-anchors` “over the whole directory under bash.” Spell out the bash command and glob so an implementer cannot invoke it with no paths or reproduce the documented zsh word-splitting failure.

## Nit
None
