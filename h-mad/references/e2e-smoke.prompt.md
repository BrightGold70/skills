# H-MAD dispatch-surface live-e2e smoke

You are a scheduled health check for the `hmad-dispatch` Orca transport in the
`BrightGold70/skills` repo. Run the smoke below **non-interactively** in the repo
root and report a single PASS/FAIL verdict. Do not modify any tracked file. This
is a self-test of the dispatch surface itself — no feature work.

Put the wrapper on PATH first:

```bash
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
```

## Checks (all must pass)

1. **Substrate + orchestration + identity** — `hmad-dispatch env` must print
   `substrate: orca`, `orchestration: on`, and resolve BOTH agents (neither line
   is `-> UNRESOLVED`). A pinned `HMAD_ORCA_CODEX_TERMINAL` / `HMAD_ORCA_AGY_TERMINAL`
   is acceptable and expected (preview auto-detect decays — see monitoring H4).
2. **Single-agent resolve** — `hmad-dispatch resolve agy` and
   `hmad-dispatch resolve codex` each print a non-empty handle and exit 0;
   `hmad-dispatch resolve bogus` exits 2 with `unknown agent` on stderr.
3. **Report-file round-trip** — stage `RP=/tmp/hmad_e2e_smoke.report.md`; remove
   `$RP` and `$RP.done`; write a one-line report to `$RP`, then `: > "$RP.done"`;
   `hmad-dispatch report-wait "$RP" --timeout 30` must echo that line and exit 0.
4. **Suite** — `python3 -m pytest handoff/scripts/test_handoff_paths.py h-mad/tests/ -q`
   reports all-passing, zero failures.

## Report

Emit exactly one final line: `E2E: PASS` if every check passed, else
`E2E: FAIL — <first failing check + observed output>`. If a report-file path is
provided to you by the automation runner, write your full check log there and
create the `.done` marker; otherwise print the log to the terminal.
