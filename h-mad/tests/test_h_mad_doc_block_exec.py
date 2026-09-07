"""Task 1 RED: scanner/selection contracts and the docsections second consumer.

The module-level import intentionally gives the plan's new-symbol collection
RED. The independently runnable caller wire pin lives in test_docsections.py.
No docsections import belongs at module scope: its import-path mutant must
reach the subprocess assertion, not break collection of its own killer.
"""

from __future__ import annotations

import ast
from contextlib import contextmanager
import dataclasses
import errno
import json
import math
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "h-mad" / "scripts"
DOCSECTIONS = Path(__file__).with_name("docsections.py")
sys.path.insert(0, str(SCRIPTS))
import h_mad_doc_block_exec as dbe  # noqa: E402


@pytest.fixture
def hostile():
    """Obtain actual agent-shaped data from the prescribed hostile stub knob."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("HMAD_STUB_")}
    env["HMAD_STUB_HOSTILE"] = "all"
    result = subprocess.run(
        ["bash", str(Path(__file__).with_name("stubs") / "orca"), "worktree", "set"],
        env=env, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, f"hostile stub failed: {result.stderr}"
    payload = json.loads(result.stdout)["result"]["worktree"]["comment"]
    assert all(value in payload for value in ("*", "[", "\n", "\t", "⟦/h-mad⟧"))
    return payload


def write_doc(tmp_path, text, name="fixture [*] ⟦∕h-mad⟧.md"):
    path = tmp_path / name
    path.write_bytes(text.encode("utf-8"))
    return path


def scan(tmp_path, body, heading="## Section"):
    return dbe.extract(write_doc(tmp_path, body), heading)


def tagged(body="echo wanted\n", info="hmad:exec"):
    return f"```bash {info}\n{body}```\n"


def test_tagged_fence_under_heading_is_extracted(tmp_path, hostile):
    title = hostile.splitlines()[0]
    body = hostile + "\n"
    doc = f"## {title}\n```bash\nunselected\n```\n" + tagged(body)
    blocks = scan(tmp_path, doc, f"## {title}")
    assert len(blocks) == 1, "extract must select only tagged bash fences"
    block = blocks[0]
    assert (block.text, block.shell, block.lineno) == (body, "strict", 5)
    assert block.info.strip() == "hmad:exec", "Block.info excludes the language word"


def test_untagged_fence_is_not_a_candidate(tmp_path):
    doc = "## Section\n```bash\nignored\n```\n```python hmad:exec\nignored\n```\n"
    assert scan(tmp_path, doc) == [], "only tagged backtick bash openers are candidates"


def test_two_tagged_blocks_without_index_are_ambiguous(tmp_path):
    blocks = scan(tmp_path, "## Section\n" + tagged("one\n") + tagged("two\n"))
    assert len(blocks) == 2, "extract returns every candidate without count policy"
    with pytest.raises(dbe.AmbiguousBlock) as error:
        dbe.select(blocks)
    assert error.value.n == 2, "select must report the ambiguous candidate count"


def test_index_selects_and_past_end_is_not_found():
    blocks = [dbe.Block("one", "strict", 1, "hmad:exec"), dbe.Block("two", "plain", 4, "hmad:exec")]
    assert dbe.select(blocks, 2) is blocks[1], "index is one-based and returns the original Block"
    assert dbe.select(blocks[:1]) is blocks[0]
    with pytest.raises(dbe.BlockNotFound):
        dbe.select(blocks, 3)


def test_absent_heading_and_empty_selection(tmp_path):
    assert scan(tmp_path, "## Elsewhere\n" + tagged()) == [], "missing heading is an empty scan"
    for index in (None, 1):
        with pytest.raises(dbe.BlockNotFound):
            dbe.select([], index)


def test_section_owns_deeper_headings(tmp_path):
    for boundary in ("## Next", "# Next"):
        doc = "## Section\n### Child\n" + tagged("owned\n") + boundary + "\n" + tagged("outside\n")
        assert [b.text for b in scan(tmp_path, doc)] == ["owned\n"], (
            "a section owns deeper headings and stops at same-or-shallower headings"
        )


def test_find_heading_accepts_full_and_bare_forms():
    text = "intro\n## Text\nbody\n"
    expected = (len("intro\n## Text\n"), 2)
    assert dbe.find_heading(text, "## Text") == expected
    assert dbe.find_heading(text, "Text") == expected
    text = "### Text\nbody\n"
    assert dbe.find_heading(text, "## Text") is None, "full-form heading level must match"
    assert dbe.find_heading(text, "Text") == (len("### Text\n"), 3)
    assert dbe.find_heading("   ## Text\n", "   ## Text") == (11, 2)


def test_full_form_request_accepts_tab_and_eol():
    for line in ("##\tText", "##"):
        assert dbe.find_heading(line + "\nbody", line) == (len(line) + 1, 2), (
            "full-form requests must share the scanner's tab and end-of-line ATX arms"
        )


def test_heading_form_precedence_full_wins():
    text = "### ## Text\nfirst\n## Text\nsecond\n"
    try:
        full = dbe.find_heading(text, "## Text")
        nested_title = dbe.find_heading(text, "### ## Text")
    except dbe.AmbiguousHeading as error:
        pytest.fail(f"full form must win rather than unioning bare matches: {error!r}")
    assert full == (text.index("second"), 2)
    assert nested_title == (text.index("first"), 3)
    assert dbe.find_heading("### ## Text\n", "## Text") is None


def test_closing_hash_run_does_not_change_heading_identity():
    for closing in (" ##", "\t##"):
        text = "## Text" + closing + "  \nbody\n"
        end = text.index("body")
        for request in ("Text", "## Text", "## Text" + closing):
            assert dbe.find_heading(text, request) == (end, 2), "normalize both request and event text"
        doubled = text + "## Text\n"
        for request in ("Text", "## Text"):
            with pytest.raises(dbe.AmbiguousHeading) as error:
                dbe.find_heading(doubled, request)
            assert error.value.n == 2, "closing hashes cannot hide a duplicate heading"
    assert dbe.find_heading("## Text##\n", "Text##") == (10, 2), "attached hashes remain title text"


def test_adjacent_heading_bounds_the_section(tmp_path):
    text = "## A\n## B\n" + tagged()
    start, level = dbe.find_heading(text, "## A")
    assert dbe.fence_aware_end(text, start, level) == start, "boundary includes event.start == start"
    assert scan(tmp_path, text, "## A") == [], "adjacent heading's block belongs to B"


def test_heading_lookalikes_are_not_headings(tmp_path):
    lookalikes = ["#hashtag", "#######", "    ## x"] + [" " * n + "\t## x" for n in range(4)]
    text = "## Section\n" + "\n".join(lookalikes) + "\n" + tagged("owned\n")
    assert [b.text for b in scan(tmp_path, text)] == ["owned\n"], "lookalikes cannot end a section"
    for request in ("# hashtag", "## x", "#######"):
        assert dbe.find_heading(text, request) is None, f"prose is not a heading: {request!r}"
    assert dbe.find_heading("   ## x\n", "## x") == (8, 2), "three spaces still allow ATX"


def test_titleless_heading_is_a_new_only_member(tmp_path):
    path = write_doc(tmp_path, "before\n#\nafter\n", "titleless.md")
    text = path.read_text(encoding="utf-8")
    old = re.compile(r"^(?P<marks>#+) (?P<title>.*?)\s*$")
    old_lines = {n for n, line in enumerate(text.splitlines(), 1) if old.match(line)}
    headings = [e for e in dbe._fence_events(text) if e.kind == "heading"]
    titleless = sum(e.text == "" for e in headings)
    new_only = {e.lineno for e in headings} - old_lines
    assert (titleless, len(new_only)) == (1, 1), "fixture must prove titleless=1 new_only=1"
    assert [(e.lineno, e.level, e.text) for e in headings] == [(2, 1, "")]
    assert dbe.find_heading(text, "#") == (9, 1)


def test_requested_heading_quoted_inside_a_fence_is_not_a_section_start(tmp_path):
    text = "````markdown\n## Section\n" + tagged("quoted\n") + "````\n## Section\n" + tagged("real\n")
    assert [b.text for b in scan(tmp_path, text)] == ["real\n"], "find_heading must use scanner heading events"


def test_quoted_tag_inside_longer_fence_is_not_an_opener(tmp_path):
    for closing in ("````\n", ""):
        # A too-short closer BEFORE the tagged opener exposes a false candidate
        # when run length is ignored; quoting only the opener would miss it.
        text = "## Section\n````markdown\n```\n" + tagged("quoted\n") + closing
        assert scan(tmp_path, text) == [], "shorter backticks inside a longer fence are body"


def test_tag_quoted_inside_a_tilde_fence_is_not_an_opener(tmp_path):
    text = "## Section\n~~~markdown\n" + tagged("quoted\n") + "~~~\n"
    assert scan(tmp_path, text) == [], "tilde fence state protects quoted backtick tags"
    assert scan(tmp_path, "## Section\n~~~bash hmad:exec\nignored\n~~~\n") == [], (
        "a tagged tilde bash fence is not itself an executable candidate"
    )


def test_indented_literal_tag_is_not_a_candidate(tmp_path):
    for indent in ("    ", "\t", " \t", "  \t", "   \t"):
        text = "## Section\n" + indent + "```bash hmad:exec\nignored\n" + indent + "```\n"
        assert scan(tmp_path, text) == [], "four columns of opener indentation mean literal code"


def test_backtick_in_info_string_is_not_an_opener(tmp_path):
    text = "## Section\n```bash hmad:exec `x`\nprose\n```\n# fenced\n"
    assert scan(tmp_path, text) == [], "backtick-containing info is prose, never BadInfoString"
    assert [e.kind for e in dbe._fence_events(text)] == ["heading", "prose", "prose", "open", "body"]


def test_closer_with_trailing_text_does_not_close(tmp_path):
    text = "## Section\n```markdown\n```trailing\n" + tagged("quoted\n") + "```\n"
    assert scan(tmp_path, text) == [], "a closer with trailing text cannot expose a quoted tag"


def test_indented_closer_does_not_close(tmp_path):
    text = "## Section\n```bash hmad:exec\none\n    ```\n# body\n```\n"
    assert [b.text for b in scan(tmp_path, text)] == ["one\n    ```\n# body\n"], (
        "a four-space marker inside a fence remains body text"
    )


def test_indented_fence_body_is_deindented(tmp_path):
    for indent in (1, 2, 3):
        for newline in ("\n", "\r\n"):
            pad = " " * indent
            lines = ["## Section", pad + "```bash hmad:exec", pad + "full", " less", "bare", pad + "  extra", "\ttab", "   ````\t "]
            text = newline.join(lines) + newline
            expected = newline.join(["full", "less", "bare", "  extra", "\ttab"]) + newline
            assert [b.text for b in scan(tmp_path, text)] == [expected], (
                "strip at most opener spaces per body line and preserve newline spelling"
            )


def test_duplicate_headings_refuse(tmp_path):
    text = "### Repeated\n" + tagged("first\n") + "### Repeated\n" + tagged("second\n")
    with pytest.raises(dbe.AmbiguousHeading) as error:
        scan(tmp_path, text, "### Repeated")
    assert error.value.n == 2, "duplicate full-form headings must refuse instead of choosing first"


def test_bare_form_duplicate_headings_refuse():
    with pytest.raises(dbe.AmbiguousHeading) as error:
        dbe.find_heading("## Text\n### Text\n", "Text")
    assert error.value.n == 2, "bare-form duplicates count matches across levels"


def test_bounder_ignores_a_heading_inside_a_tilde_fence():
    text = "## Section\n~~~\n# body\n~~~\nkept\n## Next\n"
    assert dbe.fence_aware_end(text, len("## Section\n"), 2) == text.index("## Next"), (
        "fence_aware_end must track tilde fences"
    )


def test_bounder_ignores_an_indented_literal_fence():
    text = "## Section\n    ```\n## Next\n"
    assert dbe.fence_aware_end(text, len("## Section\n"), 2) == text.index("## Next"), (
        "an indented literal cannot open a fence and hide the boundary"
    )


def test_bounder_from_an_offset_inside_a_fence():
    text = "## Section\n```bash\nanchor\n# body\n```\nkept\n## Next\n"
    assert dbe.fence_aware_end(text, text.index("anchor") + 2, 2) == text.index("## Next"), (
        "bounder must build fence state before an interior start offset"
    )


def test_bounder_offset_after_a_marker_run_on_a_non_closing_line():
    text = "## Section\n```bash\n```trailing\n# body\n```\n## Next\n"
    start = text.index("```trailing") + 3
    assert dbe.fence_aware_end(text, start, 2) == text.index("## Next"), (
        "prefix state must scan the complete marker line, not text[:start]"
    )


def test_bounder_skips_a_heading_that_started_before_midline_offset():
    text = "## Before\nbody\n## Next\n"
    assert dbe.fence_aware_end(text, 3, 2) == text.index("## Next"), (
        "only heading events whose start >= offset can bound the section"
    )
    assert dbe.fence_aware_end(text, len(text), 2) == len(text)


def test_fence_events_trace_on_every_hostile_fixture():
    # Expected classifications are literal fixture data, not a second scanner.
    # All lines pin offsets, lineno, kind, candidate, level and heading text,
    # plus opener metadata (neutral on every non-open event per decision D1).
    fixtures = [
        ("balanced-four", "## T\n````markdown\n```bash hmad:exec\n```\n````\n", ["heading", "open", "body", "body", "close"], {2: ("`", 4, 0, "markdown", False)}),
        ("unbalanced-four", "## T\n````markdown\n```\n# body", ["heading", "open", "body", "body"], {2: ("`", 4, 0, "markdown", False)}),
        ("tilde-quoted", "~~~markdown\n```bash hmad:exec\n```\n~~~\n", ["open", "body", "body", "close"], {1: ("~", 3, 0, "markdown", False)}),
        ("backtick-info", "```bash hmad:exec `x`\n```\n# body\n", ["prose", "open", "body"], {2: ("`", 3, 0, "", False)}),
        ("indented-literal", "    ```bash hmad:exec\n\t```bash hmad:exec\n## T\n", ["prose", "prose", "heading"], {}),
        ("trailing-closer", "```bash hmad:exec\n```trailing\n# body\n```\n", ["open", "body", "body", "close"], {1: ("`", 3, 0, "bash hmad:exec", True)}),
        ("offset-inside", "## T\n  ```bash hmad:exec\n  anchor\n# body\n  ```\n", ["heading", "open", "body", "body", "close"], {2: ("`", 3, 2, "bash hmad:exec", True)}),
        ("wrong-marker", "```bash hmad:exec\n~~~\n   ````\t \nprose\n", ["open", "body", "close", "prose"], {1: ("`", 3, 0, "bash hmad:exec", True)}),
    ]
    for name, source, kinds, openers in fixtures:
        for newline in ("\n", "\r\n"):
            text = source.replace("\n", newline)
            events = list(dbe._fence_events(text))
            assert [e.kind for e in events] == kinds, f"scanner trace kind mismatch: {name}/{newline!r}"
            cursor = 0
            for lineno, (line, event) in enumerate(zip(text.splitlines(keepends=True), events), 1):
                assert (event.lineno, event.start, event.end) == (lineno, cursor, cursor + len(line)), (
                    f"scanner owns exact character offsets: {name}, line {lineno}"
                )
                cursor += len(line)
                assert event.level == (2 if event.kind == "heading" else 0)
                assert event.text == ("T" if event.kind == "heading" else "")
                assert event.candidate is openers.get(lineno, (None, 0, 0, "", False))[4]
                assert (event.marker, event.run, event.indent, event.info, event.candidate) == openers.get(
                    lineno, (None, 0, 0, "", False)
                ), f"scanner opener metadata must be neutral on non-open events: {name}, line {lineno}"
            assert cursor == len(text), "one scanner event must account for every complete or final partial line"


def recognition_sites(source):
    """AST-scoped guard for the stated literal/regex/toggle recognition family.

    Docstrings and event-field reads are not recognition. Nested parser helpers
    belong to their containing top-level function. Computed/obfuscated grammars
    are outside this syntactic guard; behavioural fixtures cover those inputs.
    """
    tree = ast.parse(source)
    sites = set()

    def inspect(node, owner):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and owner == "<module>":
            owner = node.name
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return  # docstrings are explanations, not grammar recognition
        if isinstance(node, ast.Name) and node.id == "in_fence":
            sites.add(owner)
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            value = node.value
            if "```" in value or "~~~" in value or re.search(r"[`~#][^\n]{0,12}\{[136],", value):
                sites.add(owner)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "startswith":
            if any(isinstance(arg, ast.Constant) and isinstance(arg.value, str) and arg.value.startswith("#") for arg in node.args):
                sites.add(owner)
        for child in ast.iter_child_nodes(node):
            inspect(child, owner)

    inspect(tree, "<module>")
    return sites


def test_extract_has_no_fence_state_of_its_own():
    source = (SCRIPTS / "h_mad_doc_block_exec.py").read_text(encoding="utf-8")
    assert recognition_sites(source) == {"_fence_events"}, (
        "marker-run and ATX recognition must live only in _fence_events"
    )
    extract = next(node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and node.name == "extract")
    attrs = {node.attr for node in ast.walk(extract) if isinstance(node, ast.Attribute)}
    assert "candidate" in attrs and "marker" not in attrs, "extract selects scanner candidate verdicts, never marker characters"


def test_extract_uses_public_heading_lookup(tmp_path, monkeypatch):
    text = "## Original\n" + tagged("first\n") + "## Actual\n" + tagged("second\n")
    calls = []
    def redirected(document, heading):
        calls.append((document, heading))
        return text.index("```bash", text.index("## Actual")), 2
    monkeypatch.setattr(dbe, "find_heading", redirected)
    assert [b.text for b in scan(tmp_path, text, "## Original")] == ["second\n"], (
        "extract must use the public heading lookup's returned start"
    )
    assert calls == [(text, "## Original")]


def test_titled_section_ignores_a_heading_inside_a_fence():
    import docsections
    text = "```markdown\n## Section\nquoted\n```\n## Section\nreal\n## Next\noutside\n"
    assert docsections.titled_section(text, "Section") == "real\n", "titled_section must ignore the fenced heading copy"


def test_docsections_has_no_second_bounder():
    source = DOCSECTIONS.read_text(encoding="utf-8")
    names = {node.name for node in ast.walk(ast.parse(source)) if isinstance(node, ast.FunctionDef)}
    assert "_fence_aware_end" not in names, "docsections must delete its private second bounder"
    assert recognition_sites(source) == set(), "docsections must contain no marker-run scanner"


def test_docsections_imports_when_collected_alone():
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", "h-mad/tests/test_docsections.py"],
        cwd=REPO_ROOT, env=env, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, f"docsections must import when collected alone:\n{result.stdout}\n{result.stderr}"
    assert "test_docsections_delegates_to_the_authoritative_bounder" in result.stdout


def test_docsections_imports_from_an_unrelated_cwd(tmp_path):
    result = subprocess.run(
        [sys.executable, "-c", "import docsections"], cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(DOCSECTIONS.parent)},
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, f"docsections must resolve scripts from __file__, independent of cwd:\n{result.stderr}"


def test_docsections_unbalanced_four_backtick_fence():
    import docsections
    text = "## Section\n````bash\n```\n# comment\nstill owned\n"
    assert docsections.titled_section(text, "Section") == text[len("## Section\n"):], (
        "a triple backtick cannot close an unbalanced four-backtick fence"
    )


def test_index_zero_refuses():
    class NoLookup:
        def __len__(self):
            pytest.fail("BadIndex validation must precede even a candidate-count lookup")
        def __getitem__(self, index):
            pytest.fail("BadIndex validation must precede item lookup")
        def __iter__(self):
            pytest.fail("BadIndex validation must precede iteration")
    for index in (0, -1):
        for blocks in ([], NoLookup()):
            with pytest.raises(dbe.BadIndex) as error:
                dbe.select(blocks, index)
            assert error.value.n == index, "BadIndex must carry the original index"


def test_unknown_info_key_refuses(tmp_path):
    for token in ("shell=fish", "mode=x", "hmad:exec-extra"):
        with pytest.raises(dbe.BadInfoString) as error:
            scan(tmp_path, "## Section\n" + tagged(info="hmad:exec " + token))
        assert error.value.key == token, "BadInfoString must name the offending token"


def test_duplicate_info_tokens_refuse(tmp_path):
    for info, repeated in (("hmad:exec hmad:exec", "hmad:exec"), ("hmad:exec shell=strict shell=plain", "shell=plain"), ("hmad:exec shell=plain shell=plain", "shell=plain")):
        with pytest.raises(dbe.BadInfoString) as error:
            scan(tmp_path, "## Section\n" + tagged(info=info))
        assert error.value.key == repeated, "duplicate recognised token must name the repeated spelling"


def test_untagged_fence_info_string_is_never_inspected(tmp_path):
    text = "## Section\n```bash --frozen shell=fish mode=x\nignored\n```\n"
    assert scan(tmp_path, text) == [], "untagged info must not be validated"


def test_shell_modes_and_whitespace_tokens(tmp_path):
    for info, mode in (("hmad:exec", "strict"), ("shell=strict\thmad:exec", "strict"), ("hmad:exec\t shell=plain", "plain")):
        blocks = scan(tmp_path, "## Section\n" + tagged(info=info))
        assert len(blocks) == 1 and blocks[0].shell == mode, "recognised whitespace-separated shell mode must propagate"


def test_invalid_utf8_document_is_unreadable(tmp_path):
    path = tmp_path / "invalid.md"
    path.write_bytes(b"## Section\n\xff")
    with pytest.raises(dbe.DocUnreadable):
        dbe.extract(path, "## Section")


def test_oserror_document_is_unreadable(tmp_path):
    for path in (tmp_path / "absent.md", tmp_path):
        with pytest.raises(dbe.DocUnreadable):
            dbe.extract(path, "## Section")


def test_extract_accepts_string_paths_and_preserves_final_body(tmp_path):
    path = write_doc(tmp_path, "## Section\n```bash hmad:exec\nno final newline")
    block = dbe.extract(str(path), "## Section")[0]
    assert block.text == "no final newline", "str is a path and EOF body gains no synthetic newline"


def test_block_is_frozen_and_keeps_all_fields(hostile):
    block = dbe.Block(hostile, "plain", 17, " hmad:exec\tshell=plain")
    assert dataclasses.is_dataclass(block)
    assert dataclasses.asdict(block) == dict(text=hostile, shell="plain", lineno=17, info=" hmad:exec\tshell=plain")
    with pytest.raises(dataclasses.FrozenInstanceError):
        block.text = "changed"


def test_exception_hierarchy_and_star_exports_are_complete(hostile):
    errors = {
        "DocBlockError", "DocUnreadable", "BadInfoString", "BlockNotFound", "AmbiguousBlock", "AmbiguousHeading", "BadIndex",
        "BadSubstArg", "MissingSubstitution", "OverlappingSubstitution", "BadTimeout", "BlockTimeout", "CleanupFailed", "LaunchFailed",
        "StreamPathUnwritable", "StreamPathsAlias", "PreambleUnreadable", "StreamWriteFailed", "StreamCloseFailed", "BadArgs",
    }
    required = errors | {"Block", "extract", "select", "fence_aware_end", "find_heading"}
    exported = {}
    exec("from h_mad_doc_block_exec import *", exported)
    assert required <= set(dbe.__all__), "Task 1 must export all 20 exceptions and all five public API names"
    assert len(dbe.__all__) == len(set(dbe.__all__)), "exports must have no duplicate names"
    for name in required:
        assert exported[name] is getattr(dbe, name), f"star import must resolve {name}"
    for name in errors - {"DocBlockError"}:
        assert issubclass(getattr(dbe, name), dbe.DocBlockError), f"{name} must share the public error base"
    assert issubclass(dbe.DocBlockError, Exception)
    err = OSError(hostile)
    pairs = [("overlap", "a", "ab", None), ("intersect", "ab", "bc", 1)]
    cases = [
        ("BadInfoString", (hostile,), {"key": hostile}),
        ("AmbiguousBlock", (2,), {"n": 2}), ("AmbiguousHeading", (2,), {"n": 2}),
        ("BadIndex", (-1,), {"n": -1}), ("BadSubstArg", (hostile,), {"raw": hostile, "duplicate_key": None}),
        ("BadSubstArg", (hostile, "[key]*"), {"raw": hostile, "duplicate_key": "[key]*"}),
        ("MissingSubstitution", ([hostile, "first"],), {"keys": [hostile, "first"]}),
        ("OverlappingSubstitution", (pairs,), {"pairs": pairs}),
        ("BadTimeout", (hostile,), {"value": hostile}), ("BlockTimeout", (1.5,), {"seconds": 1.5}),
        ("CleanupFailed", (hostile, err), {"path": hostile, "cleanup_error": err}),
        ("CleanupFailed", (hostile, None), {"path": hostile, "cleanup_error": None}),
        ("LaunchFailed", ("spawn", err), {"stage": "spawn", "err": err, "pgid": None}),
        ("LaunchFailed", ("reap", err, 123), {"stage": "reap", "err": err, "pgid": 123}),
        ("StreamPathUnwritable", (), {"leftover": None}), ("StreamPathUnwritable", (hostile,), {"leftover": hostile}),
        ("StreamWriteFailed", (["stdout"], "stderr", [], hostile), {"written": ["stdout"], "failed": "stderr", "skipped": [], "verify": hostile}),
        ("StreamWriteFailed", ([], "stdout", ["stderr"]), {"written": [], "failed": "stdout", "skipped": ["stderr"], "verify": None}),
        ("StreamCloseFailed", ("stderr", err), {"stream": "stderr", "close_error": err}),
        ("BadArgs", (hostile,), {"message": hostile}),
    ]
    for name, args, fields in cases:
        error = getattr(dbe, name)(*args)
        for field, expected in fields.items():
            assert getattr(error, field) == expected, f"{name}.{field} must preserve constructor data"
    for name in ("DocBlockError", "DocUnreadable", "BlockNotFound", "StreamPathsAlias", "PreambleUnreadable"):
        assert str(getattr(dbe, name)(hostile)) == hostile, f"{name} retains normal Exception constructor behaviour"


# Task 2 RED: substitute is a new symbol; every call also pins its GREEN contract.
def test_path_substitution_replaces_the_key(hostile):
    key = "~/.claude/skills/h-mad/scripts/h_mad_audit_gate.py"
    block = dbe.Block(f"{hostile}\npython {key}\n", "plain", 17, " hmad:exec\tshell=plain")
    original = dataclasses.replace(block)
    result, counts = dbe.substitute(block, {key: "/tmp/x y/gate.py"})
    assert result == dataclasses.replace(block, text=f"{hostile}\npython /tmp/x y/gate.py\n")
    assert result is not block, "substitute must return a new Block preserving metadata"
    assert block == original, "substitute must not mutate the input Block"
    assert counts == {key: 1}, "the path must be replaced exactly once"
    assert "substitute" in dbe.__all__


def test_absent_key_refuses(hostile):
    block = dbe.Block("no matching token", "strict", 1, "hmad:exec")
    with pytest.raises(dbe.MissingSubstitution) as error:
        dbe.substitute(block, {hostile: "replacement"})
    assert error.value.keys == [hostile], "missing-key diagnostics preserve the literal hostile key"


def test_empty_substitution_map_is_a_no_op(hostile, monkeypatch):
    block = dbe.Block(hostile, "plain", 19, "hmad:exec shell=plain")
    calls = []

    def forbidden_regex(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("empty substitution maps must return before building or running regexes")

    # Scope patches to the API call so pytest's own regex use is unaffected.
    with monkeypatch.context() as patch:
        for name in ("compile", "escape", "finditer", "sub"):
            patch.setattr(re, name, forbidden_regex)
        result, counts = dbe.substitute(block, {})
    assert result == block and result is not block, "even a no-op must copy the Block"
    assert counts == {} and calls == [], "an empty map must short-circuit all regex work"


def test_two_missing_keys_are_listed_in_map_order(hostile):
    block = dbe.Block("neither token occurs", "strict", 1, "hmad:exec")
    with pytest.raises(dbe.MissingSubstitution) as error:
        dbe.substitute(block, {"B": hostile, "A": "2"})
    assert error.value.keys == ["B", "A"], "missing keys retain map insertion order, not sorted order"


def test_metacharacter_key_is_literal(hostile):
    block = dbe.Block("a.[b]* | axbbb | aZ | a.[b]", "strict", 3, "hmad:exec")
    result, counts = dbe.substitute(block, {"a.[b]*": hostile})
    assert result == dataclasses.replace(block, text=hostile + " | axbbb | aZ | a.[b]")
    assert counts == {"a.[b]*": 1}, "regex metacharacters in keys must match literally"


def test_multi_occurrence_count_equals_replacements(hostile):
    block = dbe.Block("TOKEN / TOKEN\nTOKEN", "strict", 4, "hmad:exec")
    result, counts = dbe.substitute(block, {"TOKEN": hostile})
    assert result.text == f"{hostile} / {hostile}\n{hostile}"
    assert counts == {"TOKEN": 3}
    assert result.text.count(hostile) == 3, "reported count must equal the replacements performed"
    # Overlapping occurrences of the SAME key remain valid; str.count agrees
    # with the simultaneous replacement pass's non-overlapping replacements.
    result, counts = dbe.substitute(dataclasses.replace(block, text="aaa"), {"aa": "Z"})
    assert (result.text, counts) == ("Za", {"aa": 1})


def test_value_containing_another_key_is_not_rescanned(hostile):
    block = dbe.Block("A B", "strict", 1, "hmad:exec")
    for subs in ({"A": "B", "B": "C"}, {"B": "C", "A": "B"}):
        result, counts = dbe.substitute(block, subs)
        assert (result.text, counts) == ("B C", {"A": 1, "B": 1}), (
            "replacement values must not be rescanned, regardless of map order"
        )
    for subs in ({"A": "B" + hostile, "B": "C"}, {"B": "C", "A": "B" + hostile}):
        result, counts = dbe.substitute(block, subs)
        assert (result.text, counts) == ("B" + hostile + " C", {"A": 1, "B": 1})
    assert block.text == "A B"


def test_overlapping_keys_refuse(hostile):
    block = dbe.Block("", "strict", 1, "hmad:exec")
    expected = [("overlap", "a", "ab", None), ("overlap", "a", "abc", None), ("overlap", "ab", "abc", None)]
    for keys in (("a", "ab", "abc"), ("abc", "ab", "a")):
        with pytest.raises(dbe.OverlappingSubstitution) as error:
            dbe.substitute(block, dict.fromkeys(keys, hostile))
        assert error.value.pairs == expected, "map-static substring overlap outranks missing keys"
        assert isinstance(error.value.pairs, list)
        assert {key for _, a, b, _ in error.value.pairs for key in (a, b)} == {"a", "ab", "abc"}


def test_substitute_refuses_intersecting_spans(hostile):
    for subs in ({"ab": "X", "bc": "Y"}, {"bc": "Y", "ab": "X"}):
        for text in ("abc", "abc---abc"):
            block = dbe.Block(text, "plain", 7, "hmad:exec shell=plain")
            original = dataclasses.replace(block)
            with pytest.raises(dbe.OverlappingSubstitution) as error:
                dbe.substitute(block, subs)
            assert error.value.pairs == [("intersect", "ab", "bc", 1)], (
                "one lexically ordered pair carries the minimum shared index across all spans"
            )
            assert {key for _, a, b, _ in error.value.pairs for key in (a, b)} == {"ab", "bc"}
            assert block == original, "refusal must leave the original Block unchanged"
        block = dbe.Block("ab bc ab bc", "strict", 1, "hmad:exec")
        result, counts = dbe.substitute(block, subs)
        assert (result.text, counts) == ("X Y X Y", {"ab": 2, "bc": 2}), (
            "different keys with disjoint spans must substitute successfully"
        )
    with pytest.raises(dbe.OverlappingSubstitution) as error:
        dbe.substitute(dataclasses.replace(block, text="abc"), {"missing": hostile, "ab": "X", "bc": "Y"})
    assert error.value.pairs == [("intersect", "ab", "bc", 1)], "intersection outranks missing keys"
    # Both predicates contribute to one tagged list, even when a substring
    # pair is also present; intersection ordering is by offset, then keys.
    with pytest.raises(dbe.OverlappingSubstitution) as error:
        dbe.substitute(dataclasses.replace(block, text="xyz abc"), {"bc": "Y", "yz": "Q", "a": hostile, "xy": "P", "ab": "X"})
    assert error.value.pairs == [
        ("overlap", "a", "ab", None),
        ("intersect", "xy", "yz", 1),
        ("intersect", "a", "ab", 4),
        ("intersect", "ab", "bc", 5),
    ], "substring and span predicates must both run before refusing"


def test_substitute_refuses_overlapping_occurrences_of_one_key(hostile):
    block = dbe.Block("aaab", "strict", 1, "hmad:exec")
    with pytest.raises(dbe.OverlappingSubstitution) as error:
        dbe.substitute(block, {"aa": hostile, "ab": "Y"})
    assert error.value.pairs == [("intersect", "aa", "ab", 2)], (
        "lookahead must see aa at [1, 3), which shares index 2 with ab"
    )
    assert block.text == "aaab"


def test_empty_key_is_refused_by_the_api(hostile):
    block = dbe.Block(hostile, "strict", 1, "hmad:exec")
    for subs in ({"": "v"}, {"missing": hostile, "": "v", "a": "X", "ab": "Y"}):
        with pytest.raises(dbe.BadSubstArg) as error:
            dbe.substitute(block, subs)
        assert error.value.raw == "", "empty-key validation precedes overlaps and missing-key checks"


def test_empty_substitution_key_validation_routes_api_and_cli_through_one_predicate(tmp_path, monkeypatch):
    class PredicateCalled(Exception):
        pass

    calls = []

    def predicate(key):
        calls.append(key)
        raise PredicateCalled

    monkeypatch.setattr(dbe, "_is_valid_substitution_key", predicate)
    with pytest.raises(PredicateCalled):
        dbe.substitute(dbe.Block("true\n", "strict", 1, "hmad:exec"), {"": "v"})
    doc = write_doc(tmp_path, "## Section\n" + tagged("true\n"))
    with pytest.raises(PredicateCalled):
        dbe.main([str(doc), "--heading", "## Section", "--subst", "=V"])
    assert calls == ["", ""], "API and CLI empty-key validation must delegate to the shared predicate"


# Task 3 RED: execution and bounded reclamation (all behavioural calls use run_block).


def execution_block(text, shell="strict"):
    return dbe.Block(text, shell, 1, "hmad:exec")


@pytest.fixture
def recording_spawn(monkeypatch):
    real_popen = subprocess.Popen
    records = []

    def record(*args, **kwargs):
        entry = {"argv": args[0], "cwd": kwargs.get("cwd"), "proc": None}
        records.append(entry)
        entry["proc"] = real_popen(*args, **kwargs)
        return entry["proc"]

    monkeypatch.setattr(dbe.subprocess, "Popen", record)
    return records


def assert_cwd_gone(records):
    assert len(records) == 1, "run_block must launch exactly one bash"
    assert records[0]["cwd"] is not None, "run_block must supply its private cwd"
    assert not os.path.lexists(records[0]["cwd"]), "private cwd must be removed"


def test_block_runs_in_the_temp_cwd(tmp_path):
    result = dbe.run_block(execution_block("pwd"))
    cwd = Path(result.stdout.strip())
    assert cwd.resolve() not in (REPO_ROOT.resolve(), tmp_path.resolve())
    assert not cwd.exists(), "reported execution directory must be removed"
    assert isinstance(result, dbe.RunResult)
    assert result.shell == "strict"
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.rc = 99
    assert {"RunResult", "run_block"} <= set(dbe.__all__)


def test_block_leaves_the_working_tree_untouched(hostile):
    before = subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO_ROOT)
    result = dbe.run_block(execution_block("printf %s " + shlex.quote(hostile) + " > created-file"))
    after = subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO_ROOT)
    assert result.rc == 0
    assert after == before, "block-created files must not touch the working tree"


def test_unset_variable_fails_under_strict(monkeypatch):
    monkeypatch.delenv("UNSET_X", raising=False)
    assert dbe.run_block(execution_block("echo $UNSET_X")).rc != 0
    assert dbe.run_block(execution_block("echo $UNSET_X", "plain")).rc == 0


def test_bare_exit_in_plain_mode_returns_rc():
    result = dbe.run_block(execution_block("exit 3", "plain"))
    assert result.rc == 3 and result.shell == "plain"


def test_pipefail_strict_vs_plain():
    assert dbe.run_block(execution_block("false | true")).rc != 0
    assert dbe.run_block(execution_block("false | true", "plain")).rc == 0


def test_streams_are_separate_str(hostile):
    result = dbe.run_block(execution_block("printf %s " + shlex.quote(hostile + "é") + "; printf '\\xff' >&2"))
    assert result.rc == 0
    assert result.stdout == hostile + "é"
    assert result.stderr == "\ufffd", "invalid UTF-8 must be replaced in the separate stderr stream"


def test_preamble_binds_a_variable_and_leaves_text_unchanged(hostile):
    block = execution_block('printf %s "$VALUE"')
    original = dataclasses.replace(block)
    result = dbe.run_block(block, preamble="VALUE=" + shlex.quote(hostile) + "\n\n")
    assert result.stdout == hostile and result.rc == 0
    assert block == original, "composition must not mutate Block.text"


def test_preamble_and_substitution_compose(hostile):
    block = execution_block('printf "%s|%s" "$PREFIX" VALUE_TOKEN')
    substituted = dbe.substitute(block, {"VALUE_TOKEN": shlex.quote(hostile)})[0]
    result = dbe.run_block(substituted, preamble="PREFIX=bound")
    assert result.stdout == "bound|" + hostile and result.rc == 0


def test_preamble_without_trailing_newline_still_precedes_the_block():
    result = dbe.run_block(execution_block('printf %s "$X"'), preamble="X=separated")
    assert result.stdout == "separated" and result.rc == 0


def test_failing_preamble_is_visible_as_the_combined_rc(hostile):
    result = dbe.run_block(execution_block("echo should-not-run"),
                           preamble="printf %s " + shlex.quote(hostile) + " >&2\nfalse")
    assert result.rc != 0 and result.stderr == hostile and result.stdout == ""


def test_cwd_mode_is_0700_under_hostile_umask():
    old = os.umask(0o777)
    try:
        result = dbe.run_block(execution_block("stat -f %Lp ." if sys.platform == "darwin" else "stat -c %a ."))
    finally:
        os.umask(old)
    assert result.rc == 0 and result.stdout.strip() == "700"


def test_chmod_failure_is_a_verdict_and_removes_the_cwd(monkeypatch):
    run = dbe.run_block
    created = []
    injected = PermissionError(errno.EACCES, "chmod refused")

    def fail(path, mode):
        created.append(path)
        raise injected

    monkeypatch.setattr(dbe.os, "chmod", fail)
    with pytest.raises(dbe.LaunchFailed) as error:
        run(execution_block("true"))
    assert error.value.stage == "mkdtemp" and error.value.err is injected
    assert len(created) == 1 and not os.path.lexists(created[0])


def test_chmod_rollback_failure_is_cleanup_failed(monkeypatch):
    run = dbe.run_block
    real_rmtree = shutil.rmtree
    created = []
    chmod_error = PermissionError(errno.EACCES, "chmod refused")
    cleanup_error = PermissionError(errno.EACCES, "remove refused")

    def fail_chmod(path, mode):
        created.append(path)
        raise chmod_error

    def fail_remove(*args, **kwargs):
        raise cleanup_error

    monkeypatch.setattr(dbe.os, "chmod", fail_chmod)
    monkeypatch.setattr(dbe.shutil, "rmtree", fail_remove)
    try:
        with pytest.raises(dbe.CleanupFailed) as error:
            run(execution_block("true"))
        assert isinstance(error.value.__cause__, dbe.LaunchFailed)
        assert error.value.__cause__.stage == "mkdtemp"
        assert error.value.__cause__.err is chmod_error
    finally:
        for cwd in created:
            real_rmtree(cwd)


def forbidden_command_in_source(names):
    """Scan string values for argv tokens or shell command words."""
    tree = ast.parse(Path(dbe.__file__).read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            value = node.value
            if value in names or re.search(r"(?:^|[;&|\n])\s*(?:" + "|".join(names) + r")(?:\s|$)", value):
                return value
    return None


def test_no_mktemp_invocation_in_source():
    assert forbidden_command_in_source({"mktemp"}) is None, "external mktemp invocation is forbidden"


def test_no_timeout_invocation_in_source():
    assert forbidden_command_in_source({"timeout", "gtimeout"}) is None, "external timeout invocation is forbidden"


def permission_cleanup_case(timeout=None):
    run = dbe.run_block
    if os.geteuid() == 0:
        pytest.skip("root bypasses directory permissions")
    cwd = None
    try:
        text = "mkdir keep && chmod 000 keep" + ("; sleep 300" if timeout else "")
        with pytest.raises(dbe.CleanupFailed) as error:
            run(execution_block(text), **({"timeout": timeout} if timeout else {}))
        cwd = error.value.path
        assert isinstance(error.value.cleanup_error, PermissionError)
        if timeout:
            assert isinstance(error.value.__cause__, dbe.BlockTimeout)
    finally:
        if cwd is not None:
            os.chmod(Path(cwd) / "keep", 0o700)
            shutil.rmtree(cwd)


def test_cleanup_failure_is_reported():
    permission_cleanup_case()


def test_cleanup_failure_outranks_timeout():
    permission_cleanup_case(timeout=1)


@contextmanager
def cleanup_injection(monkeypatch, mode, *, timeout=None):
    run = dbe.run_block
    real_rmtree = shutil.rmtree
    retained = []
    injected = PermissionError(errno.EACCES, "injected cleanup failure")

    def fake(path, ignore_errors=False, **kwargs):
        retained.append(path)
        if mode == "silent":
            return
        if mode == "removed":
            real_rmtree(path)
        if mode == "honour" and ignore_errors:
            return
        raise injected

    monkeypatch.setattr(dbe.shutil, "rmtree", fake)
    try:
        with pytest.raises(dbe.CleanupFailed) as error:
            run(execution_block("sleep 300" if timeout else "echo hi"),
                **({"timeout": timeout} if timeout else {}))
        assert len(retained) == 1 and error.value.path == retained[0]
        yield error.value, injected, retained[0]
    finally:
        for cwd in retained:
            real_rmtree(cwd, ignore_errors=mode == "removed")


def test_cleanup_failure_carries_the_os_error(monkeypatch):
    with cleanup_injection(monkeypatch, "honour") as (error, injected, cwd):
        assert error.cleanup_error is injected, "rmtree errors must be retained, not ignored"
        assert os.path.lexists(cwd)


def test_cleanup_readback_catches_silent_retention(monkeypatch):
    with cleanup_injection(monkeypatch, "silent") as (error, _, cwd):
        assert error.cleanup_error is None and os.path.lexists(cwd)


def test_cleanup_error_after_successful_removal_is_still_a_failure(monkeypatch):
    with cleanup_injection(monkeypatch, "removed") as (error, injected, cwd):
        assert error.cleanup_error is injected and not os.path.lexists(cwd)


def test_cleanup_failure_outranks_timeout_injected(monkeypatch):
    with cleanup_injection(monkeypatch, "raise", timeout=1) as (error, injected, cwd):
        assert isinstance(error.__cause__, dbe.BlockTimeout)
        assert error.cleanup_error is injected and os.path.lexists(cwd)


def test_cleanup_failure_after_successful_run_is_chained(monkeypatch):
    with cleanup_injection(monkeypatch, "raise") as (error, injected, _):
        assert error.__cause__ is injected, "successful-run cleanup must explicitly chain the cleanup error"


def test_normal_run_reads_back_absent(recording_spawn):
    assert dbe.run_block(execution_block("true")).rc == 0
    assert_cwd_gone(recording_spawn)


def test_mkdtemp_failure_is_a_verdict(monkeypatch, recording_spawn):
    run = dbe.run_block
    injected = OSError(errno.ENOSPC, "no temporary space")

    def fail(*args, **kwargs):
        raise injected

    monkeypatch.setattr(dbe.tempfile, "mkdtemp", fail)
    with pytest.raises(dbe.LaunchFailed) as error:
        run(execution_block("true"))
    assert error.value.stage == "mkdtemp" and error.value.err is injected
    assert recording_spawn == []


def test_spawn_failure_is_a_verdict(tmp_path, monkeypatch, recording_spawn):
    monkeypatch.setenv("PATH", str(tmp_path))
    with pytest.raises(dbe.LaunchFailed) as error:
        dbe.run_block(execution_block("true"))
    assert error.value.stage == "spawn" and isinstance(error.value.err, OSError)
    assert recording_spawn[0]["proc"] is None
    assert_cwd_gone(recording_spawn)


def test_nul_in_document_block_is_a_launch_failure(recording_spawn):
    with pytest.raises(dbe.LaunchFailed) as error:
        dbe.run_block(execution_block("true\x00"))
    assert error.value.stage == "spawn" and isinstance(error.value.err, ValueError)
    assert recording_spawn[0]["proc"] is None, "NUL argv must fail before a child instance exists"
    assert_cwd_gone(recording_spawn)


def test_nul_in_preamble_is_a_launch_failure(recording_spawn):
    with pytest.raises(dbe.LaunchFailed) as error:
        dbe.run_block(execution_block("true"), preamble="true\x00")
    assert error.value.stage == "spawn" and isinstance(error.value.err, ValueError)
    assert recording_spawn[0]["proc"] is None
    assert_cwd_gone(recording_spawn)


def kill_if_present(kill, pid, sig=signal.SIGKILL):
    try:
        kill(pid, sig)
    except ProcessLookupError:
        pass


def assert_bounded(start):
    assert time.monotonic() - start < 1 + 2 * dbe.DRAIN_SECONDS + 2, "reclamation exceeded timeout plus two drain bounds"


def test_reap_failure_is_a_verdict_within_the_drain_bound(monkeypatch, recording_spawn):
    run = dbe.run_block
    real_killpg = os.killpg
    seen = []

    def fail(pgid, sig):
        seen.append(pgid)
        raise PermissionError(errno.EPERM, "group denied")

    monkeypatch.setattr(dbe.os, "killpg", fail)
    start = time.monotonic()
    try:
        with pytest.raises(dbe.LaunchFailed) as error:
            run(execution_block("sleep 300"), timeout=1)
        proc = recording_spawn[0]["proc"]
        assert error.value.stage == "reap" and error.value.pgid == proc.pid
        assert seen == [proc.pid]
        assert_bounded(start)
        assert_cwd_gone(recording_spawn)
    finally:
        for entry in recording_spawn:
            proc = entry["proc"]
            if proc is not None:
                kill_if_present(real_killpg, proc.pid)
                proc.wait(timeout=5)
                with pytest.raises(ProcessLookupError):
                    real_killpg(proc.pid, 0)


@pytest.fixture
def escapee(tmp_path):
    esc = tmp_path / "escape [*] é.py"
    pid_file = tmp_path / "escape [*] é.pid"
    esc.write_text("import os, sys, time\nos.setsid()\nwith open(sys.argv[1], 'w') as f:\n    f.write(str(os.getpid()))\ntime.sleep(300)\n")
    yield esc, pid_file
    if pid_file.exists():
        kill_if_present(os.kill, int(pid_file.read_text()))


def escape_block(escapee, tail="sleep 300"):
    esc, pid_file = escapee
    return dbe.substitute(execution_block("python3 ESC_PATH PID_PATH & " + tail),
                          {"ESC_PATH": shlex.quote(str(esc)), "PID_PATH": shlex.quote(str(pid_file))})[0]


def wrapped_process(monkeypatch, method, injected):
    real_popen = subprocess.Popen
    records = []
    calls = []

    def record(*args, **kwargs):
        inst = real_popen(*args, **kwargs)
        records.append({"proc": inst, "cwd": kwargs["cwd"],
                        "real_poll": inst.poll, "real_wait": inst.wait})
        real_method = getattr(inst, method)

        def raise_once(*a, **kw):
            calls.append(kw)
            if len(calls) == 1:
                raise injected
            return real_method(*a, **kw)

        setattr(inst, method, raise_once)
        return inst

    monkeypatch.setattr(dbe.subprocess, "Popen", record)
    return records, calls


def collect_case(monkeypatch, method, block, escapee=None, expiry=False):
    run = dbe.run_block
    real_killpg = os.killpg
    injected = (subprocess.TimeoutExpired(cmd=["bash"], timeout=dbe.DRAIN_SECONDS) if expiry
                else OSError(errno.ECHILD if method == "poll" else errno.EIO, "injected child I/O failure"))
    records, calls = wrapped_process(monkeypatch, method, injected)
    start = time.monotonic()
    try:
        with pytest.raises(dbe.LaunchFailed) as error:
            run(block, **({} if method == "communicate" else {"timeout": 1}))
        proc = records[0]["proc"]
        assert error.value.stage == ("reap" if expiry else "collect")
        assert error.value.err is injected and error.value.pgid == proc.pid
        if method != "communicate":
            assert isinstance(error.value.__context__, dbe.BlockTimeout)
        if expiry:
            assert calls[0].get("timeout") == dbe.DRAIN_SECONDS, "helper wait must receive the bounded timeout keyword"
        assert_bounded(start)
        assert_cwd_gone(records)
        if method == "communicate":
            with pytest.raises(ProcessLookupError):
                real_killpg(proc.pid, 0)
        if method == "poll":
            with pytest.raises(ProcessLookupError):
                real_killpg(proc.pid, 0)
    finally:
        if escapee is not None and escapee[1].exists():
            kill_if_present(os.kill, int(escapee[1].read_text()))
        for entry in records:
            proc = entry["proc"]
            # The injected wait can leave the killed leader unreaped: its
            # zombie-only group yields EPERM on macOS. Reap via the original
            # poll, and signal only if the owned leader is still running.
            if entry["real_poll"]() is None:
                kill_if_present(real_killpg, proc.pid)
            entry["real_wait"](timeout=5)


def test_communicate_oserror_is_launch_failed_collect(monkeypatch):
    collect_case(monkeypatch, "communicate", execution_block("echo hi"))


def test_drain_wait_oserror_is_launch_failed_collect(monkeypatch, escapee):
    collect_case(monkeypatch, "wait", escape_block(escapee), escapee)


def test_poll_oserror_is_launch_failed_collect(monkeypatch):
    collect_case(monkeypatch, "poll", execution_block("sleep 300"))


@contextmanager
def owned_recovery_process(monkeypatch, communicate_failure):
    """Retain real pipes and reap the owned leader even when a guard fails."""
    real_popen = subprocess.Popen
    records = []

    def spawn(*args, **kwargs):
        proc = real_popen(*args, **kwargs)
        records.append({"proc": proc, "cwd": kwargs["cwd"]})
        real_communicate = proc.communicate
        calls = []

        def communicate(*a, **kw):
            calls.append(kw)
            communicate_failure(len(calls), kw)
            return real_communicate(*a, **kw)

        monkeypatch.setattr(proc, "communicate", communicate)
        return proc

    monkeypatch.setattr(dbe.subprocess, "Popen", spawn)
    try:
        yield records
    finally:
        for entry in records:
            proc = entry["proc"]
            try:
                # Reap first: a zombie-only group can return EPERM on macOS.
                if proc.poll() is None:
                    kill_if_present(os.killpg, proc.pid)
                proc.wait(timeout=5)
            finally:
                proc.stdout.close()
                proc.stderr.close()
                if os.path.lexists(entry["cwd"]):
                    shutil.rmtree(entry["cwd"])


def test_stderr_is_closed_after_drain_timeout(monkeypatch):
    def expire(call, kwargs):
        # Force both collection and drain expiry without an orphan escapee.
        raise subprocess.TimeoutExpired(cmd=["bash"], timeout=kwargs["timeout"])

    with owned_recovery_process(monkeypatch, expire) as records:
        with pytest.raises(dbe.BlockTimeout):
            dbe.run_block(execution_block("exec sleep 300"), timeout=1)
        proc = records[0]["proc"]
        assert proc.stderr.closed, "production must close stderr after drain timeout"
        assert proc.stdout.closed
        assert_cwd_gone(records)


def test_collect_failure_kills_running_group(monkeypatch):
    injected = OSError(errno.EIO, "injected collection failure")

    def fail_first(call, kwargs):
        if call == 1:
            raise injected

    with owned_recovery_process(monkeypatch, fail_first) as records:
        with pytest.raises(dbe.LaunchFailed) as error:
            dbe.run_block(execution_block("exec sleep 300"), timeout=1)
        proc = records[0]["proc"]
        assert error.value.stage == "collect" and error.value.err is injected
        assert proc.poll() == -signal.SIGKILL, "production must kill the leader after collect failure"
        with pytest.raises(ProcessLookupError):
            os.killpg(proc.pid, 0)
        assert_cwd_gone(records)


def test_wait_after_kill_is_bounded(monkeypatch, escapee):
    collect_case(monkeypatch, "wait", escape_block(escapee), escapee, expiry=True)


def test_sleeping_block_times_out():
    start = time.monotonic()
    with pytest.raises(dbe.BlockTimeout) as error:
        dbe.run_block(execution_block("sleep 300"), timeout=1)
    assert error.value.seconds == 1
    assert_bounded(start)


def test_in_group_descendant_is_reaped(tmp_path):
    pid_file = tmp_path / "descendant [*] é.pid"
    block = dbe.substitute(execution_block("sleep 300 & echo $! > PID_PATH; sleep 300"),
                           {"PID_PATH": shlex.quote(str(pid_file))})[0]
    try:
        with pytest.raises(dbe.BlockTimeout):
            dbe.run_block(block, timeout=1)
        pid = int(pid_file.read_text())
        with pytest.raises(ProcessLookupError):
            os.kill(pid, 0)
    finally:
        if pid_file.exists():
            kill_if_present(os.kill, int(pid_file.read_text()))


def test_temp_cwd_removed_after_timeout(recording_spawn):
    with pytest.raises(dbe.BlockTimeout):
        dbe.run_block(execution_block("sleep 300"), timeout=1)
    assert_cwd_gone(recording_spawn)


def test_timeout_survives_a_group_that_already_emptied(escapee, recording_spawn):
    try:
        with pytest.raises(dbe.BlockTimeout):
            dbe.run_block(escape_block(escapee, "exit 0"), timeout=1)
    finally:
        if escapee[1].exists():
            kill_if_present(os.kill, int(escapee[1].read_text()))
        if recording_spawn:
            assert_cwd_gone(recording_spawn)


def test_timeout_drain_is_bounded_against_an_escapee(escapee, recording_spawn):
    start = time.monotonic()
    try:
        with pytest.raises(dbe.BlockTimeout):
            dbe.run_block(escape_block(escapee), timeout=1)
        assert_bounded(start)
    finally:
        if escapee[1].exists():
            kill_if_present(os.kill, int(escapee[1].read_text()))
        if recording_spawn:
            assert_cwd_gone(recording_spawn)


def timeout_recorders(monkeypatch):
    real_mkdtemp = tempfile.mkdtemp
    created = []

    def record(*args, **kwargs):
        path = real_mkdtemp(*args, **kwargs)
        created.append(path)
        return path

    monkeypatch.setattr(dbe.tempfile, "mkdtemp", record)
    return created


def test_nonpositive_timeout_refuses_before_spawn(monkeypatch, recording_spawn):
    run = dbe.run_block
    created = timeout_recorders(monkeypatch)
    for value in (0, -1, math.nan, math.inf, "not-a-timeout"):
        with pytest.raises(dbe.BadTimeout) as error:
            run(execution_block("echo hi"), timeout=value)
        assert error.value.value is value, "BadTimeout must preserve the raw caller value"
        assert recording_spawn == [] and created == [], "validation must precede allocation and spawn"


def test_unrepresentable_timeout_refuses_before_spawn(monkeypatch, recording_spawn):
    run = dbe.run_block
    created = timeout_recorders(monkeypatch)
    value = 2147483.648
    with pytest.raises(dbe.BadTimeout) as error:
        run(execution_block("echo hi"), timeout=value)
    assert error.value.value is value
    assert recording_spawn == [] and created == [], "unrepresentable bounds must refuse before allocation"
    result = run(execution_block("echo hi"), timeout=(2**31 - 1) / 1000)
    assert result.rc == 0 and result.stdout == "hi\n", "the representable boundary must execute normally"
    assert len(created) == 1
    assert_cwd_gone(recording_spawn)


# Task 4 RED: CLI verdicts, stream ownership, and the helper registry.
# Keep case loops inside test functions: one function is one dispatch RED item.
CLI_SCRIPT = SCRIPTS / "h_mad_doc_block_exec.py"


@pytest.fixture
def cli_case(tmp_path, hostile):
    heading = '## Section [*] "한글" rc=7'
    marker = tmp_path / 'executed [*] 한글'
    out = tmp_path / 'stdout [*] 한글'
    err = tmp_path / 'stderr [*] 한글'
    doc = write_doc(tmp_path, '')

    def prepare(body=None, *, info='hmad:exec', text=None):
        if body is None:
            body = 'printf %s ' + shlex.quote(hostile) + '\n'
        doc.write_text(text if text is not None else heading + '\n' + tagged(body, info), encoding='utf-8')
        return [str(doc), '--heading', heading]

    return dict(prepare=prepare, doc=doc, heading=heading, marker=marker,
                out=out, err=err, hostile=hostile,
                effect='touch ' + shlex.quote(str(marker)) + '\n')


def cli_run(argv, *, env=None, timeout=15):
    return subprocess.run([sys.executable, str(CLI_SCRIPT), *map(str, argv)],
                          capture_output=True, text=True, env=env, timeout=timeout)


def cli_fields(tail):
    """Parse the full field grammar; reject trailing garbage or duplicate keys."""
    fields = {}
    decoder = json.JSONDecoder()
    while tail:
        match = re.match(r' +([a-z_]+)=', tail)
        assert match, f'invalid verdict field grammar: {tail!r}'
        key = match[1]
        assert key not in fields, f'duplicate verdict field: {key}'
        tail = tail[match.end():]
        if tail.startswith('"'):
            value, end = decoder.raw_decode(tail)
            assert isinstance(value, str), 'quoted verdict values must be strings'
        else:
            bare = re.match(r'[^\s"]+', tail)
            assert bare, f'invalid bare field: {tail!r}'
            value, end = bare[0], bare.end()
        fields[key] = value
        tail = tail[end:]
    return fields


def cli_verdict(result, head, code=0):
    rc, stdout, stderr = (result.returncode, result.stdout, result.stderr)
    lines = stdout.splitlines()
    assert lines and lines[0].startswith('DOCBLOCK: ' + head), f'expected {head} verdict, got {stdout!r}'
    assert rc == code, f'{head} must exit {code}: {rc}, {stderr!r}'
    assert sum(line.startswith('DOCBLOCK:') for line in lines) == 1, 'exactly one verdict is required'
    assert 'Traceback' not in stderr and 'usage:' not in stderr, 'verdict must not leak a traceback or argparse usage'
    return lines


def main_result(main, argv, capsys):
    rc = main(list(map(str, argv)))
    captured = capsys.readouterr()
    return subprocess.CompletedProcess(argv, rc, captured.out, captured.err)


def stream_args(case):
    return ['--stdout', str(case['out']), '--stderr', str(case['err'])]


def cli_refusal(case, argv, head, code=0):
    result = cli_run([*argv, *stream_args(case)])
    lines = cli_verdict(result, head, code)
    assert not case['marker'].exists(), 'refused input must not execute the block'
    assert not case['out'].exists() and not case['err'].exists(), 'input refusal must precede stream reservation'
    return lines


def test_cli_ambiguous_prints_blocks_and_heading(cli_case):
    c = cli_case
    argv = c['prepare'](text=c['heading'] + '\n' + tagged(c['effect']) * 2)
    lines = cli_refusal(c, argv, 'AMBIGUOUS')
    assert lines[0] == 'DOCBLOCK: AMBIGUOUS blocks=2 heading=' + json.dumps(c['heading'], ensure_ascii=False)


def test_cli_index_past_end_is_not_found(cli_case):
    c = cli_case
    cli_refusal(c, c['prepare'](c['effect']) + ['--index', '2'], 'NOT_FOUND')


def test_cli_duplicate_headings_refuse(cli_case):
    c = cli_case
    argv = c['prepare'](text=(c['heading'] + '\n' + tagged(c['effect'])) * 2)
    lines = cli_refusal(c, argv, 'AMBIGUOUS_HEADING')
    assert lines[0] == 'DOCBLOCK: AMBIGUOUS_HEADING count=2 heading=' + json.dumps(c['heading'], ensure_ascii=False)


def test_cli_index_zero_and_negative_are_bad_index(cli_case):
    c = cli_case
    for value in ('0', '-1'):
        lines = cli_refusal(c, c['prepare'](c['effect']) + ['--index', value], 'BAD_INDEX')
        assert lines[0] == 'DOCBLOCK: BAD_INDEX index=' + json.dumps(value)


def test_non_integer_index_is_bad_index(cli_case):
    c = cli_case
    value = c['hostile']
    lines = cli_refusal(c, c['prepare'](c['effect']) + ['--index', value], 'BAD_INDEX')
    assert lines[0] == 'DOCBLOCK: BAD_INDEX index=' + json.dumps(value, ensure_ascii=False)


def test_cli_missing_keys_list_in_argument_order(cli_case):
    c = cli_case
    keys = ['Z' + c['hostile'], 'A' + c['hostile']]
    argv = c['prepare'](c['effect'])
    for key in keys:
        argv += ['--subst', key + '=value']
    lines = cli_refusal(c, argv, 'SUBST_MISSING')
    assert lines == ['DOCBLOCK: SUBST_MISSING keys=2'] + ['missing_key: ' + json.dumps(k, ensure_ascii=False) for k in keys]


def test_cli_overlap_counts_distinct_keys(cli_case):
    c = cli_case
    argv = c['prepare']('true\n') + ['--subst', 'a=1', '--subst', 'ab=2', '--subst', 'abc=3']
    lines = cli_refusal(c, argv, 'SUBST_OVERLAP')
    assert lines[0] == 'DOCBLOCK: SUBST_OVERLAP keys=3', 'count distinct keys, not pair endpoints'


def test_cli_no_subst_runs(cli_case):
    c = cli_case
    cli_verdict(cli_run(c['prepare']() + stream_args(c)), 'RAN rc=0')
    assert c['out'].read_text() == c['hostile'], 'zero substitutions must preserve executable text'


def test_subst_without_equals_is_bad_subst(cli_case):
    c = cli_case
    raw = 'invalid\n[*] 한글'
    lines = cli_refusal(c, c['prepare'](c['effect']) + ['--subst', raw], 'BAD_SUBST')
    assert lines[0] == 'DOCBLOCK: BAD_SUBST arg=' + json.dumps(raw, ensure_ascii=False)


def test_subst_empty_key_is_bad_subst(cli_case):
    c = cli_case
    lines = cli_refusal(c, c['prepare'](c['effect']) + ['--subst', '=V'], 'BAD_SUBST')
    assert lines[0] == 'DOCBLOCK: BAD_SUBST arg="=V"', 'main must preserve the raw empty-key argument'


def test_duplicate_substitution_key_refuses(cli_case):
    c = cli_case
    lines = cli_refusal(c, c['prepare'](c['effect']) + ['--subst', 'K=first', '--subst', 'K=second'], 'BAD_SUBST')
    assert lines == ['DOCBLOCK: BAD_SUBST arg="K=second"', 'duplicate_key: "K"']


def test_subst_value_may_contain_equals(cli_case):
    c = cli_case
    # Argument acceptance isolates split-on-every-equals from D6's pass-through.
    # Only test_cli_subst_value_reaches_the_child observes substituted stdout.
    value = shlex.quote('value=with=equals ' + c['hostile'])
    argv = c['prepare']('echo K\n') + ['--subst', 'K=' + value]
    cli_verdict(cli_run(argv), 'RAN rc=0')


def test_cli_subst_value_reaches_the_child(cli_case):
    c = cli_case
    argv = c['prepare']('echo K\n') + ['--subst', 'K=sentinel-value', '--stdout', str(c['out'])]
    cli_verdict(cli_run(argv), 'RAN rc=0')
    actual = c['out'].read_bytes()
    assert b'sentinel-value' in actual and b'K' not in actual, 'run_block must receive substitute\'s returned block'


def test_cli_unknown_info_key_is_bad_info(cli_case):
    c = cli_case
    key = 'unknown=[*]한글'
    lines = cli_refusal(c, c['prepare'](c['effect'], info='hmad:exec ' + key), 'BAD_INFO')
    assert lines[0] == 'DOCBLOCK: BAD_INFO key=' + json.dumps(key, ensure_ascii=False)


def test_cli_invalid_utf8_document_is_unreadable(cli_case):
    c = cli_case
    argv = c['prepare'](c['effect'])
    c['doc'].write_bytes(c['doc'].read_bytes() + b'\xff')
    cli_refusal(c, argv, 'UNREADABLE reason=doc_unreadable', 2)


def test_invalid_utf8_preamble_is_unreadable(cli_case):
    c = cli_case
    preamble = c['doc'].with_suffix('.pre')
    preamble.write_bytes(b'\xff')
    cli_refusal(c, c['prepare'](c['effect']) + ['--preamble-file', str(preamble)], 'UNREADABLE reason=preamble_unreadable', 2)


def test_unreadable_preamble_path_refuses(cli_case):
    c = cli_case
    preamble = c['doc'].with_suffix('.absent')
    cli_refusal(c, c['prepare'](c['effect']) + ['--preamble-file', str(preamble)], 'UNREADABLE reason=preamble_unreadable', 2)


def test_cli_preamble_file_reaches_the_block(cli_case):
    c = cli_case
    preamble = c['doc'].with_suffix('.pre')
    preamble.write_text('VALUE=' + shlex.quote(c['hostile']), encoding='utf-8')
    argv = c['prepare']('printf %s "$VALUE"\n') + ['--preamble-file', str(preamble)] + stream_args(c)
    cli_verdict(cli_run(argv), 'RAN rc=0')
    assert c['out'].read_text() == c['hostile'], 'preamble file must bind variables in the child'


def test_stream_paths_receive_the_streams(cli_case):
    c = cli_case
    body = 'printf %s ' + shlex.quote(c['hostile']) + '; printf %s stderr-only >&2\n'
    cli_verdict(cli_run(c['prepare'](body) + stream_args(c)), 'RAN rc=0')
    assert c['out'].read_text() == c['hostile'] and c['err'].read_bytes() == b'stderr-only'


def test_streams_optional(cli_case):
    c = cli_case
    lines = cli_verdict(cli_run(c['prepare']()), 'RAN rc=0')
    assert len(lines) == 1, 'child streams must not enter the verdict channel when artifact options are absent'
    assert not c['out'].exists() and not c['err'].exists()


def test_stream_paths_truncate_an_existing_file(cli_case):
    c = cli_case
    for path in (c['out'], c['err']):
        path.write_bytes(b'old bytes much longer than new output' * 10)
    cli_verdict(cli_run(c['prepare']('printf new; printf err >&2\n') + stream_args(c)), 'RAN rc=0')
    assert c['out'].read_bytes() == b'new' and c['err'].read_bytes() == b'err', 'final writes must truncate both old files'


def test_streams_untouched_after_a_timeout(cli_case):
    c = cli_case
    for path in (c['out'], c['err']):
        path.write_bytes(b'keep\xff')
    lines = cli_verdict(cli_run(c['prepare']('echo partial; sleep 300\n') + stream_args(c) + ['--shell-timeout', '1']), 'TIMEOUT')
    assert lines[0] == 'DOCBLOCK: TIMEOUT seconds="1.0"'
    assert all(p.read_bytes() == b'keep\xff' for p in (c['out'], c['err'])), 'reservation must not truncate before RAN'


def write_failure_case(cli_case, monkeypatch, capsys, *, fail_at=1, noop=False):
    main = dbe.main
    c = cli_case
    real_write = dbe._final_write
    calls = []
    for path in (c['out'], c['err']):
        path.write_bytes(b'original')

    def injected(handle, text):
        calls.append(handle)
        if len(calls) == fail_at:
            if noop:
                return
            raise OSError(errno.EIO, 'write [*] "한글" failed')
        return real_write(handle, text)

    monkeypatch.setattr(dbe, '_final_write', injected)
    result = main_result(main, c['prepare']('printf new; printf err >&2\n') + stream_args(c), capsys)
    lines = cli_verdict(result, 'UNREADABLE reason=stream_write_failed', 2)
    assert 'rc=' not in lines[0], 'stream refusal must not expose a child rc'
    return lines, calls


def test_stream_write_failure_after_the_run_is_a_refusal(cli_case, monkeypatch, capsys):
    lines, calls = write_failure_case(cli_case, monkeypatch, capsys)
    assert len(calls) == 1 and 'failed: "stdout"' in lines


def test_first_stream_write_failure_skips_the_second(cli_case, monkeypatch, capsys):
    lines, calls = write_failure_case(cli_case, monkeypatch, capsys)
    assert len(calls) == 1, 'stdout failure must skip stderr final write'
    assert 'failed: "stdout"' in lines and 'skipped: "stderr"' in lines
    assert cli_case['err'].read_bytes() == b'original'


def test_second_stream_write_failure_leaves_the_first_as_written(cli_case, monkeypatch, capsys):
    lines, calls = write_failure_case(cli_case, monkeypatch, capsys, fail_at=2)
    assert len(calls) == 2 and 'written: "stdout"' in lines and 'failed: "stderr"' in lines
    assert cli_case['out'].read_bytes() == b'new'


def final_write_proxy_case(cli_case, monkeypatch, capsys, *, flush_fails):
    main = dbe.main
    real_write = dbe._final_write
    closed = []

    class Proxy:
        def __init__(self, handle):
            self.handle = handle

        def __getattr__(self, key):
            return getattr(self.handle, key)

        def flush(self):
            if flush_fails:
                raise OSError(errno.EIO, 'first flush failure')
            return self.handle.flush()

        def close(self):
            closed.append(self.handle)
            raise OSError(errno.EIO, 'second close failure')

    def injected(handle, text):
        return real_write(Proxy(handle), text)

    monkeypatch.setattr(dbe, '_final_write', injected)
    c = cli_case
    result = main_result(main, c['prepare']() + stream_args(c), capsys)
    lines = cli_verdict(result, 'UNREADABLE reason=stream_write_failed', 2)
    assert 'failed: "stdout"' in lines and 'rc=' not in lines[0]
    assert closed, '_final_write must close in finally, including after flush raises'
    assert all(handle.closed for handle in closed), 'backstop must close the underlying real handles'


def test_final_write_close_failure_is_mapped(cli_case, monkeypatch, capsys):
    final_write_proxy_case(cli_case, monkeypatch, capsys, flush_fails=False)


def test_final_write_failure_before_close_still_closes(cli_case, monkeypatch, capsys):
    final_write_proxy_case(cli_case, monkeypatch, capsys, flush_fails=True)


def test_final_write_readback_catches_a_silent_no_op(cli_case, monkeypatch, capsys):
    lines, calls = write_failure_case(cli_case, monkeypatch, capsys, noop=True)
    assert len(calls) == 1, 'verify stdout immediately, before writing stderr'
    assert 'verify: "stdout"' in lines and 'failed: "stdout"' in lines and 'skipped: "stderr"' in lines
    assert cli_case['err'].read_bytes() == b'original'


def close_failure_case(cli_case, monkeypatch, capsys, *, alias):
    main = dbe.main
    c = cli_case
    handles = []
    cwds = []
    real_mkdtemp = dbe.tempfile.mkdtemp

    def mkdtemp(*args, **kwargs):
        cwd = real_mkdtemp(*args, **kwargs)
        cwds.append(cwd)
        return cwd

    def fail(handle):
        handles.append(handle)
        raise OSError(errno.EIO, 'close [*] "한글" failed')

    monkeypatch.setattr(dbe, '_close_stream', fail)
    monkeypatch.setattr(dbe.tempfile, 'mkdtemp', mkdtemp)
    argv = c['prepare'](c['effect'] if alias else 'sleep 300\n') + ['--stdout', str(c['out'])]
    argv += ['--stderr', str(c['out'])] if alias else ['--shell-timeout', '1']
    try:
        result = main_result(main, argv, capsys)
        head = 'stream_paths_alias' if alias else 'stream_close_failed'
        lines = cli_verdict(result, 'UNREADABLE reason=' + head, 2)
        if alias:
            assert not c['marker'].exists(), 'alias refusal must precede execution'
        else:
            assert 'stream: "stdout"' in lines
            errors = [line.removeprefix('os_error: ') for line in lines if line.startswith('os_error: ')]
            assert len(errors) == 1 and 'close [*] "한글" failed' in json.loads(errors[0])
            assert cwds and all(not os.path.lexists(p) for p in cwds), 'timeout cleanup must still remove cwd'
        assert handles, 'backstop must call the one closure seam'
    finally:
        for handle in handles:
            if not handle.closed:
                handle.close()


def test_backstop_close_failure_on_timeout_is_mapped(cli_case, monkeypatch, capsys):
    close_failure_case(cli_case, monkeypatch, capsys, alias=False)


def test_backstop_close_failure_does_not_outrank_a_refusal(cli_case, monkeypatch, capsys):
    close_failure_case(cli_case, monkeypatch, capsys, alias=True)


def test_stream_handles_are_closed_on_every_path(cli_case, monkeypatch, capsys):
    main = dbe.main
    c = cli_case
    real_open = os.open
    for timeout in (True, False):
        fds = []
        with monkeypatch.context() as patch:
            def record(path, flags, *args, **kwargs):
                fd = real_open(path, flags, *args, **kwargs)
                if str(path) in (str(c['out']), str(c['err'])):
                    fds.append(fd)
                return fd

            def fail(*args):
                raise OSError(errno.EIO, 'final write failed')

            patch.setattr(dbe.os, 'open', record)
            if not timeout:
                patch.setattr(dbe, '_final_write', fail)
            argv = c['prepare']('sleep 300\n' if timeout else 'echo hi\n') + stream_args(c)
            if timeout:
                argv += ['--shell-timeout', '1']
            result = main_result(main, argv, capsys)
        cli_verdict(result, 'TIMEOUT' if timeout else 'UNREADABLE reason=stream_write_failed', 0 if timeout else 2)
        assert len(fds) == 2, 'both stream reservations must be exercised'
        for fd in fds:
            with pytest.raises(OSError):
                os.fstat(fd)


def alias_case(c, kind):
    out, err = c['out'], c['err']
    if kind == 'symlink':
        err.symlink_to(out)
    elif kind == 'hardlink':
        out.write_bytes(b'keep')
        os.link(out, err)
    else:
        err = str(out.parent) + '/./' + out.name
    result = cli_run(c['prepare'](c['effect']) + ['--stdout', str(out), '--stderr', str(err)])
    cli_verdict(result, 'UNREADABLE reason=stream_paths_alias', 2)
    assert not c['marker'].exists(), 'inode aliases must refuse before child execution'
    if kind == 'hardlink':
        assert out.read_bytes() == b'keep' and c['err'].read_bytes() == b'keep'
    else:
        assert not out.exists(), 'alias refusal must unlink a newly created reservation'


def test_symlinked_stream_paths_refuse(cli_case):
    alias_case(cli_case, 'symlink')


def test_dot_slash_spelling_refuses(cli_case):
    alias_case(cli_case, 'dot')


def test_hard_linked_stream_paths_refuse(cli_case):
    alias_case(cli_case, 'hardlink')


def rollback_case(cli_case, monkeypatch, capsys, *, alias=False, mismatch=False, newline=False):
    main = dbe.main
    c = cli_case
    out = c['out'].with_name('left\nDOCBLOCK: RAN rc=0 blocks=1 shell=strict') if newline else c['out']
    parent = c['err']
    parent.write_bytes(b'parent is a regular file')
    err = out if alias else parent / 'child'
    real_unlink, real_lstat = os.unlink, os.lstat
    calls = []

    def unlink(path, *args, **kwargs):
        calls.append(str(path))
        if mismatch:
            return
        raise PermissionError(errno.EACCES, 'unlink refused')

    def lstat(path, *args, **kwargs):
        original = real_lstat(path, *args, **kwargs)
        if str(path) == str(out):
            values = list(original)
            values[1] += 1  # st_ino; retain the remaining real stat fields.
            return os.stat_result(values)
        return original

    try:
        with monkeypatch.context() as patch:
            patch.setattr(dbe.os, 'unlink', unlink)
            if mismatch:
                patch.setattr(dbe.os, 'lstat', lstat)
            argv = c['prepare'](c['effect']) + ['--stdout', str(out), '--stderr', str(err)]
            result = main_result(main, argv, capsys)
        lines = cli_verdict(result, 'UNREADABLE reason=' + ('stream_paths_alias' if alias else 'stream_path_unwritable'), 2)
        assert 'leftover: ' + json.dumps(str(out), ensure_ascii=False) in lines, 'surviving reservation must be reported with its exact quoted path'
        assert out.read_bytes() == b'', 'refusal leftover must be present and empty'
        assert not c['marker'].exists(), 'failed reservation must never execute the block'
        if mismatch:
            assert calls == [], 'rollback must not unlink a path with a different inode identity'
        else:
            assert str(out) in calls, 'test must actually reach the injected unlink failure'
        return lines
    finally:
        if os.path.lexists(out):
            real_unlink(out)


def test_alias_refusal_unlink_failure_reports_leftover(cli_case, monkeypatch, capsys):
    rollback_case(cli_case, monkeypatch, capsys, alias=True)


def test_rollback_unlink_failure_reports_leftover(cli_case, monkeypatch, capsys):
    rollback_case(cli_case, monkeypatch, capsys)


def test_rollback_skips_unlink_on_identity_mismatch(cli_case, monkeypatch, capsys):
    rollback_case(cli_case, monkeypatch, capsys, mismatch=True)


def test_stream_path_under_a_regular_file_refuses(cli_case):
    c = cli_case
    c['out'].write_bytes(b'parent')
    result = cli_run(c['prepare'](c['effect']) + ['--stdout', str(c['out'] / 'child')])
    cli_verdict(result, 'UNREADABLE reason=stream_path_unwritable', 2)
    assert not c['marker'].exists()


def test_stream_path_char_device_refuses(cli_case):
    c = cli_case
    result = cli_run(c['prepare'](c['effect']) + ['--stdout', '/dev/null'])
    cli_verdict(result, 'UNREADABLE reason=stream_path_unwritable', 2)
    assert not c['marker'].exists(), 'S_ISREG must reject a successfully opened character device'


def test_stream_path_fifo_without_reader_refuses_bounded(cli_case):
    c = cli_case
    os.mkfifo(c['out'])
    start = time.monotonic()
    result = cli_run(c['prepare'](c['effect']) + ['--stdout', str(c['out'])], timeout=5)
    elapsed = time.monotonic() - start
    cli_verdict(result, 'UNREADABLE reason=stream_path_unwritable', 2)
    assert elapsed < 1, 'readerless FIFO reservation must use O_NONBLOCK and refuse within one second'
    assert not c['marker'].exists()


def test_stdout_survives_a_failed_stderr_reservation(cli_case):
    c = cli_case
    c['err'].write_bytes(b'regular parent')
    for existing in (True, False):
        if existing:
            c['out'].write_bytes(b'original\xff')
        else:
            c['out'].unlink()
        argv = c['prepare'](c['effect']) + ['--stdout', str(c['out']), '--stderr', str(c['err'] / 'child')]
        cli_verdict(cli_run(argv), 'UNREADABLE reason=stream_path_unwritable', 2)
        assert not c['marker'].exists()
        if existing:
            assert c['out'].read_bytes() == b'original\xff', 'rollback must preserve a pre-existing stdout'
        else:
            assert not c['out'].exists(), 'rollback must remove a stdout created by this invocation'


def test_ran_line_and_exit_zero_with_nonzero_rc(cli_case):
    result = cli_run(cli_case['prepare']('exit 3\n', info='hmad:exec shell=plain'))
    assert cli_verdict(result, 'RAN')[0] == 'DOCBLOCK: RAN rc=3 blocks=1 shell=plain'


def missing_heading_result(c, heading, capsys):
    main = dbe.main
    argv = c['prepare']()
    argv[-1] = heading
    result = main_result(main, argv, capsys)
    lines = cli_verdict(result, 'NOT_FOUND')
    return lines, cli_fields(lines[0].removeprefix('DOCBLOCK: NOT_FOUND'))


def test_dynamic_field_cannot_forge_a_token(cli_case, capsys):
    lines, fields = missing_heading_result(cli_case, 'x rc=0', capsys)
    assert fields == {'heading': 'x rc=0'}, 'caller spaces must not forge an rc field on NOT_FOUND'


def test_quote_in_dynamic_field_cannot_close_the_value(cli_case, capsys):
    lines, fields = missing_heading_result(cli_case, 'x" rc=0', capsys)
    assert fields == {'heading': 'x" rc=0'}, 'caller quote must not terminate the JSON value'
    assert 'heading="x\\" rc=0"' in lines[0], 'embedded quote must retain its JSON backslash escape'


def test_malformed_invocation_is_a_verdict(cli_case, capsys):
    main = dbe.main
    valid = cli_case['prepare']()
    for argv, diagnostic in ((valid + ['--nope'], 'unrecognized arguments: --nope'),
                             ([valid[0], '--heading'], 'argument --heading: expected one argument')):
        result = main_result(main, argv, capsys)
        lines = cli_verdict(result, 'BAD_ARGS')
        assert lines == ['DOCBLOCK: BAD_ARGS message=' + json.dumps(diagnostic)]
        assert 'usage:' not in result.stdout and 'usage:' not in result.stderr, 'argparse errors must route through BadArgs'


def test_help_anywhere_exits_zero_without_a_verdict(cli_case, capsys):
    main = dbe.main
    valid = cli_case['prepare']()
    for argv in (['--help'], ['--bogus', '--help'], valid + ['--help'],
                 ['--help', '--bogus'], [valid[0], '--help']):
        with pytest.raises(SystemExit) as raised:
            main(argv)
        captured = capsys.readouterr()
        assert raised.value.code == 0, 'argparse help keeps its exit-zero exemption in every listed position'
        assert 'usage:' in captured.out and captured.err == ''
        assert not any(line.startswith('DOCBLOCK:') for line in captured.out.splitlines()), 'help must never emit a verdict'


def test_unicode_line_separators_cannot_split_a_verdict_line(cli_case, capsys):
    heading = 'x\u0085\u2028\u2029\u007f'
    lines, fields = missing_heading_result(cli_case, heading, capsys)
    assert len(lines) == 1, 'Cc/Zl/Zp characters must not split one verdict into physical lines'
    assert fields == {'heading': heading}
    assert 'heading="x\\u0085\\u2028\\u2029\\u007f"' in lines[0]


def test_newline_in_dynamic_fields_cannot_forge_a_verdict_line(cli_case, monkeypatch, capsys):
    main = dbe.main
    c = cli_case
    forged = 'DOCBLOCK: RAN rc=0 blocks=1 shell=strict'
    payload = 'x\n' + forged

    def check(lines, quoted):
        assert sum(line.startswith('DOCBLOCK:') for line in lines) == 1
        assert forged not in lines, 'caller newline must never create a second verdict'
        assert any(quoted in line for line in lines), 'newline must appear as backslash-n inside a quoted value'

    lines, fields = missing_heading_result(c, payload, capsys)
    assert fields == {'heading': payload}
    check(lines, 'heading=' + json.dumps(payload))
    for raw, head, quoted in (
        ('missing\n[*]=value\n' + forged, 'SUBST_MISSING', 'missing_key: ' + json.dumps('missing\n[*]')),
        ('malformed\n' + forged.replace('=', ':'), 'BAD_SUBST', None),
    ):
        result = main_result(main, c['prepare'](c['effect']) + ['--subst', raw] + stream_args(c), capsys)
        lines = cli_verdict(result, head)
        check(lines, quoted or 'arg=' + json.dumps(raw))
        assert not c['marker'].exists() and not c['out'].exists() and not c['err'].exists()
    lines = rollback_case(c, monkeypatch, capsys, newline=True)
    check(lines, 'leftover: ' + json.dumps(str(c['out'].with_name('left\n' + forged)), ensure_ascii=False))


CLI_HEAD_CODES = {
    'RAN': 0, 'NOT_FOUND': 0, 'AMBIGUOUS': 0, 'AMBIGUOUS_HEADING': 0,
    'BAD_INDEX': 0, 'BAD_TIMEOUT': 0, 'BAD_ARGS': 0, 'BAD_SUBST': 0,
    'SUBST_MISSING': 0, 'SUBST_OVERLAP': 0, 'BAD_INFO': 0, 'TIMEOUT': 0,
    'CLEANUP_FAILED': 2, 'LAUNCH_FAILED stage=mkdtemp': 2,
    'LAUNCH_FAILED stage=spawn': 2, 'LAUNCH_FAILED stage=reap': 2,
    'LAUNCH_FAILED stage=collect': 2, 'UNREADABLE reason=doc_unreadable': 2,
    'UNREADABLE reason=preamble_unreadable': 2, 'UNREADABLE reason=stream_paths_alias': 2,
    'UNREADABLE reason=stream_path_unwritable': 2, 'UNREADABLE reason=stream_write_failed': 2,
    'UNREADABLE reason=stream_close_failed': 2,
}
CLI_INJECTED_HEADS = {
    'CLEANUP_FAILED', 'LAUNCH_FAILED stage=mkdtemp', 'LAUNCH_FAILED stage=reap',
    'LAUNCH_FAILED stage=collect', 'UNREADABLE reason=stream_write_failed',
    'UNREADABLE reason=stream_close_failed',
}


def real_cli_producer(c, head):
    argv = c['prepare'](c['effect'])
    env = None
    if head == 'NOT_FOUND':
        argv = c['prepare'](text=c['heading'] + '\nno tagged fence\n')
    elif head == 'AMBIGUOUS':
        argv = c['prepare'](text=c['heading'] + '\n' + tagged(c['effect']) * 2)
    elif head == 'AMBIGUOUS_HEADING':
        argv = c['prepare'](text=(c['heading'] + '\n' + tagged(c['effect'])) * 2)
    elif head in ('BAD_INDEX', 'BAD_TIMEOUT', 'BAD_ARGS', 'BAD_SUBST', 'SUBST_MISSING', 'SUBST_OVERLAP'):
        argv += {
            'BAD_INDEX': ['--index', '0'], 'BAD_TIMEOUT': ['--shell-timeout', 'nan'],
            'BAD_ARGS': ['--nope'], 'BAD_SUBST': ['--subst', '=V'],
            'SUBST_MISSING': ['--subst', 'absent-key=value'],
            'SUBST_OVERLAP': ['--subst', 'a=1', '--subst', 'ab=2'],
        }[head]
    elif head == 'BAD_INFO':
        argv = c['prepare'](c['effect'], info='hmad:exec unknown=[*]')
    elif head == 'TIMEOUT':
        argv = c['prepare']('sleep 300\n') + ['--shell-timeout', '1']
    elif head == 'LAUNCH_FAILED stage=spawn':
        env = dict(os.environ, PATH='')
    elif head == 'UNREADABLE reason=doc_unreadable':
        c['doc'].write_bytes(b'\xff')
    elif head == 'UNREADABLE reason=preamble_unreadable':
        argv += ['--preamble-file', str(c['doc'].with_suffix('.missing'))]
    elif head == 'UNREADABLE reason=stream_paths_alias':
        argv += ['--stdout', str(c['out']), '--stderr', str(c['out'])]
    elif head == 'UNREADABLE reason=stream_path_unwritable':
        argv += ['--stdout', str(c['doc'] / 'child')]
    else:
        assert head == 'RAN', f'no real producer for {head}'
    return cli_run(argv, env=env)


def injected_cli_producer(c, head, monkeypatch, capsys):
    main = dbe.main
    real_mkdtemp, real_rmtree, real_killpg = tempfile.mkdtemp, shutil.rmtree, os.killpg
    cwds, processes = [], []
    injected = OSError(errno.EIO, 'injected [*] "한글"\nerror')

    def fail(*args, **kwargs):
        raise injected

    def mkdtemp(*args, **kwargs):
        cwd = real_mkdtemp(*args, **kwargs)
        cwds.append(cwd)
        return cwd

    with monkeypatch.context() as patch:
        patch.setattr(dbe.tempfile, 'mkdtemp', mkdtemp)
        argv = c['prepare']('echo hi\n')
        if head == 'CLEANUP_FAILED':
            patch.setattr(dbe.shutil, 'rmtree', fail)
        elif head == 'LAUNCH_FAILED stage=mkdtemp':
            patch.setattr(dbe.tempfile, 'mkdtemp', fail)
        elif head == 'LAUNCH_FAILED stage=collect':
            processes, _ = wrapped_process(patch, 'communicate', injected)
        elif head == 'LAUNCH_FAILED stage=reap':
            real_popen = subprocess.Popen

            def popen(*args, **kwargs):
                proc = real_popen(*args, **kwargs)
                processes.append(dict(proc=proc, real_poll=proc.poll, real_wait=proc.wait))
                return proc

            patch.setattr(dbe.subprocess, 'Popen', popen)
            patch.setattr(dbe.os, 'killpg', fail)
            argv = c['prepare']('sleep 300\n') + ['--shell-timeout', '1']
        elif head == 'UNREADABLE reason=stream_write_failed':
            patch.setattr(dbe, '_final_write', fail)
            argv += stream_args(c)
        elif head == 'UNREADABLE reason=stream_close_failed':
            real_close = dbe._close_stream

            def close(handle):
                real_close(handle)
                raise injected

            patch.setattr(dbe, '_close_stream', close)
            argv = c['prepare']('sleep 300\n') + ['--shell-timeout', '1', '--stdout', str(c['out'])]
        else:
            raise AssertionError(f'no injected producer for {head}')
        try:
            result = main_result(main, argv, capsys)
        finally:
            for entry in processes:
                proc = entry['proc']
                if entry['real_poll']() is None:
                    kill_if_present(real_killpg, proc.pid)
                entry['real_wait'](timeout=5)
            for cwd in cwds:
                if os.path.lexists(cwd):
                    real_rmtree(cwd)
    return result


def test_verdict_table_exit_codes(cli_case, monkeypatch, capsys):
    table = dbe.VERDICT_TABLE
    assert set(CLI_HEAD_CODES) == set(table), 'every full-granularity head needs exactly one producer'
    assert table == CLI_HEAD_CODES, 'exit-zero refusals and exit-two environmental failures have a fixed partition'
    for head in CLI_HEAD_CODES:
        result = (injected_cli_producer(cli_case, head, monkeypatch, capsys) if head in CLI_INJECTED_HEADS
                  else real_cli_producer(cli_case, head))
        lines = cli_verdict(result, head, table[head])
        if head in ('LAUNCH_FAILED stage=reap', 'LAUNCH_FAILED stage=collect'):
            pgids = [line.removeprefix('pgid: ') for line in lines if line.startswith('pgid: ')]
            assert len(pgids) == 1 and re.fullmatch(r'"[0-9]+"', pgids[0]), 'reap/collect must expose a quoted pgid'


def test_every_docblockerror_subclass_has_a_verdict():
    renderers = dbe._VERDICT_FOR
    pending = list(dbe.DocBlockError.__subclasses__())
    while pending:
        cls = pending.pop()
        assert cls in renderers and callable(renderers[cls]), f'{cls.__name__} needs a class-keyed head renderer'
        pending.extend(cls.__subclasses__())


def test_cli_exit_zero_propagates(cli_case):
    c = cli_case
    result = cli_run(c['prepare'](text=c['heading'] + '\nno tagged fence\n'))
    cli_verdict(result, 'NOT_FOUND', 0)
    assert result.returncode == dbe.VERDICT_TABLE['NOT_FOUND'], '__main__ must propagate main return value'


def test_cli_exit_two_propagates(cli_case):
    c = cli_case
    argv = c['prepare']()
    c['doc'].write_bytes(b'\xff')
    result = cli_run(argv)
    cli_verdict(result, 'UNREADABLE reason=doc_unreadable', 2)
    assert result.returncode == dbe.VERDICT_TABLE['UNREADABLE reason=doc_unreadable'], '__main__ must propagate exit two'


def test_cli_subst_overlap_detail_lines(cli_case):
    c = cli_case
    first = cli_refusal(c, c['prepare']('abc\n') + ['--subst', 'ab=X', '--subst', 'bc=Y'], 'SUBST_OVERLAP')
    assert first == ['DOCBLOCK: SUBST_OVERLAP keys=2', 'intersect: "ab" "bc" "1"'], 'intersect kind needs three quoted values and the shared offset'
    # No matching spans: isolate the map-static substring predicate.
    second = cli_refusal(c, c['prepare']('true\n') + ['--subst', 'a=1', '--subst', 'ab=2', '--subst', 'abc=3'], 'SUBST_OVERLAP')
    assert second == ['DOCBLOCK: SUBST_OVERLAP keys=3', 'overlap: "a" "ab"', 'overlap: "a" "abc"', 'overlap: "ab" "abc"']
    assert not any(line.startswith('intersect:') for line in second)


def test_no_refusal_carries_rc(cli_case):
    for head in CLI_HEAD_CODES.keys() - CLI_INJECTED_HEADS - {'RAN'}:
        result = real_cli_producer(cli_case, head)
        line = cli_verdict(result, head, CLI_HEAD_CODES[head])[0]
        fields = cli_fields(' ' + line.split(' ', 2)[2])
        assert 'rc' not in fields, f'{head} refusal must not carry rc'


def test_only_ambiguous_carries_blocks(cli_case):
    for head in CLI_HEAD_CODES.keys() - CLI_INJECTED_HEADS:
        result = real_cli_producer(cli_case, head)
        line = cli_verdict(result, head, CLI_HEAD_CODES[head])[0]
        fields = cli_fields(' ' + line.split(' ', 2)[2])
        if head in ('RAN', 'AMBIGUOUS'):
            assert 'blocks' in fields, f'{head} must carry its bare block count'
        else:
            assert 'blocks' not in fields, f'{head} must not carry blocks'


def registry_tokens():
    text = (SCRIPTS.parent / 'SKILL.md').read_text(encoding='utf-8')
    match = re.search(r'^- `h_mad_doc_block_exec\.py` —.*?(?=^- |\Z)', text, re.M | re.S)
    assert match, 'SKILL.md must contain the doc-block CLI helper entry'
    entry = match[0]
    assert not re.search(r'^ {0,3}`{3,}bash\s+hmad:exec', entry, re.M), 'registry must describe the executable tag inline'
    rows = re.findall(r'^\| `([^`]+)`([^\n]*)$', entry, re.M)
    assert rows and all(re.search(r'\|\s*\S', rest) for _, rest in rows), 'every registry row needs a remedy'
    return [token for token, _ in rows]


def test_every_emittable_line_has_a_registry_row():
    expected = set(dbe.VERDICT_TABLE) | set(dbe.DETAIL_KEYS)
    tokens = registry_tokens()
    assert expected <= set(tokens), f'undocumented emittable lines: {expected - set(tokens)}'
    assert len(tokens) == len(set(tokens)), 'one registry row per emittable line'


def test_registry_rows_cover_only_emittable_lines():
    expected = set(dbe.VERDICT_TABLE) | set(dbe.DETAIL_KEYS)
    tokens = registry_tokens()
    assert set(tokens) <= expected, f'registry advertises non-emittable lines: {set(tokens) - expected}'
    assert '_field' not in dbe.__all__, 'the private renderer is not part of the registry/API'


def test_cli_nul_composition_is_a_verdict_on_both_paths(cli_case, tmp_path):
    c = cli_case
    root = tmp_path / 'child temporary root [*]'
    root.mkdir()
    env = dict(os.environ, TMPDIR=str(root))
    for preamble in (False, True):
        argv = c['prepare']('true\n' if preamble else 'true\x00\n')
        if preamble:
            path = c['doc'].with_suffix('.pre')
            path.write_bytes(b'X=a\x00b')
            argv += ['--preamble-file', str(path)]
        result = cli_run(argv, env=env)
        lines = cli_verdict(result, 'LAUNCH_FAILED stage=spawn', 2)
        assert 'rc=' not in lines[0]
        diagnostics = [line.removeprefix('os_error: ') for line in lines if line.startswith('os_error: ')]
        assert diagnostics == [json.dumps('embedded null byte')], 'spawn ValueError must be a quoted os_error diagnostic'
        assert list(root.iterdir()) == [], 'NUL composition refusal must remove the temporary cwd'


def test_cli_launch_failed_lines(cli_case, monkeypatch, capsys):
    for head in ('LAUNCH_FAILED stage=spawn', 'LAUNCH_FAILED stage=mkdtemp'):
        result = (real_cli_producer(cli_case, head) if head.endswith('spawn')
                  else injected_cli_producer(cli_case, head, monkeypatch, capsys))
        lines = cli_verdict(result, head, 2)
        assert 'rc=' not in lines[0]
        diagnostics = [line.removeprefix('os_error: ') for line in lines if line.startswith('os_error: ')]
        assert len(diagnostics) == 1 and diagnostics[0].startswith('"') and json.loads(diagnostics[0]), 'launch failure must render its quoted OS error'


def test_cli_bad_timeout_values(cli_case):
    c = cli_case
    c['err'].write_bytes(b'keep\xff')
    for value in ('0', '-1', 'nan', 'inf', 'abc'):
        result = cli_run(c['prepare'](c['effect']) + ['--shell-timeout', value] + stream_args(c))
        lines = cli_verdict(result, 'BAD_TIMEOUT')
        assert lines[0] == 'DOCBLOCK: BAD_TIMEOUT value=' + json.dumps(value)
        assert not c['marker'].exists() and not c['out'].exists(), 'validate timeout before execution or reservation'
        assert c['err'].read_bytes() == b'keep\xff', 'invalid timeout must not change existing stderr'


def test_non_numeric_timeout_is_bad_timeout(cli_case):
    c = cli_case
    raw = c['hostile']
    lines = cli_refusal(c, c['prepare'](c['effect']) + ['--shell-timeout', raw], 'BAD_TIMEOUT')
    assert lines[0] == 'DOCBLOCK: BAD_TIMEOUT value=' + json.dumps(raw, ensure_ascii=False)


def test_parser_rejects_all_dir_and_abbreviations(cli_case):
    c = cli_case
    for extra in (['--all'], ['--dir', 'x'], ['--shell-t', '5']):
        result = cli_run(c['prepare'](c['effect']) + extra)
        lines = cli_verdict(result, 'BAD_ARGS')
        assert len(lines) == 1 and lines[0].startswith('DOCBLOCK: BAD_ARGS message="')
        assert 'usage:' not in result.stdout and not c['marker'].exists(), 'complete argv must reject abbreviations before running'


def test_exactly_one_tagged_fence_in_the_tree():
    tagged = []
    for path in REPO_ROOT.glob("*/**/*.md"):
        rel = path.relative_to(REPO_ROOT)
        if (
            rel.parts[0] not in ("h-mad", "handoff")
            or "archive" in rel.parts
            or any(part.startswith(".") for part in rel.parts)
        ):
            continue
        tagged.extend(
            event for event in dbe._fence_events(path.read_text(encoding="utf-8"))
            if event.kind == "open" and event.candidate and "hmad:exec" in event.info.split()[1:]
        )
    assert len(tagged) == 1, "the executed markdown documentation surface must contain exactly one hmad:exec fence"


def test_suite_floor_holds():
    if os.environ.get("DOCBLOCK_FLOOR_INNER") == "1":
        pytest.skip("inner collection run")

    env = {**os.environ, "DOCBLOCK_FLOOR_INNER": "1"}
    common = [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"]
    suite = subprocess.run(common, cwd=REPO_ROOT, env=env, capture_output=True, text=True, timeout=120)
    module = subprocess.run(
        common + ["h-mad/tests/test_h_mad_doc_block_exec.py"],
        cwd=REPO_ROOT, env=env, capture_output=True, text=True, timeout=120,
    )
    assert suite.returncode == 0 and module.returncode == 0, (
        f"collection must succeed:\n{suite.stdout}\n{suite.stderr}\n{module.stdout}\n{module.stderr}"
    )
    required = (
        "h-mad/tests/test_h_mad_collect_report_docs.py::test_gate_block_resolves_through_doc_block_exec",
        "h-mad/tests/test_h_mad_collect_report_docs.py::test_recipe_runs_through_run_block",
        "h-mad/tests/test_h_mad_collect_report_docs.py::test_gate_block_refuses_an_untagged_recipe",
        "h-mad/tests/test_h_mad_collect_report_docs.py::test_exec_block_scan_performs_no_execution",
        "h-mad/tests/test_h_mad_collect_report_docs.py::test_consumer_calls_the_helper_module_qualified",
        "h-mad/tests/test_h_mad_collect_report_docs.py::test_only_the_exec_scan_hand_rolls_extraction",
        "h-mad/tests/test_docsections.py::test_docsections_delegates_to_the_authoritative_bounder",
        "h-mad/tests/test_h_mad_portable_timeout.py::test_no_document_or_script_emits_a_bare_timeout_command[h_mad_doc_block_exec.py]",
        "h-mad/tests/test_h_mad_portable_timeout.py::test_no_document_or_script_rests_on_an_unconditional_absence_claim[h_mad_doc_block_exec.py]",
    )
    for node in required:
        assert node in suite.stdout, f"the suite floor must account for {node}"
    suite_count = int(re.search(r"(\d+) tests collected", suite.stdout).group(1))
    module_count = int(re.search(r"(\d+) tests collected", module.stdout).group(1))
    assert suite_count >= 2748 + module_count + len(required), (
        "the repository-root suite floor must include this feature's collected nodes"
    )
