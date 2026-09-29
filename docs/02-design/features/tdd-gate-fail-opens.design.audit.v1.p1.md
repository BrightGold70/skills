AUDIT-tdd-gate-fail-opens-design-v1-BEGIN
## Summary
The design covers the feature's main paths, but its leaf-symlink algorithm and Claude wire format leave path-identity gaps, and several required negative controls are not planned. The comparator's normal FAIL exit also conflicts with the supplied audit-gate signal invariant. Evidence: 7 files opened, 5 greps run, 4 graft calls.

| Spec AC | Classification |
|---|---|
| AC-1.1 | implemented-as-written |
| AC-1.2 | implemented-as-written |
| AC-1.3 | implemented-as-written |
| AC-1.4 | implemented-as-written |
| AC-1.5 | implemented-as-written |
| AC-1.6 | implemented-as-written |
| AC-1.7 | restated |
| AC-1.8 | implemented-as-written |
| AC-1.9 | implemented-as-written |
| AC-1.10 | implemented-as-written |
| AC-1.11 | implemented-as-written |
| AC-2.1 | implemented-as-written |
| AC-2.2 | implemented-as-written |
| AC-2.3 | implemented-as-written |
| AC-2.4 | implemented-as-written |
| AC-2.5 | implemented-as-written |
| AC-3.1 | implemented-as-written |
| AC-3.2 | implemented-as-written |
| AC-3.3 | implemented-as-written |
| AC-3.4 | restated |
| AC-3.5 | implemented-as-written |
| AC-3.6 | implemented-as-written |
| AC-4.1 | implemented-as-written |
| AC-4.2 | implemented-as-written |
| AC-4.3 | implemented-as-written |
| AC-4.4 | implemented-as-written |
| AC-4.5 | implemented-as-written |
| AC-4.6 | implemented-as-written |
| AC-4.7 | implemented-as-written |
| AC-5.1 | implemented-as-written |
| AC-5.2 | implemented-as-written |
| AC-5.3 | restated |
| AC-5.4 | implemented-as-written |
| AC-5.5 | implemented-as-written |
| AC-6.1 | restated |
| AC-6.2 | absent |
| AC-6.3 | implemented-as-written |
| AC-7.1 | implemented-as-written |
| AC-8.1 | implemented-as-written |
| AC-8.2 | implemented-as-written |
| AC-8.3 | implemented-as-written |
| AC-8.4 | implemented-as-written |
| AC-8.5 | implemented-as-written |
| AC-8.6 | implemented-as-written |

## Must-fix
- Specify how a leaf symlink is followed to its referent's canonical parent before scanning names, and exclude symlink entries from the hard-link set — the stated operations open the deepest directory and never the leaf, so a scan of `src/` for `src/link.py -> ../tests/t.py` cannot produce the referent's `tests/t.py` name; following `DirEntry.stat()` would also mistake a symlink sibling for a hard link. This can fail the required leaf-symlink ALLOW and AC-1.9.
  class: build
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › `A leaf symlink is followed (every symlink on the walk is followed).`
- Define a byte-preserving Claude record decode and prove a filename ending in newline round-trips — `_pct_decode` prints raw bytes, while ordinary Bash command substitution strips trailing newlines (confirmed with `v=$(printf "a\\n")`, which yielded `a`). The claimed any-byte name transport otherwise changes identity and can turn a production alias into an exemption.
  class: build
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › `The decoder is this one function.`
- Use filesystem encoding with surrogate escape for F_GETPATH and percent encoding — a POSIX directory entry can contain non-UTF-8 bytes, but the design says only “decodes” and promises every non-NUL byte. A default UTF-8 decode or encode raises before the governed-only arm can be returned, making the wire contract false.
  class: build
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › `Percent-encoding carries every directory-entry byte except NUL.`
- Make `compare_readings.py` emit a FAIL token with exit 0 for a valid comparison that finds an unapproved softening — the supplied base invariant requires normal check verdicts on stdout with exit 0; non-zero is reserved for operational errors. Keep non-zero for unreadable or invalid inputs.
  class: build
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › `The comparator exits non-zero when a key`
- AC-1.7 is restated as a direct canonicaliser unit call and omits the required run with `os.path.realpath` substituted — without that negative control the test's discrimination against a spelling-preserving resolver is unobserved.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.spec.md › `same test fails (the negative control is run, not asserted).`
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › `| Canonicaliser unit: walk, F_GETPATH, inode match, lexical remainder | direct call | 1.7, 1.10 |`
- AC-3.4 is restated as generic loop coverage and omits the direct resolver assertion paired with a run showing `os.path.realpath` returns without error — the spec requires that controlled pair to distinguish the FR-3 predicate from a realpath-only implementation.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.spec.md › `with a negative control that \`os.path.realpath\` of the same path returns without error.`
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › ``| Dangling, loop, and mode-`0311` open or list failure, governed | allow on the unfixed tree for AC-3.6 (a); deny `no-test-resolved` for (b) | 3.1–3.6 |``
- AC-5.3 is restated as one generic reap scenario; specify separate timed `judge()` tests for a detaching name-map script and a detaching fake venv interpreter — a test of `_run_bounded` alone cannot prove both judge mappings or the per-path bound.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.spec.md › `and separately with a fake`
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › ``| Reap past `REAP_GRACE_S` | `judge-timeout` within 4.0 s; plain timeout stays `timeout` | 5.1–5.5 |``
- AC-6.1 is restated as a new differential test without the required unfixed-tree run and its exact two failure sets — a fixed-tree green result does not prove that the published M-cell disagreements and expectation failures are discriminating.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.spec.md › `assertion fails on exactly M-4, M-5, M-6, M-7, M-8, M-11 and M-12`
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › `| Differential over the FR-6 domain | new test | 6.1–6.3 |`
- AC-6.2 is absent: run the differential once with FR-1 removed from Claude and once with it removed from Codex — the design's generic T8 guard mutations do not commit to this two-sided differential check.
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.spec.md › `removing FR-1 from either gate alone makes the differential fail (run once per gate).`
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › `| Differential over the FR-6 domain | new test | 6.1–6.3 |`
- Test each new connection in both directions, including forced unconditional invocation with a negative case — the design explicitly plans only removal-of-call tests for the Claude import and Codex fold, while the supplied Connection enforcement invariant requires both removal and unconditional-fire controls.
  class: build
  quote: docs/02-design/features/tdd-gate-fail-opens.design.md › `A connection test fails when the call is removed and the callee remains`

## Should-fix
None

## Nit
None
AUDIT-tdd-gate-fail-opens-design-v1-END
