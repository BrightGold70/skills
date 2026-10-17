"""FR-9/FR-10 pins for the implementer-neutral Phase 5 dispatch prompt."""

from test_h_mad_tdd_gate_docs import IMPLEMENTER_PROMPT, _hook_block


def test_prompt_opening_names_no_implementer():
    text = IMPLEMENTER_PROMPT.read_text(encoding="utf-8")
    opening = next((line for line in text.splitlines() if line.startswith("You are")), "")
    assert "the Phase-5 implementer" in opening, (
        "Prompt opening must name the Phase-5 implementer"
    )
    for name in ("Codex", "agy", "grok", "Claude"):
        assert name.casefold() not in opening.casefold(), (
            f"Prompt opening must not name implementer {name!r} (case-insensitive)"
        )
    for slot in ("<INLINE_MODULE_NAME>", "<INLINE_FEATURE>"):
        assert slot in opening, f"Prompt opening must preserve template slot {slot!r}"


def test_hook_line_names_the_agy_gate():
    hook_line = _hook_block(IMPLEMENTER_PROMPT.read_text(encoding="utf-8")).splitlines()[0]
    assert "h-mad-agy-tdd-gate.py" in hook_line, (
        "Hook line must name agy's h-mad-agy-tdd-gate.py gate"
    )


def test_hook_line_names_the_agy_write_tools():
    hook_line = _hook_block(IMPLEMENTER_PROMPT.read_text(encoding="utf-8")).splitlines()[0]
    assert "agy" in hook_line, "Hook line must name agy for its class-(b) write tools"
    for tool in ("write_to_file", "replace_file_content", "multi_replace_file_content",
                 "sed_file", "notebook_edit"):
        assert tool in hook_line, f"Hook line must name agy's class-(b) write tool {tool!r}"


def test_hook_line_says_grok_has_no_write_time_gate():
    hook_line = _hook_block(IMPLEMENTER_PROMPT.read_text(encoding="utf-8")).splitlines()[0]
    assert "grok" in hook_line, "Hook line must name grok's write-time gate status"
    assert "no write-time gate" in hook_line, (
        "Hook line must state that grok has no write-time gate"
    )
