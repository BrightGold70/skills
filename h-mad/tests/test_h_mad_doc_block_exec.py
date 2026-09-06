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
