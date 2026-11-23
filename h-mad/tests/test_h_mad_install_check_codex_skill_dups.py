"""The install check could not see a second skill of the same name in a codex home.

Codex loads skills from `<codex home>/skills` and from the shared `~/.agents/skills`
root, and lists them by frontmatter `name`. Measured 2026-11-22: an Orca codex
home held a plain `skills/h-mad/` directory (one 5 KB SKILL.md written
2026-09-09) beside `~/.agents/skills/h-mad -> <checkout>/h-mad`, and three codex
session files from that day each listed `h-mad` twice, the stale copy first.
`h_mad_install_check.py` read `INSTALL: PASS`. A second duplicate (`ieumoffice`)
sat in `~/.codex`, a different home, so a check of one home sees half of them.

These tests pin an ADVISORY, not a verdict: one `CODEX_SKILL_DUPLICATE:` line per
codex-home copy of a name the agents root also holds, could-not-check kept
distinct from none, and the `INSTALL:` summary untouched.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SCRIPT = SCRIPTS / "h_mad_install_check.py"
sys.path.insert(0, str(SCRIPTS))

DUP = "CODEX_SKILL_DUPLICATE:"
SHADOWED = "CODEX_SKILL_SHADOWED:"
UNKNOWN = "CODEX_SKILL_DUPLICATE_UNKNOWN:"


def _skill(root: Path, dirname: str, name: str | None = None, body: str = "body") -> Path:
    """A real skill directory `<root>/<dirname>/SKILL.md`; returns the SKILL.md."""
    d = root / dirname
    d.mkdir(parents=True, exist_ok=True)
    path = d / "SKILL.md"
    path.write_text(f"---\nname: {name or dirname}\ndescription: d\n---\n\n{body}\n",
                    encoding="utf-8")
    return path


def _linked_skill(root: Path, dirname: str, checkout: Path, body: str = "checkout") -> Path:
    """`<root>/<dirname> -> <checkout>/<dirname>`, as `~/.agents/skills/h-mad` is."""
    _skill(checkout, dirname, body=body)
    root.mkdir(parents=True, exist_ok=True)
    (root / dirname).symlink_to(checkout / dirname)
    return root / dirname / "SKILL.md"


def _the_measured_case(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    """codex home with a stale plain `h-mad`, agents root linking to the checkout."""
    home = tmp_path / "codex-home"
    agents = tmp_path / "agents-skills"
    stale = _skill(home / "skills", "h-mad", body="# H-MAD for Codex (stale)")
    linked = _linked_skill(agents, "h-mad", tmp_path / "checkout")
    return home, agents, stale, linked


def _check(homes, agents):
    import h_mad_install_check as mod
    return mod.check_codex_skill_duplicates(None if homes is None else list(homes), agents)


def _dups(lines):
    return [line for line in lines if line.startswith(DUP)]


def _unknowns(lines):
    return [line for line in lines if line.startswith(UNKNOWN)]


def _pin(home: Path, *skill_mds: Path, enabled: bool = False) -> Path:
    home.mkdir(parents=True, exist_ok=True)
    config = home / "config.toml"
    text = 'model = "x"\n'
    for path in skill_mds:
        text += f'\n[[skills.config]]\npath = "{path}"\nenabled = {"true" if enabled else "false"}\n'
    config.write_text(text, encoding="utf-8")
    return config


# --- outcomes ---------------------------------------------------------------

def test_a_stale_copy_beside_the_linked_skill_is_reported_with_both_paths(tmp_path):
    home, agents, stale, linked = _the_measured_case(tmp_path)
    lines = _check([home], agents)
    dups = _dups(lines)
    assert len(dups) == 1, lines
    assert dups[0].startswith(f"{DUP}h-mad "), dups[0]
    assert str(stale) in dups[0], "the line must name the codex-home copy"
    assert str(linked) in dups[0], "the line must name the agents-root copy"
    assert "[[skills.config]]" in dups[0], "the line must name a remedy"
    assert not _unknowns(lines), lines


def test_distinct_names_are_silent(tmp_path):
    home, agents = tmp_path / "codex-home", tmp_path / "agents-skills"
    _skill(home / "skills", "omx-plan")
    _linked_skill(agents, "h-mad", tmp_path / "checkout")
    assert _check([home], agents) == []


@pytest.mark.parametrize("missing", ["codex-skills", "codex-home", "agents-root"])
def test_an_absent_root_is_silent_not_unknown(tmp_path, missing):
    home, agents = tmp_path / "codex-home", tmp_path / "agents-skills"
    if missing != "codex-home":
        home.mkdir()
    if missing == "agents-root":
        _skill(home / "skills", "h-mad")
    else:
        _linked_skill(agents, "h-mad", tmp_path / "checkout")
    assert _check([home], agents) == []


def test_two_links_to_the_same_skill_are_not_a_duplicate(tmp_path):
    """Both roots linking to one checkout skill cannot drift apart or shadow."""
    home, agents, checkout = tmp_path / "codex-home", tmp_path / "agents", tmp_path / "checkout"
    _linked_skill(agents, "h-mad", checkout)
    (home / "skills").mkdir(parents=True)
    (home / "skills" / "h-mad").symlink_to(checkout / "h-mad")
    assert _check([home], agents) == []
    # Positive control: the same layout with a real copy in the codex home reports.
    (home / "skills" / "h-mad").unlink()
    _skill(home / "skills", "h-mad", body="copy")
    assert len(_dups(_check([home], agents))) == 1


def test_the_name_compared_is_the_frontmatter_name_not_the_folder(tmp_path):
    home, agents = tmp_path / "codex-home", tmp_path / "agents-skills"
    renamed = _skill(home / "skills", "workflow", name="h-mad")
    _linked_skill(agents, "h-mad", tmp_path / "checkout")
    dups = _dups(_check([home], agents))
    assert len(dups) == 1 and dups[0].startswith(f"{DUP}h-mad "), dups
    assert str(renamed) in dups[0]


def test_same_folder_name_with_different_skill_names_is_silent(tmp_path):
    home, agents = tmp_path / "codex-home", tmp_path / "agents-skills"
    _skill(home / "skills", "h-mad", name="something-else")
    _linked_skill(agents, "h-mad", tmp_path / "checkout")
    assert _dups(_check([home], agents)) == []


def test_every_home_is_checked_and_each_names_its_own_copy(tmp_path):
    """2026-11-22: `h-mad` sat in the Orca home, `ieumoffice` in `~/.codex`."""
    agents = tmp_path / "agents-skills"
    _linked_skill(agents, "h-mad", tmp_path / "checkout")
    _skill(agents, "ieumoffice", body="vendor")
    orca, dot_codex = tmp_path / "orca-home", tmp_path / "dot-codex"
    a = _skill(orca / "skills", "h-mad", body="stale")
    b = _skill(dot_codex / "skills", "ieumoffice", body="vendor copy")
    dups = _dups(_check([orca, dot_codex], agents))
    assert len(dups) == 2, dups
    assert any(line.startswith(f"{DUP}h-mad ") and str(a) in line for line in dups)
    assert any(line.startswith(f"{DUP}ieumoffice ") and str(b) in line for line in dups)


def test_the_same_home_named_twice_reports_once(tmp_path):
    home, agents, _, _ = _the_measured_case(tmp_path)
    alias = tmp_path / "alias-home"
    alias.symlink_to(home)
    assert len(_dups(_check([home, alias], agents))) == 1


# --- the documented remedy silences it, and only it -------------------------

def test_the_codex_home_copy_disabled_in_that_homes_config_is_not_reported(tmp_path):
    home, agents, stale, _ = _the_measured_case(tmp_path)
    assert len(_dups(_check([home], agents))) == 1, "control: unpinned must report"
    _pin(home, stale)
    assert _check([home], agents) == []


def test_disabling_the_linked_copy_is_reported_as_shadowed_not_silenced(tmp_path):
    """Turning off the agents copy leaves the stale codex-home copy as the ONLY
    one codex uses: the defect this advisory exists for, made worse."""
    home, agents, stale, linked = _the_measured_case(tmp_path)
    _pin(home, linked)
    lines = _check([home], agents)
    assert not _dups(lines), lines
    shadowed = [l for l in lines if l.startswith(SHADOWED)]
    assert len(shadowed) == 1 and shadowed[0].startswith(f"{SHADOWED}h-mad "), lines
    assert str(stale) in shadowed[0] and str(linked) in shadowed[0]


def test_a_relative_pin_path_does_not_silence(tmp_path, monkeypatch):
    """A relative `path` would resolve against the caller's cwd, not the home."""
    home, agents, _, _ = _the_measured_case(tmp_path)
    (home / "config.toml").write_text(
        'model = "x"\n\n[[skills.config]]\npath = "skills/h-mad/SKILL.md"\nenabled = false\n',
        encoding="utf-8")
    monkeypatch.chdir(home)
    assert len(_dups(_check([home], agents))) == 1


def test_an_explicitly_enabled_entry_does_not_silence_it(tmp_path):
    home, agents, stale, _ = _the_measured_case(tmp_path)
    _pin(home, stale, enabled=True)
    assert len(_dups(_check([home], agents))) == 1


def test_a_pin_in_another_homes_config_does_not_silence_this_home(tmp_path):
    home, agents, stale, _ = _the_measured_case(tmp_path)
    other = tmp_path / "other-home"
    _pin(other, stale)
    assert len(_dups(_check([home, other], agents))) == 1


# --- more than one copy of a name, and homes that share a skills dir ---------

def test_a_correct_link_does_not_hide_a_stale_copy_beside_it(tmp_path):
    """`skills/h-mad -> checkout` plus `skills/h-mad.bak/` naming itself h-mad."""
    home, agents, checkout = tmp_path / "codex-home", tmp_path / "agents", tmp_path / "checkout"
    _linked_skill(agents, "h-mad", checkout)
    (home / "skills").mkdir(parents=True)
    (home / "skills" / "h-mad").symlink_to(checkout / "h-mad")
    assert _check([home], agents) == [], "control: the link alone is not a duplicate"
    bak = _skill(home / "skills", "h-mad.bak", name="h-mad", body="stale")
    dups = _dups(_check([home], agents))
    assert len(dups) == 1 and str(bak) in dups[0], dups


def test_every_stale_copy_of_one_name_is_reported(tmp_path):
    home, agents, _, _ = _the_measured_case(tmp_path)
    second = _skill(home / "skills", "h-mad-old", name="h-mad", body="older")
    dups = _dups(_check([home], agents))
    assert len(dups) == 2 and any(str(second) in l for l in dups), dups


def test_a_pin_in_one_home_does_not_silence_another_home_sharing_its_skills_dir(tmp_path):
    """An Orca home may link `skills` to `~/.codex/skills` and still have its own
    config: the pin that turns the copy off for one home does nothing for the other."""
    dot_codex, agents, stale, _ = _the_measured_case(tmp_path)
    _pin(dot_codex, stale)
    orca = tmp_path / "orca-home"
    orca.mkdir()
    (orca / "skills").symlink_to(dot_codex / "skills")
    assert _check([dot_codex], agents) == [], "control: the pinned home alone is silent"
    dups = _dups(_check([dot_codex, orca], agents))
    assert len(dups) == 1, dups
    assert str(orca / "config.toml") in dups[0], "the line must name the unpinned home's config"
    # Spelled through THIS home: whether codex matches a pin by literal or real
    # path is unmeasured, so the path an operator copies must be this home's own.
    assert f"codex={orca / 'skills' / 'h-mad' / 'SKILL.md'} " in dups[0], dups[0]


def test_the_line_names_a_live_agents_copy_not_a_disabled_one(tmp_path):
    home, agents, _, linked = _the_measured_case(tmp_path)
    alt = _skill(agents, "h-mad-alt", name="h-mad", body="second live copy")
    _pin(home, linked)
    dups = _dups(_check([home], agents))
    assert len(dups) == 1, dups
    assert f"agents={alt} " in dups[0], "the disabled copy is not the one codex lists"


def test_the_remedy_does_not_assume_which_copy_is_stale(tmp_path):
    """The codex home may hold the link and the agents root the stale copy."""
    home, agents, checkout = tmp_path / "codex-home", tmp_path / "agents", tmp_path / "checkout"
    _skill(checkout, "h-mad")
    (home / "skills").mkdir(parents=True)
    (home / "skills" / "h-mad").symlink_to(checkout / "h-mad")
    _skill(agents, "h-mad", body="stale")
    dups = _dups(_check([home], agents))
    assert len(dups) == 1, dups
    assert "codex-home copy out" not in dups[0] and "[[skills.config]]" in dups[0]


def test_a_skill_md_with_no_frontmatter_name_is_not_compared(tmp_path):
    """Whether codex lists such a file at all is unmeasured; guessing its name from
    the folder would report a duplicate codex may never show."""
    home, agents = tmp_path / "codex-home", tmp_path / "agents-skills"
    d = home / "skills" / "h-mad"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text("# notes, no frontmatter\n", encoding="utf-8")
    _linked_skill(agents, "h-mad", tmp_path / "checkout")
    assert _check([home], agents) == []


# --- could-not-check is never "none" ----------------------------------------

@pytest.mark.skipif(os.geteuid() == 0, reason="root reads through mode 000")
@pytest.mark.parametrize("locked", ["codex-home", "agents-parent"])
def test_a_root_that_cannot_be_examined_is_unknown_on_every_python(tmp_path, locked):
    """`Path.is_dir()` raises EACCES up to python 3.13 and returns False after:
    one crashed main() after the verdict, the other read as 'no duplicates'."""
    home = tmp_path / "codex-home"
    agents = tmp_path / "agents-parent" / "skills"
    _skill(home / "skills", "h-mad", body="stale")
    _linked_skill(agents, "h-mad", tmp_path / "checkout")
    target = home if locked == "codex-home" else agents.parent
    target.chmod(0o000)
    try:
        lines = _check([home], agents)
    finally:
        target.chmod(0o755)
    assert not _dups(lines), lines
    unknown = _unknowns(lines)
    assert len(unknown) == 1 and str(target) in unknown[0], lines
    assert unknown[0].endswith("reason=unreadable:PermissionError"), unknown
    assert len(_dups(_check([home], agents))) == 1, "control: readable again, it reports"


@pytest.mark.parametrize("raw", ['skills = "weird"\n', '[skills]\nconfig = "weird"\n',
                                 '[skills]\nconfig = ["not-a-table"]\n'],
                         ids=["skills-scalar", "config-scalar", "entry-not-table"])
def test_a_config_of_unexpected_shape_is_unknown_and_never_suppresses(tmp_path, raw):
    home, agents, _, _ = _the_measured_case(tmp_path)
    (home / "config.toml").write_text(raw, encoding="utf-8")
    lines = _check([home], agents)
    assert len(_dups(lines)) == 1, lines
    assert len(_unknowns(lines)) == 1 and "reason=config-shape" in _unknowns(lines)[0], lines


def test_no_homes_or_no_agents_root_never_reports_the_verifier(tmp_path, monkeypatch):
    import h_mad_install_check as mod
    monkeypatch.setattr(mod, "DUPLICATE_VERIFIER", tmp_path / "absent" / "verify.py")
    assert mod.check_codex_skill_duplicates([], tmp_path) == []
    assert mod.check_codex_skill_duplicates([tmp_path], tmp_path / "absent-agents") == []


def test_an_exception_inside_the_advisory_cannot_fail_the_run(tmp_path, monkeypatch):
    """The verdict is already printed; a traceback after it turns exit 0 into 1."""
    import h_mad_install_check as mod

    def boom(*_args, **_kwargs):
        raise RuntimeError("kaboom")

    monkeypatch.setattr(mod, "check_codex_skill_duplicates", boom)
    lines = mod.codex_skill_duplicate_lines([tmp_path], tmp_path)
    assert len(lines) == 1 and lines[0].startswith(UNKNOWN), lines
    assert "reason=crashed:RuntimeError" in lines[0]
    assert str(tmp_path) not in lines[0], "a crash is not a fact about any one path"


def test_an_unparseable_config_never_suppresses_the_duplicate(tmp_path):
    home, agents, _, _ = _the_measured_case(tmp_path)
    (home / "config.toml").write_text("[[skills.config]\nthis is not toml", encoding="utf-8")
    lines = _check([home], agents)
    assert len(_dups(lines)) == 1, lines
    unknown = _unknowns(lines)
    assert len(unknown) == 1 and str(home / "config.toml") in unknown[0], lines
    assert "reason=config-unparseable" in unknown[0]


def test_a_config_is_not_read_when_there_is_no_duplicate(tmp_path):
    home, agents = tmp_path / "codex-home", tmp_path / "agents-skills"
    _skill(home / "skills", "omx-plan")
    _linked_skill(agents, "h-mad", tmp_path / "checkout")
    (home / "config.toml").write_text("not toml [", encoding="utf-8")
    assert _check([home], agents) == []


@pytest.mark.skipif(os.geteuid() == 0, reason="root reads through mode 000")
def test_an_unlistable_skills_dir_is_unknown_not_clean(tmp_path):
    home, agents, _, _ = _the_measured_case(tmp_path)
    skills = home / "skills"
    skills.chmod(0o000)
    try:
        lines = _check([home], agents)
    finally:
        skills.chmod(0o755)
    assert not _dups(lines), lines
    unknown = _unknowns(lines)
    assert len(unknown) == 1 and str(skills) in unknown[0], lines
    assert unknown[0].endswith("reason=unreadable:PermissionError"), unknown
    # Positive control: readable again, the same tree reports the duplicate.
    assert len(_dups(_check([home], agents))) == 1


def test_a_missing_verifier_module_is_unknown_not_clean(tmp_path, monkeypatch):
    import h_mad_install_check as mod
    home, agents, _, _ = _the_measured_case(tmp_path)
    monkeypatch.setattr(mod, "DUPLICATE_VERIFIER", tmp_path / "absent" / "verify.py")
    lines = mod.check_codex_skill_duplicates([home], agents)
    assert not _dups(lines)
    assert len(_unknowns(lines)) == 1 and "reason=verifier-missing" in lines[0], lines


def test_the_patch_readme_says_retiring_it_breaks_this_check():
    """The verifier lives in a patch directory with a documented retirement that
    deletes it; without this line the advisory turns into a permanent UNKNOWN."""
    import h_mad_install_check as mod
    readme = (mod.DUPLICATE_VERIFIER.parent / "README.md").read_text(encoding="utf-8")
    retiring = readme[readme.index("Retiring"):]
    assert "h_mad_install_check.py" in retiring


# --- main() -----------------------------------------------------------------

def _main(tmp_path, hermetic_env, *argv, agents=None, extra_env=None, drop_env=()):
    cmd = [sys.executable, str(SCRIPT),
           "--skills-link", str(tmp_path / "no-claude" / "h-mad"),
           "--hook-link", str(tmp_path / "no-claude" / "gate.sh"),
           "--agy-skills-dir", str(tmp_path / "no-agy-skills")]
    if agents is not None:
        cmd += ["--agents-skills-dir", str(agents)]
    env = hermetic_env(**(extra_env or {}))
    for key in drop_env:
        env.pop(key, None)
    return subprocess.run(cmd + [str(a) for a in argv], capture_output=True, text=True,
                          cwd=tmp_path, env=env, timeout=60.0)


def test_main_prints_the_advisory_and_leaves_the_summary_and_issue_count(tmp_path, hermetic_env):
    home, agents, stale, _ = _the_measured_case(tmp_path)
    clean = tmp_path / "clean-home"
    _skill(clean / "skills", "omx-plan")
    dup = _main(tmp_path, hermetic_env, "--codex-home", home, agents=agents)
    ref = _main(tmp_path, hermetic_env, "--codex-home", clean, agents=agents)
    assert dup.returncode == ref.returncode == 0, (dup.stderr, ref.stderr)
    assert not any(l.startswith("CODEX_SKILL_") for l in ref.stdout.splitlines()), ref.stdout
    first_dup, first_ref = dup.stdout.splitlines()[0], ref.stdout.splitlines()[0]
    assert first_ref.startswith("INSTALL: ")
    assert first_dup == first_ref, "an advisory must not change the INSTALL: summary or issues="
    lines = dup.stdout.splitlines()
    hits = [i for i, l in enumerate(lines) if l.startswith(DUP)]
    assert len(hits) == 1 and str(stale) in lines[hits[0]], dup.stdout
    assert hits[0] > 0, "the advisory prints after the verdict"


def test_main_codex_home_is_repeatable(tmp_path, hermetic_env):
    home, agents, _, _ = _the_measured_case(tmp_path)
    _skill(agents, "ieumoffice")
    second = tmp_path / "second-home"
    _skill(second / "skills", "ieumoffice", body="copy")
    proc = _main(tmp_path, hermetic_env, "--codex-home", home, "--codex-home", second,
                 agents=agents)
    assert len(_dups(proc.stdout.splitlines())) == 2, proc.stdout


def test_main_reads_the_homes_from_the_env_override(tmp_path, hermetic_env):
    home, agents, stale, _ = _the_measured_case(tmp_path)
    second = tmp_path / "second-home"
    _skill(agents, "ieumoffice")
    _skill(second / "skills", "ieumoffice", body="copy")
    proc = _main(tmp_path, hermetic_env, agents=agents,
                 extra_env={"HMAD_CODEX_HOMES": os.pathsep.join([str(home), str(second)])})
    assert len(_dups(proc.stdout.splitlines())) == 2, proc.stdout
    # An override that is set but empty means "no homes", never "discover".
    none = _main(tmp_path, hermetic_env, agents=agents,
                 extra_env={"HMAD_CODEX_HOMES": "", "HOME": str(tmp_path / "fake-home"),
                            "CODEX_HOME": str(home)})
    assert not _dups(none.stdout.splitlines()), none.stdout


def test_main_reports_an_empty_codex_home_value_instead_of_reading_the_cwd(tmp_path, hermetic_env):
    """`Path("")` is the cwd: an empty flag would read `<cwd>/skills`. Dropping it
    silently is no better: a wrapper passing an unset variable checks nothing."""
    home, agents, _, _ = _the_measured_case(tmp_path)
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--skills-link", str(tmp_path / "x" / "h-mad"),
         "--hook-link", str(tmp_path / "x" / "gate.sh"),
         "--agy-skills-dir", str(tmp_path / "no-agy"), "--agents-skills-dir", str(agents),
         "--codex-home", ""],
        capture_output=True, text=True, cwd=home, env=hermetic_env(), timeout=60.0)
    assert proc.returncode == 0, proc.stderr
    lines = proc.stdout.splitlines()
    assert not _dups(lines), proc.stdout
    unknown = _unknowns(lines)
    assert len(unknown) == 1 and "--codex-home" in unknown[0], proc.stdout
    assert "reason=empty-value" in unknown[0]


def test_a_relative_home_is_printed_as_an_absolute_path(tmp_path, monkeypatch):
    """A relative path names a different tree from every other cwd."""
    home, agents, stale, _ = _the_measured_case(tmp_path)
    monkeypatch.chdir(tmp_path)
    dups = _dups(_check([Path(home.name)], agents))
    assert len(dups) == 1, dups
    assert f"codex={stale} " in dups[0] and f"in {home / 'config.toml'}" in dups[0], dups[0]


def test_an_unreadable_item_with_a_newline_in_its_path_keeps_its_error():
    import h_mad_install_check as mod
    line = mod._unknown_line("/p\nq/skills (PermissionError)")
    assert line.endswith("reason=unreadable:PermissionError"), line


def _discovery_layout(tmp_path):
    agents = tmp_path / "agents-skills"
    _linked_skill(agents, "h-mad", tmp_path / "checkout")
    _skill(agents, "ieumoffice")
    fake_home = tmp_path / "fake-home"
    in_dot_codex = _skill(fake_home / ".codex" / "skills", "ieumoffice", body="copy")
    accounts = fake_home / "Library" / "Application Support" / "orca" / "codex-accounts"
    return agents, fake_home, in_dot_codex, accounts


def test_main_discovers_every_orca_account_home(tmp_path, hermetic_env):
    agents, fake_home, in_dot_codex, accounts = _discovery_layout(tmp_path)
    in_account = _skill(accounts / "acct-b" / "home" / "skills", "h-mad", body="stale")
    (accounts / "not-a-dir").write_text("stray file", encoding="utf-8")
    proc = _main(tmp_path, hermetic_env, agents=agents,
                 drop_env=("HMAD_CODEX_HOMES", "CODEX_HOME"),
                 extra_env={"HOME": str(fake_home)})
    lines = proc.stdout.splitlines()
    dups = _dups(lines)
    assert len(dups) == 2 and not _unknowns(lines), proc.stdout
    assert any(str(in_dot_codex) in l for l in dups) and any(str(in_account) in l for l in dups)


@pytest.mark.skipif(os.geteuid() == 0, reason="root reads through mode 000")
@pytest.mark.parametrize("locked", ["codex-home-env", "account-dir", "accounts-root"])
def test_main_discovery_reports_a_home_it_cannot_examine_and_keeps_going(
        tmp_path, hermetic_env, locked):
    """Discovery used `is_dir()`: on python 3.11 one unreadable candidate dropped
    EVERY home, and on 3.14+ the unreadable one vanished without a line."""
    agents, fake_home, in_dot_codex, accounts = _discovery_layout(tmp_path)
    env = {"HOME": str(fake_home)}
    drop = ["HMAD_CODEX_HOMES", "CODEX_HOME"]
    if locked == "codex-home-env":
        target = tmp_path / "locked"
        _skill(target / "home" / "skills", "h-mad", body="stale")
        env["CODEX_HOME"] = str(target / "home")
        drop.remove("CODEX_HOME")
    else:
        _skill(accounts / "acct-a" / "home" / "skills", "h-mad", body="stale")
        target = accounts / "acct-a" if locked == "account-dir" else accounts
    target.chmod(0o000)
    try:
        proc = _main(tmp_path, hermetic_env, agents=agents, drop_env=drop, extra_env=env)
    finally:
        target.chmod(0o755)
    assert proc.returncode == 0, proc.stderr
    lines = proc.stdout.splitlines()
    dups = _dups(lines)
    assert len(dups) == 1 and str(in_dot_codex) in dups[0], \
        f"the readable home must still be checked: {proc.stdout}"
    unknown = _unknowns(lines)
    assert len(unknown) == 1 and str(target) in unknown[0], proc.stdout
    assert "reason=unreadable:PermissionError" in unknown[0], unknown


def test_main_discovers_dot_codex_and_codex_home_when_nothing_is_named(tmp_path, hermetic_env):
    """With no flag and no override the check covers `~/.codex` AND `$CODEX_HOME`:
    on an Orca host those are different homes and both are live."""
    agents = tmp_path / "agents-skills"
    _linked_skill(agents, "h-mad", tmp_path / "checkout")
    _skill(agents, "ieumoffice")
    fake_home = tmp_path / "fake-home"
    in_dot_codex = _skill(fake_home / ".codex" / "skills", "ieumoffice", body="copy")
    orca = tmp_path / "orca-home"
    in_orca = _skill(orca / "skills", "h-mad", body="stale")
    proc = _main(tmp_path, hermetic_env, agents=agents, drop_env=("HMAD_CODEX_HOMES",),
                 extra_env={"HOME": str(fake_home), "CODEX_HOME": str(orca)})
    dups = _dups(proc.stdout.splitlines())
    assert any(str(in_dot_codex) in l for l in dups), proc.stdout
    assert any(str(in_orca) in l for l in dups), proc.stdout
    assert len(dups) == 2, proc.stdout
