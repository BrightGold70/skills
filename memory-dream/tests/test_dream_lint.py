"""Tests for memory-dream/scripts/dream_lint.py.

Fixtures are hostile on purpose: the live store holds TOML `[[skills.config]]`
headers, regex classes like `[[:space:]]`, aliased links, links inside code, and
names that differ from their file stems. A tidy fixture would pass a parser that
rewrites all of those.
"""
from __future__ import annotations

import os
import pathlib
import stat
import subprocess
import sys

import pytest

SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import dream_lint as dl  # noqa: E402

SCRIPT = SCRIPTS / "dream_lint.py"


def note(name: str, body: str, slug: str | None = None) -> str:
    fm = f"---\nname: {slug}\ndescription: d\nmetadata:\n  type: feedback\n---\n" if slug else ""
    return fm + body


@pytest.fixture
def store(tmp_path: pathlib.Path) -> pathlib.Path:
    files = {
        "MEMORY.md": "# Memory Index\n- [A](feedback_alpha.md) — a\n- [B](beta_note.md) — b\n"
                     "- [C](collide_x.md) — c\n- [D](collide-x2.md) — d\n",
        "MEMORY-ARCHIVE.md": "- [S](stub_old.md) — retired\n",
        "feedback_alpha.md": note("a", "See [[feedback-beta-note]] and [[Beta Note|the beta]].\n"
                                       "```toml\n[[skills.config]]\npath = 'x'\n```\n"
                                       "Grep `[[:space:]]` here; and `[[feedback-beta-note]]` in code.\n"
                                       "Exact: [[beta_note]]. Later: [[page-not-yet-written]].\n",
                                  slug="feedback_alpha"),
        "beta_note.md": note("b", "Back to [[feedback_alpha]].\n", slug="feedback-beta-note-slug"),
        "collide_x.md": note("c", "x\n"),
        "collide-x2.md": note("d", "Ambiguous: [[Collide X]] vs [[collidex2]]\n"),
        "collide_x_2.md": note("e", "dupe\n"),
        "stub_old.md": "MOVED TO [[feedback_alpha]]\n",
        "orphan_one.md": note("o", "nobody links me\n"),
    }
    for n, t in files.items():
        (tmp_path / n).write_text(t, encoding="utf-8")
    return tmp_path


def kinds(root: pathlib.Path) -> dict[tuple[str, str], str]:
    s = dl.Store(root)
    return {(n, inner): kind for n, _s, _e, inner, kind, _t in s.links()}


class TestClassification:
    def test_code_fences_and_inline_code_are_not_links(self, store):
        k = kinds(store)
        assert ("feedback_alpha.md", "skills.config") not in k
        assert ("feedback_alpha.md", ":space:") not in k
        # the inline-code copy of a fixable link must not be seen at all:
        alpha = [inner for (n, inner) in k if n == "feedback_alpha.md"]
        assert alpha.count("feedback-beta-note") == 1

    def test_exact_stem_or_slug_resolves(self, store):
        k = kinds(store)
        assert k[("feedback_alpha.md", "beta_note")] == "RESOLVED"
        assert k[("beta_note.md", "feedback_alpha")] == "RESOLVED"

    def test_spelling_variant_with_one_target_is_fixable(self, store):
        k = kinds(store)
        assert k[("feedback_alpha.md", "Beta Note|the beta")] == "FIXABLE"

    def test_a_link_to_nothing_is_dangling_not_fixable(self, store):
        k = kinds(store)
        assert k[("feedback_alpha.md", "page-not-yet-written")] == "DANGLING"
        # normalises to 'feedbackbetanote' — matches no stem; slug is ...slug
        assert k[("feedback_alpha.md", "feedback-beta-note")] == "DANGLING"

    def test_two_normalised_targets_are_ambiguous(self, store):
        k = kinds(store)
        assert k[("collide-x2.md", "collidex2")] == "AMBIGUOUS"
        assert k[("collide-x2.md", "Collide X")] == "FIXABLE"  # one target: collide_x.md

    def test_nonlink_patterns(self):
        s = dl.NONLINK
        for t in ("skills.config", ":space:", "", "a=b"):
            assert s.search(t)
        for t in ("feedback_alpha", "some page with spaces", "x-y"):
            assert not s.search(t)


class TestStructure:
    def test_orphans_ignore_both_indexes(self, store):
        assert dl.Store(store).orphans() == ["collide_x_2.md", "orphan_one.md"]

    def test_stub_detected(self, store):
        assert dl.Store(store).stubs() == ["stub_old.md"]

    def test_missing_index_is_unreadable_exit_2(self, tmp_path):
        (tmp_path / "x.md").write_text("hi")
        r = subprocess.run([sys.executable, SCRIPT, str(tmp_path)], capture_output=True, text=True)
        assert r.returncode == 2 and "UNREADABLE" in r.stderr

    def test_nonexistent_dir_is_exit_2(self, tmp_path):
        r = subprocess.run([sys.executable, SCRIPT, str(tmp_path / "nope")], capture_output=True, text=True)
        assert r.returncode == 2


class TestFix:
    def test_rewrite_targets_the_name_slug_and_keeps_the_label(self, store):
        s = dl.Store(store)
        new = dl.fixed_text(s, "feedback_alpha.md")
        assert "[[feedback-beta-note-slug|the beta]]" in new
        # everything else byte-identical
        assert new.replace("[[feedback-beta-note-slug|the beta]]", "[[Beta Note|the beta]]") == \
            s.text["feedback_alpha.md"]

    def test_dry_run_writes_nothing(self, store):
        before = {p.name: p.read_bytes() for p in store.glob("*.md")}
        r = subprocess.run([sys.executable, SCRIPT, str(store), "--fix-links"],
                           capture_output=True, text=True)
        assert "+See [[feedback-beta-note]] and [[feedback-beta-note-slug|the beta]]." in r.stdout
        assert {p.name: p.read_bytes() for p in store.glob("*.md")} == before

    def test_apply_requires_backup_dir(self, store):
        r = subprocess.run([sys.executable, SCRIPT, str(store), "--fix-links", "--apply"],
                           capture_output=True, text=True)
        assert r.returncode == 2

    def test_apply_backs_up_and_writes(self, store, tmp_path_factory):
        bak = tmp_path_factory.mktemp("bak")
        orig = (store / "feedback_alpha.md").read_bytes()
        r = subprocess.run([sys.executable, SCRIPT, str(store), "--fix-links", "--apply",
                            "--backup-dir", str(bak)], capture_output=True, text=True)
        assert "written=2 skipped=0" in r.stdout
        (run,) = list(bak.iterdir())
        assert (run / "feedback_alpha.md").read_bytes() == orig
        assert "[[feedback-beta-note-slug|the beta]]" in (store / "feedback_alpha.md").read_text()
        # second run: nothing fixable left
        k = kinds(store)
        assert "FIXABLE" not in k.values()

    def test_file_changed_after_read_is_skipped_not_clobbered(self, store, tmp_path_factory):
        s = dl.Store(store)
        foreign = "a concurrent session wrote this\n"

        def concurrent_write(path):
            if path.name == "feedback_alpha.md":
                path.write_text(foreign, encoding="utf-8")

        written, skipped, _ = dl.apply_fixes(s, tmp_path_factory.mktemp("bak"),
                                             before_write=concurrent_write)
        assert skipped == ["feedback_alpha.md (changed since read)"]
        assert written == ["collide-x2.md"]
        assert (store / "feedback_alpha.md").read_text() == foreign


class TestExitCodes:
    def test_clean_store_exits_0(self, tmp_path):
        (tmp_path / "MEMORY.md").write_text("- [A](a.md) — a\n")
        (tmp_path / "a.md").write_text(note("a", "self [[a]]\n", slug="a"))
        r = subprocess.run([sys.executable, SCRIPT, str(tmp_path)], capture_output=True, text=True)
        assert r.returncode == 0, r.stdout
        assert "FIXABLE=0" in r.stdout and "last_dream=never" in r.stdout

    def test_dangling_alone_is_not_actionable(self, tmp_path):
        (tmp_path / "MEMORY.md").write_text("- [A](a.md) — a\n")
        (tmp_path / "a.md").write_text(note("a", "later [[unwritten-page]]\n", slug="a"))
        r = subprocess.run([sys.executable, SCRIPT, str(tmp_path)], capture_output=True, text=True)
        assert r.returncode == 0 and "DANGLING=1" in r.stdout

    def test_findings_exit_1(self, store):
        r = subprocess.run([sys.executable, SCRIPT, str(store)], capture_output=True, text=True)
        assert r.returncode == 1

    def test_stamp_age(self, tmp_path):
        import datetime as dt
        (tmp_path / dl.STAMP).write_text("2026-11-01\n")
        assert dl.last_dream_days(tmp_path, dt.date(2026, 11, 19)) == 18
        (tmp_path / dl.STAMP).write_text("garbage")
        assert dl.last_dream_days(tmp_path, dt.date(2026, 11, 19)) is None


# ---- regressions from the 2026-11-19 fresh-context review --------------------------


def mk(root: pathlib.Path, files: dict[str, str | bytes]) -> pathlib.Path:
    idx = "".join(f"- [{n}]({n}) — x\n" for n in files if n.endswith(".md") and n != "MEMORY.md")
    (root / "MEMORY.md").write_text(files.pop("MEMORY.md", idx) if "MEMORY.md" in files else idx)
    for n, t in files.items():
        (root / n).write_bytes(t if isinstance(t, bytes) else t.encode())
    return root


def found(text: str) -> list[str]:
    return [inner for _s, _e, inner in dl.link_spans(text)]


class TestCodeRegions:
    def test_shorter_fence_does_not_close_a_longer_one(self):
        t = "````md\n```\n[[in-code]]\n```\n````\n[[after]]\n"
        assert found(t) == ["after"]

    def test_fence_opening_line_is_code(self):
        assert found("~~~ [[in-info]]\nx\n~~~\n[[out]]\n") == ["out"]

    def test_tilde_fence_not_closed_by_backticks(self):
        assert found("~~~\n[[in]]\n```\n[[still-in]]\n~~~\n[[out]]\n") == ["out"]

    def test_indented_line_is_code(self):
        assert found("para\n\n    [[indented-code]]\n\t[[tab-code]]\n[[real]]\n") == ["real"]

    def test_code_span_across_lines(self):
        assert found("`start\n[[in-span]] end` and [[real]]\n") == ["real"]

    def test_code_span_never_crosses_a_blank_line(self):
        assert found("a lone ` backtick\n\n[[real]] and `x`\n") == ["real"]

    def test_double_backtick_run_does_not_swallow_a_link(self):
        assert found("`` [[visible]] `x`\n") == ["visible"]

    def test_backtick_line_with_backticks_in_info_is_not_a_fence(self):
        assert found("```inline``` [[real-link]]\n") == ["real-link"]

    def test_offsets_survive_crlf(self):
        t = "x\r\n```\r\n[[a]]\r\n```\r\n see [[b]]\r\n"
        (s, e, inner), = list(dl.link_spans(t))
        assert inner == "b" and t[s:e] == "[[b]]"


class TestRewriteRoundTrip:
    def test_slug_that_names_another_file_falls_back_to_stem(self, tmp_path):
        root = mk(tmp_path, {
            "a_target.md": note("", "x\n", slug="something-else"),
            "something-else.md": note("", "y\n"),
            "user.md": note("", "see [[A Target]]\n", slug="user"),
        })
        s = dl.Store(root)
        assert s.classify("something-else") == ("AMBIGUOUS", None)
        assert s.classify("A Target") == ("FIXABLE", "a_target.md")
        assert "[[a_target]]" in dl.fixed_text(s, "user.md")

    def test_quoted_or_dotted_slug_uses_the_stem(self, tmp_path):
        root = mk(tmp_path, {
            "quoted_note.md": note("", "x\n", slug='"Quoted Note"'),
            "dotted.md": note("", "x\n", slug="Codex skills.config scope"),
            "user.md": note("", "[[QUOTED NOTE]] [[DOTTED]]\n", slug="user"),
        })
        new = dl.fixed_text(dl.Store(root), "user.md")
        assert new == note("", "[[quoted_note]] [[dotted]]\n", slug="user")

    def test_no_safe_spelling_is_unsafe_not_rewritten(self, tmp_path):
        root = mk(tmp_path, {
            "a.b.md": note("", "x\n", slug="x.y"),
            "user.md": note("", "[[A B]]\n", slug="user"),
        })
        s = dl.Store(root)
        # stem 'a.b' and slug 'x.y' are both NONLINK spellings
        assert s.classify("A B")[0] in ("UNSAFE", "DANGLING")
        assert dl.fixed_text(s, "user.md") == s.text["user.md"]

    def test_name_is_read_from_frontmatter_only(self, tmp_path):
        root = mk(tmp_path, {
            "aa.md": "no frontmatter\nname: wrong-slug\n",
            "user.md": note("", "[[AA]]\n", slug="user"),
        })
        s = dl.Store(root)
        assert s.slug["aa.md"] is None
        assert "[[aa]]" in dl.fixed_text(s, "user.md")


class TestWriteSafety:
    def test_edit_between_store_read_and_apply_is_skipped(self, tmp_path, tmp_path_factory):
        root = mk(tmp_path, {"beta_x.md": note("", "b\n", slug="beta_x"),
                             "user.md": note("", "see [[Beta X]]\n", slug="user")})
        s = dl.Store(root)
        with open(root / "user.md", "a") as fh:
            fh.write("CONCURRENT LINE\n")
        written, skipped, _ = dl.apply_fixes(s, tmp_path_factory.mktemp("bak"))
        assert written == [] and skipped == ["user.md (changed since read)"]
        assert "CONCURRENT LINE" in (root / "user.md").read_text()

    def test_crlf_preserved(self, tmp_path, tmp_path_factory):
        root = mk(tmp_path, {"beta_x.md": note("", "b\n", slug="beta_x"),
                             "user.md": b"line one\r\nsee [[Beta X]]\r\nend\r\n"})
        dl.apply_fixes(dl.Store(root), tmp_path_factory.mktemp("bak"))
        assert (root / "user.md").read_bytes() == b"line one\r\nsee [[beta_x]]\r\nend\r\n"

    def test_mode_preserved(self, tmp_path, tmp_path_factory):
        root = mk(tmp_path, {"beta_x.md": note("", "b\n", slug="beta_x"),
                             "user.md": note("", "see [[Beta X]]\n", slug="user")})
        os.chmod(root / "user.md", 0o644)
        dl.apply_fixes(dl.Store(root), tmp_path_factory.mktemp("bak"))
        assert stat.S_IMODE((root / "user.md").stat().st_mode) == 0o644

    def test_symlinked_topic_is_skipped(self, tmp_path, tmp_path_factory):
        real = tmp_path_factory.mktemp("elsewhere") / "user.md"
        real.write_text(note("", "see [[Beta X]]\n", slug="user"))
        root = mk(tmp_path, {"beta_x.md": note("", "b\n", slug="beta_x")})
        (root / "user.md").symlink_to(real)
        written, skipped, _ = dl.apply_fixes(dl.Store(root), tmp_path_factory.mktemp("bak"))
        assert skipped[0].startswith("user.md (symlink") and "[[Beta X]]" in real.read_text()

    def test_each_run_gets_its_own_backup_dir(self, tmp_path, tmp_path_factory):
        root = mk(tmp_path, {"beta_x.md": note("", "b\n", slug="beta_x"),
                             "user.md": note("", "see [[Beta X]]\n", slug="user")})
        bak = tmp_path_factory.mktemp("bak")
        _, _, d1 = dl.apply_fixes(dl.Store(root), bak)
        (root / "user.md").write_text(note("", "see [[Beta X]] again\n", slug="user"))
        _, _, d2 = dl.apply_fixes(dl.Store(root), bak)
        assert d1 != d2 and (d1 / "user.md").exists() and (d2 / "user.md").exists()


class TestExitCodeEdges:
    def test_non_utf8_is_exit_2(self, tmp_path):
        mk(tmp_path, {"bad.md": b"\xff\xfe broken"})
        r = subprocess.run([sys.executable, SCRIPT, str(tmp_path)], capture_output=True, text=True)
        assert r.returncode == 2 and "UNREADABLE" in r.stderr

    def test_backup_dir_that_is_a_file_is_usage_exit_2(self, store, tmp_path_factory):
        f = tmp_path_factory.mktemp("x") / "afile"
        f.write_text("x")
        r = subprocess.run([sys.executable, SCRIPT, str(store), "--fix-links", "--apply",
                            "--backup-dir", str(f)], capture_output=True, text=True)
        assert r.returncode == 2 and "Traceback" not in r.stderr

    def test_apply_on_clean_after_fix_exits_0(self, tmp_path, tmp_path_factory):
        mk(tmp_path, {"beta_x.md": note("", "b\n", slug="beta_x"),
                      "user.md": note("", "see [[Beta X]]\n", slug="user")})
        r = subprocess.run([sys.executable, SCRIPT, str(tmp_path), "--fix-links", "--apply",
                            "--backup-dir", str(tmp_path_factory.mktemp("bak"))],
                           capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr

    def test_index_links_with_dot_slash_and_anchor_are_not_orphans(self, tmp_path):
        mk(tmp_path, {"MEMORY.md": "- [A](./a.md) — x\n- [B](b.md#sec) — y\n",
                      "a.md": "a\n", "b.md": "b\n"})
        assert dl.Store(tmp_path).orphans() == []


# ---- regressions from the second review pass ---------------------------------------


class TestRoundTwo:
    def test_slug_with_closing_brackets_is_never_written(self, tmp_path, tmp_path_factory):
        root = mk(tmp_path, {"brk.md": note("", "x\n", slug="x]]y"),
                             "user.md": note("", "see [[BRK]]\n", slug="user")})
        s = dl.Store(root)
        assert "[[brk]]" in dl.fixed_text(s, "user.md")      # falls back to the stem

    def test_pipe_slug_falls_back_to_the_stem(self, tmp_path):
        root = mk(tmp_path, {"piped.md": note("", "x\n", slug="pipe|name"),
                             "user.md": note("", "see [[PIPED]]\n", slug="user")})
        s = dl.Store(root)
        assert s.classify("PIPED") == ("FIXABLE", "piped.md")
        assert dl.fixed_text(s, "user.md") == note("", "see [[piped]]\n", slug="user")

    def test_every_fixable_link_is_actually_rewritten(self, store):
        s = dl.Store(store)
        for n, _s, _e, inner, kind, tgt in s.links():
            if kind == "FIXABLE":
                assert f"[[{inner}]]" not in dl.fixed_text(s, n) or \
                    dl.fixed_text(s, n).count(f"[[{inner}]]") < s.text[n].count(f"[[{inner}]]")

    def test_code_span_scan_is_linear(self):
        import time
        t0 = time.monotonic()
        dl.mask_code("```" + " ``" * 400 + "\n")
        assert time.monotonic() - t0 < 1.0

    def test_longer_inner_run_stays_inside_the_span(self):
        assert found("`` a ``` [[x]] ``\n[[real]]\n") == ["real"]

    def test_hard_linked_topic_is_skipped(self, tmp_path, tmp_path_factory):
        root = mk(tmp_path, {"beta_x.md": note("", "b\n", slug="beta_x"),
                             "user.md": note("", "see [[Beta X]]\n", slug="user")})
        other = tmp_path_factory.mktemp("o") / "twin.md"
        os.link(root / "user.md", other)
        written, skipped, _ = dl.apply_fixes(dl.Store(root), tmp_path_factory.mktemp("bak"))
        assert written == [] and skipped[0].startswith("user.md (")
        assert "[[Beta X]]" in other.read_text()
