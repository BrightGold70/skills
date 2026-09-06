"""Task 1 RED: scanner/selection contracts and the docsections second consumer.

The module-level import intentionally gives the plan's new-symbol collection
RED. The independently runnable caller wire pin lives in test_docsections.py.
No docsections import belongs at module scope: its import-path mutant must
reach the subprocess assertion, not break collection of its own killer.
"""

from __future__ import annotations

import ast
import dataclasses
import json
import os
from pathlib import Path
import re
import subprocess
import sys

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
