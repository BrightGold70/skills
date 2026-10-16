# agy-coder-fallback — design audit cycle 2 decision sheet (orchestrator) — FINAL CORRECTIVE REVISION
Round cap (2) reached at design cycle 2. This revision is NOT re-audited (SKILL.md §"Document-audit round cap" rule 4): fix ONLY findings cycle 2 filed (plus the listed carried spec items); every fix mechanically checkable; no new scope. A new discovery is reported as owed / OPEN-DECISION for the impl-plan, not added.
Reports: docs/02-design/features/agy-coder-fallback.design.audit.v2.p1.md (codex), .v2.p2.md (agy). Audited design v1.1 @c8e4f24c, spec v1.7 @c117a695, plan v1.6 @8e242d06. All findings tagged build; orchestrator agrees. Note: p1's effort line reads tools=0 because the counter cannot parse codex-text logs; its findings cite executed controlled pairs.
Premise spot-checked: h_mad_assemble_tdd.py `ap.add_argument("--agent", choices=("codex", "grok"), default="codex")` present; assemble_tdd_agent.json row w10a-grok-by-default present. Authors verify every other premise; decline with evidence if one fails.

DESIGN (design-author):
E1 (codex+agy) FR-4 step 5 workspacePaths cross-check and class (c)'s CommandLine presence check must stand down unless phase5_status in {active, unknown} (spec FR-4/AC-4.1). Close the class: audit EVERY deny in FR-4 for its step5 gating.
E2 (codex) FR-7 recovery is lossy: store the complete set of successful implementation authors (not a projection), so recovery after lost dispatch context cannot mark a self-review independent. Fixture: authors [agy, codex], grok 5e-review, codex 5e-verify, agy 6a-prime → non-independent.
E3 (codex) AC-X T4 non-empty-string mutation fixture cannot bite because step 3 chdir(root) makes "" resolve to root → choose a fixture that observes the check (or drop/replace the row with one that bites).
E4 (codex) attribution phase: successful implementation = accepted 5e GREEN (+ subsequent accepted fixes), never a 5d RED dispatch.
E5 (agy) class (b) empty-string path: treat "" as an empty target list like the Codex gate (`[path] if path else []`) and deny under active/unknown; not canonicalise("").
E6 (agy) every deny carries `kind=<kind>`: assign a kind to T4, T5, and class (c) missing-command / shell-allowance / disallowed-command denies; correct the "unknown denies judge-error as the Codex gate does" claim against the Codex gate's actual kinds.
E7 (agy) existing mutation anchors broken by FR-5/FR-7 edits: assemble_tdd_agent.json w10a-grok-by-default (the --agent choices line) and heartbeat_beat.json rows → list each, with the re-anchor (same intent) in the stage that breaks it. Close the class: sweep every mutation spec for anchors on lines the design edits.
E8 (agy) property_valid for implementer_switch must guard isinstance(value, dict) (type ["object","null"]); align with _semantic_ok.

SPEC (spec-author) — carried + cycle-2:
S1 FR-4 deny shape: spec says every deny is `{"decision":"deny","reason":"<text> kind=<kind>"}` — name the kind set (mirror E6's final list from the design author's report if available; else state the rule: every deny path has a kind from a closed list the design enumerates).
S2 (carried from plan v1.6) AC for the FR-7 Attribution fixture (AC-7.x), incl. E2's multi-author case and E4's phase rule (accepted 5e GREEN + accepted fixes; never 5d RED).
S3 (carried) drop ", not 60" from the quoted leap-second ValueError text (Python-version dependent).
S4 (carried, advisory from design v1.1) FR-4 "same rules as the Codex gate": adopt or reject the design's 4 deliberate differences (design §FR-4) — record which, with reason.
S5 (carried, advisory) FR-7 "names that agent" when the reviewer is none of the authors: the design names the author of the latest successful dispatch — adopt or state otherwise.
