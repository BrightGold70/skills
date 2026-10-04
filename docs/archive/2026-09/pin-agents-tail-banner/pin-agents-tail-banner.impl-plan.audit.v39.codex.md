AUDIT-pin-agents-tail-banner-impl-plan-v39-BEGIN
## Summary
I audited the supplied v1.37 target bytes and re-derived 45 test nodes (32 RED failures, 13 RED passes), 38 mutations, and the 290-test baseline. Two hard plan defects remain: Task 3's two connections collapse into one registry record, and the mutation code block omits mechanism metadata that its own ACs require.

## Must-fix
- Task 3 repeats bare `WIRE` / `WIRE-PIN` labels for two connections instead of numbering the pairs — the actual gate parses both with suffix `None`, pairs both wires with the last pin, and registers both under identity `(pin-agents-tail-banner, Task 3)`, so the `_agent_tail_re` record upserts `_orca_tail_sig` and the latter is registered with the wrong pin before disappearing. Use matched numbered labels (`WIRE 1` / `WIRE-PIN 1`, `WIRE 2` / `WIRE-PIN 2`); otherwise the declared `_orca_find -> _orca_tail_sig` connection is absent from the registry, breaching Connection enforcement.
- The embedded mutation spec has `_mechanism` on only 20 of 38 entries; all nine mutations singled out by AC-6.12–AC-6.20 are among the 18 omissions — those ACs require each discriminator's mechanism line to name the node and explain the intended kill, so the prescribed JSON does not implement its own acceptance contract and leaves accidental/equivalent kills undocumented.

## Should-fix
- Add the tail pass to the existing `_orca_find` comment that says Codex “relies on the preview signature or … a pin/launch” — after this feature, retained tail evidence is precisely the recovery path when the preview decays, so T5 should update and pin this third documentation site.
- AC-3.17 says none of the 24 probes matches “the anchored one,” but the same AC later reports that the anchor-only revision declines only 7/24 — replace “anchored one” with “current bounded banner grammar” so the prose agrees with the normative `_agent_tail_re` block.

## Nit
- AC-4.6 has a stray closing `**` after “both directions,” producing broken emphasis.
AUDIT-pin-agents-tail-banner-impl-plan-v39-END
