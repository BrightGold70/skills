# Live check — pin-agents-tail-banner — FAILED 2026-09-02

Verification item 3 of `docs/01-plan/features/pin-agents-tail-banner.impl-plan.md`.
Run at Phase 5 completion: all 6 tasks GREEN, suite 2663/0, mutations 46/46 ALL_CAUGHT.

## Verdict: the feature does not resolve a real Codex pane.

`hmad-dispatch env`, isolated pin file, pins cleared, no ambient `HMAD_ORCA_*_TERMINAL`:

    codex -> UNRESOLVED
    PREFLIGHT: FAIL unresolved=codex

`bound … by tail evidence` — the marker only this pass emits — is ABSENT (grep -c = 0).

## The earlier passes were confirmed blind, so the tail pass was reached

Orca's own diagnostic: three panes in the worktree, "absent from `worktree ps` agents[]"
(Pass 0 blind) "and their previews are empty" (Passes 1-2 blind). So the tail pass ran and
declined. It is not a wiring failure — Task 3's wire mutations prove the call is made.

## Root cause: the grammar cannot match a real Codex TUI banner

`term_f483657a` IS a live Codex pane. Its retained tail carries the banner at line 4:

    │ >_ OpenAI Codex (v0.149.1)                          │

Measured against the SHIPPED `_agent_tail_re codex`:

    │ >_ OpenAI Codex (v0.149.1)   … │   NO MATCH   <- the real thing
    OpenAI Codex (v0.145.0)             match
    ␣␣OpenAI Codex (v0.145.0)           match
    │ OpenAI Codex (v0.149.1)           match       <- box prefix alone is fine
    │ >_ OpenAI Codex (v0.149.1)        NO MATCH    <- `>_` alone breaks it
    │ OpenAI Codex (v0.149.1)   │       NO MATCH    <- trailing frame alone breaks it

Two independent causes, each sufficient:

1. **`>_` in the prefix.** The prefix class is `[│┃╎┆[:space:]]{0,6}` — box-drawing and
   whitespace only. The Codex TUI renders a `>_` prompt glyph inside the frame. `>` was
   deliberately REMOVED from the prefix class at v1.49 to reject Markdown blockquotes.
2. **Trailing frame.** The banner sits inside a box, so the line ends with padding and a
   closing `│`. Every arm of the grammar requires the banner to END the line (`[[:space:]]*$`).

## Why nothing caught it

The real TUI shape is in NEITHER corpus — not as a positive, not as a negative (grep = 0).
Every one of the 12 positives is an idealised bare or single-box-prefixed banner. So 53
impl-plan audit cycles, 335 unit tests, 46 mutations and two clean audit surfaces all agreed
on a grammar that has never been shown the string it exists to match. This is the
"hostile fixtures over tidy ASCII" failure: a corpus is only as strong as the shapes in it,
and the plan says so itself, four separate times, about four earlier revisions.

## Fix direction (needs design back-propagation, not a patch)

A real banner is FRAMED — a leading box character AND a closing one. A Markdown blockquote
(`> OpenAI Codex`, in the negative corpus) has a leading `>` and no frame. Candidate
discriminators, both preserving the existing rejections:

- admit the literal `>_` prompt glyph (Markdown uses `> `, never `>_`), and/or
- admit an optional trailing `[[:space:]]*[│┃╎┆]` so a closed frame does not defeat the
  line-complete rule.

Whichever is chosen must be added to the corpus as POSITIVES with the real strings, and the
existing blockquote/table negatives must be re-measured, since the prefix and line-end rules
are what reject them.

---

## RE-RUN 2026-09-02 after the grammar fix — PASS

Same protocol: isolated pin file, dummy handles seeded and their PRESENCE proven (2), cleared,
ABSENCE proven (0), no ambient `HMAD_ORCA_*_TERMINAL` exported.

    codex -> term_f483657a-92e4-46a0-ac3a-d440034232f9
    agy   -> term_a3b4c1dd-f30b-48da-87d9-69bda517844d
    PREFLIGHT: PASS
    bound term_f483657a-92e4-46a0-ac3a-d440034232f9 by tail evidence

The marker is emitted by this pass and by nothing else, so it is the only output that proves
the tail-evidence pass produced the resolution. Both agents resolved to their correct panes:
`term_f483657a` is the pane whose tail carries `OpenAI Codex (v0.149.1)`, `term_a3b4c1dd` the
one carrying `Antigravity CLI 1.1.22`. No cross-assignment.

Isolated pin directory removed and confirmed gone; the operator's real `.h-mad/orca-pins.env`
was never written (mtime unchanged, 1 Sep). No pane was created for either run.

### The fix

Prefix `[│┃╎┆▄▀▐▌░▒▓[:space:]]{0,24}(>_[[:space:]]*)?` and line end
`[[:space:]]*[│┃╎┆]?[[:space:]]*$` on both arms. `>_` is a UNIT, not a bare `>` added to the
class: bare `>` matches the negatives `> OpenAI Codex` and `> Antigravity CLI 1.1.22`
(measured), and `tail-re-bare-gt-prefix` now pins that decision.

Corpus 36 negatives / 15 positives — the three real strings added as positives. Suite 335;
mutations 49/49 ALL_CAUGHT with all 49 anchors resolving. The "what follows the signature"
rule that separates banner from prose is unchanged; only the decoration rules moved.

---

## RE-RUN 2026-09-02 on the MERGED skill (`main` @ `bf1c851`) — PASS

The two runs above were on `feature/pin-agents-tail-banner`. `~/.claude/skills/h-mad ->
/Users/kimhawk/orca/skills/h-mad`, so until the merge the *installed* skill still carried the
old grammar. This run re-proves the check against what is actually installed.

Same protocol. Isolated `HMAD_ORCA_PIN_FILE` under a `mktemp -d`; no ambient
`HMAD_ORCA_{CODEX,AGY,COORDINATOR}_TERMINAL` (`env | grep HMAD` empty before the run).

    seed (--force)   codex=term_DUMMY-CODEX-0000, agy=term_DUMMY-AGY-0000   PRESENT: 2 lines
    clear            pin-agents --clear                                     ABSENT:  0 lines
    env              codex -> term_f483657a-92e4-46a0-ac3a-d440034232f9
                     agy   -> term_a3b4c1dd-f30b-48da-87d9-69bda517844d
                     PREFLIGHT: PASS
    stderr           [H-MAD] codex: bound term_f483657a-92e4-46a0-ac3a-d440034232f9
                     by tail evidence

Both agents resolved to their correct panes, no cross-assignment. The tail-evidence marker is
emitted for `codex` only, which is the expected shape and not a partial pass: Codex has no title
identity by construction, so it is the agent the tail pass exists for; `agy` is resolved by the
earlier passes and never reaches it.

Seeding needs `--force` — plain `pin` refuses a handle absent from `orca terminal list`
("refusing to pin … — no such terminal"). The earlier runs' "dummy handles" wording omits this.

No repo mutation: `.h-mad/orca-pins.env` byte-identical before and after
(`9b12035ecdca4c090129cc53595267431bd5b8aa7b4f0720570f1457df5e831a`, mtime `1788221362`
unchanged); `git status --short` shows only the pre-existing untracked handoff doc and the 55
deliberate `.done` markers. The isolated directory held `env.out`, `env.err` and
`.h-mad/preflight.receipt` — the receipt landing there rather than in the repo is itself the
proof that `_receipt_file()` follows `dirname(_pin_file)` — and was removed, confirmed gone.

Alongside this, on the same merge result: full suite **2736 passed / 0 failed** (381s, run alone).
