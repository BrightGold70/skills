# h-mad reference — audit prompt assembly and dispatch

_Moved verbatim from `h-mad/SKILL.md` (row 2910); SKILL.md keeps a pointer stub under the same heading. Edit the text here. Everything below the marker line is the section body exactly as it stood in SKILL.md._

## Audit prompt assembly

<!-- h-mad split body: SKILL.md §"Audit prompt assembly" -->

**When authoring a source-level assertion, assert the call form, not an occurrence count over a whole method.** A count over a method policing one call site over-constrains it and recruits the implementer into damaging unrelated code; assert the specific call/argument shape at the one site the contract concerns.

**Re-verify every impl-plan pin against the tree at dispatch time.** Every line number, site count, and "live defect" claim must be confirmed against the current tree before it is passed to an implementer — a stale pin produces a wrong edit or a fabricated failure (measured on `feature/193`: `:1583`→`:1575`, "three log sites"→two, "live defect"→already-citable).

**Substrate preflight (once per H-MAD run — at Phase 5 start, or the first audit dispatch if earlier; skip if the substrate was already recorded this run).** Run `hmad-dispatch env`.
If it exits non-zero → halt `<phase>:no_substrate`. Record the printed substrate +
agent mapping into state so the run log states which environment it dispatched under:

```bash
python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py docs/.bkit-memory.json \
  --feature "<feature>" \
  --set substrate='{"name":"orca","agents":{"codex":"term_…","agy":"term_…"}}'
```

State is the carrier and `h_mad_telemetry.py record` is the reporter — it copies the
field onto the Phase-7 row it already builds from this record. Writing it here is what
makes the step executable at Phase-5 time; `record` is a close-out call and cannot
serve a Phase-5-start instruction. This is the explicit environment check (cmux vs orca) — do it
before any `send`/`read`. See `references/agent-substrate.md`.

For each audit (Phase 3, 4, 5b), run one complete cycle with the verb:

```bash
hmad-dispatch audit-cycle --feature <feature> --phase plan|design|impl-plan \
  --cycle <N> --passes <K> --project-root <PROJECT_ROOT>
```

`audit-cycle` runs exactly one cycle: assemble, dispatch, collect, gate, and print one
`AUDITCYCLE:` verdict. It is not the revision loop; re-auditing until
`must=0 should=0` remains the orchestrator's job. For the codex second surface
used by the exec leg, see §"Second surface — the codex leg".

**Read the `Effort:` block before you trust a clean cycle.** The verb hands each pass's
NDJSON log to the combiner, which reports `tools=/ok=/failed=/thinking=` per pass and marks
`low-evidence` when a pass made at most the 2 successful calls the report-file contract
itself costs — the report write and the `.done` marker — so it cannot have read anything.
Measured across the 8 passes of cycles 21–24 on `grounding-evidence-coverage`: *every*
substantive finding came from a pass with high thinking or ~34 tool calls, while cycle 21
pass A made **0** tool calls and returned "CLEAN PASS" on a plan the other pass proved
defective, and cycle 24 double-cleaned with thinking collapsed to 6.2 k / 4.4 k and exactly
the 2 delivery calls each. At the `AUDITCYCLE:` line those are indistinguishable from real
clean passes.

It is a **scoring caveat, not a gate**, and deliberately so: a pass with 2 tool calls
honoured the contract exactly as asked, and one such pass in this repo (5,356 thinking,
2 calls) still returned a real finding. Treat `low-evidence` on a clean pass as a reason to
re-dispatch that pass, never as a verdict. `combine()` cannot see the block, and a log that
was named but could not be read renders `unreadable` rather than zeros — `tools=0` is
exactly what a genuinely hollow pass looks like, so zeros from an unread file would
manufacture the finding.

**Check the working tree after every audit dispatch, and treat any delta as a finding.** An audit
reads; it does not write. `git status --short` before and after a cycle should be identical, and a
difference is not a bonus fix — it is the reviewer having edited what it was measuring, which
destroys the evidence the next cycle depends on. Revert it (preserve the diff first, so a real
finding buried in it is not lost) and re-read the report knowing its author mutated the tree.
Measured 2026-08-28: a 5b audit changed three tracked files, one of them a test unrelated to the
feature, made green by stubbing out the call it existed to exercise — and its report described that
as restoring a green suite while asserting a cause the edit could not have affected. The prompt now
forbids this (`audit-prompt.template.md` §READ-ONLY), so the check is a backstop rather than the
guard, but a prompt rule is advice and the tree is fact.

For each audit pass, the verb **assembles with the script** — it performs steps 1
through 7.2 below deterministically and refuses to emit a prompt that fails the preflight:

```bash
# Orca report-file transport; for the sentinel scrape omit RP, --report-file and --out.
RUN=$(date -u +%Y%m%dT%H%M%SZ)-$$   # a fresh run token per dispatch, re-dispatches included
RP=/tmp/audit_<feature>_<phase>_cycle<N>_run$RUN.report.md
python3 ~/.claude/skills/h-mad/scripts/h_mad_assemble_audit.py \
  --feature <feature> --phase plan|design|impl-plan --cycle <N> \
  --project-root <PROJECT_ROOT> \
  --report-file "$RP" \
  --out /tmp/audit_<feature>_<phase>_cycle<N>_run$RUN.txt
echo "RUN=$RUN RP=$RP"
```

It prints `ASSEMBLE: PASS <path> <size> sentinel=<s> size_status=verified|unverified` or
`ASSEMBLE: HALT <phase>:preflight` with the
reasons, **exiting 0 either way** (a rejected prompt is a verdict, not a tool failure —
see the base invariant on audit-gate signal discipline). A halted prompt is deliberately
not written, so it cannot be dispatched by mistake. A non-zero exit means unreadable
inputs. On `HALT <phase>:preflight`, fix the template or invariants file and re-run; never
hand-patch the staged prompt.

With `--report-file`, the assembler also **claims the report path and its prompt path,
once**. Before it writes anything it refuses a report path or `--out` that already exists, then
creates a marker exclusively under `$XDG_CACHE_HOME/h-mad/handed/` (default
`~/.cache/h-mad/handed/`), and it writes the prompt exclusively; nothing ever releases either.
The marker is keyed by the realpath of the parent joined with the filename, casefolded as a
whole, so `/tmp` and `/private/tmp` (or two case spellings) share one claim, and the marker
never lands in a project. The claim directory is keyed on `XDG_CACHE_HOME`/`HOME`, so
assemblers that must see each other's claims need the same values; a write-restricted sandbox
fails closed with `report_path_marker_unwritable`. Without `--out`, the prompt path is the
report path with `.report.md` turned into `.txt` (any other report path gets `.txt` appended),
so minting one mints the other. The derived prompt path sits beside RP, so pass an explicit
`--out` for a report path in the docs tree.
Every dispatch therefore needs a fresh pair: the recipes below mint one per dispatch with a
`RUN` token, and `audit-cycle` mints a fresh stem per run. Stale markers are harmless: they only
refuse paths nobody should reuse. Nothing reaps them, nor the per-run files the verb leaves in
`/tmp`. The verb stages those files in the directory `HMAD_AUDIT_STEM_DIR` names, `/tmp` when it
is unset or empty, and refuses one that is relative, missing or contains `:`; the test suite points it at
its own basetemp, because `/tmp` is shared with every other session on the machine and a suite
that tidied `/tmp` deleted a concurrent suite's stems. Five more HALTs can come back. A HALT
deletes nothing.

- `ASSEMBLE: HALT <phase>:report_path_handed path=<RP> held=<path>` — the report path or the
  prompt path (`held=` names which) was claimed by an earlier hand or already exists. On
  `ASSEMBLE: HALT <phase>:report_path_handed`, mint a new `RUN`, which moves both paths. Never
  reuse either, even if its leg looks dead (#49o).
- `ASSEMBLE: HALT <phase>:report_path_not_absolute path=<path>` — `--report-file` and `--out`
  must be absolute: a relative path resolves against the agent's cwd, not the assembler's.
- `ASSEMBLE: HALT <phase>:report_path_is_prompt_path path=<RP>` — `--out` names the same
  file as `--report-file`, so the prompt would sit at the report path; give it its own path.
- `ASSEMBLE: HALT <phase>:report_path_unreadable path=<RP>` — the report or prompt path could
  not be measured, so it is not known to be fresh; fix the permissions on the report directory
  and re-run.
- `ASSEMBLE: HALT <phase>:report_path_marker_unwritable path=<RP>` — the claim directory could
  not be created or written, so no prompt was written; fix it (or `XDG_CACHE_HOME`) and re-run.
  There is no fallback directory.

**Assert `ASSEMBLE: PASS` before dispatching the assembled prompt** — the same mandated
read as the Phase-5 `PREFLIGHT:` assertion, for the same reason: the script exits 0 on
both verdicts, so `$?` cannot tell you which one you got, and an unread token is worth no
more than the unread `STALE` line it is modelled on.

**Read `size_status=` on the same line, not just the token.** `verified` means the prompt
is no larger than the biggest one confirmed answered (92,055 B — see
`references/agent-substrate.md`). `size_status=unverified` still dispatches, because
prompts that size have answered; what it changes is *diagnosis*. If the reply comes back
empty, **suspect size before re-dispatching** — first re-read the full buffer, since a
tail-grep reports SILENT for replies the TUI merely reflowed, and only then apply step 5.5.

The field is on the verdict line deliberately. It used to be a separate `!` warning beside
`ASSEMBLE: PASS`, which an orchestrator following this contract exactly never had to read —
the same defect the `PREFLIGHT:` token exists to fix, one signal over. Note the verdict
token stays exactly `PASS`/`HALT`: a `PASS_OVERSIZE` variant would still match every
`grep "ASSEMBLE: PASS"` consumer and would have reproduced the defect rather than fixed it.

Every defect this area has had came from doing the steps by hand: the rubrics were
inlined twice, `{Design only — cross-doc:}` reached the reviewer in 69 of 69 dispatched
prompts, and a hand-written duplication grep hardcoded a project-authored heading. None
of them raised an error. Use the script.

The steps below are what it implements — read them when debugging a `HALT`, or when
assembling by hand because the script is unavailable:

1. Start from `~/.claude/skills/h-mad/audit-prompt.template.md`, **dropping the leading orchestrator note** — every line from `<!-- ORCHESTRATOR-NOTE:START` through `ORCHESTRATOR-NOTE:END -->` inclusive. That block is assembly instructions to you, not reviewer content; left in, the prompt opens by telling the reviewer it is reading a template.
1.5. **Resolve the `{{ONLY:…}}` applicability markers** for this audit's type (`plan`,
   `design`, or `impl-plan`). A marker is an assembly directive and must never reach the
   reviewer. If the audience list contains this audit's type → delete the marker, keep the
   content. Otherwise → delete the marker **and the content it governs**. Inline form
   (`{{ONLY:design}} <content>`, possibly after a `- ` bullet) governs the rest of that line
   plus any following lines indented deeper than it; block form (marker alone on its line)
   governs down to the matching `{{END-ONLY}}`, both marker lines included.

   **Delete the whole line — never blank the slot and keep its label.** `Paired audited
   plan:` followed by nothing tells the reviewer a document is *missing*, not that it was
   inapplicable, and a design audit reading "the plan wasn't provided" discounts the
   cross-doc check it was supposed to perform.
2. Replace `<INLINE_TARGET_DOC>` with full text of the target doc (plan.md, design.md, or impl-plan.md).
3. Replace `<INLINE_BASE_INVARIANTS>` with full text of `~/.claude/skills/h-mad/invariants.base.md` (workflow-universal Axis B — always inlined, base before project, regardless of whether a project file exists).
4. Replace `<INLINE_PROJECT_INVARIANTS>` with full text of `<PROJECT_ROOT>/.h-mad/invariants.md` (domain Axis B). If the project file is absent/empty, leave the slot empty — the base layer still applies.
5. For design audits only: replace `<INLINE_PAIRED_PLAN>` with audited plan.md.
5.5. For plan and design audits: replace `<INLINE_PAIRED_SPEC>` with full text of `docs/01-plan/features/<feature>.spec.md` — the Axis C source of truth. Without it the reviewer has no AC list to reconcile against and Axis C degrades to prose review, which is the failure it exists to prevent: the paired plan carries only incidental AC references, not the enumeration. For impl-plan audits leave the slot empty; that audit contracts against the design.

   **Prompt size.** Axis C makes an already-large prompt larger: measured on a real feature, design 45 KB + plan 21 KB + spec 16 KB assembled to 88 KB (72 KB without the spec). Whether that is a problem depends on the transport. On the **`exec` path** it is not at these sizes — 266,342 B was confirmed answered 8 of 8 on 2026-08-22 (agy 1.1.18, both transports honoured every time), so dispatch the whole thing. The one `exec` ceiling is **1,048,576 characters** on both agents (codex refuses past it with `input_too_large`; agy's arg is bounded by `ARG_MAX` at the same figure), and a full-history design or impl-plan inline CAN reach it (measured 2026-09-05): the assembler then HALTs `oversize` and writes no prompt, and the **first remedy is `--vh-tail N`** — keep every body byte, inline only the last N Version History entries of each embedded document — never a trimmed document. On the **pane path** the confirmed-answered frontier is ~92 KB via file indirection (a 92,055 B prompt was answered by a live agy pane on 2026-07-30, falsifying the earlier ~61 KB ceiling); the old "49 KB normal / 53 KB silent" figure was a delivery-mode artifact (a paste, not file indirection) and never reproduced (see `references/agent-substrate.md`). A real audit assembles to at most ~88 KB, so it sits inside the confirmed pane frontier — but if a pane prompt ever does run past ~92 KB, two things follow. First, **do not solve it by trimming the design** — showing the reviewer only its AC-bearing sections is self-defeating, since `absent` becomes undetectable and `absent` is the failure Axis C exists to catch. Inlining the spec's `## Functional Requirements` section alone rather than the whole spec is a legitimate saving (~7 KB) and loses no AC; switching that dispatch to `exec` lifts the ceiling to the 1,048,576-character one above. Second, an over-long prompt is a **safe** failure: `h_mad_extract_report.py` exits 2 on a missing or empty sentinel pair, so the cycle halts instead of scoring silence as a clean gate.

   **Before treating a silent reply as a size failure, read the whole buffer.** `hmad-dispatch read <agent> --from-start`, not a tail — the TUI reflows a reply across redraw frames, and a tail-grep for a sentinel reports SILENT for prompts that answered (measured; see `references/agent-substrate.md`). Most "size failures" are this.

   **If it really is size, "split by FR group" usually will not help.** Only the spec divides; everything else is carried by every split. Measured on a real design audit totalling 50.9 KB:

   | term | size | divides on an FR split? |
   |---|---|---|
   | design | 22.4 KB | no |
   | plan | 10.3 KB | no |
   | audit template | 8.0 KB | no |
   | base + project invariants | 5.5 KB | no |
   | spec (FR-only trim) | 4.7 KB | **yes** |

   46.2 KB of 50.9 KB is fixed, so a two-way split yields ~48.5 KB per half — about 2 KB of relief for two dispatches, two audit files and two gate runs. The remedy silently assumes the *spec* is the marginal term; whenever the design dominates, which is the normal case for a detailed design, it does not work.

   The options that do work, in order:
   1. **Inline only the spec's `## Functional Requirements`** — ~7 KB, loses no AC. Already the default.
   2. **Shorten the design itself** — tighten prose and remove restated plan content. Note the constraint above: do *not* do this by showing the reviewer only AC-bearing sections.
   3. **Split the feature**, not the audit. Fewer FRs per feature shrinks the design, plan *and* spec together — it is the only division that touches the fixed terms.
   4. **Trim the rubric** as a last resort, remembering `invariants.base.md` is inlined into every audit prompt, so a rule added there is paid for by all of them.
6. For impl-plan audits only: replace `<INLINE_PAIRED_DESIGN>` with audited design.md.
6.5. Replace `<AUDIT_SENTINEL>` with `AUDIT-<feature>-<phase>-v<N>` — the per-cycle stem step 9 extracts on. It must be unique per cycle; reusing a previous cycle's stem reopens the stale-scrollback trap it exists to close.
6.6. **Report-file transport (preferred under Orca).** If `hmad-dispatch env` reports `substrate: orca`, replace `<REPORT_FILE_PATH>` with an absolute staged path `RP=/tmp/audit_<feature>_<phase>_cycle<N>_run$RUN.report.md`, minting `RUN=$(date -u +%Y%m%dT%H%M%SZ)-$$` once per dispatch and using it for the staged prompt too (step 7), so no dispatch ever reuses a report or prompt path. A hand assembly claims nothing: minting a fresh `RUN` is its only guard (only the script claims both paths and HALTs on reuse). Carry the literal `RUN` and `RP` values into steps 7–9, since each Bash call is a fresh shell; the agent will write its report there and mark `$RP.done`. Otherwise (cmux / unpinned) leave `<REPORT_FILE_PATH>` empty and rely on the sentinel scrape. Measured on `audit-cycle-verb`: across the 18 impl-plan audit passes, 17 delivered via the report file (file present, non-empty, `.done` written); 1 did not — cycle 7 pass 1 wrote neither the report file nor the marker, and its report was recovered from `--out`. The verb therefore always arms the `--out` fallback. **Arming it was not the same as it working**: until #16 the fallback passed `--after-marker` unconditionally, which requires the dispatch boundary that only the PANE transport writes, so on every `exec` `--out` file extraction exited 2 and the fallback silently yielded nothing. Measured: a codex pass wrote a **0-byte report file plus its `.done` marker** while `--out` held the complete report, and collection answered `COLLECT: MISSING delivered=none`. The flag is now passed only when the boundary is actually present. See `references/orchestration-mode.md` §"Report-file transport".
7. Stage: `cat > /tmp/audit_<feature>_<phase>_cycle<N>_run$RUN.txt`.
7.2. **Residual-placeholder preflight — mandatory, before any `send`.** Substitution is a
   literal string replace over the whole file, so it is silent in both failure directions: a
   slot you forgot stays in the prompt as a raw token, and a bracketed slot *mention* in prose
   gets replaced too, splicing a second copy of a rubric into the middle of a sentence. Neither
   raises an error; both reach the reviewer. Check:
   ```bash
   P=/tmp/audit_<feature>_<phase>_cycle<N>_run$RUN.txt
   grep -n '<INLINE_\|<AUDIT_SENTINEL>\|<REPORT_FILE_PATH>' "$P" && \
     echo "HALT <phase>:unfilled_slot" || echo "slots OK"
   grep -n '{{' "$P" && \
     echo "HALT <phase>:unresolved_conditional" || echo "conditionals OK"
   # Duplication check — each rubric must appear exactly once. Derive the needle from
   # each inlined file's own first line: the PROJECT invariants heading is written by
   # the project (HemaSuite's reads "# HPW Project Axis B Invariants"), so a hardcoded
   # heading reports a false 0 in every repo but the one it was written against.
   # Do NOT anchor to '^': a stray copy spliced into a blockquote is prefixed '> # …',
   # so an anchored grep reports a clean 1 while the prompt carries 2.
   BASE_MD=~/.claude/skills/h-mad/invariants.base.md
   PROJ_MD=<PROJECT_ROOT>/.h-mad/invariants.md
   grep -Fc "$(head -1 "$BASE_MD")" "$P"                          # must be 1
   [ -s "$PROJ_MD" ] && grep -Fc "$(head -1 "$PROJ_MD")" "$P"     # must be 1 when a project file exists
   ```
   Any hit on either grep, or a count > 1 on either rubric → halt (`<phase>:unfilled_slot` /
   `<phase>:unresolved_conditional`),
   fix the template/invariants file, re-assemble. Do **not** dispatch a prompt that still shows
   a raw `<INLINE_…>`: the reviewer reads it as an unfilled template and silently discounts the
   axis it belongs to, which scores as a clean gate on a rubric that was never delivered.

   This is a live failure, not a hypothetical: `<INLINE_BASE_INVARIANTS>` and
   `<INLINE_PROJECT_INVARIANTS>` were once written **bracketed** inside the template's own
   header blockquote and inside `invariants.base.md`'s header, so every assembled prompt carried
   both rubrics twice (measured: 2 copies of each in every `/tmp/audit_*.txt` on this machine —
   ~4–6 KB of dead bloat against the ~49–53 KB reviewer cliff in step 5.5) and still displayed a
   raw `<INLINE_BASE_INVARIANTS>` token. **Prose refers to a slot by bare name
   (`INLINE_BASE_INVARIANTS`); only a real slot is bracketed.** Keep it that way in any new
   template or invariants file.
7.5. **On cycle 1 of each audit phase (and after confirming agy is alive via `hmad-dispatch alive agy`), clear agy's context** (see §"Agent-pane context hygiene") so a prior feature's/phase's transcript can't drift the verdict or pollute the scrollback you later grep. Later cycles of the SAME audit reuse the warm context (the running revision thread is wanted).
8. Dispatch:
   ```bash
   hmad-dispatch send agy /tmp/audit_<feature>_<phase>_cycle<N>_run$RUN.txt
   ```
   `send` chooses its own delivery mode by size: it inlines below
   `HMAD_SEND_INLINE_MAX` (default 8192 bytes) and otherwise tells the agent to
   read the staged file by absolute path. Audit prompts run 16–90 KB, so they
   take the indirection path — no need to hand-roll it.
9. Capture the report. **Under Orca (report-file transport), skip the scrape entirely** — the agent wrote a clean file, so read it directly and jump to the gate:
   ```bash
   hmad-dispatch report-wait "$RP" --timeout 600 \
     > docs/01-plan/features/<feature>.<phase>.audit.v<N>.md
   ```
   The gate refuses a path named like a transport file (`audit_*.report.md`) — gate the docs path, never `$RP`.
   This has no sentinel-extraction step (the file is already the report), no `wait`, and no dedent/`•`-normalize (the file is clean markdown, not a TUI render). On timeout, the agent did not honour the contract — fall back to the scrape path below.

   **Never gate an audit on the dispatch's `result.status`.** The report file and its `.done` marker are the delivery contract; `status` is not. ANY failed or refused tool call yields `status: ERROR` beside a complete, correct answer, and the cause is usually incidental to the audit — measured three times with three unrelated causes: a refused `.tmp` write (`grounding-evidence-coverage` impl-plan cycle 22 pass B, on a report carrying two independently-verified real findings), a `find_by_name` timeout plus a `view_file` on a nonexistent path (2026-08-24, 31 tool calls / 29 ok, schema-correct report), and a `write_to_file` rejected for a missing argument that the agent immediately retried successfully (2026-08-24). This is the same rule `h_mad_review_evidence.py` follows for 6a-prime (step 6a-prime above): report `result.status`, never gate on it. Read the file and the marker.

   **Scrape fallback (cmux / unpinned, or when `report-wait` times out) — never hand a raw scrape to the gate.** The scrape holds live scrollback, so the previous cycle's report is usually still above the prompt; extracting on the first `## Summary` scores the wrong cycle:
   ```bash
   hmad-dispatch read agy --lines 200 > /tmp/scrape_<feature>_<phase>_cycle<N>.txt
   python3 ~/.claude/skills/h-mad/scripts/h_mad_extract_report.py \
     /tmp/scrape_<feature>_<phase>_cycle<N>.txt \
     --feature <feature> --phase <phase> --cycle <N> \
     > docs/01-plan/features/<feature>.<phase>.audit.v<N>.md
   ```
   The extractor takes the **last** complete `<AUDIT_SENTINEL>-BEGIN`/`-END` pair, so neither an older cycle nor a retry within this one can win. It exits 2 and writes nothing when the pair is missing or its body is empty — that is the "dispatched, went idle, produced nothing" case, and it must halt the cycle rather than be scored. On exit 2: re-read with `--from-start` (a larger tail does not escape an overdrawn frame region — J3), and if the report genuinely never arrived, `hmad-dispatch clear agy` and re-dispatch.
10. Design audits write to `docs/02-design/features/` instead; adjust the redirect above.
11. Run the gate — the verdict unit counts bullets in BOTH `## Must-fix` AND `## Should-fix` (excluding the bare-`None` sentinel, a stray `- None`, and any `## Acknowledged-not-fixed` items in the same file or a sidecar `.audit.v<N+1>.md` passed via `--ack-file`):
    ```bash
    python3 ~/.claude/skills/h-mad/scripts/h_mad_audit_gate.py <audit-file>
    ```
    The gate **prints a verdict token and always exits 0** on a verdict (a non-zero exit is reserved for operational errors such as a missing file — never for a FAIL, so the gate never registers as a tool failure). Parse the **token**, not `$?`:
    - `GATE: PASS must=0 should=0` → gate passes (must-fix=0 AND should-fix=0). Proceed.
    - `GATE: FAIL must=N should=M` (N or M > 0) → gate fails. Surface the bullets, revise, re-audit.
   Then read the second line, `GATE-CLASS: build=N measurement=M untagged=K ack_refused=R`: a FAIL whose musts are all measurement-class is routed to the `## Acknowledged-not-fixed` sidecar with their re-run commands rather than to another cycle, per §"Finding class — build vs measurement"; `ack_refused>0` means a build-class (or unknown-class) bullet was acknowledged and the gate refused it — fix it, do not re-ack it.
      "Revise" is where §"Close the class, never the instance" applies: before writing the fix,
      decide whether each bullet is a singleton or one member of an open-ended set, and for a set
      write the rule **and** the exactly-stated residual. Fixing the member the reviewer named is
      what turns one defect into a seven-cycle series.

    **Pass `--gated <doc>` for every document the audit judged, and read the stamp back before relying on the PASS.** The gate reads the *audit file* and never the document the audit was about, so a PASS survives every later edit to the thing it passed — including the edits that fix the previous cycle. Measured: a design that gated clean twice produced 9 findings on the next cycle, and 4 of them were created by the fixes for the cycle before. `--gated` is repeatable and a cycle that gates a design **and** an impl-plan must name both; a stamp is written only on PASS (a stamp over a FAIL would let the readback report `CURRENT` for a verdict that blocked), and a gated file that cannot be read yields `GATE: UNSTAMPABLE` and writes nothing rather than recording a verdict over content the gate never saw. Then:
    ```bash
    python3 ~/.claude/skills/h-mad/scripts/h_mad_audit_gate.py <audit-file> --verify-stamp
    ```
    Read the `GATESTAMP:` token — deliberately **not** `GATE:`, so a consumer globbing the verdict line cannot conflate the two. `CURRENT` → the PASS is still about what is on disk. `STALE` → it is not; the changed files are named, and the edits since are themselves ungated — halt `audit_gate:verdict_stale` and re-audit. `UNSTAMPED` (exit 2) is a **cannot-judge**, never `CURRENT`: nothing was recorded, so nothing was compared, and it is the same class of lie as an empty scrape reading as "no findings".
    When you revise, bump the doc's `## Version History` with the helper, never with a hand-rolled
    anchored substitution:
    ```bash
    python3 ~/.claude/skills/h-mad/scripts/h_mad_version_history.py <doc> \
      --version v1.<N> --text "Audit v<N> fixes from <audit-file> — <summary>."
    ```
    **A cycle whose findings were all rejected has nothing to bump — do not bump it.** The Version
    History records *fixes*; a rejection goes to `<feature>.<phase>.rejections.md`
    (§"Record a rejected finding in the rejections ledger, never in a gated document"). Bumping
    here for a rejection edits a gated file, which resets the both-clean streak and costs a second
    cycle for a finding that was not real in the first place.
    Read the `VERSION-HISTORY:` token, not `$?` alone. This step runs once per cycle per doc, so it
    is the most-repeated edit in the loop and the one that fails most quietly: a `.replace()` whose
    anchor has drifted writes nothing and reports success, and appending at the end of a
    newest-first section puts the entry in the wrong place with no observable error. The helper
    refuses both, plus a re-run of the same version and the table-shaped sections it must not
    reformat. A `REFUSED` is a real stop — fix the doc or the arguments; never fall back to editing
    the section by hand, which is the failure this replaces.
    The gate emits a `[H-MAD] <feature> gate <verdict>` marker line. Nits never block. If the `GATE:` token is absent from stdout (unexpected), treat it as an operational error and halt `step<N>:gate_token_missing` with a `[H-MAD]` marker — never silently treat a missing token as PASS.

**Between revising and re-auditing, sweep the corrected VALUE.** After applying an audit fix,
`grep` the corrected value — not the section, the value — across every live doc in the feature. The
same claim is usually restated in two or three places and the fix lands in one. Roughly two-thirds
of one session's 79 findings were this single class, and four stale copies survived **two
independent reviewers**: a spec FR's description contradicting its own AC, a plan risk row still
asserting a disproven `exec` behaviour, a design cross-reference to a deleted plan clause, and an AC
counter that went stale twice. A sweep has five surfaces — prose, code blocks, comments, ACs, and
the PAIRED design — and numeral forms count. Closing a class in only one document of a pair
RELOCATES it rather than fixing it.

