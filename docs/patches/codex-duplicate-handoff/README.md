# codex-duplicate-handoff

Keeps Codex offered exactly one `handoff` skill: this repo's (via `~/.agents/skills/handoff`).

Two things have given Codex a second one, and `verify.py` checks both:

1. **STALE** — Matt Pocock's plugin `handoff` is disabled by a config pin that goes stale on
   every plugin update (below).
2. **DUPLICATE** — a standalone skill named `handoff` in a Codex home. An Orca account carried
   one ("Handoff for Codex", a 4 KB plain copy in `<account>/home/skills/handoff`, dated
   2026-09-09), removed 2026-11-10. Its folder sat among `[OMX]` skills, so OMX setup probably
   installed it and would put it back.

Neither is a code patch; nothing in a plugin is modified. `patch-verify-on-update.sh` runs
`verify.py` like any other carried patch.

## The pin

Each Codex config that enables `mattpocock-skills@mattpocock` carries:

```toml
[[skills.config]]
path = "/Users/kimhawk/.codex/plugins/cache/mattpocock/mattpocock-skills/<version>/skills/productivity/handoff/SKILL.md"
enabled = false
```

It lives in **user-level** configs:

- `~/.codex/config.toml` (Codex started outside Orca)
- `~/Library/Application Support/orca/codex-accounts/<id>/home/config.toml` (Codex under Orca, where `CODEX_HOME` points)

Each config is judged against the plugin copies under its own Codex home
(`<config dir>/plugins/cache/...`). Today an Orca account's `home/plugins` is a symlink to
`~/.codex/plugins`, so both configs pin the same file; if an account ever gets a real
`plugins` directory, its config must pin that copy, and `verify.py` checks it that way.

**Not** in a project's `.codex/config.toml`. Codex ignores `skills.config` there. Measured
2026-11-10 on codex-cli 0.167.0: the same entry hid a skill when passed as `-c` and did
nothing from the trusted project's `.codex/config.toml`.

The skill sets `disable-model-invocation: true`, so it never appears in Codex's automatic
skill list either way. The pin is what stops an explicit `$mattpocock-skills:handoff` from
loading it. That is why `codex debug prompt-input` cannot show whether the pin works; check a
real `codex exec` session file for the skill body instead.

## Why it goes stale

The path contains the plugin version. A plugin update installs `<new-version>/` and removes
the old folder, so the entry stops matching anything and the skill loads again, with no error.

## The duplicate check

Scanned: the `skills/` folder of every Codex home (`~/.codex`, `$CODEX_HOME`, every
`~/Library/Application Support/orca/codex-accounts/<id>/home`) and `~/.agents/skills`, up to
two folders deep (`skills/<a>/SKILL.md` and `skills/<a>/<b>/SKILL.md`, so `.system/<x>` and
one vendor level, but not templates deep inside a skill), following symlinked folders. Every `SKILL.md`
whose frontmatter `name` is exactly `handoff` is a duplicate, whatever its folder is called,
unless its folder resolves to **this repo's** `handoff/` (the expected
`~/.agents/skills/handoff` link does; a link elsewhere does not). Other names containing
"handoff" (`ai-memory-handoff`, …) are not.

The top-level `name` is read with a line parser, not YAML; indented lines (nested keys,
block-scalar text) never count. It accepts the variants seen or plausible from
an installer: a BOM, CRLF, a quoted key, spaces around the colon, a trailing `# comment`,
quoted values, and a `>`/`|` block scalar. A flow mapping (`{name: handoff}`) is not read.
A skill folder that cannot be listed or read makes the check exit 2, never 0.

## When the hook warns

`[patch-verify] … codex-duplicate-handoff: patch MISSING or wrong`. Run:

```bash
python3 /Users/kimhawk/orca/skills/docs/patches/codex-duplicate-handoff/verify.py
```

- `PROBLEM <config>: no enabled=false entry for <path>` — run `verify.py --fix`. It repoints the
  stale `[[skills.config]]` entry's `path` to `<path>` (or appends the entry if there is none),
  touching nothing else in the file (line endings included), keeping its mode (the temp file is
  created at that mode), and leaving a `config.toml.bak-handoff-<timestamp>` beside it. It
  writes the resolved (`~/.codex/...`) path, which is what Codex under Orca matches. It refuses,
  says `NOT FIXED`, and writes nothing when:
  - the config is a symlink (fix the file it points to; the tool that manages it owns it);
  - the stale path appears more than once, or not on a plain `path = "…"` line (inline table);
  - an entry explicitly sets that handoff `enabled = true`;
  - the result would not parse;
  - Codex rewrote the config while it ran (re-run it). By hand: change the `path` of the stale entry to `<path>`.
- `PROBLEM duplicate handoff skill: <dir>` — back up and delete `<dir>`. If OMX setup put it
  back, it will again on its next run; this warning is how you find out.

Re-run `verify.py` until it prints `VERIFY: OK`.

Exit codes: `0` one handoff only, `1` stale/missing pin or a duplicate, `2` could not judge (no
config found, a config would not parse, a SKILL.md unreadable), which is not a pass.

## Retiring

Delete this directory, its `pytest.ini` `testpaths` entry, and `codex_fp` in
`docs/patches/patch-verify-on-update.sh` if no other patch needs it; then re-copy the hook.
Remove the `[[skills.config]]` entries from the configs above.
