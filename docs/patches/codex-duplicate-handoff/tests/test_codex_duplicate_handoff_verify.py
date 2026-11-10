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
