"""Prescribed python blocks are run against their target module's self-source guards.

Skill-candidates row "run prescribed test-helper blocks against the live module's
guards before RED" (2026-09-02). The pin-agents-tail-banner impl-plan prescribed a
`_orca_read_dir` helper for `test_hmad_dispatch.py` that called the banned temp-dir
constructor; that module's own guard refuses the literal in its source. 53 audit
cycles passed the block because nobody ran it beside the guard, and the first RED
dispatch came back with 3 failures instead of 2.

The checker selects guards by what they DO (read their own `__file__`), not by
their name: only one of the repo's three self-source guards is named `*_guard`.
"""
from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parent.parent
REPO_ROOT = SKILL.parent
SCRIPT = SKILL / "scripts" / "h_mad_prescribed_block_guards.py"

BANNED = "tempfile." + "mkdtemp("

FIXTURE_MODULE = textwrap.dedent(
    '''\
    from pathlib import Path


    def test_no_banned_constructor():
        source = Path(__file__).read_text()
        assert "tempfile." + "mkdtemp(" not in source, "the temp-dir constructor is banned here"


    def test_reads_another_module_not_itself():
        import json
        assert "zzz" + "_forbidden" not in Path(json.__file__).read_text()


    class TestNested:
        def test_one_findall(self):
            assert Path(__file__).read_text().count("re.find" + "all(") <= 1, "one findall only"


    def test_ordinary():
        assert 1 + 1 == 2
    '''
)


def _repo(tmp_path: Path, module: str = FIXTURE_MODULE, name: str = "test_fixture_mod.py") -> Path:
    tests = tmp_path / "tests"
    tests.mkdir(exist_ok=True)
    (tests / name).write_text(module, encoding="utf-8")
    return tmp_path


def _plan(tmp_path: Path, body: str) -> Path:
    plan = tmp_path / "f.impl-plan.md"
    plan.write_text(textwrap.dedent(body), encoding="utf-8")
    return plan


def _run(plan: Path, root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(plan), "--repo-root", str(root)],
        capture_output=True, text=True, cwd=root, timeout=300,
    )


def _verdict(proc: subprocess.CompletedProcess) -> str:
    lines = [ln for ln in proc.stdout.splitlines() if ln.startswith("PRESCRIBED-BLOCKS:")]
    assert len(lines) == 1, proc.stdout + proc.stderr
    return lines[0]


def test_a_banned_literal_in_a_prescribed_block_is_a_collision(tmp_path):
    root = _repo(tmp_path)
    plan = _plan(tmp_path, f"""\
        ## Task 1

        Test helpers added to `tests/test_fixture_mod.py`:
        ```python
        def _scratch(tmp_path):
            return {BANNED}dir=tmp_path)
        ```
        """)
    proc = _run(plan, root)
    assert proc.returncode == 0, proc.stderr
    assert _verdict(proc).startswith("PRESCRIBED-BLOCKS: FAIL collisions=1 "), proc.stdout
    collision = [ln for ln in proc.stdout.splitlines() if ln.startswith("COLLISION:")]
    assert collision == [
        f"COLLISION: {plan}:4 tests/test_fixture_mod.py::test_no_banned_constructor"
        " -- the temp-dir constructor is banned here"
    ], proc.stdout


def test_a_clean_block_passes(tmp_path):
    root = _repo(tmp_path)
    plan = _plan(tmp_path, """\
        Helpers for `tests/test_fixture_mod.py`:
        ```python
        def _scratch(tmp_path):
            d = tmp_path / "x"
            d.mkdir()
            return d
        ```
        """)
    proc = _run(plan, root)
    assert _verdict(proc) == "PRESCRIBED-BLOCKS: PASS checked=1 skipped=0 guards=2", proc.stdout


def test_a_guard_is_found_by_reading_its_own_file_not_by_its_name(tmp_path):
    # `TestNested.test_one_findall` is a method, and neither guard is named *_guard.
    root = _repo(tmp_path)
    plan = _plan(tmp_path, """\
        Add to `tests/test_fixture_mod.py`:
        ```python
        def _bodies(text):
            return re.findall(r"a", text) + re.findall(r"b", text)
        ```
        """)
    proc = _run(plan, root)
    assert _verdict(proc).startswith("PRESCRIBED-BLOCKS: FAIL collisions=1 "), proc.stdout
    assert "tests/test_fixture_mod.py::TestNested::test_one_findall -- one findall only" in proc.stdout


def test_a_guard_reading_another_modules_source_is_not_run(tmp_path):
    root = _repo(tmp_path)
    plan = _plan(tmp_path, """\
        Add to `tests/test_fixture_mod.py`:
        ```python
        X = "zzz_forbidden"
        ```
        """)
    proc = _run(plan, root)
    assert _verdict(proc) == "PRESCRIBED-BLOCKS: PASS checked=1 skipped=0 guards=2", proc.stdout


def test_a_test_that_only_locates_siblings_from_its_file_is_not_a_guard(tmp_path):
    # Measured on the corpus: selecting on "names __file__" picked up tests that
    # build `Path(__file__).parent / ...`, and the redirect broke them (24 false
    # collisions in one plan, all FileNotFoundError).
    module = FIXTURE_MODULE + textwrap.dedent(
        '''

        def test_sibling_exists():
            assert (Path(__file__).resolve().parent / "test_fixture_mod.py").is_file()
        ''')
    root = _repo(tmp_path, module)
    plan = _plan(tmp_path, """\
        Add to `tests/test_fixture_mod.py`:
        ```python
        A = 1
        ```
        """)
    proc = _run(plan, root)
    assert _verdict(proc) == "PRESCRIBED-BLOCKS: PASS checked=1 skipped=0 guards=2", proc.stdout


def test_a_mutation_replace_block_is_skipped(tmp_path):
    # A mutation row's `replace` text is MEANT to trip the guard.
    root = _repo(tmp_path)
    plan = _plan(tmp_path, f"""\
        Mutation for `tests/test_fixture_mod.py`; `replace` is:
        ```python
        d = {BANNED})
        ```
        """)
    proc = _run(plan, root)
    assert _verdict(proc) == "PRESCRIBED-BLOCKS: PASS checked=0 skipped=1 guards=0", proc.stdout


def test_a_block_whose_prose_names_two_modules_is_not_attributed(tmp_path):
    root = _repo(tmp_path)
    _repo(tmp_path, "def test_x():\n    pass\n", name="test_other.py")
    plan = _plan(tmp_path, f"""\
        Unlike `tests/test_other.py`, `tests/test_fixture_mod.py` gets:
        ```python
        d = {BANNED})
        ```
        """)
    proc = _run(plan, root)
    assert _verdict(proc) == "PRESCRIBED-BLOCKS: PASS checked=0 skipped=1 guards=0", proc.stdout


def test_attribution_comes_only_from_prose_since_the_previous_fence(tmp_path):
    root = _repo(tmp_path)
    plan = _plan(tmp_path, f"""\
        Add to `tests/test_fixture_mod.py`:
        ```python
        A = 1
        ```
        And separately, in a new script:
        ```python
        d = {BANNED})
        ```
        """)
    proc = _run(plan, root)
    assert _verdict(proc) == "PRESCRIBED-BLOCKS: PASS checked=1 skipped=1 guards=2", proc.stdout


def test_a_bare_basename_resolves_when_it_is_unique(tmp_path):
    root = _repo(tmp_path)
    plan = _plan(tmp_path, f"""\
        Add to `test_fixture_mod.py`:
        ```python
        d = {BANNED})
        ```
        """)
    proc = _run(plan, root)
    assert _verdict(proc).startswith("PRESCRIBED-BLOCKS: FAIL collisions=1 "), proc.stdout


def test_a_block_for_a_module_that_does_not_exist_is_not_checked(tmp_path):
    root = _repo(tmp_path)
    plan = _plan(tmp_path, f"""\
        Create `tests/test_brand_new.py`:
        ```python
        d = {BANNED})
        ```
        """)
    proc = _run(plan, root)
    assert _verdict(proc) == "PRESCRIBED-BLOCKS: PASS checked=0 skipped=1 guards=0", proc.stdout


def test_prose_naming_a_module_that_does_not_exist_yet_is_not_attributed(tmp_path):
    # "Create the new module, modelled on the existing one": the block belongs to
    # the NEW file, so the existing module's guards say nothing about it.
    root = _repo(tmp_path)
    plan = _plan(tmp_path, f"""\
        Create `tests/test_brand_new.py`, modelled on `tests/test_fixture_mod.py`:
        ```python
        d = {BANNED})
        ```
        """)
    proc = _run(plan, root)
    assert _verdict(proc) == "PRESCRIBED-BLOCKS: PASS checked=0 skipped=1 guards=0", proc.stdout


def test_only_python_blocks_are_checked(tmp_path):
    root = _repo(tmp_path)
    plan = _plan(tmp_path, f"""\
        Run beside `tests/test_fixture_mod.py`:
        ```sh
        echo "{BANNED})"
        ```
        """)
    proc = _run(plan, root)
    assert _verdict(proc) == "PRESCRIBED-BLOCKS: PASS checked=0 skipped=0 guards=0", proc.stdout


def test_a_block_carrying_triple_quotes_is_still_checked(tmp_path):
    root = _repo(tmp_path)
    plan = _plan(tmp_path, f"""\
        Add to `tests/test_fixture_mod.py`:
        ```python
        def _h():
            \'\'\'doc\'\'\'
            \"\"\"doc\"\"\"
            return {BANNED}dir=x,   # rest elided: does not parse, carries both quote forms
        ```
        """)
    proc = _run(plan, root)
    assert _verdict(proc).startswith("PRESCRIBED-BLOCKS: FAIL collisions=1 "), proc.stdout
    assert "WRAPPED:" in proc.stdout


def test_a_guard_already_red_on_the_live_module_is_not_blamed_on_the_block(tmp_path):
    module = FIXTURE_MODULE + f"\n\nLIVE = '{BANNED})'\n"
    root = _repo(tmp_path, module)
    plan = _plan(tmp_path, """\
        Add to `tests/test_fixture_mod.py`:
        ```python
        A = 1
        ```
        """)
    proc = _run(plan, root)
    assert _verdict(proc).startswith("PRESCRIBED-BLOCKS: INCOMPLETE "), proc.stdout
    assert "BASELINE-RED: tests/test_fixture_mod.py::test_no_banned_constructor" in proc.stdout
    assert "COLLISION:" not in proc.stdout


def test_a_module_that_cannot_import_is_incomplete_not_pass(tmp_path):
    module = "import no_such_module_anywhere\n" + FIXTURE_MODULE
    root = _repo(tmp_path, module)
    plan = _plan(tmp_path, f"""\
        Add to `tests/test_fixture_mod.py`:
        ```python
        d = {BANNED})
        ```
        """)
    proc = _run(plan, root)
    assert proc.returncode == 0, proc.stderr
    assert _verdict(proc).startswith("PRESCRIBED-BLOCKS: INCOMPLETE "), proc.stdout
    assert "UNRUNNABLE: tests/test_fixture_mod.py" in proc.stdout


def test_a_self_source_guard_that_takes_a_fixture_is_unrunnable(tmp_path):
    module = FIXTURE_MODULE + textwrap.dedent(
        '''

        def test_needs_fixture(tmp_path):
            assert "nope" not in Path(__file__).read_text()
        ''')
    root = _repo(tmp_path, module)
    plan = _plan(tmp_path, """\
        Add to `tests/test_fixture_mod.py`:
        ```python
        A = 1
        ```
        """)
    proc = _run(plan, root)
    assert _verdict(proc).startswith("PRESCRIBED-BLOCKS: INCOMPLETE "), proc.stdout
    assert "UNRUNNABLE: tests/test_fixture_mod.py::test_needs_fixture" in proc.stdout


def test_the_live_module_and_its_directory_are_never_written(tmp_path):
    root = _repo(tmp_path)
    module = root / "tests" / "test_fixture_mod.py"
    before = module.read_bytes()
    plan = _plan(tmp_path, f"""\
        Add to `tests/test_fixture_mod.py`:
        ```python
        d = {BANNED})
        ```
        """)
    _run(plan, root)
    assert module.read_bytes() == before
    assert sorted(p.name for p in (root / "tests").iterdir() if p.name != "__pycache__") == [
        "test_fixture_mod.py"
    ]


def test_an_unreadable_plan_is_unreadable_and_exits_2(tmp_path):
    proc = _run(tmp_path / "missing.impl-plan.md", tmp_path)
    assert proc.returncode == 2
    assert _verdict(proc) == "PRESCRIBED-BLOCKS: UNREADABLE"


def test_skill_md_runs_the_check_before_the_first_red_and_lists_the_script():
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    red = next(ln for ln in text.splitlines() if ln.startswith("- **5d** — RED dispatch"))
    assert "h_mad_prescribed_block_guards.py" in red
    assert "Before the feature's first RED dispatch" in red
    assert "`PRESCRIBED-BLOCKS:` token" in red
    assert "re-dispatch `implplan-author` with each `COLLISION:` line" in red
    assert "- `h_mad_prescribed_block_guards.py` —" in text


def test_the_original_incident_is_caught_against_the_real_module(tmp_path):
    """The block v1.59 of pin-agents-tail-banner had to rewrite, against the live guard."""
    plan = _plan(tmp_path, f"""\
        Test helpers added to `h-mad/tests/test_hmad_dispatch.py`:
        ```python
        def _orca_read_dir(tmp_path, envelopes):
            d = {BANNED}dir=tmp_path, prefix="reads-")
            for handle, text in envelopes.items():
                (Path(d) / f"{{handle}}.json").write_text(text, encoding="utf-8")
            return d
        ```
        """)
    proc = _run(plan, REPO_ROOT)
    assert _verdict(proc).startswith("PRESCRIBED-BLOCKS: FAIL collisions=1 "), proc.stdout
    assert ("h-mad/tests/test_hmad_dispatch.py::test_no_mkdtemp_and_no_pin_file_leak_guard"
            in proc.stdout), proc.stdout


# --- Review round 1 (change-reviewer, 2026-10-04): fail-open shapes and corpus misses ---

def _block_plan(tmp_path: Path, literal: str = BANNED) -> Path:
    return _plan(tmp_path, f"""\
        Add to `tests/test_fixture_mod.py`:
        ```python
        def _h(tmp_path):
            return {literal}dir=tmp_path)
        ```
        """)


@pytest.mark.parametrize("shape", ["module_constant", "helper", "decorated", "derived_constant"])
def test_a_guard_reading_its_file_indirectly_still_sees_the_block(tmp_path, shape):
    # Rebinding `__file__` in the test's own globals reached none of these: the
    # constant was read at import, the helper and the wrapper keep the live globals.
    bodies = {
        "module_constant": '''
            SOURCE = Path(__file__).read_text()

            def test_g():
                assert "tempfile." + "mkdtemp(" not in SOURCE, "banned"
            ''',
        "derived_constant": '''
            SOURCE = Path(__file__).read_text()
            LINES = SOURCE.splitlines()

            def test_g():
                assert not any("tempfile." + "mkdtemp(" in ln for ln in LINES), "banned"
            ''',
        "helper": '''
            def _source():
                return Path(__file__).read_text()

            def test_g():
                assert "tempfile." + "mkdtemp(" not in _source(), "banned"
            ''',
        "decorated": '''
            import functools

            def _deco(fn):
                @functools.wraps(fn)
                def wrapper():
                    return fn()
                return wrapper

            @_deco
            def test_g():
                assert "tempfile." + "mkdtemp(" not in Path(__file__).read_text(), "banned"
            ''',
    }
    module = "from pathlib import Path\n" + textwrap.dedent(bodies[shape])
    root = _repo(tmp_path, module)
    proc = _run(_block_plan(tmp_path), root)
    assert _verdict(proc).startswith("PRESCRIBED-BLOCKS: FAIL collisions=1 "), proc.stdout
    assert "tests/test_fixture_mod.py::test_g -- banned" in proc.stdout


def test_a_guard_that_parses_its_own_source_sees_the_block_as_code(tmp_path):
    module = textwrap.dedent('''\
        import ast
        from pathlib import Path

        def test_no_mkdtemp_attribute():
            tree = ast.parse(Path(__file__).read_text())
            assert not [n for n in ast.walk(tree)
                        if isinstance(n, ast.Attribute) and n.attr == "mkdtemp"], "ast banned"
        ''')
    root = _repo(tmp_path, module)
    proc = _run(_block_plan(tmp_path), root)
    assert _verdict(proc).startswith("PRESCRIBED-BLOCKS: FAIL collisions=1 "), proc.stdout
    assert "WRAPPED:" not in proc.stdout


def test_an_excerpt_that_does_not_parse_in_place_is_wrapped_and_says_so(tmp_path):
    root = _repo(tmp_path)
    plan = _plan(tmp_path, f"""\
        Add to `tests/test_fixture_mod.py`:
        ```python
        d = {BANNED}dir=tmp_path,   # rest of the call elided
        ```
        """)
    proc = _run(plan, root)
    assert _verdict(proc).startswith("PRESCRIBED-BLOCKS: FAIL collisions=1 "), proc.stdout
    assert f"WRAPPED: {plan}:2" in proc.stdout


def test_a_guard_reading_its_file_through_open_is_selected(tmp_path):
    module = textwrap.dedent('''\
        def test_open_guard():
            with open(__file__, encoding="utf-8") as handle:
                assert "tempfile." + "mkdtemp(" not in handle.read(), "open banned"
        ''')
    root = _repo(tmp_path, module)
    proc = _run(_block_plan(tmp_path), root)
    assert _verdict(proc).startswith("PRESCRIBED-BLOCKS: FAIL collisions=1 "), proc.stdout
    assert "::test_open_guard -- open banned" in proc.stdout


def test_a_guard_red_by_a_non_assertion_error_is_a_collision(tmp_path):
    # pytest.fail raises a BaseException subclass, not AssertionError.
    module = textwrap.dedent('''\
        from pathlib import Path

        class Failed(BaseException):
            pass

        def test_raises_guard():
            if "tempfile." + "mkdtemp(" in Path(__file__).read_text():
                raise Failed("raised banned")
        ''')
    root = _repo(tmp_path, module)
    proc = _run(_block_plan(tmp_path), root)
    assert _verdict(proc).startswith("PRESCRIBED-BLOCKS: FAIL collisions=1 "), proc.stdout
    assert "::test_raises_guard -- Failed: raised banned" in proc.stdout


def test_a_guard_that_locates_siblings_and_reads_itself_is_not_broken_by_the_check(tmp_path):
    module = textwrap.dedent('''\
        from pathlib import Path

        def test_both():
            assert (Path(__file__).parent / "test_fixture_mod.py").is_file(), "sibling lost"
            assert "zzz" + "_banned" not in Path(__file__).read_text(), "zzz banned"
        ''')
    root = _repo(tmp_path, module)
    plan = _plan(tmp_path, """\
        Add to `tests/test_fixture_mod.py`:
        ```python
        A = 1
        ```
        """)
    proc = _run(plan, root)
    assert _verdict(proc) == "PRESCRIBED-BLOCKS: PASS checked=1 skipped=0 guards=1", proc.stdout


def test_a_template_production_block_is_not_checked_against_the_test_module(tmp_path):
    # references/inline-protocols.md puts **Production file** and **Test file** above
    # the **Code structure** block, which holds PRODUCTION code.
    root = _repo(tmp_path)
    plan = _plan(tmp_path, f"""\
        **Production file**: `scripts/m.py`
        **Test file**: `tests/test_fixture_mod.py`

        **Code structure**:
        ```python
        def make():
            return {BANNED})
        ```
        """)
    proc = _run(plan, root)
    assert _verdict(proc) == "PRESCRIBED-BLOCKS: PASS checked=0 skipped=1 guards=0", proc.stdout


def test_a_template_block_whose_production_file_is_a_test_module_is_checked(tmp_path):
    # preflight-signal-discipline Task 1: the harness IS the unit under test, so its
    # **Production file** is `test_hmad_dispatch.py` and the block belongs there.
    root = _repo(tmp_path)
    plan = _plan(tmp_path, f"""\
        **Production file**: `tests/test_fixture_mod.py`
        **Test file**: `tests/test_fixture_mod.py`

        **Code structure**:
        ```python
        # {BANNED}) would be wrong here
        ```
        """)
    proc = _run(plan, root)
    assert _verdict(proc).startswith("PRESCRIBED-BLOCKS: FAIL collisions=1 "), proc.stdout


def test_a_block_whose_first_comment_names_its_module_is_attributed_to_it(tmp_path):
    # pin-agents-tail-banner:1456 and doc-block-exec:4201 open with
    # `# h-mad/tests/<module>.py — ...`; the prose above names nothing.
    root = _repo(tmp_path)
    plan = _plan(tmp_path, f"""\
        Then, in the same task:
        ```python
        # tests/test_fixture_mod.py — added beside the existing helpers
        d = {BANNED})
        ```
        """)
    proc = _run(plan, root)
    assert _verdict(proc).startswith("PRESCRIBED-BLOCKS: FAIL collisions=1 "), proc.stdout


def test_a_subproject_relative_path_resolves_by_unique_suffix(tmp_path):
    root = tmp_path
    (root / "sub" / "tests").mkdir(parents=True)
    (root / "sub" / "tests" / "test_fixture_mod.py").write_text(FIXTURE_MODULE, encoding="utf-8")
    plan = _plan(tmp_path, f"""\
        The spec says `tests/test_fixture_mod.py`; the file is `sub/tests/test_fixture_mod.py`:
        ```python
        d = {BANNED})
        ```
        """)
    proc = _run(plan, root)
    assert _verdict(proc).startswith("PRESCRIBED-BLOCKS: FAIL collisions=1 "), proc.stdout


def test_an_ambiguous_bare_basename_is_refused(tmp_path):
    root = tmp_path
    for sub in ("a", "b"):
        (root / sub).mkdir()
        (root / sub / "test_fixture_mod.py").write_text(FIXTURE_MODULE, encoding="utf-8")
    plan = _plan(tmp_path, f"""\
        Add to `test_fixture_mod.py`:
        ```python
        d = {BANNED})
        ```
        """)
    proc = _run(plan, root)
    assert _verdict(proc) == "PRESCRIBED-BLOCKS: PASS checked=0 skipped=1 guards=0", proc.stdout


def test_a_heading_resets_the_attribution_prose(tmp_path):
    root = _repo(tmp_path)
    plan = _plan(tmp_path, f"""\
        Context: `tests/test_fixture_mod.py` is untouched by this task.

        ## Task 2 — a new script

        ```python
        d = {BANNED})
        ```
        """)
    proc = _run(plan, root)
    assert _verdict(proc) == "PRESCRIBED-BLOCKS: PASS checked=0 skipped=1 guards=0", proc.stdout


def test_a_list_indented_python_fence_is_checked(tmp_path):
    root = _repo(tmp_path)
    plan = _plan(tmp_path, f"""\
        - [ ] AC-1: add to `tests/test_fixture_mod.py`:
              ```python
              def _h(tmp_path):
                  return {BANNED}dir=tmp_path)
              ```
        - [ ] AC-2: nothing.
        """)
    proc = _run(plan, root)
    assert _verdict(proc).startswith("PRESCRIBED-BLOCKS: FAIL collisions=1 "), proc.stdout
    assert f"COLLISION: {plan}:2 " in proc.stdout


def test_an_unclosed_python_fence_is_reported_not_silent(tmp_path):
    root = _repo(tmp_path)
    plan = _plan(tmp_path, f"""\
        Add to `tests/test_fixture_mod.py`:
        ```python
        d = {BANNED})
        """)
    proc = _run(plan, root)
    assert _verdict(proc).startswith("PRESCRIBED-BLOCKS: INCOMPLETE "), proc.stdout
    assert f"UNRUNNABLE: {plan}:2 -- python fence never closed" in proc.stdout


def test_a_brace_line_printed_at_import_is_not_read_as_the_childs_result(tmp_path):
    module = 'print(\'{"config": 1}\')\n' + FIXTURE_MODULE + textwrap.dedent('''

        def test_noisy():
            print("scanning", end="")
            assert "zzz" + "_banned" not in Path(__file__).read_text()
        ''')
    root = _repo(tmp_path, module)
    proc = _run(_block_plan(tmp_path), root)
    assert proc.returncode == 0, proc.stderr
    assert _verdict(proc).startswith("PRESCRIBED-BLOCKS: FAIL collisions=1 "), proc.stdout


def test_a_fail_token_also_carries_what_did_not_run(tmp_path):
    module = FIXTURE_MODULE + textwrap.dedent('''

        def test_needs_fixture(tmp_path):
            assert "nope" not in Path(__file__).read_text()
        ''')
    root = _repo(tmp_path, module)
    proc = _run(_block_plan(tmp_path), root)
    assert _verdict(proc).startswith(
        "PRESCRIBED-BLOCKS: FAIL collisions=1 unrunnable=1 baseline_red=0 "), proc.stdout


def _load_script():
    import importlib.util
    spec = importlib.util.spec_from_file_location("_pbg_under_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_a_child_that_times_out_is_unrunnable_not_pass(tmp_path, monkeypatch):
    pbg = _load_script()
    root = _repo(tmp_path)

    def hang(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], 1)

    monkeypatch.setattr(pbg.subprocess, "run", hang)
    token, details = pbg.check(_block_plan(tmp_path), root)
    assert token.startswith("PRESCRIBED-BLOCKS: INCOMPLETE unrunnable=1 "), (token, details)


def test_a_guard_missing_from_the_childs_result_is_unrunnable_not_pass(tmp_path, monkeypatch):
    pbg = _load_script()
    root = _repo(tmp_path)
    calls = []

    def partial(module, source, names, root_):
        calls.append(source)
        if len(calls) == 1:   # baseline: every guard green
            return {"results": {n: {"status": "pass"} for n in names}}
        return {"results": {}}

    monkeypatch.setattr(pbg, "_run_guards", partial)
    token, details = pbg.check(_block_plan(tmp_path), root)
    assert token.startswith("PRESCRIBED-BLOCKS: INCOMPLETE "), (token, details)
    assert any(d.startswith("UNRUNNABLE: tests/test_fixture_mod.py::") for d in details), details


# --- Review round 2: static selection gaps, attribution false positives, unpinned branches ---

@pytest.mark.parametrize("shape", ["self_path", "parent_dir", "path_open", "class_attr", "read_bytes_constant"])
def test_more_ways_of_reading_its_own_file_are_selected(tmp_path, shape):
    bodies = {
        "self_path": '''
            SELF = Path(__file__).resolve()

            def test_g():
                assert "tempfile." + "mkdtemp(" not in SELF.read_text(), "banned"
            ''',
        "parent_dir": '''
            TESTS = Path(__file__).resolve().parent

            def test_g():
                assert "tempfile." + "mkdtemp(" not in (TESTS / "test_fixture_mod.py").read_text(), "banned"
            ''',
        "path_open": '''
            def test_g():
                with Path(__file__).open(encoding="utf-8") as fh:
                    assert "tempfile." + "mkdtemp(" not in fh.read(), "banned"
            ''',
        "class_attr": '''
            class TestSource:
                SOURCE = Path(__file__).read_text()

                def test_g(self):
                    assert "tempfile." + "mkdtemp(" not in self.SOURCE, "banned"
            ''',
        "read_bytes_constant": '''
            RAW = Path(__file__).read_bytes()

            def test_g():
                assert b"tempfile." + b"mkdtemp(" not in RAW, "banned"
            ''',
    }
    module = "from pathlib import Path\n" + textwrap.dedent(bodies[shape])
    root = _repo(tmp_path, module)
    proc = _run(_block_plan(tmp_path), root)
    assert _verdict(proc).startswith("PRESCRIBED-BLOCKS: FAIL collisions=1 "), proc.stdout


def test_a_new_module_is_not_resolved_onto_another_projects_file_by_suffix(tmp_path):
    root = tmp_path
    (root / "projB" / "tests").mkdir(parents=True)
    (root / "projB" / "tests" / "test_fixture_mod.py").write_text(FIXTURE_MODULE, encoding="utf-8")
    plan = _plan(tmp_path, f"""\
        Create the new module `tests/test_fixture_mod.py` for projA:
        ```python
        d = {BANNED})
        ```
        """)
    proc = _run(plan, root)
    assert _verdict(proc) == "PRESCRIBED-BLOCKS: PASS checked=0 skipped=1 guards=0", proc.stdout


def test_a_helper_block_in_a_task_with_a_production_header_is_still_checked(tmp_path):
    # The Production-file rule is for the template's **Code structure** block only.
    root = _repo(tmp_path)
    plan = _plan(tmp_path, f"""\
        **Production file**: `scripts/m.py`
        **Test file**: `tests/test_fixture_mod.py`

        **Description**: the work. Test helpers added to `tests/test_fixture_mod.py`:
        ```python
        def _h(tmp_path):
            return {BANNED}dir=tmp_path)
        ```
        """)
    proc = _run(plan, root)
    assert _verdict(proc).startswith("PRESCRIBED-BLOCKS: FAIL collisions=1 "), proc.stdout


def test_a_first_comment_that_leads_with_a_production_path_is_not_self_named(tmp_path):
    root = _repo(tmp_path)
    plan = _plan(tmp_path, f"""\
        Then:
        ```python
        # scripts/m.py -- contract pinned by tests/test_fixture_mod.py
        d = {BANNED})
        ```
        """)
    proc = _run(plan, root)
    assert _verdict(proc) == "PRESCRIBED-BLOCKS: PASS checked=0 skipped=1 guards=0", proc.stdout


def test_only_the_first_line_can_self_name_a_block(tmp_path):
    root = _repo(tmp_path)
    plan = _plan(tmp_path, f"""\
        Then:
        ```python
        # a new script
        # (unlike tests/test_fixture_mod.py)
        d = {BANNED})
        ```
        """)
    proc = _run(plan, root)
    assert _verdict(proc) == "PRESCRIBED-BLOCKS: PASS checked=0 skipped=1 guards=0", proc.stdout


def test_an_indented_fence_cut_off_by_a_heading_is_reported(tmp_path):
    root = _repo(tmp_path)
    plan = _plan(tmp_path, f"""\
        - [ ] AC-1: add to `tests/test_fixture_mod.py`:
              ```python
              d = {BANNED})

        ## Task 2
        """)
    proc = _run(plan, root)
    assert _verdict(proc).startswith("PRESCRIBED-BLOCKS: INCOMPLETE "), proc.stdout
    assert f"UNRUNNABLE: {plan}:2 -- python fence never closed" in proc.stdout


def test_a_tilde_python_fence_is_checked(tmp_path):
    root = _repo(tmp_path)
    plan = _plan(tmp_path, f"""\
        Add to `tests/test_fixture_mod.py`:
        ~~~python
        d = {BANNED})
        ~~~
        """)
    proc = _run(plan, root)
    assert _verdict(proc).startswith("PRESCRIBED-BLOCKS: FAIL collisions=1 "), proc.stdout


def test_a_repo_root_that_is_not_a_directory_is_unreadable(tmp_path):
    plan = _block_plan(tmp_path)
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), str(plan), "--repo-root", str(tmp_path / "no-such-dir")],
        capture_output=True, text=True, cwd=tmp_path, timeout=60)
    assert proc.returncode == 2
    assert _verdict(proc) == "PRESCRIBED-BLOCKS: UNREADABLE"


def test_a_malformed_child_result_is_unrunnable_not_a_crash(tmp_path, monkeypatch):
    pbg = _load_script()
    root = _repo(tmp_path)

    def bad_child(argv, **kwargs):
        Path(argv[-1]).write_text('{"foo": 1}', encoding="utf-8")
        return subprocess.CompletedProcess(argv, 0, "", "")

    monkeypatch.setattr(pbg.subprocess, "run", bad_child)
    token, details = pbg.check(_block_plan(tmp_path), root)
    assert token.startswith("PRESCRIBED-BLOCKS: INCOMPLETE unrunnable=1 "), (token, details)


def test_the_child_writes_no_bytecode_beside_the_live_module(tmp_path):
    root = _repo(tmp_path)
    _run(_block_plan(tmp_path), root)
    assert not (root / "tests" / "__pycache__").exists()
