"""A re-dispatched auditor gets a FRESH report path, never one another agent was handed.

Two re-dispatched audit legs were handed the original legs' report paths: one
clobber, one near-clobber. Both originals were alive and slow, wrongly declared
dead from a hook's `Running:` set (#49o). The rule "never re-dispatch to a report
path another agent was handed" was prose, and nothing enforced it: `audit-cycle`
derived fixed `${stem}_p${i}.report.md` paths, `rm -f`'d them and reused them.

Claim once, never release (round 3), tightened in round 4:

- given `--report-file RP`, the assembler claims RP exactly once with an O_EXCL
  marker under `$XDG_CACHE_HOME/h-mad/handed` (default `~/.cache/h-mad/handed`) --
  process-independent, unlike TMPDIR -- and writes the prompt at `--out` with
  O_EXCL too, so neither the report path nor the prompt path is ever reused;
- a reused RP or `--out` HALTs `report_path_handed`, names which was held, and
  deletes nothing; the only remedy is a new RUN, which moves RP and `--out`
  together (round 3's `next=` kept the old `--out` and overwrote a live leg's
  prompt);
- `--report-file` and `--out` must be absolute, and the marker key is the
  realpath of the parent plus the casefolded filename;
- the verb mints a fresh stem per invocation, and the recipes mint a RUN token.
"""
import hashlib
import os
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = REPO_ROOT / "h-mad"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_h_mad_assemble_audit import SCRIPT, _project  # noqa: E402
from test_hmad_dispatch import _bindir, run  # noqa: E402
from test_hmad_dispatch_audit_cycle import (  # noqa: E402
    assert_registered_verb,
    dispatch_args,
    install_audit_cycle_stubs,
    project_with_docs,
    read_jsonl,
    run_audit_cycle,
)
from test_h_mad_collect_report import (  # noqa: E402
    collect_args,
    docs_path,
    run_collect_cli,
    write_report,
)
import h_mad_assemble_audit as aa  # noqa: E402

RUN_STEM = r"_run\d{8}T\d{6}Z-\d+"


def _argv(root: Path, out: Path | None, rp, *, cycle: str = "3") -> list[str]:
    argv = ["--feature", "demo", "--phase", "plan", "--cycle", cycle,
            "--project-root", str(root), "--report-file", str(rp)]
    return argv + (["--out", str(out)] if out is not None else [])


def _cache(tmp_path: Path) -> Path:
    return tmp_path / "xdg-cache"


def _env(tmp_path: Path, **extra: str) -> dict:
    return {**os.environ, "XDG_CACHE_HOME": str(_cache(tmp_path)), **extra}


def _assemble(tmp_path: Path, root: Path, out, rp, *extra: str, env=None):
    # cwd=tmp_path: a relative claim directory (a mutant's, say) lands in the test's
    # tree, never in the repository.
    return subprocess.run([sys.executable, str(SCRIPT), *_argv(root, out, rp), *extra],
                          capture_output=True, text=True, env=env or _env(tmp_path),
                          cwd=tmp_path)


def _key(path: str) -> str:
    parent, name = os.path.split(path)
    ident = os.path.join(os.path.realpath(parent), name).casefold()
    return hashlib.sha256(ident.encode("utf-8")).hexdigest()


def _marker(tmp_path: Path, rp) -> Path:
    return _cache(tmp_path) / "h-mad" / "handed" / f"{_key(str(rp))}.handed"


def _rp(tmp_path: Path, name: str = "audit_demo_plan_cycle3_p1.report.md") -> Path:
    reports = tmp_path / "reports"
    reports.mkdir(exist_ok=True)
    return reports / name


def _first(r) -> str:
    return r.stdout.splitlines()[0] if r.stdout else ""


def _passed(r) -> bool:
    return r.stdout.startswith("ASSEMBLE: PASS")


def _halted_handed(r, held) -> bool:
    return _first(r).startswith("ASSEMBLE: HALT plan:report_path_handed") and \
        _first(r).endswith(f" held={held}")


# --- claim once ---------------------------------------------------------------

def test_a_fresh_path_passes_and_is_claimed_in_the_cache_dir(tmp_path):
    root = _project(tmp_path / "proj")
    rp = _rp(tmp_path)
    out = tmp_path / "prompt.txt"

    r = _assemble(tmp_path, root, out, rp)

    assert _passed(r), r.stdout + r.stderr
    assert out.exists() and out.stat().st_size > 0
    lines = _marker(tmp_path, rp).read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1, lines
    assert re.match(rf"^\S+Z path={re.escape(str(rp))} out={re.escape(str(out))} "
                    r"feature=demo phase=plan cycle=3$", lines[0]), lines[0]
    assert not list(rp.parent.glob("*.handed")), "nothing may be written beside RP"
    assert not rp.exists(), "the assembler claims RP; only the agent writes it"


def test_home_cache_is_the_default_claim_dir(tmp_path):
    root = _project(tmp_path / "proj")
    rp = _rp(tmp_path)
    home = tmp_path / "home"
    home.mkdir()
    env = {k: v for k, v in os.environ.items() if k != "XDG_CACHE_HOME"}
    env["HOME"] = str(home)

    r = _assemble(tmp_path, root, tmp_path / "p.txt", rp, env=env)

    assert _passed(r), r.stdout + r.stderr
    assert (home / ".cache" / "h-mad" / "handed" / f"{_key(str(rp))}.handed").exists()


def test_the_claim_does_not_follow_tmpdir(tmp_path):
    """Two assemblers with different TMPDIRs (a sandboxed one, say) must share one
    claim directory, or both hand the same report path."""
    root = _project(tmp_path / "proj")
    rp = _rp(tmp_path)
    t1, t2 = tmp_path / "t1", tmp_path / "t2"
    t1.mkdir()
    t2.mkdir()

    first = _assemble(tmp_path, root, tmp_path / "a.txt", rp, env=_env(tmp_path, TMPDIR=str(t1)))
    second = _assemble(tmp_path, root, tmp_path / "b.txt", rp, env=_env(tmp_path, TMPDIR=str(t2)))

    assert _passed(first), first.stdout
    assert _halted_handed(second, rp), second.stdout


def test_a_second_hand_halts_even_when_the_first_leg_finished(tmp_path):
    root = _project(tmp_path / "proj")
    rp = _rp(tmp_path)
    assert _passed(_assemble(tmp_path, root, tmp_path / "a.txt", rp))
    Path(str(rp) + ".done").write_text("", encoding="utf-8")  # leg A finished

    r = _assemble(tmp_path, root, tmp_path / "b.txt", rp)

    assert _first(r) == f"ASSEMBLE: HALT plan:report_path_handed path={rp} held={rp}", r.stdout
    assert "next=" not in r.stdout, "the only remedy is a new RUN"
    assert "mint a new RUN" in r.stdout, r.stdout
    assert not (tmp_path / "b.txt").exists()


def test_an_existing_report_path_halts(tmp_path):
    root = _project(tmp_path / "proj")
    rp = _rp(tmp_path)
    rp.write_text("a report from somewhere else\n", encoding="utf-8")

    r = _assemble(tmp_path, root, tmp_path / "prompt.txt", rp)

    assert _halted_handed(r, rp), r.stdout
    assert "already exists" in r.stdout, r.stdout
    assert not _marker(tmp_path, rp).exists(), "a path that is not fresh is not claimed"


def test_a_new_report_path_with_the_old_prompt_path_halts(tmp_path):
    """The round-3 review's reproduction: a re-dispatch that moved only RP (as the
    `next=` remedy told it to) overwrote the live leg's prompt with its own RP."""
    root = _project(tmp_path / "proj")
    out = tmp_path / "prompt_z.txt"
    rp1 = _rp(tmp_path, "audit_demo_plan_cycle3_z.report.md")
    rp2 = _rp(tmp_path, "audit_demo_plan_cycle3_z_r2.report.md")
    assert _passed(_assemble(tmp_path, root, out, rp1))  # leg L1, alive and slow
    prompt = out.read_bytes()

    r = _assemble(tmp_path, root, out, rp2)

    assert _halted_handed(r, out), r.stdout
    assert "already exists" in r.stdout, "refused by the up-front check, before any claim"
    assert out.read_bytes() == prompt, "the live leg's prompt must be untouched"
    assert not _marker(tmp_path, rp2).exists(), "a refused hand claims nothing"


def test_a_prompt_path_taken_after_the_check_is_still_refused(tmp_path, monkeypatch, capsys):
    """The prompt is written with O_EXCL: a --out that appears between the check and
    the write HALTs, and the report-path claim just made is rolled back."""
    root = _project(tmp_path / "proj")
    rp = _rp(tmp_path)
    out = tmp_path / "prompt.txt"
    out.write_text("another leg's prompt\n", encoding="utf-8")
    monkeypatch.setenv("XDG_CACHE_HOME", str(_cache(tmp_path)))
    real_present = aa._present
    monkeypatch.setattr(aa, "_present", lambda p: False if str(p) == str(out) else real_present(p))

    rc = aa.main(_argv(root, out, rp))

    assert rc == 0
    first = capsys.readouterr().out.splitlines()[0]
    assert first == f"ASSEMBLE: HALT plan:report_path_handed path={rp} held={out}", first
    assert out.read_text(encoding="utf-8") == "another leg's prompt\n"
    assert not _marker(tmp_path, rp).exists(), "the claim on RP must be rolled back"


def test_out_defaults_to_a_path_derived_from_the_report_path(tmp_path):
    """Minting RP mints the prompt path, instead of every dispatch of a cycle sharing
    `/tmp/audit_<f>_<p>_cycle<N>.txt`."""
    root = _project(tmp_path / "proj")
    rp = _rp(tmp_path)
    other = _rp(tmp_path, "teammate-b.md")

    r = _assemble(tmp_path, root, None, rp)
    r2 = _assemble(tmp_path, root, None, other)

    derived = rp.parent / "audit_demo_plan_cycle3_p1.txt"
    assert _first(r).startswith(f"ASSEMBLE: PASS {derived} "), r.stdout
    assert derived.exists()
    assert _first(r2).startswith(f"ASSEMBLE: PASS {rp.parent / 'teammate-b.md.txt'} "), r2.stdout


def test_a_txt_report_path_derives_an_appended_prompt_path(tmp_path):
    """Round-4 review: replacing the extension mapped `review_x.txt` onto itself, so
    the prompt was written AT the report path before any agent ran."""
    root = _project(tmp_path / "proj")
    rp = _rp(tmp_path, "review_x.txt")

    r = _assemble(tmp_path, root, None, rp)

    assert _first(r).startswith(f"ASSEMBLE: PASS {rp.parent / 'review_x.txt.txt'} "), r.stdout
    assert not rp.exists(), "the report path must not exist before an agent writes it"


def test_a_prompt_path_equal_to_the_report_path_halts(tmp_path):
    root = _project(tmp_path / "proj")
    rp = _rp(tmp_path, "audit_demo_plan_cycle3_x.report.md")
    same_file = _rp(tmp_path, "audit_demo_plan_CYCLE3_x.report.md")  # one file on APFS

    for out in (rp, same_file):
        r = _assemble(tmp_path, root, out, rp)
        assert _first(r) == f"ASSEMBLE: HALT plan:report_path_is_prompt_path path={rp}", r.stdout
        assert not rp.exists() and not out.exists(), "nothing may be written"
        assert not _marker(tmp_path, rp).exists(), "and nothing claimed"


def test_a_derived_prompt_path_sits_beside_the_report_path(tmp_path):
    """What SKILL.md now says: the marker never lands in a project, but the derived
    prompt sits beside RP -- so a docs-tree RP needs an explicit --out."""
    root = _project(tmp_path / "proj")
    docs = docs_path(root, feature="demo", cycle=3)
    docs.parent.mkdir(parents=True, exist_ok=True)

    r = _assemble(tmp_path, root, None, docs)

    beside = Path(str(docs) + ".txt")
    assert _first(r).startswith(f"ASSEMBLE: PASS {beside} "), r.stdout
    assert not list(root.rglob("*.handed"))


def test_a_relative_xdg_cache_home_is_ignored(tmp_path):
    """XDG says a relative XDG_CACHE_HOME is invalid; honouring it would key the
    claims off each process's cwd."""
    root = _project(tmp_path / "proj")
    rp = _rp(tmp_path)
    home = tmp_path / "home"
    home.mkdir()

    r = _assemble(tmp_path, root, tmp_path / "p.txt", rp,
                  env=_env(tmp_path, XDG_CACHE_HOME="relative-cache", HOME=str(home)))

    assert _passed(r), r.stdout + r.stderr
    assert (home / ".cache" / "h-mad" / "handed" / f"{_key(str(rp))}.handed").exists()
    assert not (tmp_path / "relative-cache").exists()


def test_a_halt_deletes_nothing(tmp_path):
    root = _project(tmp_path / "proj")
    rp = _rp(tmp_path)
    out = tmp_path / "prompt.txt"
    assert _passed(_assemble(tmp_path, root, out, rp))
    rp.write_text("the leg's report\n", encoding="utf-8")
    Path(str(rp) + ".done").write_text("", encoding="utf-8")
    before = {p: (p.read_bytes(), p.stat().st_mtime_ns)
              for p in (out, rp, Path(str(rp) + ".done"), _marker(tmp_path, rp))}

    r = _assemble(tmp_path, root, out, rp)  # the same recipe, re-run

    assert _first(r).startswith("ASSEMBLE: HALT plan:report_path_handed"), r.stdout
    after = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in before}
    assert after == before, "a HALT must not delete or touch the prompt, report, .done or claim"


def test_concurrent_hands_of_one_path_pass_exactly_once(tmp_path):
    root = _project(tmp_path / "proj")
    rp = _rp(tmp_path)
    procs = [
        subprocess.Popen([sys.executable, str(SCRIPT), *_argv(root, tmp_path / f"p{i}.txt", rp)],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                         env=_env(tmp_path))
        for i in range(8)
    ]
    firsts = [p.communicate()[0].splitlines()[0] for p in procs]

    passes = [f for f in firsts if f.startswith("ASSEMBLE: PASS")]
    halts = [f for f in firsts if f.startswith("ASSEMBLE: HALT plan:report_path_handed")]
    assert len(passes) == 1 and len(halts) == 7, firsts


# --- marker identity -----------------------------------------------------------

def test_a_relative_report_path_halts(tmp_path):
    root = _project(tmp_path / "proj")
    r = subprocess.run([sys.executable, str(SCRIPT),
                        *_argv(root, tmp_path / "p.txt", "reports/x.report.md")],
                       capture_output=True, text=True, env=_env(tmp_path), cwd=tmp_path)
    assert _first(r) == "ASSEMBLE: HALT plan:report_path_not_absolute path=reports/x.report.md", \
        r.stdout
    assert not (tmp_path / "p.txt").exists()


def test_a_relative_prompt_path_halts(tmp_path):
    root = _project(tmp_path / "proj")
    rp = _rp(tmp_path)
    r = subprocess.run([sys.executable, str(SCRIPT), *_argv(root, "p.txt", rp)],
                       capture_output=True, text=True, env=_env(tmp_path), cwd=tmp_path)
    assert _first(r) == "ASSEMBLE: HALT plan:report_path_not_absolute path=p.txt", r.stdout
    assert not _marker(tmp_path, rp).exists()


def test_a_case_variant_shares_the_claim(tmp_path):
    """On case-insensitive APFS two spellings name one file, and `realpath` does not
    case-fold a path that does not exist yet."""
    root = _project(tmp_path / "proj")
    lower = _rp(tmp_path, "audit_demo_plan_cycle3_y.report.md")
    upper = _rp(tmp_path, "audit_demo_plan_CYCLE3_y.report.md")
    assert _passed(_assemble(tmp_path, root, tmp_path / "a.txt", lower))

    r = _assemble(tmp_path, root, tmp_path / "b.txt", upper)

    assert _halted_handed(r, upper), r.stdout


def test_a_symlinked_spelling_shares_the_claim(tmp_path):
    """`/tmp` is a symlink to `/private/tmp` on macOS; pytest's tmp_path is already
    resolved, so this is the test that exercises the realpath."""
    root = _project(tmp_path / "proj")
    real = tmp_path / "real-reports"
    real.mkdir()
    link = tmp_path / "linked-reports"
    link.symlink_to(real, target_is_directory=True)
    via_link = link / "audit_demo_plan_cycle3_s.report.md"
    via_real = real / "audit_demo_plan_cycle3_s.report.md"
    assert _passed(_assemble(tmp_path, root, tmp_path / "a.txt", via_link))

    r = _assemble(tmp_path, root, tmp_path / "b.txt", via_real)

    assert _halted_handed(r, via_real), r.stdout


def test_tmp_and_private_tmp_share_the_claim(tmp_path):
    alias, real_root = "/tmp", os.path.realpath("/tmp")
    assert real_root != alias, "expects macOS, where /tmp is a symlink to /private/tmp"
    root = _project(tmp_path / "proj")
    d = f"hmad-claim-{uuid.uuid4().hex}"
    os.makedirs(os.path.join(alias, d))
    try:
        first = _assemble(tmp_path, root, tmp_path / "a.txt", f"{alias}/{d}/x.report.md")
        second = _assemble(tmp_path, root, tmp_path / "b.txt", f"{real_root}/{d}/x.report.md")
        assert _passed(first), first.stdout
        assert _halted_handed(second, f"{real_root}/{d}/x.report.md"), second.stdout
    finally:
        shutil.rmtree(os.path.join(alias, d), ignore_errors=True)


# --- failures stay closed --------------------------------------------------------

def test_a_failed_prompt_write_releases_only_its_own_claim(tmp_path):
    root = _project(tmp_path / "proj")
    rp = _rp(tmp_path)
    ro = tmp_path / "ro-out"
    ro.mkdir()
    ro.chmod(0o500)
    try:
        r = _assemble(tmp_path, root, ro / "prompt.txt", rp)
    finally:
        ro.chmod(0o700)

    assert r.returncode == 1, (r.returncode, r.stdout, r.stderr)
    assert "ASSEMBLE: PASS" not in r.stdout
    assert not _marker(tmp_path, rp).exists(), "a claim with no prompt behind it is withdrawn"


def test_a_claim_whose_marker_cannot_be_filled_is_rolled_back(tmp_path, monkeypatch, capsys):
    root = _project(tmp_path / "proj")
    rp = _rp(tmp_path)
    out = tmp_path / "prompt.txt"
    monkeypatch.setenv("XDG_CACHE_HOME", str(_cache(tmp_path)))
    real_open = open

    class _Full:
        def __init__(self, f):
            self.f = f

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            self.f.close()

        def write(self, _text):
            raise OSError(28, "No space left on device")

    def fake_open(path, mode="r", *a, **k):
        f = real_open(path, mode, *a, **k)
        return _Full(f) if str(path).endswith(".handed") else f

    monkeypatch.setattr(aa, "open", fake_open, raising=False)

    rc = aa.main(_argv(root, out, rp))

    assert rc == 0
    first = capsys.readouterr().out.splitlines()[0]
    assert first.startswith(f"ASSEMBLE: HALT plan:report_path_marker_unwritable path={rp}"), first
    assert not _marker(tmp_path, rp).exists(), "an empty claim must not hold the path"
    assert not out.exists()


def test_an_uncreatable_claim_dir_halts_without_falling_back(tmp_path):
    root = _project(tmp_path / "proj")
    rp = _rp(tmp_path)
    out = tmp_path / "prompt.txt"
    ro = tmp_path / "ro-cache-parent"
    ro.mkdir()
    ro.chmod(0o500)
    try:
        r = _assemble(tmp_path, root, out, rp, env=_env(tmp_path, XDG_CACHE_HOME=str(ro / "c")))
    finally:
        ro.chmod(0o700)

    assert _first(r).startswith(
        f"ASSEMBLE: HALT plan:report_path_marker_unwritable path={rp}"), r.stdout
    assert not out.exists(), "no prompt may be written without a claim behind it"


def test_an_unwritable_claim_dir_halts_before_any_prompt(tmp_path):
    root = _project(tmp_path / "proj")
    rp = _rp(tmp_path)
    out = tmp_path / "prompt.txt"
    claims = _cache(tmp_path) / "h-mad" / "handed"
    claims.mkdir(parents=True)
    claims.chmod(0o500)
    try:
        r = _assemble(tmp_path, root, out, rp)
    finally:
        claims.chmod(0o700)

    assert _first(r).startswith(
        f"ASSEMBLE: HALT plan:report_path_marker_unwritable path={rp}"), r.stdout
    assert not out.exists()


def test_an_unreadable_report_dir_halts_and_deletes_nothing(tmp_path):
    root = _project(tmp_path / "proj")
    locked = tmp_path / "locked"
    locked.mkdir()
    rp = locked / "audit_demo_plan_cycle3_p1.report.md"
    out = tmp_path / "prompt.txt"
    locked.chmod(0o600)  # readable listing, but no search bit: lstat() raises EACCES
    try:
        r = _assemble(tmp_path, root, out, rp)
    finally:
        locked.chmod(0o700)

    assert r.returncode == 0, r.stderr
    assert _first(r).startswith(f"ASSEMBLE: HALT plan:report_path_unreadable path={rp}"), r.stdout
    assert not out.exists()


def test_unreadable_does_not_depend_on_path_exists(tmp_path, monkeypatch, capsys):
    """Python 3.14's `Path.exists` returns False on EACCES where 3.11 raised, which
    would read an unmeasured path as fresh. Simulate 3.14 on any version."""
    root = _project(tmp_path / "proj")
    locked = tmp_path / "locked"
    locked.mkdir()
    rp = locked / "audit_demo_plan_cycle3_p1.report.md"
    out = tmp_path / "prompt.txt"
    monkeypatch.setenv("XDG_CACHE_HOME", str(_cache(tmp_path)))
    monkeypatch.setattr(Path, "exists", lambda self, *a, **k: False)
    locked.chmod(0o600)
    try:
        rc = aa.main(_argv(root, out, rp))
    finally:
        locked.chmod(0o700)

    assert rc == 0
    first = capsys.readouterr().out.splitlines()[0]
    assert first.startswith(f"ASSEMBLE: HALT plan:report_path_unreadable path={rp}"), first
    assert not out.exists()


def test_a_preflight_halt_stakes_no_claim(tmp_path):
    root = _project(tmp_path / "proj")
    rp = _rp(tmp_path)
    bad_template = tmp_path / "bad.template.md"
    bad_template.write_text(
        "Target: <INLINE_TARGET_DOC>\nBase: <INLINE_BASE_INVARIANTS>\n"
        "Project: <INLINE_PROJECT_INVARIANTS>\n"
        "Sentinel: <AUDIT_SENTINEL>\nReport: <REPORT_FILE_PATH>\n"
        "Stray: <INLINE_NEVER_FILLED>\n")

    r = _assemble(tmp_path, root, tmp_path / "prompt.txt", rp, "--template", str(bad_template))

    assert _first(r).startswith("ASSEMBLE: HALT plan:preflight"), r.stdout
    assert not _marker(tmp_path, rp).exists()


def test_no_report_file_means_no_claim_and_the_old_out_rules(tmp_path):
    root = _project(tmp_path / "proj")
    out = tmp_path / "p.txt"
    out.write_text("an earlier prompt\n", encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPT), "--feature", "demo", "--phase", "plan",
                        "--project-root", str(root), "--out", str(out)],
                       capture_output=True, text=True, env=_env(tmp_path))
    assert _passed(r), r.stdout
    assert out.read_text(encoding="utf-8") != "an earlier prompt\n", (
        "sentinel mode keeps overwriting --out: only a claimed report path claims its prompt")
    assert not (_cache(tmp_path) / "h-mad").exists()


# --- collect has no marker side effects ----------------------------------------

def test_collect_leaves_no_marker_side_effects(tmp_path):
    """A report path handed straight to the docs tree: the claim lives in the cache
    dir, so the project gets no stray marker, and collect neither reads nor removes
    it -- so a collected path stays claimed and cannot be re-handed."""
    root = _project(tmp_path / "proj")
    docs = docs_path(root, feature="demo", cycle=3)
    docs.parent.mkdir(parents=True, exist_ok=True)
    assert _passed(_assemble(tmp_path, root, tmp_path / "a.txt", docs))
    marker = _marker(tmp_path, docs)
    claim = marker.read_bytes()
    write_report(docs, done=True)  # the agent delivers

    c = run_collect_cli(collect_args(root, docs, feature="demo", cycle=3))

    assert c.stdout.splitlines()[0].startswith("COLLECT: OK"), c.stdout + c.stderr
    assert not list(root.rglob("*.handed")), "no marker may land in the project tree"
    assert marker.read_bytes() == claim, "collect must not touch the claim"
    assert _first(_assemble(tmp_path, root, tmp_path / "b.txt", docs)).startswith(
        "ASSEMBLE: HALT plan:report_path_handed")
    for script in ("h_mad_collect_report.py", "h_mad_audit_cycle.py"):
        assert ".handed" not in (SKILL_DIR / "scripts" / script).read_text(encoding="utf-8")


# --- the verb mints a fresh stem per invocation -------------------------------

def _verb_feature(tmp_path):
    return f"handed-{os.getpid()}-{tmp_path.name}"


def _cleanup(feature, cycle="7"):
    for path in Path("/tmp").glob(f"audit_{feature}_plan_cycle{cycle}_*"):
        path.unlink(missing_ok=True)


def test_verb_mints_a_fresh_run_stem(tmp_path):
    root = project_with_docs(tmp_path)
    script_dir, assemble_calls, cycle_calls = install_audit_cycle_stubs(tmp_path)
    feature = _verb_feature(tmp_path)
    try:
        r = run_audit_cycle(
            tmp_path, dispatch_args(feature=feature, root=root, passes="2"),
            env={"HMAD_AUDIT_CYCLE_SCRIPT_DIR": str(script_dir)},
            capture=tmp_path / "agy.calls",
        )
        assert r.returncode == 0, r.stderr
        assert_registered_verb(r)
        reports = [a[a.index("--report-file") + 1] for a in read_jsonl(assemble_calls)]
        outs = [a[a.index("--out") + 1] for a in read_jsonl(assemble_calls)]
        stem = re.escape(f"/tmp/audit_{feature}_plan_cycle7") + RUN_STEM
        for i, (report, out) in enumerate(zip(reports, outs), start=1):
            assert re.fullmatch(stem + rf"_p{i}\.report\.md", report), report
            assert re.fullmatch(stem + rf"_p{i}\.txt", out), out
        assert reports[0].rsplit("_p1", 1)[0] == reports[1].rsplit("_p2", 1)[0], reports
        cycle_argv = read_jsonl(cycle_calls)[0]
        assert any(arg.startswith(f"1:{reports[0]}:") for arg in cycle_argv), cycle_argv
    finally:
        _cleanup(feature)


def test_verb_stems_differ_within_one_clock_second(tmp_path):
    """The `-$$` half of the stem, pinned without timing: a fake `date` pins the
    timestamp, so only the pid can tell two runs apart."""
    feature = _verb_feature(tmp_path)
    reports = []
    try:
        for n in range(2):
            run_dir = tmp_path / f"run{n}"
            run_dir.mkdir()
            root = project_with_docs(run_dir)
            script_dir, assemble_calls, _ = install_audit_cycle_stubs(run_dir)
            b = _bindir(run_dir, ["agy"])
            (b / "date").write_text(
                '#!/bin/sh\n'
                'if [ "$*" = "-u +%Y%m%dT%H%M%SZ" ]; then echo 20991231T235959Z; '
                'else exec /bin/date "$@"; fi\n', encoding="utf-8")
            (b / "date").chmod(0o755)
            r = run(dispatch_args(feature=feature, root=root, passes="1"), env={
                "_BINDIR": b,
                "HMAD_STUB_HOSTILE": "all",
                "HMAD_STUB_AGY_RESP": "# Audit\\n\\n## Must-fix\\nNone\\n\\n## Should-fix\\nNone\\n",
                "HMAD_AUDIT_CYCLE_SCRIPT_DIR": str(script_dir),
            }, capture=run_dir / "agy.calls")
            assert r.returncode == 0, r.stderr
            argv = read_jsonl(assemble_calls)[0]
            reports.append(argv[argv.index("--report-file") + 1])
        assert all("_run20991231T235959Z-" in rep for rep in reports), reports
        assert reports[0] != reports[1], reports
    finally:
        _cleanup(feature)


def test_two_verb_runs_against_the_real_assembler_use_different_stems(tmp_path):
    """REAL assembler: the second run of the same cycle must not be refused, and
    must not reuse the first run's paths."""
    root = _project(tmp_path / "proj")
    cycle = f"8{os.getpid()}"
    env = {"XDG_CACHE_HOME": str(_cache(tmp_path))}
    try:
        for n in range(2):
            run_dir = tmp_path / f"run{n}"  # each run needs its own stub bindir
            run_dir.mkdir()
            r = run_audit_cycle(
                run_dir,
                dispatch_args(feature="demo", cycle=cycle, passes="1", root=root)
                + ["--report-grace", "0", "--timeout", "60"],
                env=env, capture=run_dir / "agy.calls",
            )
            assert r.returncode == 0, r.stderr
            assert "assemble_halt" not in r.stdout, r.stdout
        asm = sorted(Path("/tmp").glob(f"audit_demo_plan_cycle{cycle}_run*_p1.asm.txt"))
        assert len(asm) == 2, asm
        for a in asm:
            assert re.fullmatch(rf"audit_demo_plan_cycle{cycle}{RUN_STEM}_p1\.asm\.txt", a.name)
            assert a.read_text(encoding="utf-8").startswith("ASSEMBLE: PASS"), a.read_text()
        claims = list((_cache(tmp_path) / "h-mad" / "handed").glob("*.handed"))
        assert len(claims) == 2, claims
    finally:
        _cleanup("demo", cycle)


# --- the docs ------------------------------------------------------------------

def _flat(path: Path) -> str:
    # Whitespace-normalised: the docs wrap at ~100 columns.
    return " ".join(path.read_text(encoding="utf-8").split())


def test_the_rule_says_claim_once_and_where():
    skill = _flat(SKILL_DIR / "SKILL.md")
    rule = "- **Never re-dispatch to a report path another agent was handed** — suffix it."
    enforced = (
        "Enforced for legs staged through `h_mad_assemble_audit.py --report-file` and the "
        "`audit-cycle` verb: every staged report path and its prompt path are claimed once and "
        "never handed again, and the recipes and the verb mint a fresh pair per dispatch. Hand "
        "assembly (steps 6.6–8 without the script), dispatches that bypass the assembler "
        "(6a-prime, an `Agent()` given a hand-picked path) and sentinel mode (empty "
        "`--report-file`) are not guarded.")
    assert f"{rule} {enforced}" in skill
    discipline = _flat(SKILL_DIR / "references" / "measurement-discipline.md")
    assert ("Enforced only for audit legs staged through `h_mad_assemble_audit.py "
            "--report-file` (the recipes and `audit-cycle`): every staged report path and its "
            "prompt path are claimed once and never handed again. Hand assembly, sentinel mode "
            "and other dispatches are not guarded.") in discipline


def test_the_assembler_section_matches_claim_once():
    skill = _flat(SKILL_DIR / "SKILL.md")
    for text in (
        "`ASSEMBLE: HALT <phase>:report_path_handed path=<RP> held=<path>`",
        "`ASSEMBLE: HALT <phase>:report_path_not_absolute path=<path>`",
        "`ASSEMBLE: HALT <phase>:report_path_unreadable path=<RP>`",
        "`ASSEMBLE: HALT <phase>:report_path_marker_unwritable path=<RP>`",
        "A HALT deletes nothing.",
        "Stale markers are harmless",
        "`$XDG_CACHE_HOME/h-mad/handed/`",
        "`ASSEMBLE: HALT <phase>:report_path_is_prompt_path path=<RP>`",
        "The claim directory is keyed on `XDG_CACHE_HOME`/`HOME`, so assemblers that must see "
        "each other's claims need the same values; a write-restricted sandbox fails closed with "
        "`report_path_marker_unwritable`.",
        "The derived prompt path sits beside RP, so pass an explicit `--out` for a report path "
        "in the docs tree.",
        "the realpath of the parent joined with the filename, casefolded as a whole",
    ):
        assert text in skill, text
    for gone in ("delete `<RP>.handed`", "always belongs to the current holder",
                 "withdraws any earlier prompt", "next=", "<tempdir>/hmad-handed",
                 "report_path_marker_unreadable", "leaves nothing in the project",
                 "with `.report.md` replaced by `.txt`"):
        assert gone not in skill, gone


RUN_LINE = "RUN=$(date -u +%Y%m%dT%H%M%SZ)-$$"
ECHO_LINE = 'echo "RUN=$RUN RP=$RP"'
ON_HALT = "On `ASSEMBLE: HALT <phase>:report_path_handed`, mint a new `RUN`"
CARRY = ("Substitute those literal values into every later step: each Bash call is a fresh "
         "shell, so `$RUN` and `$RP` do not survive into the next block.")


def _section(doc: str, start: str, end: str) -> str:
    i = doc.index(start)
    return doc[i:doc.index(end, i + len(start))]


def _blocks(section: str) -> list[str]:
    return re.findall(r"```(?:bash)?\n(.*?)```", section, re.S)


def _opt(block: str, flag: str) -> str:
    m = re.search(rf"{re.escape(flag)} (\S+)", block)
    assert m, (flag, block)
    return m.group(1)


def test_every_hand_recipe_mints_and_carries_one_report_and_prompt_path():
    skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    orch = (SKILL_DIR / "references" / "orchestration-mode.md").read_text(encoding="utf-8")
    for doc in (skill, orch):
        assert 'rm -f "$RP" "$RP.done"' not in doc and "(and `rm -f" not in doc
        assert "next=" not in doc
        lines = doc.splitlines()
        for i, line in enumerate(lines):
            if re.search(r'RP="?/tmp/audit_', line):
                assert "rm -f" not in line + "\n".join(lines[i + 1:i + 3]), line

    # primary recipe (the verb's assembly, step 1-7.2)
    primary = _blocks(_section(skill, "For each audit pass, the verb **assembles with the script**",
                               "It prints `ASSEMBLE: PASS"))[0]
    assert RUN_LINE in primary and primary.rstrip().endswith(ECHO_LINE)
    assert "RP=/tmp/audit_<feature>_<phase>_cycle<N>_run$RUN.report.md" in primary
    assert _opt(primary, "--out") == "/tmp/audit_<feature>_<phase>_cycle<N>_run$RUN.txt"
    # ... and steps 8 and 9, each a fresh shell, use the same prompt path and RP.
    step8 = _blocks(_section(skill, "\n8. Dispatch:", "\n9. Capture the report."))[0]
    step9 = _blocks(_section(skill, "\n9. Capture the report.", "The gate refuses a path"))[0]
    assert re.search(r"send agy (\S+)", step8).group(1) == _opt(primary, "--out")
    assert 'report-wait "$RP"' in step9

    # codex leg: assemble -> exec -> collect, all on one RP / prompt / out
    codex = _section(skill, "## Second surface — the codex leg", "Read the `COLLECT:` token.")
    asm, exe, col = _blocks(codex)[:3]
    assert RUN_LINE in asm and asm.rstrip().endswith(ECHO_LINE)
    assert _opt(asm, "--report-file") == '"$RP"'
    assert re.search(r"exec codex (\S+)", exe).group(1) == _opt(asm, "--out")
    assert _opt(col, "--report") == '"$RP"'
    assert _opt(col, "--out") == _opt(exe, "--out")

    # teammate leg: assemble -> Agent(PROMPT=, REPORT=) -> collect
    team = _section(skill, "stage the report under a `teammate` surface",
                    "Read the `COLLECT:` token exactly as the codex leg does")
    asm, agent, col = _blocks(team)[:3]
    assert RUN_LINE in asm and asm.rstrip().endswith(ECHO_LINE)
    assert _opt(asm, "--report-file") == '"$RP"'
    assert re.search(r"PROMPT=(\S+)", agent).group(1) == _opt(asm, "--out")
    assert "REPORT=<the $RP above>" in agent
    assert _opt(col, "--report") == '"$RP"'

    # orchestration-mode flow: assemble -> send -> report-wait, one block
    flow = _blocks(_section(orch, "**Flow (coordinator).**", "`report-wait` is substrate-agnostic"))[0]
    assert RUN_LINE in flow
    assert re.search(r"send agy (\S+)", flow).group(1) == _opt(flow, "--out")
    assert 'report-wait "$RP"' in flow

    flat_skill, flat_orch = " ".join(skill.split()), " ".join(orch.split())
    assert flat_skill.count(CARRY) >= 2, flat_skill.count(CARRY)
    assert flat_skill.count(ON_HALT) >= 3 and ON_HALT in flat_orch


def test_step_6_6_does_not_promise_a_hand_assembler_a_halt():
    skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    step = skill[skill.index("6.6. **Report-file transport"):skill.index("\n7. Stage:")]
    flat = " ".join(step.split())
    assert "A hand assembly claims nothing" in flat, flat[:600]
    assert "Carry the literal `RUN` and `RP` values into steps 7–9" in flat, flat[:900]
    assert RUN_LINE in step
