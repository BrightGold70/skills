"""Task 14c RED: assembler read/check pins and require integration."""

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from test_grok_audit_surface_containment import (
    containment_module, _containment_cli, _containment_main,
    _assert_containment_token,
)
from test_hmad_dispatch_audit_cycle import STUB_PATH_SCOPE_CLAUSE


@pytest.fixture
def read_repo(tmp_path, monkeypatch):
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")
    repo = tmp_path / "repo [a]* ⟦h-mad⟧"
    scripts = repo / "h-mad/scripts"
    scripts.mkdir(parents=True)
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
    (scripts / "tracked.py").write_text("pass\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", "initial"], check=True, capture_output=True)
    return repo, scripts


def _git_clean_env(extra=None):
    env = dict(os.environ)
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_OBJECT_DIRECTORY",
                "GIT_ALTERNATE_OBJECT_DIRECTORIES", "HMAD_AUDIT_CYCLE_SCRIPT_DIR"):
        env.pop(key, None)
    env.update(extra or {})
    return env


def _read(repo, here, **extra):
    return subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1] / "scripts/h_mad_grok_containment.py"),
                             "assembler-read", "--here", str(here)], env=_git_clean_env(extra),
                            capture_output=True, text=True, timeout=15)


def _assert_read(result, expected):
    _assert_containment_token(result.returncode, result.stdout, result.stderr, 0, expected, "assembler-read")


def test_assembler_read_clean_tree_reads_sha_and_no(read_repo):
    repo, here = read_repo
    sha = subprocess.run(["git", "-C", str(here), "rev-parse", "--verify", "HEAD"], check=True,
                         capture_output=True, text=True).stdout.strip()
    _assert_read(_read(repo, here), f"ASSEMBLER-READING: sha={sha} dirty=no script_dir_env=unset here={here.resolve()}")


def test_assembler_read_dirty_h_mad_reads_yes(read_repo):
    repo, here = read_repo
    (repo / "h-mad/hostile [*].txt").write_text("dirty\n", encoding="utf-8")
    sha = subprocess.run(["git", "-C", str(here), "rev-parse", "--verify", "HEAD"], check=True,
                         capture_output=True, text=True).stdout.strip()
    _assert_read(_read(repo, here), f"ASSEMBLER-READING: sha={sha} dirty=yes script_dir_env=unset here={here.resolve()}")


def test_assembler_read_outside_git_reads_unreadable(tmp_path):
    here = tmp_path / "outside [*]"; here.mkdir()
    probe = subprocess.run(["git", "-C", str(here.parent), "rev-parse", "--git-dir"], capture_output=True)
    assert probe.returncode != 0, "outside fixture must not resolve to a git repository"
    _assert_read(_read(tmp_path, here), f"ASSEMBLER-READING: sha=unreadable dirty=unknown script_dir_env=unset here={here.resolve()}")


@pytest.mark.parametrize("value", ["agent supplied [*]", ""], ids=["nonempty", "empty"])
def test_assembler_read_records_a_set_script_dir_env(read_repo, value):
    repo, here = read_repo
    sha = subprocess.run(["git", "-C", str(here), "rev-parse", "--verify", "HEAD"], check=True,
                         capture_output=True, text=True).stdout.strip()
    _assert_read(_read(repo, here, HMAD_AUDIT_CYCLE_SCRIPT_DIR=value),
                 f"ASSEMBLER-READING: sha={sha} dirty=no script_dir_env=set here={here.resolve()}")


def test_assembler_read_sha256_repository_reads_unreadable(tmp_path):
    repo = tmp_path / "sha256"; repo.mkdir()
    p = subprocess.run(["git", "init", "--object-format=sha256", str(repo)], capture_output=True)
    if p.returncode:
        pytest.skip("git lacks sha256 object format")
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
    (repo / "x").write_text("x", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", "initial"], check=True, capture_output=True)
    sha = subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify", "HEAD"], check=True,
                         capture_output=True, text=True).stdout.strip()
    assert len(sha) == 64, "control must prove a successful 64-character SHA-256 lookup"
    _assert_read(_read(repo, repo), f"ASSEMBLER-READING: sha=unreadable dirty=no script_dir_env=unset here={repo.resolve()}")


def test_assembler_read_usage_error_exits_2(read_repo):
    repo, here = read_repo
    result = subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1] / "scripts/h_mad_grok_containment.py"),
                             "assembler-read", "--unknown-hostile"], env=_git_clean_env(),
                            capture_output=True, text=True, timeout=15)
    _assert_containment_token(result.returncode, result.stdout, result.stderr, 2,
                              "ASSEMBLER-READING: unreadable reason=internal:UsageError", "assembler-read usage")
    assert "QUARANTINE:" not in result.stdout


@pytest.fixture
def assembler_case(tmp_path, monkeypatch, containment_module):
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")
    module = containment_module()
    self_dir = tmp_path / "script [*]"
    self_dir.mkdir()
    monkeypatch.setattr(module, "SELF_DIR", self_dir, raising=False)
    (self_dir / "h_mad_assemble_audit.py").write_text(
        f"PATH_SCOPE_CLAUSE = {STUB_PATH_SCOPE_CLAUSE!r}\n", encoding="utf-8")
    reading = tmp_path / "reading [*]"
    (reading / "resmoke/p1").mkdir(parents=True)
    (reading / "resmoke/p1/p1.prompt.txt").write_text(STUB_PATH_SCOPE_CLAUSE + "\n", encoding="utf-8")
    stems = tmp_path / "stems [*]"; stems.mkdir()
    for name in ("s1-grok", "s2-d1-v1"):
        d = stems / name; d.mkdir()
        (d / "audit.here.txt").write_text(f"here={self_dir}\n", encoding="utf-8")
    start, end = tmp_path / "start.txt", tmp_path / "end.txt"
    payload = f"ASSEMBLER-READING: sha={'a'*40} dirty=no script_dir_env=unset here={self_dir}\n"
    start.write_text(payload, encoding="utf-8"); end.write_text(payload, encoding="utf-8")
    return dict(module=module, self_dir=self_dir, reading=reading, stems=stems, start=start, end=end)


def _check(case, capsys, expected, *, stages="resmoke", mutate=None):
    if mutate: mutate(case)
    rc, out, err = _containment_main(case["module"], capsys, "assembler-check", "--start", case["start"],
        "--end", case["end"], "--reading", case["reading"], "--stems", case["stems"], "--stages", stages)
    _assert_containment_token(rc, out, err, 0, expected, "assembler-check")


def test_assembler_check_pinned(assembler_case, capsys):
    c=assembler_case; _check(c, capsys, f"ASSEMBLER: PINNED sha={'a'*40} prompts=1 here={c['self_dir']}")


def test_assembler_check_unparseable_reading(assembler_case, capsys):
    c=assembler_case; c["start"].write_text("broken\n")
    _check(c, capsys, "ASSEMBLER: UNPINNED reason=reading_unparseable:start")


def test_assembler_check_script_dir_set(assembler_case, capsys):
    c=assembler_case; c["start"].write_text(c["start"].read_text().replace("unset", "set"))
    _check(c, capsys, "ASSEMBLER: UNPINNED reason=script_dir_set")


def test_assembler_check_sha_unreadable(assembler_case, capsys):
    c=assembler_case; c["start"].write_text(c["start"].read_text().replace("a"*40, "unreadable"))
    _check(c, capsys, "ASSEMBLER: UNPINNED reason=sha_unreadable")


def test_assembler_check_here_changed(assembler_case, capsys):
    c=assembler_case; c["end"].write_text(c["end"].read_text().replace(str(c["self_dir"]), "/changed"))
    _check(c, capsys, "ASSEMBLER: UNPINNED reason=here_changed")


def test_assembler_check_sha_changed(assembler_case, capsys):
    c=assembler_case; c["end"].write_text(c["end"].read_text().replace("a"*40, "b"*40))
    _check(c, capsys, "ASSEMBLER: UNPINNED reason=sha_changed")


@pytest.mark.parametrize("dirty", ["yes", "unknown"], ids=["yes", "unknown"])
def test_assembler_check_dirty(assembler_case, capsys, dirty):
    c=assembler_case; c["start"].write_text(c["start"].read_text().replace("dirty=no", f"dirty={dirty}"))
    _check(c, capsys, f"ASSEMBLER: UNPINNED reason=dirty:{dirty}")


def test_assembler_check_here_not_self(assembler_case, capsys):
    c=assembler_case; c["start"].write_text(c["start"].read_text().replace(str(c["self_dir"]), "/other"))
    c["end"].write_text(c["start"].read_text())
    _check(c, capsys, "ASSEMBLER: UNPINNED reason=here_not_self")


@pytest.mark.parametrize("kind", ["none", "two"], ids=["none", "two"])
def test_assembler_check_here_unrecorded(assembler_case, capsys, kind):
    c=assembler_case; d=c["stems"] / "s1-grok"
    for f in d.glob("*.here.txt"): f.unlink()
    if kind == "two":
        (d / "one.here.txt").write_text(f"here={c['self_dir']}\n")
        (d / "two.here.txt").write_text(f"here={c['self_dir']}\n")
    _check(c, capsys, "ASSEMBLER: UNPINNED reason=here_unrecorded:s1-grok")


def test_assembler_check_here_mismatch(assembler_case, capsys):
    c=assembler_case; (c["stems"] / "s1-grok/audit.here.txt").write_text("here=/other\n")
    _check(c, capsys, "ASSEMBLER: UNPINNED reason=here_mismatch:s1-grok")


def test_assembler_check_ignores_sibling_agy_log_dirs(assembler_case, capsys):
    c=assembler_case; (c["stems"] / "s2-d1-v1.agy-log").mkdir()
    (c["stems"] / "s2-d1-v1.p1.root.txt").write_text("noise\n")
    _check(c, capsys, f"ASSEMBLER: PINNED sha={'a'*40} prompts=1 here={c['self_dir']}")


def test_assembler_check_assemble_halt_cycle_beside_good_v2_is_pinned(assembler_case, capsys):
    # The fixture already made s2-d1-v1 with its one audit.here.txt.
    c=assembler_case
    (c["stems"] / "s2-d1-v1/UNVERIFIED.txt").write_text("UNVERIFIED reason=assemble_halt:p2\n")
    (c["stems"] / "s2-d1-v2").mkdir()
    (c["stems"] / "s2-d1-v2/a.here.txt").write_text(f"here={c['self_dir']}\n")
    for v in ("v1", "v2"):
        p=c["reading"] / f"s2/d1/{v}"; p.mkdir(parents=True)
        (p / "p1.prompt.txt").write_text(STUB_PATH_SCOPE_CLAUSE + "\n")
    _check(c, capsys, f"ASSEMBLER: PINNED sha={'a'*40} prompts=3 here={c['self_dir']}", stages="resmoke,s2")


def test_assembler_check_clause_unavailable(assembler_case, capsys):
    c=assembler_case; (c["self_dir"] / "h_mad_assemble_audit.py").unlink()
    _check(c, capsys, f"ASSEMBLER: NO_CLAUSE reason=clause_unavailable sha={'a'*40}")


@pytest.mark.parametrize("stage", ["resmoke", "s2"], ids=["resmoke", "s2"])
def test_assembler_check_no_prompts(assembler_case, capsys, stage):
    c=assembler_case
    if stage == "resmoke":
        for p in (c["reading"] / "resmoke").rglob("*.prompt.txt"): p.unlink()
        _check(c, capsys, f"ASSEMBLER: NO_CLAUSE reason=no_prompts:resmoke sha={'a'*40}")
    else:
        _check(c, capsys, f"ASSEMBLER: NO_CLAUSE reason=no_prompts:s2 sha={'a'*40}", stages="resmoke,s2")


def test_assembler_check_clause_missing(assembler_case, capsys):
    c=assembler_case; (c["reading"] / "resmoke/p1/p1.prompt.txt").write_text("missing\n")
    _check(c, capsys, f"ASSEMBLER: NO_CLAUSE reason=clause_missing:resmoke/p1/p1.prompt.txt sha={'a'*40}")


def test_assembler_check_clause_twice_is_missing(assembler_case, capsys):
    c=assembler_case; (c["reading"] / "resmoke/p1/p1.prompt.txt").write_text(STUB_PATH_SCOPE_CLAUSE + "\n" + STUB_PATH_SCOPE_CLAUSE + "\n")
    _check(c, capsys, f"ASSEMBLER: NO_CLAUSE reason=clause_missing:resmoke/p1/p1.prompt.txt sha={'a'*40}")


def test_assembler_check_internal_exits_2(assembler_case, capsys, monkeypatch):
    c=assembler_case
    def explode(*args, **kwargs): raise RuntimeError("hostile [*]")
    monkeypatch.setattr(c["module"], "_assembler_clause", explode, raising=False)
    rc,out,err=_containment_main(c["module"], capsys, "assembler-check", "--start", c["start"], "--end", c["end"],
        "--reading", c["reading"], "--stems", c["stems"], "--stages", "resmoke")
    _assert_containment_token(rc,out,err,2,"ASSEMBLER: UNPINNED reason=internal:RuntimeError","assembler-check internal")


def test_assembler_check_usage_error_exits_2(assembler_case, capsys):
    c=assembler_case
    rc,out,err=_containment_main(c["module"], capsys, "assembler-check", "--unknown-hostile")
    _assert_containment_token(rc,out,err,2,"ASSEMBLER: UNPINNED reason=internal:UsageError","assembler-check usage")
    assert "QUARANTINE:" not in out


@pytest.mark.parametrize("last,ok", [("ASSEMBLER: PINNED sha="+"a"*40,True),
    ("ASSEMBLER: UNPINNED reason=dirty:yes",False),("ASSEMBLER: NO_CLAUSE reason=no_prompts:s2 sha=x",False),
    ("",False),(None,False)], ids=["PINNED","UNPINNED","NO_CLAUSE","empty","absent"])
def test_require_assembler_ok_only_on_pinned(tmp_path, last, ok):
    token=tmp_path/"token [*].txt"; halt=tmp_path/"halt.txt"
    if last is not None: token.write_text(last+"\n",encoding="utf-8")
    result=_containment_cli("require","--verb","assembler","--token-file",token,"--halt-file",halt)
    expected="REQUIRE: OK" if ok else "REQUIRE: STOP reason="+(last or f"no_token:{token}")
    _assert_containment_token(result.returncode,result.stdout,result.stderr,0,expected,"require assembler")
    assert not halt.exists(), "assembler require must never create a halt file"
