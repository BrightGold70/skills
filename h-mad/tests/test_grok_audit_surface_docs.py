"""Pins for the Grok audit surface's exclusions and operator documentation."""

from pathlib import Path
import re
import subprocess

from docsections import titled_section


REPO = Path(__file__).resolve().parents[2]
EXCLUSIONS = REPO / "docs/03-analysis/probes/grok-audit-surface/exclusions.txt"
SKILL_MD = REPO / "h-mad/SKILL.md"


def test_exclusion_list_holds_the_required_entries() -> None:
    assert EXCLUSIONS.is_file(), (
        "the declared exclusion list must exist and hold exactly D5's six entries "
        f"in order: {EXCLUSIONS}"
    )
    entries = [
        line.strip()
        for line in EXCLUSIONS.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert entries == [
        "dir docs/archive/2026-09/audit-report-docs-copy",
        "dir docs/archive/2026-09/tdd-gate-fail-opens",
        "dir docs/archive/2026-10/agy-coder-fallback",
        "dir docs/03-analysis/probes/grok-audit-surface",
        "dir docs/03-analysis/agy-coder-fallback.authoring",
        "name-contains grok-audit-surface",
    ], "the declared exclusion list must hold exactly D5's six entries in order"


def test_teammate_section_names_hmad_dispatch_audit_cycle() -> None:
    section = " ".join(
        titled_section(
            SKILL_MD.read_text(encoding="utf-8"),
            "Teammate audit leg — when codex is unavailable",
        ).split()
    )
    command = (
        "`hmad-dispatch audit-cycle --feature <feature> --phase <phase> "
        "--cycle <N> --project-root <root> --passes 2 --surfaces agy,grok`"
    )
    assert section.count(command) == 1, (
        "the teammate section must name exactly once the complete hmad-dispatch "
        "audit-cycle command with feature, phase, cycle, project root, two passes, "
        "and agy,grok surfaces"
    )


def test_no_h_mad_md_pairs_audit_cycle_py_with_surfaces() -> None:
    tracked = subprocess.run(
        ["git", "ls-files", "-z", "h-mad/*.md"],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    paths = [path for path in tracked.split("\0") if path]
    assert "h-mad/SKILL.md" in paths, "the tracked Markdown scan must include SKILL.md"
    pattern = re.compile(r"h_mad_audit_cycle\.py[^\n]*\n?[^\n]*--surfaces")
    occurrences = []
    for path in paths:
        text = (REPO / path).read_text(encoding="utf-8")
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            occurrences.append(f"{path}:{line}: {match.group(0)}")
    assert not occurrences, (
        "tracked h-mad Markdown must never pair h_mad_audit_cycle.py with "
        "--surfaces; use hmad-dispatch audit-cycle instead:\n"
        + "\n".join(occurrences)
    )


def test_never_do_legs_bullet_states_the_first_gate_leg_set() -> None:
    section = titled_section(
        SKILL_MD.read_text(encoding="utf-8"), "What you NEVER do"
    )
    bullets = [" ".join(bullet.split()) for bullet in re.split(r"(?m)^- ", section)]
    legs_bullets = [
        bullet
        for bullet in bullets
        if bullet.startswith("**Name the reviewer legs with `--legs`")
    ]
    assert len(legs_bullets) == 1, (
        "What you NEVER do must contain exactly one reviewer --legs bullet"
    )
    sentence = (
        "The first gate and the revisions run different leg sets by design, "
        "so the streak, when it is reached, is among revision cycles."
    )
    assert legs_bullets[0].endswith(sentence), (
        "the reviewer --legs bullet must append the explanation that the first "
        "gate uses a different leg set and the streak is among revision cycles"
    )
def test_exec_grok_bullet_states_the_strict_contract():
    from pathlib import Path

    from test_grok_fallback_docs import titled_section

    skill = Path(__file__).parents[1] / "SKILL.md"
    lines = titled_section(
        skill.read_text(),
        "Exit-code dispatch for 5d/5e (`hmad-dispatch exec`) — default for one-shot",
    ).splitlines()
    start = next(
        index
        for index, line in enumerate(lines)
        if "**`exec grok`** — an explicit RED/GREEN implementer fallback" in line
    )
    end = next(
        (
            index
            for index in range(start + 1, len(lines))
            if lines[index].lstrip().startswith("- **")
        ),
        len(lines),
    )
    bullet = " ".join(" ".join(lines[start:end]).split())
    expected = (
        "From FR-11, `exec grok` always runs `--sandbox strict`: a weaker or unknown "
        "`--sandbox` value exits 2 unless `--allow-weaker-sandbox` is also given, "
        "which is recorded in `<log>.profile`, and `GROK_SANDBOX` is removed from "
        "grok's environment. In a git work tree it stages its prompt and `TMPDIR` "
        "under `<top level>/.h-mad/tmp/` and exits 2, launching nothing, when `--cd` "
        "is below the top level, when the repository does not ignore `.h-mad/tmp/`, "
        "or when `git rev-parse` fails for a reason other than \"not a git repository\"; "
        "outside a work tree it uses `<cd>/.tmp/`."
    )
    assert expected in bullet, "exec grok bullet must state the verbatim FR-11 strict contract"


def test_agent_substrate_grok_row_states_the_strict_default():
    from pathlib import Path

    from test_grok_fallback_docs import titled_section

    substrate = Path(__file__).parents[1] / "references" / "agent-substrate.md"
    section = titled_section(
        substrate.read_text(), "Agent Dispatch Substrate (cmux | orca)"
    )
    row = next(line for line in section.splitlines() if "GROK_SANDBOX" in line)
    row = " ".join(row.split())
    expected = (
        "`--sandbox` defaults to `strict`; a weaker or unknown profile exits 2 unless "
        "`--allow-weaker-sandbox` is given, and the effective profile is recorded in "
        "`<log>.profile`. `GROK_SANDBOX` is removed from the child. The prompt and "
        "`TMPDIR` are staged under `<top level>/.h-mad/tmp/` in a git work tree, or "
        "`<cd>/.tmp/` outside one, and `exec` refuses a `--cd` below the top level, "
        "an unignored `.h-mad/tmp/`, and a `git rev-parse` failure other than "
        "\"not a git repository\"."
    )
    assert "[--sandbox <profile>] [--allow-weaker-sandbox]" in row, (
        "agent-substrate exec grok command must expose the strict-default override"
    )
    assert expected in row, "agent-substrate exec grok row must state the verbatim FR-11 contract"


# S3 publish (Task 16): every-outcome pins on the measurement doc, the two
# AC-6.2 sites in SKILL.md and grok-runtime.md's outcome sentence (design D14,
# D15, D21). Each test reads the outcome from the doc's token lines.

MEASUREMENT_REL = "docs/03-analysis/grok-audit-surface.measurement.md"
MEASUREMENT = REPO / MEASUREMENT_REL
GROK_RUNTIME = REPO / "h-mad/references/grok-runtime.md"
EXEC_SECTION = "Exit-code dispatch for 5d/5e (`hmad-dispatch exec`) — default for one-shot"
TEAMMATE_SECTION = "Teammate audit leg — when codex is unavailable"
HOST_SENTENCE = "These mappings were checked against grok 1.0.41."
RESMOKED_HEAD = (
    "The audit path (the `exec grok` audit leg, the event vocabulary, `scan_grok` "
    "and report delivery) was re-smoked against grok "
)
# Any one sentence saying a (re-)smoke failed, however worded; ". " ends a
# sentence, so a version such as 1.0.62 does not.
SMOKE_FAILED = re.compile(r"(?i)smoke(?:(?!\.\s).)*?\bfailed\b")
AC39_PHRASE = "measured with the calibration-only path-scope clause (AC-3.9)"
NOT_RUN = (
    "Not run: second quarantine, fresh S2, positive control, CONTAINMENT lines "
    "(smoke failed)"
)
SEED_RESIDUAL = (
    "The seeds are build-class shapes from the four classes of spec AC-2.1, and "
    "whether recall on real defects would match is not measured."
)
CLAUSE_RESIDUAL = (
    "The measurement was taken with the calibration-only path-scope clause "
    "(AC-3.9): the calibration prompt is the production prompt plus exactly that "
    "clause, inserted once at the head of the audit body; production grok legs do "
    "not receive it, and whether a production grok leg without it behaves the "
    "same is not measured."
)


def _collapse(text: str) -> str:
    return " ".join(text.split())


def _measurement() -> str:
    assert MEASUREMENT.is_file(), f"the S3 measurement doc must exist: {MEASUREMENT_REL}"
    return MEASUREMENT.read_text(encoding="utf-8")


def _token_lines(doc: str, prefix: str) -> list[str]:
    return [line for line in doc.splitlines() if line.startswith(prefix)]


def _outcome(doc: str) -> str:
    """`SMOKE_FAIL`, or the verdict word of the doc's one `SEEDSCORE:` line."""
    smoke = _token_lines(doc, "SMOKE: ")
    assert len(smoke) == 1, "the measurement doc must carry exactly one SMOKE: line"
    if smoke[0].split()[1] == "FAIL":
        return "SMOKE_FAIL"
    scores = _token_lines(doc, "SEEDSCORE: ")
    assert len(scores) == 1, "a scored measurement doc must carry exactly one SEEDSCORE: line"
    verdict = scores[0].split()[1]
    assert verdict in {"PASS", "MISS", "INCONCLUSIVE"}, scores[0]
    return verdict


def _grok_version(doc: str) -> str:
    """D14's slot rule: the first field after `grok` in GROK-BINARY's version."""
    lines = _token_lines(doc, "GROK-BINARY:")
    assert len(lines) == 1, "the measurement doc must carry exactly one GROK-BINARY: line"
    match = re.fullmatch(r"GROK-BINARY: path=.+? version=(.+)", lines[0])
    assert match, f"GROK-BINARY: line names no recorded version: {lines[0]}"
    fields = match.group(1).split()
    assert len(fields) >= 2 and fields[0] == "grok", (
        f"D14's slot rule yields no version from: {lines[0]}"
    )
    return fields[1]


def _surface(doc: str, name: str) -> tuple[str, str]:
    lines = _token_lines(doc, f"SURFACE: {name} ")
    assert len(lines) == 1, f"the measurement doc must carry one SURFACE: {name} line"
    recall = re.search(r" recall=(\d+/27) ", lines[0])
    fab = re.search(r" fab_rate=(\d+/\d+) ", lines[0])
    assert recall and fab, lines[0]
    return recall.group(1), fab.group(1)


def _exec_grok_bullet() -> str:
    lines = titled_section(SKILL_MD.read_text(encoding="utf-8"), EXEC_SECTION).splitlines()
    start = next(
        index
        for index, line in enumerate(lines)
        if "**`exec grok`** — an explicit RED/GREEN implementer fallback" in line
    )
    end = next(
        (
            index
            for index in range(start + 1, len(lines))
            if lines[index].lstrip().startswith("- **")
        ),
        len(lines),
    )
    return _collapse(" ".join(lines[start:end]))


def _ac62_sites() -> dict[str, str]:
    teammate = titled_section(SKILL_MD.read_text(encoding="utf-8"), TEAMMATE_SECTION)
    return {"exec grok bullet": _exec_grok_bullet(), "teammate section": _collapse(teammate)}


def test_both_unmeasured_sites_point_to_the_measurement_doc() -> None:
    _measurement()
    for name, site in _ac62_sites().items():
        assert f"`{MEASUREMENT_REL}`" in site, (
            f"the {name} must point to the measurement doc {MEASUREMENT_REL}"
        )


def test_measurement_doc_states_the_transfer_residual() -> None:
    doc = _collapse(_measurement())
    assert SEED_RESIDUAL in doc, "the measurement doc must state the seed-shape transfer residual"
    assert CLAUSE_RESIDUAL in doc, (
        "the measurement doc must state the AC-3.9 path-scope transfer residual"
    )


def test_unmeasured_sites_match_the_outcome() -> None:
    doc = _measurement()
    outcome = _outcome(doc)
    version = _grok_version(doc)
    if outcome == "SMOKE_FAIL":
        expected = f"the grok {version} audit-path smoke failed"
    else:
        grok_recall, grok_fab = _surface(doc, "grok")
        agy_recall, agy_fab = _surface(doc, "agy")
        fractions = (
            f"recall {grok_recall} against agy's {agy_recall}, fabrication {grok_fab} "
            f"against agy's {agy_fab} (`SEEDSCORE: {outcome}`), {AC39_PHRASE}"
        )
        if outcome == "INCONCLUSIVE":
            reason = re.search(r" reason=(\S+)", _token_lines(doc, "SEEDSCORE: ")[0])
            assert reason, "an INCONCLUSIVE SEEDSCORE: line must carry its reason="
            expected = (
                "audit precision measured on 27 seeds but not decidable on this seed "
                f"set (`reason={reason.group(1)}`): {fractions}, so grok stays fallback-only"
            )
        else:
            expected = f"audit precision measured on 27 seeds: {fractions}"
    for name, site in _ac62_sites().items():
        assert expected in site, f"the {name} must read, for {outcome}: {expected}"
        assert "**unmeasured**" in site, (
            f"the {name} must keep GREEN, mutation and wiring **unmeasured**"
        )
        precision_unmeasured = re.search(
            r"audit precision (are|remain) \*\*unmeasured\*\*", site
        )
        if outcome == "SMOKE_FAIL":
            assert precision_unmeasured, (
                f"on a smoke failure the {name} must keep audit precision unmeasured"
            )
        else:
            assert not precision_unmeasured, (
                f"on {outcome} the {name} must retire audit precision from the "
                "unmeasured list"
            )


def test_grok_runtime_states_the_outcome_sentence() -> None:
    section = _collapse(
        titled_section(GROK_RUNTIME.read_text(encoding="utf-8"), "Version and compatibility")
    )
    assert HOST_SENTENCE in section, (
        "grok-runtime.md must keep the host-mapping sentence unchanged: " + HOST_SENTENCE
    )
    pointer = f"`{MEASUREMENT_REL}`"
    scored_shape = RESMOKED_HEAD in section
    smoke_shape = SMOKE_FAILED.search(section) is not None
    assert scored_shape or smoke_shape, (
        "grok-runtime.md §Version and compatibility must state the AC-1.5 "
        "re-smoked sentence or the AC-1.8 smoke-failure sentence"
    )
    doc = _measurement()
    outcome = _outcome(doc)
    version = _grok_version(doc)
    if outcome == "SMOKE_FAIL":
        match = re.search(
            rf"The audit path re-smoke against grok {re.escape(version)} failed[^.]*"
            rf"{re.escape(pointer)}",
            section,
        )
        assert match, (
            f"on a smoke failure grok-runtime.md must say the re-smoke against grok "
            f"{version} failed and name {MEASUREMENT_REL}"
        )
        assert RESMOKED_HEAD not in section, (
            "on a smoke failure the AC-1.5 re-smoked sentence must not ship"
        )
    else:
        sentence = f"{RESMOKED_HEAD}{version}; see {pointer}."
        assert sentence in section, f"grok-runtime.md must state: {sentence}"
        assert not smoke_shape, (
            f"on {outcome} the AC-1.8 smoke-failure sentence must not ship"
        )


def test_measurement_doc_on_smoke_failure_marks_later_stages_not_run() -> None:
    doc = _measurement()
    lines = doc.splitlines()
    if _outcome(doc) == "SMOKE_FAIL":
        assert NOT_RUN in lines, f"a smoke-failure doc must state the line: {NOT_RUN}"
        assert not _token_lines(doc, "CONTAINMENT:"), "a smoke-failure doc has no CONTAINMENT: line"
        assert not _token_lines(doc, "SEEDSCORE:"), "a smoke-failure doc has no SEEDSCORE: line"
        return
    assert not _token_lines(doc, "Not run:"), "a scored doc must not carry a Not run: line"
    assert len(_token_lines(doc, "QUARANTINE: VERIFIED ")) == 2, (
        "a scored doc must carry both QUARANTINE: VERIFIED lines"
    )
    positive = [
        line
        for line in _token_lines(doc, "TOOLSCAN: ")
        if re.search(r" checkout=[1-9]\d* ", line)
    ]
    assert positive, "a scored doc must carry the positive-control TOOLSCAN: line (checkout above 0)"
    cycles = re.findall(r"(?m)^d\d+: AUDITCYCLE: .* passes=(\d+) ", doc)
    assert cycles, "a scored doc must carry the S2 AUDITCYCLE: lines"
    passes = sum(map(int, cycles))
    assert len(_token_lines(doc, "CONTAINMENT: ")) == passes, (
        f"a scored doc must carry every CONTAINMENT: line, one per S2 pass ({passes})"
    )
    assert _token_lines(doc, "Codex and agy passes with `checkout=` above 0:"), (
        "a scored doc must name the codex and agy passes with checkout= above 0"
    )


def test_measurement_doc_publishes_the_exclusion_list() -> None:
    doc = _measurement()
    blobs = re.findall(r"(?m)^list_blob=([0-9a-f]{40})$", doc)
    assert len(blobs) == 1, "the stamp must state exactly one list_blob= line"
    section = titled_section(doc, "Exclusion list").splitlines()
    fences = [index for index, line in enumerate(section) if line.startswith("```")]
    assert len(fences) >= 2, "the Exclusion list section must hold a fenced block"
    published = "".join(line + "\n" for line in section[fences[0] + 1 : fences[1]])
    blob = subprocess.run(
        ["git", "cat-file", "blob", blobs[0]],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert published == blob, (
        "the published exclusion list must equal git cat-file blob of list_blob byte for byte"
    )


# S4 route (Task 17, PASS only): three-surface first gate, availability and
# twice-UNVERIFIED fallbacks, and grok must-fix falsification in SKILL.md
# §"Never gate on one audit pass" (spec AC-7.1, AC-7.2, AC-8.3; design D14).

NEVER_GATE_SECTION = "Never gate on one audit pass"
GROK_UNAVAILABLE_FALLBACK = (
    "If `command -v grok` fails, the first gate runs `--passes 2 --surfaces codex,agy`."
)
GROK_TWICE_UNVERIFIED_FALLBACK = (
    "If the grok pass is the `pN` named in `UNVERIFIED reason=…:pN` on both the "
    "first run and its one re-dispatch, the cycle is re-run as "
    "`--passes 2 --surfaces codex,agy`. Either way the stamp records the legs that "
    "actually ran."
)
GROK_FALSIFICATION = (
    'A grok must-fix goes through §"Verifying a review finding before acting on it" '
    'before it is acted on, and a rejected one is recorded per §"Record a rejected '
    'finding in the rejections ledger, never in a gated document".'
)


def _never_gate_section() -> str:
    return _collapse(titled_section(SKILL_MD.read_text(encoding="utf-8"), NEVER_GATE_SECTION))


def test_never_gate_section_names_three_surface_first_gate() -> None:
    section = _never_gate_section()
    assert "`--surfaces codex,agy,grok`" in section, (
        "§Never gate on one audit pass must name `--surfaces codex,agy,grok` for the "
        "first gate when codex is available"
    )
    assert f"`{MEASUREMENT_REL}`" in section, (
        f"§Never gate on one audit pass must point to `{MEASUREMENT_REL}`"
    )
    assert "that is three reports, of which two share a model family" not in section, (
        "§Never gate on one audit pass must reword the prohibition so it is on two "
        "reports sharing a model family, not on three reports"
    )
    assert "never the teammate full pass *plus* codex on the same phase at the same cycle" in section, (
        "§Never gate on one audit pass must keep the teammate-full-pass-plus-codex "
        "case prohibited"
    )
    assert "share a model family" in section, (
        "§Never gate on one audit pass must state that two reports sharing a model "
        "family is what is prohibited"
    )


def test_never_gate_section_names_grok_falsification() -> None:
    raw = SKILL_MD.read_text(encoding="utf-8")
    section = _collapse(titled_section(raw, NEVER_GATE_SECTION))
    assert GROK_FALSIFICATION in section, (
        "§Never gate on one audit pass must state the D14 grok must-fix "
        f"falsification sentence verbatim: {GROK_FALSIFICATION}"
    )
    cited_titles = re.findall(r'§"([^"]+)"', GROK_FALSIFICATION)
    assert len(cited_titles) == 2, cited_titles
    heading_titles = {
        match.group(1)
        for match in re.finditer(r"(?m)^#{2,6}\s+(.+?)\s*$", raw)
    }
    for title in cited_titles:
        assert title in heading_titles, (
            f"cited heading {title!r} must exist as a heading line in h-mad/SKILL.md"
        )


def test_never_gate_section_names_the_grok_unavailable_fallback() -> None:
    section = _never_gate_section()
    assert "`command -v grok`" in section, (
        "§Never gate on one audit pass must name `command -v grok` for the "
        "availability check"
    )
    assert "`--passes 2 --surfaces codex,agy`" in section, (
        "§Never gate on one audit pass must name `--passes 2 --surfaces codex,agy` "
        "when grok is unavailable"
    )
    assert GROK_UNAVAILABLE_FALLBACK in section, (
        "§Never gate on one audit pass must state the D14 unavailable fallback "
        f"sentence verbatim: {GROK_UNAVAILABLE_FALLBACK}"
    )


def test_never_gate_section_names_the_twice_unverified_grok_fallback() -> None:
    section = _never_gate_section()
    assert "UNVERIFIED reason=…:pN" in section and "one re-dispatch" in section, (
        "§Never gate on one audit pass must name the twice-UNVERIFIED re-dispatch "
        "fallback"
    )
    assert "codex,agy" in section, (
        "§Never gate on one audit pass must name `codex,agy` for the twice-UNVERIFIED "
        "fallback"
    )
    assert GROK_TWICE_UNVERIFIED_FALLBACK in section, (
        "§Never gate on one audit pass must state the D14 twice-UNVERIFIED fallback "
        f"sentences verbatim: {GROK_TWICE_UNVERIFIED_FALLBACK}"
    )

