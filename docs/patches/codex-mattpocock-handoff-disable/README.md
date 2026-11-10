# codex-mattpocock-handoff-disable

Keeps Codex from loading Matt Pocock's `handoff` skill next to this repo's `handoff`.

This is a **config pin**, not a code patch. Nothing in the plugin is modified. `verify.py`
checks that the pin still points at the installed copy, and `patch-verify-on-update.sh` runs
it like any other carried patch.

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

## When the hook warns

`[patch-verify] … codex-mattpocock-handoff-disable: patch MISSING or wrong` means a config's
pin is missing or names a version that is no longer installed. Run:

```bash
python3 /Users/kimhawk/orca/skills/docs/patches/codex-mattpocock-handoff-disable/verify.py
```

Each `PROBLEM <config>:` line names the config and the installed path it needs. In that
config, change the `path` of the stale `[[skills.config]]` entry to that path (or add the
entry if none exists). Re-run `verify.py` until it prints `VERIFY: OK`.

Exit codes: `0` pinned everywhere (or nothing to pin), `1` missing/stale, `2` could not judge
(no config found, or a config would not parse), which is not a pass.

## Retiring

Delete this directory, its `pytest.ini` `testpaths` entry, and `codex_fp` in
`docs/patches/patch-verify-on-update.sh` if no other patch needs it; then re-copy the hook.
Remove the `[[skills.config]]` entries from the configs above.
