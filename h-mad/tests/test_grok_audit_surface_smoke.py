"""Task 7 RED: D10/D11 smoke contracts, using recorded wrapper authorities."""

import ast
import json
import subprocess
import sys
from pathlib import Path

import pytest

from grokauditfixtures import _hostile_text, load_probe
from grokfixtures import f0_text, f_trunc, f0_with_completed


REPO = Path(__file__).resolve().parents[2]
PROBE = REPO / "docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py"
sys.path.insert(0, str(REPO / "h-mad/scripts"))
import h_mad_audit_cycle as cycle
from h_mad_review_evidence import GROK_MAX_DEPTH, _GROK_TYPES, _json_deeper_than, scan_grok


MISSING_TYPES = "vocab_missing:end,vocab_missing:tool_call,vocab_missing:tool_call_update"
NO_DELIVERY = "no_delivery,nongit_root_refused:grok"


def _report():
    return ("# Synthetic audit\n## Summary\n" + _hostile_text()
            + "\n## Must-fix\nNone\n## Should-fix\nNone\n")


def _result(log, report, *, delivered="report-file", gate="PASS", root=None):
    return cycle.PassResult(1, delivered, report, gate, 0, 0, [],
                            cycle.measure_effort(log, project_root=root), 0)


def _render(results, verdict="PASS", reason=None):
    return cycle.render(results, verdict, reason, feature="paper-lantern",
                        size_status="verified", passes=1)


def _write_cycle(data, surface, *, log=None, verdict="PASS", reason=None,
                 delivered="report-file", effort_item=None, halted=False):
    directory = data / surface
    directory.mkdir(parents=True, exist_ok=True)
    log_path = directory / "p1.log"
    if log is not None:
        log_path.write_text(log, encoding="utf-8")
    report = directory / "collected/paper-lantern.plan.audit.v1.p1.md"
    report.parent.mkdir(exist_ok=True)
    report.write_text(_report(), encoding="utf-8")
    results = [] if halted else [_result(log_path if log is not None else None,
                                         report, delivered=delivered)]
    text = _render(results, verdict, reason)
    if effort_item is not None:
        lines = text.splitlines()
        if "Effort:" in lines:
            start = lines.index("Effort:") + 1
            end = start
            while end < len(lines) and lines[end].startswith("- "):
                end += 1
            lines[start:end] = ["- " + effort_item]
        else:
            lines[1:1] = ["Effort:", "- " + effort_item]
        text = "\n".join(lines) + "\n"
    (directory / "auditcycle.txt").write_text(text, encoding="utf-8")
    return report


@pytest.fixture
def smoke_case(tmp_path, monkeypatch):
    monkeypatch.setenv("HMAD_STUB_HOSTILE", "all")
    data = tmp_path / "s1 [a]* ⟦h-mad⟧"
    _write_cycle(data, "grok", log=f0_text())
    _write_cycle(data, "agy")
    return data


def _run(data, *extra):
    return subprocess.run([sys.executable, str(PROBE), "smoke", "--data", str(data),
                           *map(str, extra)], capture_output=True, text=True, timeout=15)


def _assert_smoke(data, token="SMOKE: PASS", rc=0, *, extra=(), property_name=None):
    result = _run(data, *extra)
    assert (result.returncode, result.stdout.splitlines()[-1:]) == (rc, [token]), (
        f"{property_name or token}: smoke CLI must publish the exact token beside exit {rc}; "
        f"stdout={result.stdout!r}; stderr={result.stderr!r}"
    )
    assert "Traceback" not in result.stderr, "declared smoke outcomes must not print a traceback"
    return result.stdout.splitlines()


def _fail(data, reasons, **kwargs):
    return _assert_smoke(data, "SMOKE: FAIL reason=" + reasons, **kwargs)


def _unreadable(data, kind, path, **kwargs):
    return _assert_smoke(data, f"SMOKE: UNREADABLE reason={kind}:{path}", 2, **kwargs)


def _item_for(data, text, *, shape=None, root=None):
    path = data / "renderer-input.log"
    if text is not None:
        path.write_text(text, encoding="utf-8")
    elif path.exists():
        path.unlink()
    result = _result(path, data / "report.md", root=root)
    if shape is not None:
        assert result.effort["shape"] == shape, "fixture must reach its named measure_effort shape"
    return cycle._effort_items([result])[0]


def _without(text, *types):
    return "\n".join(line for line in text.split("\n")
                     if line and json.loads(line).get("type") not in types) + "\n"


def _vocab_sources(data, py_types, sh_types):
    py, sh = data / "vocab.py", data / "vocab.sh"
    py.write_text("# synthetic vocabulary\n_GROK_TYPES = frozenset(\n"
                  + repr(sorted(py_types)) + ")\n", encoding="utf-8")
    sh.write_text("_GROK_TYPES_RE='" + "|".join(sorted(sh_types)) + "'\n", encoding="utf-8")
    return ("--vocab-py", py, "--vocab-sh", sh)


def _in_process(probe, data, capsys):
    rc = probe.main(["smoke", "--data", str(data)])
    out, err = capsys.readouterr()
    return rc, out.splitlines(), err


def test_smoke_pass(smoke_case):
    lines = _assert_smoke(smoke_case)
    assert "ROOT-ACCEPT: grok=accepted agy=accepted codex=not_run" in lines
    assert "TIMEOUT: wall_seconds=unrecorded" in lines
    assert "GROK-BINARY: unrecorded" in lines
    vocab = [line for line in lines if line.startswith("VOCAB:")]
    assert vocab == sorted(vocab), "VOCAB lines must be sorted by distinct type"
    expected_types = {json.loads(line)["type"] for line in f0_text().splitlines()}
    assert {line.split()[1].removeprefix("type=") for line in vocab} == expected_types
    root_index = lines.index("ROOT-ACCEPT: grok=accepted agy=accepted codex=not_run")
    assert lines[root_index:] == [
        "ROOT-ACCEPT: grok=accepted agy=accepted codex=not_run",
        "TIMEOUT: wall_seconds=unrecorded", "GROK-BINARY: unrecorded", "SMOKE: PASS",
    ], "published lines must follow the D11 order and end on the smoke token"
    assert all(lines.index(line) < root_index for line in vocab)
    for expected in (
        "VOCAB: type=tool_call re=in frozenset=in tool=yes usage=no",
        "VOCAB: type=tool_call_update re=in frozenset=in tool=yes usage=no",
        "VOCAB: type=usage re=in frozenset=in tool=no usage=yes",
        "VOCAB: type=end re=in frozenset=in tool=no usage=yes",
    ):
        assert expected in vocab, "VOCAB flags must describe each type's event keys"
    probe = load_probe(PROBE)
    # One type reader for all three consumers; JSON failures and non-dicts do not count.
    event = {"type": "foreign\u2028kind", "x": {"toolName": _hostile_text()}}
    mixed = f0_text() + "{broken\n[]\n{\"type\":3}\n" + "[" * 2000 + "\n"
    mixed += json.dumps(event, ensure_ascii=False) + "\n"
    types = probe.grok_log_types(mixed)
    assert types["foreign\u2028kind"] == [event], "type reader must split only on LF and retain foreign types"
    assert set(types) == {json.loads(line)["type"] for line in f0_text().splitlines()} | {event["type"]}
    tree = ast.parse(PROBE.read_text(encoding="utf-8"))
    readers = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
               and node.name == "grok_log_types"]
    assert len(readers) == 1, "exactly one grok_log_types definition must serve step 2, reasons and VOCAB"


def test_smoke_pass_on_out_delivery(smoke_case):
    _write_cycle(smoke_case, "grok", log=f0_text(), delivered="out")
    _assert_smoke(smoke_case)
    report = _write_cycle(smoke_case, "grok", log=f0_text(), delivered="out", verdict="FAIL")
    report.write_text("## Must-fix\n- Restore the contract: " + _hostile_text()
                      + "\n## Should-fix\nNone\n", encoding="utf-8")
    _assert_smoke(smoke_case, property_name="GATE FAIL still proves delivery and root acceptance")


def test_smoke_truncated(smoke_case):
    _write_cycle(smoke_case, "grok", log=f_trunc(), verdict="UNVERIFIED",
                 reason="low_evidence_unmeasurable:p1")
    _fail(smoke_case, "truncated,vocab_missing:end,nongit_root_refused:grok")


def test_smoke_vocab_split(smoke_case):
    extra = _vocab_sources(smoke_case, _GROK_TYPES, _GROK_TYPES | {"new_kind"})
    _fail(smoke_case, "vocab_split", extra=extra)


def test_smoke_vocab_missing_end(smoke_case):
    _write_cycle(smoke_case, "grok", log=_without(f0_text(), "end"),
                 effort_item=_item_for(smoke_case, f0_text(), shape="grok"))
    _fail(smoke_case, "vocab_missing:end")


def test_smoke_vocab_missing_tool_call(smoke_case):
    _write_cycle(smoke_case, "grok", log=_without(f0_text(), "tool_call"))
    _fail(smoke_case, "vocab_missing:tool_call")


def test_smoke_vocab_missing_tool_call_update(smoke_case):
    _write_cycle(smoke_case, "grok", log=_without(f0_text(), "tool_call_update"))
    _fail(smoke_case, "vocab_missing:tool_call_update")


def test_smoke_no_delivery(smoke_case):
    _write_cycle(smoke_case, "grok", log=f0_text(), delivered="none")
    _fail(smoke_case, NO_DELIVERY)


def test_smoke_no_delivery_on_unscorable(smoke_case):
    for delivery in ("unscorable:in_progress", "unscorable:zero_evidence"):
        _write_cycle(smoke_case, "grok", log=f0_text(), delivered=delivery)
        _fail(smoke_case, NO_DELIVERY)
    # INVALID is a GATE verdict, not an unreadable report or a delivery.
    report = _write_cycle(smoke_case, "grok", log=f0_text())
    report.write_text("# not an audit\n" + _hostile_text(), encoding="utf-8")
    _fail(smoke_case, NO_DELIVERY)


def test_smoke_nongit_root_refused_grok(smoke_case):
    _write_cycle(smoke_case, "grok", log=f0_text(), verdict="UNVERIFIED", reason="low_evidence:p1")
    _fail(smoke_case, "nongit_root_refused:grok")


def test_smoke_nongit_root_refused_agy(smoke_case):
    _write_cycle(smoke_case, "agy", verdict="UNVERIFIED", reason="low_evidence:p1")
    _fail(smoke_case, "nongit_root_refused:agy")


def test_smoke_input_missing(smoke_case):
    # Two simultaneous missing inputs pin each edge of the fixed refusal order.
    grok = smoke_case / "grok"
    agy = smoke_case / "agy"
    (grok / "auditcycle.txt").unlink()
    (grok / "p1.log").unlink()
    (agy / "auditcycle.txt").unlink()
    _unreadable(smoke_case, "input_missing", grok / "auditcycle.txt")
    _write_cycle(smoke_case, "grok", log=f0_text())
    (grok / "p1.log").unlink()
    _unreadable(smoke_case, "input_missing", grok / "p1.log")
    (grok / "p1.log").write_text(f0_text(), encoding="utf-8")
    _unreadable(smoke_case, "input_missing", agy / "auditcycle.txt")
    _write_cycle(smoke_case, "agy")
    (smoke_case / "codex").mkdir()
    _unreadable(smoke_case, "input_missing", smoke_case / "codex/auditcycle.txt")


def test_smoke_input_missing_delivered_collected_report(smoke_case):
    report = next((smoke_case / "grok/collected").glob("*.md"))
    report.unlink()
    (smoke_case / "agy/auditcycle.txt").unlink()
    _unreadable(smoke_case, "input_missing", report)
    _write_cycle(smoke_case, "grok", log=f0_text())
    report = _write_cycle(smoke_case, "agy")
    _write_cycle(smoke_case, "codex")
    report.unlink()
    _unreadable(smoke_case, "input_missing", report)
    _write_cycle(smoke_case, "agy")
    report = next((smoke_case / "codex/collected").glob("*.md"))
    report.unlink()
    _unreadable(smoke_case, "input_missing", report)


def test_smoke_input_unparseable(smoke_case, monkeypatch, capsys):
    audit = smoke_case / "grok/auditcycle.txt"
    for text in ("AUDITCYCLE: MAYBE\n", "AUDITCYCLE: PASS\nAUDITCYCLE: PASS\n", _hostile_text()):
        audit.write_text(text, encoding="utf-8")
        _unreadable(smoke_case, "input_unparseable", audit)
    _write_cycle(smoke_case, "grok", log=f0_text())
    (smoke_case / "grok/p1.log").write_text("[]\n{broken\n{\"type\":3}\n", encoding="utf-8")
    _unreadable(smoke_case, "input_unparseable", smoke_case / "grok/p1.log")
    _write_cycle(smoke_case, "grok", log=f0_text())
    # A dispatched grok cycle without an Effort item refuses its auditcycle path.
    audit.write_text(_render([_result(None, Path("unused"))]), encoding="utf-8")
    _unreadable(smoke_case, "input_unparseable", audit)
    _write_cycle(smoke_case, "grok", log=f0_text())
    for surface in ("agy", "codex"):
        _write_cycle(smoke_case, surface)
        path = smoke_case / surface / "auditcycle.txt"
        path.write_text("AUDITCYCLE: MAYBE\n", encoding="utf-8")
        _unreadable(smoke_case, "input_unparseable", path)
        _write_cycle(smoke_case, surface)
    extra = _vocab_sources(smoke_case, _GROK_TYPES, _GROK_TYPES)
    py, sh = extra[1], extra[3]
    py.write_text("# no frozenset\n", encoding="utf-8")
    sh.write_text("# no regexp\n", encoding="utf-8")
    _unreadable(smoke_case, "input_unparseable", py, extra=extra)
    _vocab_sources(smoke_case, _GROK_TYPES, _GROK_TYPES)
    sh.write_text("# no regexp\n", encoding="utf-8")
    _unreadable(smoke_case, "input_unparseable", sh, extra=extra)
    probe = load_probe(PROBE)
    report = next((smoke_case / "grok/collected").glob("*.md"))
    original = cycle._gate_token

    def no_token(stdout, collected):
        return original("gate output without a token\n", collected)

    monkeypatch.setattr(cycle, "_gate_token", no_token)
    rc, lines, err = _in_process(probe, smoke_case, capsys)
    assert (rc, lines[-1:]) == (2, [f"SMOKE: UNREADABLE reason=input_unparseable:{report}"]), (
        "_gate_token OperationalError must map to the collected report's path"
    )
    assert "Traceback" not in err


def test_smoke_drifted_log_with_unparseable_item_fails(smoke_case):
    text = json.dumps({"type": "new_protocol", "data": _hostile_text()}) + "\n"
    assert cycle.measure_effort(_write_log(smoke_case, text))["shape"] == "unparseable"
    _write_cycle(smoke_case, "grok", log=text)
    _fail(smoke_case, MISSING_TYPES)


def _write_log(data, text):
    path = data / "authority.log"
    path.write_text(text, encoding="utf-8")
    return path


def test_smoke_drifted_log_with_parsed_item_fails(smoke_case):
    text = json.dumps({"event": "init", "type": "new_protocol", "data": _hostile_text()}) + "\n"
    assert cycle.measure_effort(_write_log(smoke_case, text))["shape"] == "parsed"
    _write_cycle(smoke_case, "grok", log=text)
    _fail(smoke_case, MISSING_TYPES)


def test_smoke_effort_codex_text_item_refuses_as_wrong_file(smoke_case):
    item = _item_for(smoke_case, "OpenAI Codex v0.145.0\n" + _hostile_text(), shape="codex-text")
    _write_cycle(smoke_case, "grok", log=f0_text(), effort_item=item)
    _unreadable(smoke_case, "input_unparseable", smoke_case / "grok/auditcycle.txt")
    next((smoke_case / "grok/collected").glob("*.md")).unlink()
    _unreadable(smoke_case, "input_unparseable", smoke_case / "grok/auditcycle.txt",
                property_name="step 3 wrong-file refusal precedes missing collected report")


def test_smoke_effort_missing_item_refuses_as_wrong_file(smoke_case):
    item = _item_for(smoke_case, None, shape="missing")
    _write_cycle(smoke_case, "grok", log=f0_text(), effort_item=item)
    _unreadable(smoke_case, "input_unparseable", smoke_case / "grok/auditcycle.txt")


def test_smoke_effort_empty_item_refuses_as_wrong_file(smoke_case):
    item = _item_for(smoke_case, "", shape="empty")
    _write_cycle(smoke_case, "grok", log=f0_text(), effort_item=item)
    _unreadable(smoke_case, "input_unparseable", smoke_case / "grok/auditcycle.txt")


def test_smoke_unrecognised_effort_item_refuses(smoke_case):
    _write_cycle(smoke_case, "grok", log=f0_text(),
                 effort_item="p1 measured by a renderer this design does not name")
    _unreadable(smoke_case, "input_unparseable", smoke_case / "grok/auditcycle.txt")


def test_smoke_parsed_item_with_all_three_types_is_the_stated_residual(smoke_case):
    text = '{"event":"init"}\n' + f0_text()
    assert cycle.measure_effort(_write_log(smoke_case, text))["shape"] == "parsed"
    _write_cycle(smoke_case, "grok", log=text)
    _assert_smoke(smoke_case)


def test_smoke_deep_grok_types_with_unparseable_item_is_the_stated_residual(smoke_case):
    v = 0
    for _ in range(GROK_MAX_DEPTH):
        v = [v]
    events = [{"type": t, "x": v} for t in ("end", "tool_call", "tool_call_update")]
    assert all(_json_deeper_than(event, GROK_MAX_DEPTH) for event in events)
    text = "".join(json.dumps(event) + "\n" for event in events)
    assert cycle.measure_effort(_write_log(smoke_case, text))["shape"] == "unparseable"
    _write_cycle(smoke_case, "grok", log=text)
    _assert_smoke(smoke_case)
    assert set(load_probe(PROBE).grok_log_types(text)) == {event["type"] for event in events}


def test_smoke_effort_grok_item_with_targets_is_grok(smoke_case):
    item = _item_for(smoke_case, f0_text(), shape="grok", root=smoke_case)
    assert " paths=" in item and " code=" in item and " unmeasured=" in item
    _write_cycle(smoke_case, "grok", log=f0_text(), effort_item=item)
    _assert_smoke(smoke_case)
    assert load_probe(PROBE).effort_form(item) == "grok"


def test_grok_item_predicate_matches_the_renderer(smoke_case):
    import inspect
    import re

    probe = load_probe(PROBE)
    shapes = set(re.findall(r'"shape"\]?\s*[:=]\s*"([a-z-]+)"',
                            inspect.getsource(cycle.measure_effort)))
    assert shapes == {"missing", "empty", "parsed", "codex-text", "grok",
                      "grok-truncated", "unparseable"}
    fixtures = (
        ("grok", f0_text(), "grok"),
        ("grok-truncated", f_trunc(), "truncated"),
        ("parsed", '{"event":"init"}\n', "counts"),
        ("unparseable", '{"type":"new_protocol"}\n', "counts"),
        ("codex-text", "OpenAI Codex v0.145.0\n" + _hostile_text(), "wrong-file"),
        ("missing", None, "wrong-file"),
        ("empty", "", "wrong-file"),
    )
    assert {shape for shape, _, _ in fixtures} == shapes
    for shape, text, form in fixtures:
        item = _item_for(smoke_case, text, shape=shape)
        assert bool(probe.GROK_ITEM_RE.match(item)) == (shape == "grok"), (
            f"positive grok predicate must match only renderer shape grok: {shape}: {item}"
        )
        assert bool(probe.COUNTS_ITEM_RE.match(item)) == (form == "counts")
        assert probe.effort_form(item) == form, f"renderer shape {shape} must map to exactly {form}"
    assert probe.effort_form("p1 measured by an unknown renderer") == "unknown"
    _assert_smoke(smoke_case)


def test_truncated_predicate_matches_the_renderer(smoke_case):
    probe = load_probe(PROBE)
    for text, shape, expected in ((f_trunc(), "grok-truncated", "truncated"),
                                  (f0_text(), "grok", "grok")):
        item = _item_for(smoke_case, text, shape=shape)
        assert probe.effort_form(item) == expected, "truncated predicate must follow the renderer wording"
    _assert_smoke(smoke_case)


def test_smoke_codex_refusal_is_not_a_reason(smoke_case):
    _write_cycle(smoke_case, "codex", verdict="UNVERIFIED", reason="no_report:p1", delivered="none")
    lines = _assert_smoke(smoke_case)
    assert "ROOT-ACCEPT: grok=accepted agy=accepted codex=refused" in lines


def test_smoke_out_of_vocabulary_type_is_not_a_reason(smoke_case):
    event = {"type": "foreign_type", "metadata": {"toolName": _hostile_text(), "tokenCount": 1}}
    text = f0_text() + json.dumps(event) + "\n"
    _write_cycle(smoke_case, "grok", log=text)
    lines = _assert_smoke(smoke_case)
    assert "VOCAB: type=foreign_type re=out frozenset=out tool=yes usage=yes" in lines


def test_smoke_halted_agy_cycle_is_a_refusal_not_unreadable(smoke_case):
    _write_cycle(smoke_case, "agy", verdict="UNVERIFIED", reason="assemble_halt:p1", halted=True)
    assert not (smoke_case / "agy/p1.log").exists()
    _fail(smoke_case, "nongit_root_refused:agy")


def test_smoke_codex_text_log_is_not_an_input(smoke_case):
    for surface in ("agy", "codex"):
        _write_cycle(smoke_case, surface, log="OpenAI Codex v0.145.0\n" + _hostile_text())
    _assert_smoke(smoke_case)
    for surface in ("agy", "codex"):
        (smoke_case / surface / "p1.log").unlink()
    _assert_smoke(smoke_case)


def test_smoke_publishes_grok_binary_line(smoke_case):
    version = "grok 9.9.9 (abc) [stable]"
    (smoke_case / "versions.txt").write_text(
        f"grok_binary=/x/grok {version}\nagy synthetic\ncodex synthetic\n", encoding="utf-8")
    lines = _assert_smoke(smoke_case)
    assert f"GROK-BINARY: path=/x/grok version={version}" in lines


def test_smoke_grok_binary_unrecorded_is_not_unreadable(smoke_case):
    versions = smoke_case / "versions.txt"
    for text in (None, "grok_binary=absent\n", "agy synthetic\ncodex synthetic\n"):
        if text is None:
            if versions.exists():
                versions.unlink()
        else:
            versions.write_text(text, encoding="utf-8")
        assert "GROK-BINARY: unrecorded" in _assert_smoke(smoke_case)


def test_smoke_two_reasons_in_order(smoke_case):
    extra = _vocab_sources(smoke_case, _GROK_TYPES, _GROK_TYPES | {"new_kind"})
    item = _item_for(smoke_case, f0_text(), shape="grok")
    _write_cycle(smoke_case, "grok", log=_without(f0_text(), "end"), effort_item=item)
    _fail(smoke_case, "vocab_split,vocab_missing:end", extra=extra)


def test_smoke_coupled_reasons_in_order(smoke_case):
    _write_cycle(smoke_case, "grok", log=f_trunc(), verdict="UNVERIFIED", delivered="none",
                 reason="no_report:p1")
    _write_cycle(smoke_case, "agy", verdict="UNVERIFIED", reason="assemble_halt:p1", halted=True)
    extra = _vocab_sources(smoke_case, _GROK_TYPES, _GROK_TYPES | {"new_kind"})
    _fail(smoke_case, "truncated,vocab_split,vocab_missing:end,no_delivery,"
          "nongit_root_refused:grok,nongit_root_refused:agy", extra=extra)


def test_smoke_unreadable_outranks_fail(smoke_case):
    _write_cycle(smoke_case, "grok", log=f_trunc(), verdict="UNVERIFIED", reason="low_evidence:p1")
    (smoke_case / "agy/auditcycle.txt").unlink()
    _unreadable(smoke_case, "input_missing", smoke_case / "agy/auditcycle.txt")


def test_smoke_prints_timeout_derivation(smoke_case):
    wall = smoke_case / "grok/wall_seconds.txt"
    for seconds, derived in ((1, 900), (600, 900), (601, 960), (1234, 1860)):
        wall.write_text(str(seconds) + "\n", encoding="utf-8")
        assert f"TIMEOUT: wall_seconds={seconds} derived={derived}" in _assert_smoke(smoke_case)
    wall.unlink()
    assert "TIMEOUT: wall_seconds=unrecorded" in _assert_smoke(smoke_case)


def test_smoke_last_resort_names_the_open_input(smoke_case, monkeypatch, capsys):
    probe = load_probe(PROBE)

    def explode(text):
        raise RuntimeError("injected grok type reader failure")

    # The reader is new in this task. Keep the injected callee available at RED
    # so this pin fails on the absent smoke caller's path propagation.
    monkeypatch.setattr(probe, "grok_log_types", explode, raising=False)
    rc, lines, err = _in_process(probe, smoke_case, capsys)
    path = smoke_case / "grok/p1.log"
    assert (rc, lines[-1:]) == (2, [f"SMOKE: UNREADABLE reason=input_unparseable:{path}"]), (
        "last resort must name the opened grok log, not the --data directory"
    )
    assert Path(probe._OPEN_INPUT) == path, "smoke must arm _OPEN_INPUT immediately before reading the log"
    assert "RuntimeError: injected grok type reader failure" in err


def test_smoke_refuses_a_malformed_effort_block(smoke_case):
    _write_cycle(smoke_case, "grok", verdict="UNVERIFIED", reason="assemble_halt:p1", halted=True,
                 effort_item="x1 tools=1 ok=1 failed=0 thinking=0")
    _unreadable(smoke_case, "input_unparseable", smoke_case / "grok/auditcycle.txt")


def test_m3_d1_end_event_beside_truncated_item_is_truncated(smoke_case):
    assert scan_grok(f0_text())["complete"] is True, "M3 raw authority says complete grok"
    item = _item_for(smoke_case, f_trunc(), shape="grok-truncated")
    _write_cycle(smoke_case, "grok", log=f0_text(), effort_item=item)
    _fail(smoke_case, "truncated")


def test_m3_d2_no_end_beside_grok_item_is_not_truncated(smoke_case):
    assert scan_grok(f_trunc())["complete"] is False, "M3 raw authority says grok-truncated"
    item = _item_for(smoke_case, f0_text(), shape="grok")
    _write_cycle(smoke_case, "grok", log=f_trunc(), effort_item=item)
    _fail(smoke_case, "vocab_missing:end")


def _raw_delivery(data, present):
    root = data / "raw export root"
    root.mkdir(exist_ok=True)
    report, out = root / "transport.md", root / "output.txt"
    if present:
        report.write_text(_report(), encoding="utf-8")
        Path(str(report) + ".done").touch()
    spec = cycle.PassSpec(1, report, out, 0, data / "grok/p1.log")
    return cycle.collect(spec, grace=0, project_root=root,
                         feature="paper-lantern", phase="plan", cycle=1)


def _assert_gate_pass(report):
    result = subprocess.run([sys.executable, str(REPO / "h-mad/scripts/h_mad_audit_gate.py"), str(report)],
                            capture_output=True, text=True, timeout=15)
    assert cycle._gate_token(result.stdout, report)[0] == "PASS", (
        "M4 collected report must separately satisfy the GATE authority: " + result.stderr
    )


def test_m4_e1_report_file_inputs_beside_delivered_none_is_no_delivery(smoke_case):
    shape, report = _raw_delivery(smoke_case, True)
    assert shape == "report-file", "M4 raw collect authority must oppose recorded none"
    _assert_gate_pass(report)
    _write_cycle(smoke_case, "grok", log=f0_text(), delivered="none")
    _fail(smoke_case, NO_DELIVERY)


def test_m4_e2a_none_inputs_beside_report_file_is_delivered(smoke_case):
    assert _raw_delivery(smoke_case, False) == ("none", None), "M4 raw collect authority must oppose report-file"
    report = _write_cycle(smoke_case, "grok", log=f0_text(), delivered="report-file")
    _assert_gate_pass(report)
    _assert_smoke(smoke_case)


def test_m4_e2b_none_inputs_beside_out_is_delivered(smoke_case):
    assert _raw_delivery(smoke_case, False) == ("none", None), "M4 raw collect authority must oppose out"
    report = _write_cycle(smoke_case, "grok", log=f0_text(), delivered="out")
    _assert_gate_pass(report)
    _assert_smoke(smoke_case)


def test_m5_f1_unverified_token_beside_busy_log_refuses_root(smoke_case):
    text = f0_with_completed(3)
    result = _result(_write_log(smoke_case, text), Path("report.md"))
    assert result.effort["ok"] > cycle.DELIVERY_FLOOR
    assert cycle.combine([result]) == ("PASS", None), "M5 raw combine authority must oppose UNVERIFIED"
    _write_cycle(smoke_case, "grok", log=text, verdict="UNVERIFIED", reason="low_evidence:p1")
    _fail(smoke_case, "nongit_root_refused:grok")


def test_m5_f2_pass_token_beside_hollow_log_accepts_root(smoke_case):
    text = _without(f0_text(), "tool_call", "tool_call_update")
    result = _result(_write_log(smoke_case, text), Path("report.md"))
    assert result.effort["ok"] == 0
    assert cycle.combine([result]) == ("UNVERIFIED", "low_evidence:p1"), (
        "M5 raw combine authority must oppose recorded PASS"
    )
    # Keep both type witnesses with no completed call: vocabulary and effort are separate observations.
    text += '{"type":"tool_call"}\n{ "type":"tool_call_update"}\n'
    result = _result(_write_log(smoke_case, text), Path("report.md"))
    assert result.effort["ok"] == 0
    assert cycle.combine([result]) == ("UNVERIFIED", "low_evidence:p1")
    _write_cycle(smoke_case, "grok", log=text)
    _assert_smoke(smoke_case)
