# Report — pin-agents-tail-banner

**Date:** 2026-09-02 · **Branch:** `feature/pin-agents-tail-banner`
**Base (5c):** `03c66d55` · **Head:** `4775c5d` · **Substrate:** orca

## What shipped

A tail-evidence resolution pass in `_orca_find`. When the paneKey join, the title pass and the
preview pass all come up blind, the pass reads each in-scope pane's retained scrollback and
identifies the agent from its startup banner. Codex has no title identity by construction, so
before this an un-owned Codex pane was unresolvable.

Six tasks: stub `terminal read` per handle · `_orca_tail_sig` + `_agent_tail_re` · the pass,
wired on two connections · rival-signature rejection before counting · pass renumbering and
SKILL.md · the shipped 49-mutation spec.

## Evidence

| gate | result |
|---|---|
| spec ACs | 16/16, match rate 100% |
| module suite | 335 passed |
| full repo suite | 2663 passed, 0 failed |
| mutations | 49/49 ALL_CAUGHT, 0 survived, 49/49 anchors |
| wire registry | PASS — 10 registered, 10 verified, 0 broken |
| 6a-prime | READY_TO_MERGE, 36 tool calls |
| live check | PASS — `bound term_f483657a… by tail evidence` |
| audit cycles | plan 6 · design 10 · impl-plan 53 |

Both wires are proven ENFORCED rather than present: the whole-module revert removes callee and
call site together and cannot tell a wired build from an unwired one, so four wire-scoped
mutations carry that direction, including `wire-disconnect-callee-intact` which severs the call
while leaving the callee intact.

## The finding that mattered

**Every offline gate was green while the feature was inert.** At Phase 5 completion the suite
was 2663/0 and mutations 46/46, and `_agent_tail_re` could not match ANY real agent banner.
Measured live:

    │ >_ OpenAI Codex (v0.149.1)                          │   codex — framed, prompt glyph
          ▄▀▀▄        Antigravity CLI 1.1.22                   agy — block art
        ▀▀▀▀▀▀▀▀      Gemini 3.1 Pro (High)                    agy — block art

Zero matched, on both arms. The prefix class held box-drawing and whitespace only and every arm
required the banner to END its line; real renderers decorate on both sides. The corpus's 12
positives were all idealised, so 53 impl-plan audit cycles and two clean audit surfaces agreed
on a grammar never shown the string it exists to match.

The fix moved only the DECORATION rules — prefix
`[│┃╎┆▄▀▐▌░▒▓[:space:]]{0,24}(>_[[:space:]]*)?`, line end `[[:space:]]*[│┃╎┆]?[[:space:]]*$` —
and left the discriminating rule (what FOLLOWS the signature) untouched. `>_` is a UNIT, not a
bare `>` in the class: bare `>` matches the negatives `> OpenAI Codex` and
`> Antigravity CLI 1.1.22`, and `tail-re-bare-gt-prefix` now pins that choice. Corpus 36/15,
0 positives lost, 0 negatives broken.

This is the fifth revision of this rule. The four before it were each falsified by a shape the
corpus lacked; this one was falsified by a running pane.

## Open follow-ups

1. **Citation, not coverage** — spec AC-4.4 is implemented and mutation-pinned but not cited
   inline in the impl-plan, because spec and plan number ACs independently and both have an
   `AC-4.4` meaning different things. Add `(spec AC-4.4)` to the two rows.
2. **Pre-existing test-isolation defect**, not this feature's:
   `test_send_unresolved_agents_is_not_refused_as_a_conflict` reads the real `.h-mad` preflight
   receipt rather than a per-test one, so it passes or fails on ambient state. Reproduced
   failing on `origin/main` in a clean detached worktree.
3. **Concurrency fragility** — two pytest runs over one tree produce different, non-reproducible
   failure sets. Observed twice today. Run the repo suite alone.
