"""Tests for `h_mad_bash4_fence_probe.py`.

Fixture docs only. The parse-diff tests need a real `/bin/bash` 3.2 and a bash
>= 4; they SKIP — never pass — when either is missing, because the instrument
cannot judge without both and a pass there would certify nothing.

The load-bearing case is `test_apostrophe_heredoc_is_a_parse32_finding`: no
feature regex can see it, so a probe without the parse diff reports a clean
tree over a block that the `/bin/bash` pin would fail to run.
"""

from __future__ import annotations

import io
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import h_mad_bash4_fence_probe as probe_mod  # noqa: E402

MODERN = probe_mod.find_modern_bash(None)


def _old_is_32() -> bool:
    try:
        out = subprocess.run([probe_mod.OLD_BASH, "-c", "echo ${BASH_VERSINFO[0]}"],
                             capture_output=True, text=True)
    except OSError:
        return False
    return out.stdout.strip() == "3"


needs_shells = pytest.mark.skipif(not (MODERN and _old_is_32()),
                                  reason="needs /bin/bash 3.2 and a bash >= 4")

FENCE = "```"


def _doc(tmp_path: Path, name: str, body: str, info: str = "bash", extra: str = "") -> Path:
    p = tmp_path / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f"# Doc\n\n{extra}{FENCE}{info}\n{body}{FENCE}\n", encoding="utf-8")
    return p


def _run(roots, include_archive=False):
    buf = io.StringIO()
    totals = probe_mod.probe([str(r) for r in roots], include_archive, MODERN, out=buf)
    return totals, buf.getvalue()


@pytest.mark.parametrize("name,pattern,sample", probe_mod.FEATURES,
                         ids=[f[0] for f in probe_mod.FEATURES])
def test_every_regex_fires_on_its_control(name, pattern, sample):
    assert dict(probe_mod.COMPILED)[name].search(sample)


def test_plain_posix_lines_fire_no_regex():
    clean = ["echo hi && ls -la", 'for f in *.md; do wc -l "$f"; done',
             "x=${y:-default}", "a=(1 2 3); echo ${a[0]}", "cmd > /dev/null 2>&1 &",
             "case $x in a) : ;; esac", "test -f x && echo yes"]
    for line in clean:
        hits = [n for n, rx in probe_mod.COMPILED if rx.search(line)]
        assert hits == [], (line, hits)


@needs_shells
def test_self_test_passes():
    assert probe_mod.self_test(MODERN) == []


@needs_shells
def test_clean_doc_is_clean(tmp_path):
    _doc(tmp_path, "a.md", "echo hi\nls\n")
    totals, _ = _run([tmp_path])
    assert totals["blocks"] == 1
    assert totals["regex_hits"] == totals["parse32_only"] == 0


@needs_shells
def test_apostrophe_heredoc_is_a_parse32_finding(tmp_path):
    _doc(tmp_path, "a.md", probe_mod.PARSE_CONTROL)
    totals, out = _run([tmp_path])
    assert totals["regex_hits"] == 0
    assert totals["parse32_only"] == 1
    assert "PARSE32" in out and "a.md:4" in out


@needs_shells
def test_both_shells_reject_is_counted_apart(tmp_path):
    _doc(tmp_path, "a.md", "if then fi (\n")
    totals, out = _run([tmp_path])
    assert totals["parse_both"] == 1 and totals["parse32_only"] == 0
    assert "PARSE32" not in out


@needs_shells
def test_regex_hit_carries_doc_line_and_tags(tmp_path):
    _doc(tmp_path, "a.md", "echo x\n# expect 0\nmapfile -t a < f\n")
    totals, out = _run([tmp_path])
    assert totals["regex_hits"] == 1
    assert "REGEX mapfile" in out and "a.md:6" in out and "screens=yes exec=no" in out


@needs_shells
def test_exec_fence_is_tagged(tmp_path):
    _doc(tmp_path, "a.md", "declare -A m\n", info="bash hmad:exec")
    _, out = _run([tmp_path])
    assert "exec=yes" in out


@needs_shells
def test_non_shell_fences_are_ignored(tmp_path):
    _doc(tmp_path, "a.md", "mapfile -t a < f\n", info="python")
    totals, _ = _run([tmp_path])
    assert totals["docs"] == totals["blocks"] == totals["regex_hits"] == 0


@needs_shells
def test_archive_is_skipped_unless_asked(tmp_path):
    _doc(tmp_path, "archive/a.md", "mapfile -t a < f\n")
    assert _run([tmp_path])[0]["regex_hits"] == 0
    assert _run([tmp_path], include_archive=True)[0]["regex_hits"] == 1


@needs_shells
def test_cli_exit_codes(tmp_path):
    clean = tmp_path / "clean"
    dirty = tmp_path / "dirty"
    _doc(clean, "a.md", "echo hi\n")
    _doc(dirty, "a.md", "coproc cat\n")
    script = str(SCRIPTS / "h_mad_bash4_fence_probe.py")
    run = lambda *a: subprocess.run([sys.executable, script, *a], capture_output=True, text=True)
    assert run(str(clean)).returncode == 0
    assert run(str(dirty)).returncode == 1
    assert run("--self-test").returncode == 0


def test_missing_modern_bash_cannot_judge(tmp_path):
    script = str(SCRIPTS / "h_mad_bash4_fence_probe.py")
    out = subprocess.run([sys.executable, script, "--modern-bash", str(tmp_path / "nope"),
                          str(tmp_path)], capture_output=True, text=True)
    assert out.returncode == 2 and "CANNOT_JUDGE" in out.stderr
