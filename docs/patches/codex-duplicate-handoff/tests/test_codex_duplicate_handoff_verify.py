"""verify.py must flag anything that gives Codex a second `handoff` skill.

Two ways: a Matt Pocock handoff disable that no longer names the installed copy, and a
standalone `handoff` skill reappearing in a Codex home (the Orca account copy, removed
2026-11-10, was probably installed by OMX setup and can come back).

Every test builds a fake HOME under tmp_path (a Codex plugin cache, ~/.codex/config.toml and an
Orca codex-account config) and runs verify.py with HOME pointed at it, so nothing here reads the
host's real Codex configs or plugin cache. The hook tests run the real SessionStart hook the same
way, to pin that a Codex plugin update re-triggers the check at all.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

PATCH_DIR = Path(__file__).resolve().parents[1]
VERIFY = PATCH_DIR / "verify.py"
HOOK = PATCH_DIR.parent / "patch-verify-on-update.sh"
REL = "skills/productivity/handoff/SKILL.md"
ORCA = "Library/Application Support/orca/codex-accounts/acct-1/home/config.toml"


def plugin(home: Path, version: str, handoff: bool = True) -> Path:
    vdir = home / ".codex/plugins/cache/mattpocock/mattpocock-skills" / version
    (vdir / "skills/engineering/tdd").mkdir(parents=True, exist_ok=True)
    (vdir / "skills/engineering/tdd/SKILL.md").write_text("---\nname: tdd\n---\n")
    path = vdir / REL
    if handoff:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("---\nname: handoff\ndisable-model-invocation: true\n---\n")
    return path


def config(path: Path, *disabled: str, plugin_enabled: bool = True, extra: str = "") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = '[plugins."mattpocock-skills@mattpocock"]\nenabled = %s\n' % str(plugin_enabled).lower()
    for p in disabled:
        body += '\n[[skills.config]]\npath = "%s"\nenabled = false\n' % p
    path.write_text(body + extra)
    return path


def link_plugins(codex_home: Path, home: Path) -> None:
    """Real Orca layout: an account's home/plugins is a symlink to ~/.codex/plugins."""
    codex_home.mkdir(parents=True, exist_ok=True)
    (home / ".codex/plugins").mkdir(parents=True, exist_ok=True)
    (codex_home / "plugins").symlink_to(home / ".codex/plugins")


def run(home: Path, extra_env: dict | None = None):
    env = {k: v for k, v in os.environ.items() if k not in ("CODEX_HOME", "HANDOFF_REPO_DIR")}
    env["HOME"] = str(home)
    env.update(extra_env or {})
    out = subprocess.run([sys.executable, str(VERIFY)], capture_output=True, text=True, env=env, timeout=30)
    return out.returncode, out.stdout + out.stderr


def test_current_disable_in_every_config_passes(tmp_path):
    hp = plugin(tmp_path, "1.3.2")
    config(tmp_path / ".codex/config.toml", str(hp))
    link_plugins((tmp_path / ORCA).parent, tmp_path)
    config(tmp_path / ORCA, str(hp))
    rc, out = run(tmp_path)
    assert rc == 0, out
    assert "VERIFY: OK 2 Codex config(s)" in out


def test_plugin_update_leaves_disable_stale(tmp_path):
    old = tmp_path / ".codex/plugins/cache/mattpocock/mattpocock-skills/1.3.2" / REL
    new = plugin(tmp_path, "1.3.3")
    config(tmp_path / ".codex/config.toml", str(old))
    rc, out = run(tmp_path)
    assert rc == 1, out
    assert str(new) in out          # names the path to repoint to
    assert "1.3.2" in out and "stale" in out.lower()
    assert out.strip().splitlines()[-1].startswith("VERIFY: STALE")


def test_orca_config_alone_stale_is_caught(tmp_path):
    hp = plugin(tmp_path, "1.3.3")
    config(tmp_path / ".codex/config.toml", str(hp))
    link_plugins((tmp_path / ORCA).parent, tmp_path)
    config(tmp_path / ORCA, str(hp).replace("1.3.3", "1.3.2"))
    rc, out = run(tmp_path)
    assert rc == 1, out
    problems = [l for l in out.splitlines() if l.startswith("PROBLEM ")]
    assert len(problems) == 1 and "acct-1" in problems[0], out


def test_codex_home_config_is_checked(tmp_path):
    hp = plugin(tmp_path, "1.3.2")
    config(tmp_path / ".codex/config.toml", str(hp))
    link_plugins(tmp_path / "elsewhere", tmp_path)
    other = config(tmp_path / "elsewhere/config.toml")   # plugin enabled, no disable
    env = {**os.environ, "HOME": str(tmp_path), "CODEX_HOME": str(other.parent)}
    out = subprocess.run([sys.executable, str(VERIFY)], capture_output=True, text=True, env=env, timeout=30)
    assert out.returncode == 1, out.stdout
    assert "elsewhere" in out.stdout


def test_orca_account_with_its_own_plugin_copy_is_judged_against_it(tmp_path):
    hp = plugin(tmp_path, "1.3.2")
    config(tmp_path / ".codex/config.toml", str(hp))
    acct = (tmp_path / ORCA).parent
    own = acct / "plugins/cache/mattpocock/mattpocock-skills/1.3.3" / REL   # a real dir, not a link
    own.parent.mkdir(parents=True)
    own.write_text("---\nname: handoff\n---\n")
    config(tmp_path / ORCA, str(hp))                       # pins ~/.codex's 1.3.2, not its own 1.3.3
    rc, out = run(tmp_path)
    assert rc == 1, out
    assert str(own) in out


def test_config_without_a_local_plugin_copy_needs_nothing(tmp_path):
    hp = plugin(tmp_path, "1.3.2")
    config(tmp_path / ".codex/config.toml", str(hp))
    config(tmp_path / ORCA)                                # enables the plugin, but has no plugins dir
    rc, out = run(tmp_path)
    assert rc == 0, out


def test_odd_table_shapes_do_not_crash(tmp_path):
    plugin(tmp_path, "1.3.2")
    p = tmp_path / ".codex/config.toml"
    p.write_text('[plugins."mattpocock-skills@mattpocock"]\nenabled = true\n[skills]\nconfig = "x"\n')
    rc, out = run(tmp_path)
    assert rc == 1, out                                    # no usable entry is a missing pin, not a crash
    assert "Traceback" not in out


def test_missing_disable_entry_fails(tmp_path):
    plugin(tmp_path, "1.3.2")
    config(tmp_path / ".codex/config.toml")
    rc, out = run(tmp_path)
    assert rc == 1, out


def test_enabled_true_entry_does_not_count(tmp_path):
    hp = plugin(tmp_path, "1.3.2")
    p = tmp_path / ".codex/config.toml"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text('[plugins."mattpocock-skills@mattpocock"]\nenabled = true\n\n'
                 '[[skills.config]]\npath = "%s"\nenabled = true\n' % hp)
    rc, out = run(tmp_path)
    assert rc == 1, out


def test_every_installed_version_needs_a_disable(tmp_path):
    a = plugin(tmp_path, "1.3.2")
    plugin(tmp_path, "1.3.3")
    config(tmp_path / ".codex/config.toml", str(a))
    rc, out = run(tmp_path)
    assert rc == 1, out
    assert "1.3.3" in out


def test_plugin_disabled_in_config_needs_nothing(tmp_path):
    plugin(tmp_path, "1.3.2")
    config(tmp_path / ".codex/config.toml", plugin_enabled=False)
    rc, out = run(tmp_path)
    assert rc == 0, out


def test_plugin_not_installed_passes(tmp_path):
    config(tmp_path / ".codex/config.toml")
    rc, out = run(tmp_path)
    assert rc == 0, out


def test_plugin_without_handoff_passes(tmp_path):
    plugin(tmp_path, "1.4.0", handoff=False)
    config(tmp_path / ".codex/config.toml")
    rc, out = run(tmp_path)
    assert rc == 0, out


def test_unparseable_config_cannot_judge(tmp_path):
    plugin(tmp_path, "1.3.2")
    p = tmp_path / ".codex/config.toml"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("[plugins\nnot toml")
    rc, out = run(tmp_path)
    assert rc == 2, out


def test_no_codex_config_cannot_judge(tmp_path):
    plugin(tmp_path, "1.3.2")
    rc, out = run(tmp_path)
    assert rc == 2, out


# --- a standalone `handoff` skill in a Codex home --------------------------------------------

def skill(dirpath: Path, name: str) -> Path:
    dirpath.mkdir(parents=True, exist_ok=True)
    (dirpath / "SKILL.md").write_text(f"---\nname: {name}\ndescription: x\n---\n# body\n")
    return dirpath / "SKILL.md"


def pinned_home(tmp_path: Path) -> Path:
    """A passing baseline: the plugin installed and pinned in ~/.codex and the Orca account."""
    hp = plugin(tmp_path, "1.3.2")
    config(tmp_path / ".codex/config.toml", str(hp))
    link_plugins((tmp_path / ORCA).parent, tmp_path)
    config(tmp_path / ORCA, str(hp))
    rc, out = run(tmp_path)
    assert rc == 0, out
    return hp


def test_orca_account_handoff_copy_reappearing_is_caught(tmp_path):
    pinned_home(tmp_path)
    copy = skill((tmp_path / ORCA).parent / "skills/handoff", "handoff")
    rc, out = run(tmp_path)
    assert rc == 1, out
    assert str(copy.parent) in out
    assert "DUPLICATE" in out.strip().splitlines()[-1]


def test_copy_under_another_folder_name_is_caught(tmp_path):
    pinned_home(tmp_path)
    copy = skill((tmp_path / ORCA).parent / "skills/handoff-codex", "handoff")
    rc, out = run(tmp_path)
    assert rc == 1, out
    assert str(copy.parent) in out


def test_quoted_name_is_caught(tmp_path):
    pinned_home(tmp_path)
    d = (tmp_path / ORCA).parent / "skills/hx"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text('---\nname: "handoff"\n---\n')
    rc, out = run(tmp_path)
    assert rc == 1, out


def test_home_codex_skills_copy_is_caught(tmp_path):
    pinned_home(tmp_path)
    skill(tmp_path / ".codex/skills/handoff", "handoff")
    rc, out = run(tmp_path)
    assert rc == 1, out


def test_system_skills_copy_is_caught(tmp_path):
    pinned_home(tmp_path)
    skill((tmp_path / ORCA).parent / "skills/.system/handoff", "handoff")
    rc, out = run(tmp_path)
    assert rc == 1, out


def repo_handoff(tmp_path: Path) -> tuple[Path, dict]:
    repo = tmp_path / "repo/handoff"
    skill(repo, "handoff")
    (tmp_path / ".agents/skills").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".agents/skills/handoff").symlink_to(repo)
    return repo, {"HANDOFF_REPO_DIR": str(repo)}


def test_link_to_the_repo_handoff_is_allowed(tmp_path):
    pinned_home(tmp_path)
    repo, env = repo_handoff(tmp_path)
    ((tmp_path / ORCA).parent / "skills").mkdir(parents=True)
    ((tmp_path / ORCA).parent / "skills/handoff").symlink_to(repo)
    rc, out = run(tmp_path, env)
    assert rc == 0, out


def test_only_the_repo_is_exempt_not_whatever_agents_points_at(tmp_path):
    pinned_home(tmp_path)
    _, env = repo_handoff(tmp_path)
    (tmp_path / ".agents/skills/handoff").unlink()
    copy = skill(tmp_path / ".agents/skills/handoff", "handoff")       # a real copy, not the repo
    (tmp_path / ".codex/skills").mkdir(parents=True)
    (tmp_path / ".codex/skills/handoff").symlink_to(copy.parent)
    rc, out = run(tmp_path, env)
    assert rc == 1, out
    problems = [l for l in out.splitlines() if l.startswith("PROBLEM duplicate")]
    assert len(problems) == 1, out                          # one copy, two roots: one report
    assert str(tmp_path / ".agents/skills/handoff") in problems[0]   # names the folder to delete


def test_second_handoff_in_agents_skills_is_caught(tmp_path):
    pinned_home(tmp_path)
    _, env = repo_handoff(tmp_path)
    skill(tmp_path / ".agents/skills/handoff-for-codex", "handoff")
    rc, out = run(tmp_path, env)
    assert rc == 1, out


def test_production_exemption_is_this_repos_handoff(tmp_path):
    pinned_home(tmp_path)
    real = Path(__file__).resolve().parents[4] / "handoff"
    if not (real / "SKILL.md").is_file():
        pytest.skip(f"{real} absent (a checkout without handoff/): the production exemption has nothing to name")
    (tmp_path / ".codex/skills").mkdir(parents=True)
    (tmp_path / ".codex/skills/handoff").symlink_to(real)               # no HANDOFF_REPO_DIR
    rc, out = run(tmp_path)
    assert rc == 0, out


import pytest  # noqa: E402


@pytest.mark.parametrize("front", [
    "\ufeff---\nname: handoff\n---\n",
    "---\nname: handoff # codex copy\n---\n",
    "---\nname: >-\n  handoff\n---\n",
    '---\n"name": handoff\n---\n',
    "---\nname : handoff\n---\n",
    "---\r\nname: handoff\r\n---\r\n",
    "---\nmetadata:\n  name: helper\nname: handoff\n---\n",          # nested key first
    "---\ndescription: |\n  name: notes\nname: handoff\n---\n",       # block text first
])
def test_frontmatter_variants_are_caught(tmp_path, front):
    pinned_home(tmp_path)
    d = tmp_path / ".codex/skills/x"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(front, encoding="utf-8", newline="")
    rc, out = run(tmp_path)
    assert rc == 1, (front, out)


def test_link_to_a_copy_outside_every_scanned_root_is_caught(tmp_path):
    pinned_home(tmp_path)
    copy = skill(tmp_path / "somewhere/else/handoff", "handoff")
    (tmp_path / ".codex/skills").mkdir(parents=True)
    (tmp_path / ".codex/skills/handoff").symlink_to(copy.parent)
    rc, out = run(tmp_path)
    assert rc == 1, out


def test_nested_name_key_alone_is_not_a_handoff(tmp_path):
    pinned_home(tmp_path)
    d = tmp_path / ".codex/skills/x"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text("---\nmetadata:\n  name: handoff\ndescription: x\n---\n")
    rc, out = run(tmp_path)
    assert rc == 0, out


def test_looped_folder_reports_a_copy_once(tmp_path):
    pinned_home(tmp_path)
    copy = skill(tmp_path / ".codex/skills/vendor/handoff", "handoff")
    (tmp_path / ".codex/skills/alias").symlink_to(tmp_path / ".codex/skills/vendor")
    (tmp_path / ".codex/skills/vendor/up").symlink_to(tmp_path / ".codex/skills/vendor")
    rc, out = run(tmp_path)
    assert rc == 1, out
    assert len([l for l in out.splitlines() if l.startswith("PROBLEM duplicate")]) == 1, out


def test_copy_first_reached_through_a_deep_link_is_still_caught(tmp_path):
    pinned_home(tmp_path)
    copy = skill(tmp_path / ".codex/skills/zzz/handoff", "handoff")
    (tmp_path / ".codex/skills/aaa").mkdir(parents=True)
    (tmp_path / ".codex/skills/aaa/vendor").symlink_to(tmp_path / ".codex/skills/zzz")   # walked first
    rc, out = run(tmp_path)
    assert rc == 1, out
    assert len([l for l in out.splitlines() if l.startswith("PROBLEM duplicate")]) == 1, out


def test_template_deep_inside_a_skill_is_not_scanned(tmp_path):
    pinned_home(tmp_path)
    skill(tmp_path / ".codex/skills/.system/skill-creator/assets/example", "handoff")
    rc, out = run(tmp_path)
    assert rc == 0, out


def test_nested_copy_is_caught(tmp_path):
    pinned_home(tmp_path)
    skill(tmp_path / ".codex/skills/vendor/handoff", "handoff")
    rc, out = run(tmp_path)
    assert rc == 1, out


def test_duplicate_wins_over_missing_config(tmp_path):
    skill(tmp_path / ".codex/skills/handoff", "handoff")             # no config.toml anywhere
    rc, out = run(tmp_path)
    assert rc == 1, out
    assert "DUPLICATE" in out.strip().splitlines()[-1]


def test_unlistable_skill_dir_cannot_judge(tmp_path):
    pinned_home(tmp_path)
    d = tmp_path / ".codex/skills/locked"
    skill(d, "notes")
    d.chmod(0)
    try:
        rc, out = run(tmp_path)
    finally:
        d.chmod(0o755)
    assert rc == 2, out
    assert "config(s)" not in out.strip().splitlines()[-1]


def test_other_handoff_named_skills_are_fine(tmp_path):
    pinned_home(tmp_path)
    skill((tmp_path / ORCA).parent / "skills/ai-memory-handoff", "ai-memory-handoff")
    skill(tmp_path / ".codex/skills/notes", "handoffs")
    rc, out = run(tmp_path)
    assert rc == 0, out


def test_copy_is_caught_even_when_the_plugin_is_not_installed(tmp_path):
    config(tmp_path / ".codex/config.toml")
    skill(tmp_path / ".codex/skills/handoff", "handoff")
    rc, out = run(tmp_path)
    assert rc == 1, out


def test_stale_pin_and_copy_both_reported(tmp_path):
    new = plugin(tmp_path, "1.3.3")
    config(tmp_path / ".codex/config.toml", str(new).replace("1.3.3", "1.3.2"))
    skill(tmp_path / ".codex/skills/handoff", "handoff")
    rc, out = run(tmp_path)
    assert rc == 1, out
    last = out.strip().splitlines()[-1]
    assert last.startswith("VERIFY: STALE") and "DUPLICATE" in last


# --- the SessionStart hook: a Codex plugin update must re-trigger the check -------------------

def hook(home: Path, patches: Path, extra_env: dict | None = None, stdin: str = ""):
    env = {k: v for k, v in os.environ.items() if k != "CODEX_HOME"}
    env.update(HOME=str(home), PATCH_VERIFY_DIR=str(patches), PATCH_VERIFY_NPM_ROOT=str(home / "npm"))
    env.update(extra_env or {})
    out = subprocess.run(["bash", str(HOOK)], input=stdin, capture_output=True, text=True, env=env, timeout=60)
    assert out.returncode == 0, out.stderr
    return out.stdout.strip()


def test_hook_rechecks_after_codex_plugin_update(tmp_path):
    patches = tmp_path / "patches"
    shutil.copytree(PATCH_DIR, patches / PATCH_DIR.name, ignore=shutil.ignore_patterns("tests", "__pycache__"))
    hp = plugin(tmp_path, "1.3.2")
    config(tmp_path / ".codex/config.toml", str(hp))
    assert hook(tmp_path, patches) == ""                     # passes, records OK state
    assert (tmp_path / ".claude/state/patch-verify.state").read_text().splitlines()[1] == "OK"

    shutil.rmtree(hp.parents[3])                             # the update replaces 1.3.2 ...
    plugin(tmp_path, "1.3.3")                                # ... with 1.3.3
    out = hook(tmp_path, patches)
    assert out, "hook stayed silent: its fingerprint does not see Codex plugin versions"
    msg = json.loads(out)["systemMessage"]
    assert PATCH_DIR.name in msg and "STALE" in msg


def fp(home: Path) -> str:
    return (home / ".claude/state/patch-verify.state").read_text().splitlines()[0]


def setup_hook(tmp_path):
    patches = tmp_path / "patches"
    shutil.copytree(PATCH_DIR, patches / PATCH_DIR.name, ignore=shutil.ignore_patterns("tests", "__pycache__"))
    hp = plugin(tmp_path, "1.3.2")
    link_plugins((tmp_path / ORCA).parent, tmp_path)
    return patches, hp, config(tmp_path / ".codex/config.toml", str(hp)), config(tmp_path / ORCA, str(hp))


def test_hook_rechecks_after_orca_config_edit(tmp_path):
    patches, hp, _, orca = setup_hook(tmp_path)
    assert hook(tmp_path, patches) == ""
    config(orca)                                             # pin dropped from the Orca config only
    out = hook(tmp_path, patches)
    assert out, "hook stayed silent: its fingerprint does not see the Orca account config"
    assert "STALE" in json.loads(out)["systemMessage"], out


def test_hook_rechecks_after_edit_in_outside_codex_home(tmp_path):
    patches, hp, _, _ = setup_hook(tmp_path)
    link_plugins(tmp_path / "elsewhere", tmp_path)
    other = config(tmp_path / "elsewhere/config.toml", str(hp))
    env = {"CODEX_HOME": str(other.parent)}
    assert hook(tmp_path, patches, env) == ""
    config(other)
    out = hook(tmp_path, patches, env)
    assert out and "STALE" in json.loads(out)["systemMessage"], out


def test_hook_fingerprint_ignores_codex_home_pointing_at_a_known_config(tmp_path):
    patches, *_ = setup_hook(tmp_path)
    acct = (tmp_path / ORCA).parent
    skill(acct / "skills/notes", "notes")                    # gives the skill-name lines content
    alias = tmp_path / "alias-home"
    alias.symlink_to(acct)                                   # CODEX_HOME spelled differently
    assert hook(tmp_path, patches) == ""
    before = fp(tmp_path)
    assert hook(tmp_path, patches, {"CODEX_HOME": str(alias)}) == ""
    assert fp(tmp_path) == before


def test_hook_fingerprint_ignores_unrelated_lines_above_the_pin(tmp_path):
    patches, _, home_cfg, _ = setup_hook(tmp_path)
    assert hook(tmp_path, patches) == ""
    before = fp(tmp_path)
    home_cfg.write_text('[projects."/new/trusted/dir"]\ntrust_level = "trusted"\n\n' + home_cfg.read_text())
    assert hook(tmp_path, patches) == ""
    assert fp(tmp_path) == before


def test_hook_rechecks_when_orca_handoff_copy_reappears(tmp_path):
    patches, *_ = setup_hook(tmp_path)
    assert hook(tmp_path, patches) == ""
    skill((tmp_path / ORCA).parent / "skills/handoff", "handoff")   # e.g. OMX setup re-runs
    out = hook(tmp_path, patches)
    assert out, "hook stayed silent: its fingerprint does not see Codex homes' skills"
    assert "DUPLICATE" in json.loads(out)["systemMessage"], out


def test_hook_rechecks_after_config_edit(tmp_path):
    patches = tmp_path / "patches"
    shutil.copytree(PATCH_DIR, patches / PATCH_DIR.name, ignore=shutil.ignore_patterns("tests", "__pycache__"))
    hp = plugin(tmp_path, "1.3.2")
    cfg = config(tmp_path / ".codex/config.toml", str(hp))
    assert hook(tmp_path, patches) == ""
    config(cfg)                                              # someone drops the disable entry
    out = hook(tmp_path, patches)
    assert out, "hook stayed silent: its fingerprint does not see the Codex configs"


# --- verify.py --fix: repoint (or add) the Matt Pocock pin -----------------------------------

import importlib.util  # noqa: E402
import stat  # noqa: E402
import tomllib  # noqa: E402


def fix(home: Path, *args: str):
    env = {k: v for k, v in os.environ.items() if k not in ("CODEX_HOME", "HANDOFF_REPO_DIR")}
    env["HOME"] = str(home)
    out = subprocess.run([sys.executable, str(VERIFY), "--fix", *args], capture_output=True, text=True,
                         env=env, timeout=30)
    return out.returncode, out.stdout + out.stderr


def backups(cfg: Path) -> list[Path]:
    return sorted(cfg.parent.glob(cfg.name + ".bak-handoff-*"))


def temps(cfg: Path) -> list[Path]:
    return sorted(cfg.parent.glob("." + cfg.name + ".handoff-fix-*"))


def stale_setup(tmp_path: Path, quote: str = '"'):
    old = str(tmp_path / ".codex/plugins/cache/mattpocock/mattpocock-skills/1.3.2" / REL)
    new = plugin(tmp_path, "1.3.3")
    cfg = tmp_path / ".codex/config.toml"
    cfg.write_text(
        "# my settings\nmodel = \"x\"\n\n"
        '[plugins."mattpocock-skills@mattpocock"]\nenabled = true\n\n'
        f"# keep the duplicate handoff off\n[[skills.config]]\npath = {quote}{old}{quote}\nenabled = false\n\n"
        '[projects."/a"]\ntrust_level = "trusted"\n')
    return cfg, old, new


def test_fix_repoints_a_stale_pin_and_nothing_else(tmp_path):
    cfg, old, new = stale_setup(tmp_path)
    before = cfg.read_text()
    rc, out = fix(tmp_path)
    assert rc == 0, out
    after = cfg.read_text()
    assert after == before.replace(old, str(new))           # only the path changed, comments kept
    assert backups(cfg) and backups(cfg)[0].read_text() == before
    assert "VERIFY: OK" in out.strip().splitlines()[-1]


def test_fix_handles_a_single_quoted_path(tmp_path):
    cfg, old, new = stale_setup(tmp_path, quote="'")
    rc, out = fix(tmp_path)
    assert rc == 0, out
    assert f"'{new}'" in cfg.read_text() and old not in cfg.read_text()


def test_fix_adds_a_pin_when_none_exists(tmp_path):
    new = plugin(tmp_path, "1.3.2")
    cfg = config(tmp_path / ".codex/config.toml", extra='\n[projects."/a"]\ntrust_level = "trusted"\n')
    before = cfg.read_text()
    rc, out = fix(tmp_path)
    assert rc == 0, out
    after = cfg.read_text()
    assert after.startswith(before)                          # appended, nothing rewritten
    data = tomllib.loads(after)
    assert {"path": str(new), "enabled": False} in data["skills"]["config"]
    assert data["projects"]["/a"]["trust_level"] == "trusted"


def test_fix_covers_every_config_and_every_missing_version(tmp_path):
    a = plugin(tmp_path, "1.3.3")
    b = plugin(tmp_path, "1.3.4")
    old = str(a).replace("1.3.3", "1.3.2")
    home_cfg = config(tmp_path / ".codex/config.toml", old)
    link_plugins((tmp_path / ORCA).parent, tmp_path)
    orca = config(tmp_path / ORCA)
    rc, out = fix(tmp_path)
    assert rc == 0, out
    for cfg in (home_cfg, orca):
        paths = {e["path"] for e in tomllib.loads(cfg.read_text())["skills"]["config"] if e["enabled"] is False}
        assert {str(a), str(b)} <= paths, (cfg, paths)
    assert old not in home_cfg.read_text()


def test_fix_refuses_an_ambiguous_stale_path(tmp_path):
    cfg, old, new = stale_setup(tmp_path)
    cfg.write_text(cfg.read_text() + f'\n# was "{old}"\n')
    before = cfg.read_text()
    rc, out = fix(tmp_path)
    assert rc == 1, out
    assert cfg.read_text() == before and not backups(cfg) and not temps(cfg)
    assert "NOT FIXED" in out


def test_fix_refuses_an_edit_that_would_not_parse(tmp_path):
    plugin(tmp_path, "1.3.2")
    cfg = tmp_path / ".codex/config.toml"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text('[plugins."mattpocock-skills@mattpocock"]\nenabled = true\n\n'
                   '[skills]\nconfig = [{ path = "/elsewhere/SKILL.md", enabled = false }]\n')
    before = cfg.read_text()
    rc, out = fix(tmp_path)                                  # appending [[skills.config]] would redefine it
    assert rc == 1, out
    assert cfg.read_text() == before and not backups(cfg) and not temps(cfg)
    assert "would not parse" in out


def test_fix_refuses_a_symlinked_config(tmp_path):
    cfg, old, new = stale_setup(tmp_path)
    managed = tmp_path / "dotfiles/codex.toml"
    managed.parent.mkdir()
    cfg.rename(managed)
    cfg.symlink_to(managed)
    before = managed.read_text()
    rc, out = fix(tmp_path)
    assert rc == 1, out
    assert cfg.is_symlink() and managed.read_text() == before
    assert "NOT FIXED" in out and str(managed) in out
    assert not backups(cfg) and not temps(cfg) and not list(managed.parent.glob("*.bak-handoff-*"))


def test_fix_keeps_crlf_line_endings(tmp_path):
    cfg, old, new = stale_setup(tmp_path)
    crlf = cfg.read_text().replace("\n", "\r\n")
    cfg.write_bytes(crlf.encode())
    rc, out = fix(tmp_path)
    assert rc == 0, out
    assert cfg.read_bytes() == crlf.replace(old, str(new)).encode()


def test_fix_appends_with_crlf_in_a_crlf_file(tmp_path):
    plugin(tmp_path, "1.3.2")
    cfg = config(tmp_path / ".codex/config.toml")
    cfg.write_bytes(cfg.read_text().replace("\n", "\r\n").encode())
    rc, out = fix(tmp_path)
    assert rc == 0, out
    raw = cfg.read_bytes()
    assert b"\r\n" in raw and b"\n" not in raw.replace(b"\r\n", b"")


def test_fix_leaves_no_temp_when_the_config_vanishes(tmp_path, monkeypatch, capsys):
    cfg, old, new = stale_setup(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("CODEX_HOME", raising=False)
    mod = load_verify()

    def gone(path):
        raise FileNotFoundError(path)

    monkeypatch.setattr(mod, "current_text", gone)
    try:
        mod.main(["--fix"])
    except FileNotFoundError:
        pass
    assert not temps(cfg) and not backups(cfg)


def test_fix_temp_is_never_wider_than_the_config(tmp_path, monkeypatch, capsys):
    cfg, old, new = stale_setup(tmp_path)
    cfg.chmod(0o600)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("CODEX_HOME", raising=False)
    mod = load_verify()
    seen = []
    real = mod.current_text

    def spy(path):
        seen.extend(stat.S_IMODE(t.stat().st_mode) for t in temps(cfg))
        return real(path)

    monkeypatch.setattr(mod, "current_text", spy)
    monkeypatch.setattr(mod.os, "chmod", lambda *a, **k: None)   # the mode must come from creation
    assert mod.main(["--fix"]) == 0
    assert seen == [0o600], seen


def test_fix_leaves_an_explicitly_enabled_handoff_alone(tmp_path):
    new = plugin(tmp_path, "1.3.2")
    cfg = tmp_path / ".codex/config.toml"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text('[plugins."mattpocock-skills@mattpocock"]\nenabled = true\n\n'
                   f'[[skills.config]]\npath = "{new}"\nenabled = true\n')
    before = cfg.read_text()
    rc, out = fix(tmp_path)
    assert rc == 1, out
    assert cfg.read_text() == before and "NOT FIXED" in out


def test_fix_does_not_touch_duplicates(tmp_path):
    cfg, old, new = stale_setup(tmp_path)
    copy = skill(tmp_path / ".codex/skills/handoff", "handoff")
    rc, out = fix(tmp_path)
    assert rc == 1, out
    assert copy.exists()
    assert str(new) in cfg.read_text()
    last = out.strip().splitlines()[-1]
    assert "DUPLICATE" in last and "STALE" not in last


def test_fix_with_nothing_to_fix_writes_nothing(tmp_path):
    hp = plugin(tmp_path, "1.3.2")
    cfg = config(tmp_path / ".codex/config.toml", str(hp))
    before, mtime = cfg.read_text(), cfg.stat().st_mtime_ns
    rc, out = fix(tmp_path)
    assert rc == 0, out
    assert cfg.read_text() == before and cfg.stat().st_mtime_ns == mtime and not backups(cfg)


def test_fix_keeps_the_file_mode(tmp_path):
    cfg, old, new = stale_setup(tmp_path)
    cfg.chmod(0o600)
    rc, out = fix(tmp_path)
    assert rc == 0, out
    assert stat.S_IMODE(cfg.stat().st_mode) == 0o600


def test_fix_never_touches_an_unreadable_config(tmp_path):
    plugin(tmp_path, "1.3.2")
    cfg = tmp_path / ".codex/config.toml"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text("[plugins\nnot toml")
    rc, out = fix(tmp_path)
    assert rc == 2, out
    assert cfg.read_text() == "[plugins\nnot toml" and not backups(cfg)


def test_stale_summary_points_at_fix(tmp_path):
    cfg, old, new = stale_setup(tmp_path)
    rc, out = run(tmp_path)
    assert rc == 1 and "--fix" in out.strip().splitlines()[-1], out
    assert len(out.strip().splitlines()[-1]) <= 160


def load_verify():
    spec = importlib.util.spec_from_file_location("verify_under_test", VERIFY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_fix_aborts_when_the_config_changes_underneath(tmp_path, monkeypatch, capsys):
    cfg, old, new = stale_setup(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("CODEX_HOME", raising=False)
    mod = load_verify()
    real = mod.current_text

    def codex_wrote_meanwhile(path):
        text = real(path)
        cfg.write_text(text + '\n[projects."/new"]\ntrust_level = "trusted"\n')   # Codex trusts a dir
        return cfg.read_text()

    monkeypatch.setattr(mod, "current_text", codex_wrote_meanwhile)
    rc = mod.main(["--fix"])
    out = capsys.readouterr().out
    assert rc == 1, out
    assert "changed while fixing" in out
    assert old in cfg.read_text() and '"/new"' in cfg.read_text()   # Codex's write survives
    assert not temps(cfg) and not backups(cfg)


def test_fix_escapes_a_backslash_in_the_new_path(tmp_path):
    new = plugin(tmp_path, "1.3\\3")
    old = str(new).replace("1.3\\3", "1.3.2")
    cfg = config(tmp_path / ".codex/config.toml", old)
    rc, out = fix(tmp_path)
    assert rc == 0, out
    paths = [e["path"] for e in tomllib.loads(cfg.read_text())["skills"]["config"]]
    assert str(new) in paths, paths


def test_fix_refuses_a_quote_it_cannot_put_in_a_literal_string(tmp_path):
    new = plugin(tmp_path, "1.3'3")
    old = str(new).replace("1.3'3", "1.3.2")
    cfg = tmp_path / ".codex/config.toml"
    cfg.write_text('[plugins."mattpocock-skills@mattpocock"]\nenabled = true\n\n'
                   f"[[skills.config]]\npath = '{old}'\nenabled = false\n")
    before = cfg.read_text()
    rc, out = fix(tmp_path)
    assert rc == 1, out
    assert cfg.read_text() == before and not backups(cfg) and "would not parse" in out


def test_two_fixes_in_one_second_keep_both_backups(tmp_path, monkeypatch, capsys):
    cfg, old, new = stale_setup(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("CODEX_HOME", raising=False)
    mod = load_verify()
    monkeypatch.setattr(mod.time, "strftime", lambda fmt: "20261110120000")
    first = cfg.read_text()
    assert mod.main(["--fix"]) == 0
    cfg.write_text(first)                                   # stale again, same second
    assert mod.main(["--fix"]) == 0
    assert [b.read_text() for b in backups(cfg)] == [first, first]


def test_fix_refuses_a_stale_path_inside_an_inline_table(tmp_path):
    new = plugin(tmp_path, "1.3.3")
    old = str(new).replace("1.3.3", "1.3.2")
    cfg = tmp_path / ".codex/config.toml"
    cfg.write_text('[plugins."mattpocock-skills@mattpocock"]\nenabled = true\n\n'
                   f'[skills]\nconfig = [{{ path = "{old}", enabled = false }}]\n')
    before = cfg.read_text()
    rc, out = fix(tmp_path)
    assert rc == 1, out
    assert cfg.read_text() == before and not backups(cfg) and not temps(cfg)
    assert "not on a plain" in out and "Traceback" not in out


def test_fix_never_removes_a_temp_it_did_not_create(tmp_path, monkeypatch, capsys):
    cfg, old, new = stale_setup(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("CODEX_HOME", raising=False)
    mod = load_verify()
    planted = cfg.with_name(f".{cfg.name}.handoff-fix-{os.getpid()}")
    planted.write_text("someone else's")
    with pytest.raises(FileExistsError):
        mod.main(["--fix"])
    assert planted.read_text() == "someone else's"
    assert cfg.read_text().count(old) == 1 and not backups(cfg)


def test_cleanup_survives_a_config_rewritten_as_non_utf8(tmp_path, monkeypatch, capsys):
    cfg, old, new = stale_setup(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("CODEX_HOME", raising=False)
    mod = load_verify()

    def binary_write(path):
        cfg.write_bytes(b"\xff\xfe not utf-8")
        raise RuntimeError("original failure")

    monkeypatch.setattr(mod, "current_text", binary_write)
    with pytest.raises(RuntimeError, match="original failure"):   # not masked by cleanup
        mod.main(["--fix"])
    assert not temps(cfg)
