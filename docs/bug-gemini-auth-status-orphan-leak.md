# Bug: `gemini auth status` relaunch children orphan and never exit (~7 GB retained)

**Component:** `gemini-cli` 0.46.0 (Homebrew) — self-relaunch path in `packages/cli/index.ts`
**Type:** Bug (resource leak — orphaned processes retained indefinitely)
**Environment:** macOS 26.5.0 (Darwin 25.5.0) · gemini-cli 0.46.0 · node 26.5.0 (Homebrew)
**Status:** Evidence captured; **caller UNIDENTIFIED** (see §"What is not established")
**Discovered:** 2026-08-06, incidentally, while repairing stale h-mad agent pane pins

## Summary

64 orphaned processes of the form

```
/opt/homebrew/Cellar/node/26.5.0/bin/node --max-old-space-size=98304 /opt/homebrew/bin/gemini auth status
```

were found alive on the machine, **all with PPID 1**, all in state `S`, aged ~7d19h–7d20h, holding
**7,313,664 KB RSS (~6.97 GB)** in aggregate (~115 MB each). They were spawned inside a
**~15.5-minute window** and had survived for **7 days 20 hours** at the moment of discovery.

`gemini`'s launcher re-executes itself as a child with an enlarged V8 heap
(`--max-old-space-size=98304`) via `getSpawnConfig` / `RELAUNCH_EXIT_CODE` in `packages/cli/index.ts`.
The leaked processes are those **relaunch children**. The PPID of 1 shows the parent `gemini`
exited normally while the relaunch child it spawned did not, leaving each child reparented to
`launchd` with no supervisor and no reaper.

The severity is not the invocation count — it is that each orphan is a ~115 MB idle node process
that persists **indefinitely**. Nothing reaps them; they survived a week and would have survived
until reboot.

## Evidence

Measured before cleanup:

| Property | Value |
|---|---|
| Count | 64 |
| PPID | `1` for all 64 (asserted per-PID, not sampled) |
| State | `S` (sleeping) — no zombies |
| RSS total | 7,313,664 KB ≈ **6.97 GB** |
| RSS each | ~84–150 MB |
| Age at discovery | oldest `07-20:05:11`, newest `07-19:49:46` |
| Spawn window | ~15.5 min → **2026-07-29 ~13:21–13:37 KST** |
| Spawn cadence | ~1 per 13–14 s |
| Open sockets | none (`lsof` showed no IPv4/IPv6/TCP) |
| Open fds | 45 each |

All 64 terminated on **SIGTERM**; no `SIGKILL` was required. Post-cleanup the pattern matched zero
processes system-wide, and `free+inactive` memory read 23.10 GB.

## Repro

**Not reproducible on this machine as of 2026-08-06.** A single control invocation was run:

```bash
count_orphans() { ps -eo pid,command | grep -F 'bin/gemini auth status' | grep -v grep | wc -l; }
count_orphans                                  # 0
/opt/homebrew/bin/gemini auth status &         # parent exited after ~9s
count_orphans                                  # 0  — no orphan produced
```

The command now exits cleanly in ~9 s and leaks nothing, because it **fails fast** before reaching
the code path that hangs:

```
Error authenticating: IneligibleTierError: This client is no longer supported for Gemini Code
Assist for individuals. To continue using Gemini, please migrate to the Antigravity suite of
products: https://antigravity.google
  reasonCode: 'UNSUPPORTED_CLIENT'
  tierId: 'free-tier'
```

This control is what makes the report honest: the leak is **condition-dependent**, not a property
of `auth status` in general. On 2026-07-29 the account was presumably still tier-eligible, so
`auth status` proceeded into real authentication work and the relaunch child blocked there forever.
The current `IneligibleTierError` short-circuits that path and masks the bug.

**Consequence for verification:** this cannot be re-tested from this machine while the account
remains `UNSUPPORTED_CLIENT`. A repro needs a tier-eligible account, or a forced stall in the
post-auth path.

## Suspected mechanism

The relaunch child appears to block indefinitely in the authentication path with no timeout and no
parent supervision:

1. `gemini auth status` starts; the launcher decides a larger heap is required.
2. It spawns `node --max-old-space-size=98304 …/gemini auth status` and exits with
   `RELAUNCH_EXIT_CODE`.
3. The child reparents to PID 1 the moment the parent exits — **by design**, so nothing is watching it.
4. The child enters authentication, blocks (network wait / OAuth / unresolved promise) and never
   reaches an exit.

Two independent defects compose here, and either alone would have contained the damage:

- **No timeout** on whatever the child waits for in the auth path.
- **No supervision** of the relaunch child, so a hung child is invisible and unreaped.

The absence of open sockets on the orphans is consistent with a connection that completed or was
torn down while a promise/await was never settled — i.e. a hang *after* the network activity, not a
process stuck in a live network read. That is an inference from the `lsof` snapshot taken 7 days
after the fact, not a proven cause.

## What is *not* established

Stated explicitly, because the surrounding facts invite a stronger conclusion than the evidence
supports:

- **The caller is unidentified.** Something invoked `gemini auth status` ~64 times in ~15.5 minutes
  (~1 per 13 s). That cadence is consistent with a retry or poll loop, but no caller was found.
  Ruled out by direct inspection:

  | Candidate | Result |
  |---|---|
  | `launchd` agents/daemons | only `com.antigravity.workflows_sync`, which runs `sync_workflows.sh` — an `rsync`-only script that never calls `gemini` |
  | `h-mad` / `hmad-dispatch.sh` | launches `agy --dangerously-skip-permissions`; never invokes `gemini auth status` |
  | `agy` binary (`~/.local/bin/agy`) | `strings` finds no `gemini auth`/`auth status` |
  | Orca app bundle | no match in `Contents/Resources` (js/mjs/cjs/json/sh) |
  | `~/.omc`, `~/.cmux`, `~/.gemini` configs | no match (`~/.gemini` hits are `gh auth status` in unrelated SKILL.md docs) |
  | `antigravity-cli` logs | log gap 11:57 → 14:31 on 2026-07-29 — **not running** during the burst |
  | `~/.zsh_history` (7231 timestamped entries, 2022-11-28 → 2026-08-03) | **zero** entries in the 2026-07-29 12:00–15:00 window |
  | macOS unified log | retention begins 2026-08-05; does not reach 2026-07-29 |

- **The process table evidence is gone.** The 64 orphans were killed during cleanup before the
  caller hunt began, so their environment, cwd, and open-fd detail can no longer be inspected. This
  is the single biggest reason the caller could not be attributed, and it was avoidable.

- **Whether a caller-side loop is itself defective is unproven.** 64 invocations is plausibly
  *correct* behaviour of a poller that had no reason to expect the callee to hang. The demonstrated
  defect is that the callee never exits.

## Recommended fixes

Upstream (`google-gemini/gemini-cli`), in priority order:

1. **Bound the auth path with a timeout.** Any wait in `auth status` should fail with a non-zero
   exit rather than block forever. A status probe in particular must be guaranteed-terminating.
2. **Do not orphan the relaunch child silently.** Either have the parent wait and propagate the
   child's exit code, or install a watchdog that kills a relaunch child exceeding a deadline.
3. **Consider a lower heap for non-interactive subcommands.** `--max-old-space-size=98304` (96 GB)
   for a status probe is what turns a hung process into a ~115 MB resident cost.

## Local detection (so the next occurrence is attributable)

The evidence needed to name the caller must be captured **before** cleanup:

```bash
# enumerate first, WITH parent/env/cwd, and only then kill
for p in $(pgrep -f 'bin/gemini auth status'); do
  ps -p "$p" -o pid,ppid,lstart,etime,rss,command
  ps -eo pid,ppid,command | awk -v p="$p" '$1==p {print "parent:", $2}'
  lsof -p "$p" 2>/dev/null | awk '$4=="cwd"'
done
```

A periodic check is cheap and worth adding to whatever health-checks this machine already runs:

```bash
N=$(pgrep -f 'bin/gemini auth status' | wc -l); [ "$N" -gt 2 ] && echo "WARN: $N orphaned gemini auth status"
```

## Cleanup performed 2026-08-06

64 PIDs were captured to a list, each asserted to match the exact command suffix
`bin/gemini auth status` **and** to have PPID 1, then sent SIGTERM by explicit PID (not by live
`pkill -f` pattern, which would race a concurrently spawning process). All 64 exited on SIGTERM.

The machine's interactive Gemini CLI — the `agy` pane pinned for h-mad dispatch — does **not**
appear as a `/opt/homebrew/bin/gemini` process and was never matched by the pattern. `hmad-dispatch
env` reported `PREFLIGHT: PASS` with the agy pin still resolving (`id: antigravity state=done`)
after the sweep, and all six Antigravity IDE MCP proxies survived.
