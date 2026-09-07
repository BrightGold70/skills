"""H7 — per-must origin tagging.

Every test here pins a way the instrument could report a *better* number than the truth,
because that is the only direction that matters: H7 exists to answer "did the
fix-introduced rate fall after H1–H9 shipped?", and every silent failure of a counter
answers "yes".

`TestAgainstTheRealCorpus` runs against the 152 records the `gateway-consolidation`
prototype captured for cycles 98–103, copied into `fixtures/` rather than read from the
HemaSuite tree — a test that reaches into another lane's working file is not portable and
breaks when that lane edits its own data.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import h_mad_audit_origins as origins  # noqa: E402

PROTOTYPE = Path(__file__).resolve().parent / "fixtures" / "audit-origins.prototype.jsonl"


def record(**overrides):
    """A record that is valid, so a test's mutation is the only thing under test."""
    base = {
        "phase": "design",
        "cycle": 99,
        "leg": "codex",
        "item": "AC-2.7 decode catches only JSONDecodeError",
        "origin": "new-mechanism",
        "by_cycle": None,
        "verified_by_execution": True,
    }
    base.update(overrides)
    return base


class TestVocabulary:
    def test_the_eight_origins_are_the_ledgers_eight(self):
        # Pinned as a literal set, not a count: a count passes when one origin is
        # renamed to another's spelling, which is exactly the silent recategorisation
        # the unknown-origin rule exists to stop.
        assert set(origins.ORIGINS) == {
            "new-mechanism", "new-consistency", "fix-introduced", "propagation-gap",
            "instrument", "record-stale", "author-self-caught", "rejected",
        }
        assert len(origins.ORIGINS) == 8

    def test_an_unknown_origin_is_REFUSED_not_counted_as_its_own_category(self):
        # The failure this prevents: `fix-intoduced` becomes a ninth bucket, the
        # fix-introduced count drops, and the ledger reads it as improvement.
        reasons = origins.validate(record(origin="fix-intoduced"))
        assert any("unknown-origin" in r for r in reasons)
        assert any("fix-intoduced" in r for r in reasons), (
            "the reason must NAME the bad value — a typo is only fixable if the "
            "output says what it was")

    def test_a_valid_origin_passes(self):
        assert origins.validate(record(origin="instrument")) == []


class TestByCycle:
    @pytest.mark.parametrize("origin", ["fix-introduced", "propagation-gap"])
    def test_by_cycle_is_REQUIRED_for_the_two_seeded_origins(self, origin):
        # "fix-introduced with no seed cycle" is the unclassified blank the ledger
        # warns reads as *new* rather than as unknown.
        reasons = origins.validate(record(origin=origin, by_cycle=None))
        assert any("by_cycle-required" in r for r in reasons)

    @pytest.mark.parametrize("origin", ["fix-introduced", "propagation-gap"])
    def test_by_cycle_present_satisfies_it(self, origin):
        assert origins.validate(record(origin=origin, by_cycle=98)) == []

    def test_by_cycle_on_OTHER_origins_is_allowed(self):
        # Measured: 33 of the prototype's 152 records do this, most of them
        # `author-self-caught` naming the cycle whose fix the author caught. A rule
        # that refused it would have rejected the corpus this instrument was built from.
        assert origins.validate(
            record(origin="author-self-caught", by_cycle=99)) == []

    def test_a_string_cycle_is_refused(self):
        assert any("cycle-not-int" in r for r in origins.validate(record(cycle="99")))


class TestAbsenceIsNotZero:
    def test_an_absent_sidecar_is_UNREADABLE_not_a_clean_measurement(self, tmp_path,
                                                                    capsys):
        rc = origins.main(["--sidecar", str(tmp_path / "nope.jsonl"), "summary"])
        out = capsys.readouterr().out
        assert rc == 2, "a cannot-judge must not exit 0"
        assert "ORIGINS: UNREADABLE" in out
        assert "OK" not in out.split("\n")[0]
        assert "NOTHING WAS TAGGED" in out, (
            "the output must say absence is not zero — a reader who takes "
            "`fix-introduced=0` from an untagged feature draws the opposite "
            "conclusion from the truth")

    def test_an_empty_sidecar_is_a_real_measurement_of_zero(self, tmp_path, capsys):
        # Distinct from the case above ON PURPOSE: a file that exists and holds no
        # records means the cycles ran and nothing was tagged yet.
        sidecar = tmp_path / "empty.jsonl"
        sidecar.write_text("", encoding="utf-8")
        rc = origins.main(["--sidecar", str(sidecar), "summary"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "ORIGINS: OK n=0" in out


class TestUnparsableLinesAreNeverSilent:
    def test_a_bad_line_is_reported_with_its_number(self, tmp_path, capsys):
        # A dropped record makes every count SMALLER, which reads as improvement.
        sidecar = tmp_path / "s.jsonl"
        sidecar.write_text(
            json.dumps(record(origin="fix-introduced", by_cycle=98)) + "\n"
            + "{not json\n"
            + json.dumps(record(origin="instrument")) + "\n",
            encoding="utf-8")
        rc = origins.main(["--sidecar", str(sidecar), "summary"])
        out = capsys.readouterr().out
        assert rc == 1
        assert "ORIGINS: INVALID" in out
        assert ":2:" in out, "the offending line number must be named"
        assert "lower bound" in out, (
            "counts over a sidecar with unreadable lines must be labelled a lower "
            "bound, or they get cited as the measurement")

    def test_a_json_scalar_line_is_not_treated_as_a_record(self, tmp_path, capsys):
        sidecar = tmp_path / "s.jsonl"
        sidecar.write_text("42\n", encoding="utf-8")
        rc = origins.main(["--sidecar", str(sidecar), "summary"])
        assert rc == 1
        assert "not-an-object" in capsys.readouterr().out


class TestTheDenominator:
    def test_rejected_is_EXCLUDED_from_the_fix_introduced_share(self):
        # No real-data coverage: `rejected` occurs zero times in the prototype, so
        # this path is pinned synthetically and that is stated in the module docstring.
        recs = ([record(origin="fix-introduced", by_cycle=98)] * 3
                + [record(origin="rejected")] * 7)
        agg = origins.aggregate(recs)
        assert agg["n"] == 10
        assert agg["rejected"] == 7
        assert agg["accepted"] == 3
        assert origins.share(agg["fix_introduced"], agg["accepted"]) == "3/3 (100.0%)"
        # The trap: over `n` this would read 30%, so a cycle that filed seven false
        # findings would look like a cycle with a low fix-introduced rate.
        assert origins.share(agg["fix_introduced"], agg["n"]) == "3/10 (30.0%)"

    def test_the_share_carries_its_denominator(self):
        assert origins.share(51, 152) == "51/152 (33.6%)"

    def test_a_zero_denominator_is_n_a_not_a_crash_and_not_zero_percent(self):
        assert origins.share(0, 0) == "n/a"

    def test_the_summary_line_states_the_exclusion(self, tmp_path, capsys):
        sidecar = tmp_path / "s.jsonl"
        sidecar.write_text(json.dumps(record(origin="rejected")) + "\n",
                           encoding="utf-8")
        origins.main(["--sidecar", str(sidecar), "summary"])
        out = capsys.readouterr().out
        assert "denominator EXCLUDES `rejected`" in out, (
            "a share whose denominator is not stated in the output gets re-derived "
            "wrongly by the next reader")


class TestAppendRefusesRatherThanWrites:
    def test_an_invalid_record_is_NOT_written(self, tmp_path, capsys):
        # A malformed record in the sidecar is worse than a missing one: every later
        # summary counts it.
        sidecar = tmp_path / "s.jsonl"
        rc = origins.main([
            "--sidecar", str(sidecar), "append", "--phase", "design",
            "--cycle", "99", "--leg", "codex", "--item", "x",
            "--origin", "fix-introduced"])          # no --by-cycle
        out = capsys.readouterr().out
        assert rc == 1
        assert "ORIGINS: INVALID" in out
        assert "nothing was appended" in out
        assert not sidecar.exists(), "the refused record must not create the sidecar"

    def test_a_valid_record_round_trips(self, tmp_path, capsys):
        sidecar = tmp_path / "nested" / "s.jsonl"
        rc = origins.main([
            "--sidecar", str(sidecar), "append", "--phase", "design",
            "--cycle", "99", "--leg", "codex", "--item", "a real finding",
            "--origin", "fix-introduced", "--by-cycle", "98",
            "--verified-by-execution"])
        assert rc == 0
        assert "ORIGINS: APPENDED" in capsys.readouterr().out
        written = json.loads(sidecar.read_text(encoding="utf-8").strip())
        assert written["origin"] == "fix-introduced"
        assert written["by_cycle"] == 98
        assert written["verified_by_execution"] is True

    def test_item_is_truncated_to_the_ledgers_eighty_chars(self, tmp_path):
        sidecar = tmp_path / "s.jsonl"
        origins.main([
            "--sidecar", str(sidecar), "append", "--phase", "design",
            "--cycle", "99", "--leg", "codex", "--item", "x" * 500,
            "--origin", "instrument"])
        assert len(json.loads(sidecar.read_text(encoding="utf-8"))["item"]) == 80

    def test_appends_accumulate_rather_than_overwrite(self, tmp_path):
        sidecar = tmp_path / "s.jsonl"
        for cycle in (99, 100):
            origins.main([
                "--sidecar", str(sidecar), "append", "--phase", "design",
                "--cycle", str(cycle), "--leg", "codex", "--item", "x",
                "--origin", "instrument"])
        assert len(sidecar.read_text(encoding="utf-8").strip().split("\n")) == 2


class TestUnknownKeysPassThrough:
    def test_severity_and_note_do_not_make_a_record_invalid(self):
        # The prototype carries both, and neither is in the ledger's schema block.
        # A validator that rejected them would have refused its own calibration corpus.
        assert origins.validate(record(severity="Must", note="see c98")) == []

    def test_a_future_key_is_not_an_error(self):
        assert origins.validate(record(some_key_invented_later=1)) == []


class TestAgainstTheRealCorpus:
    """The 152 records from `gateway-consolidation` cycles 98–103."""

    @pytest.fixture(scope="class")
    def parsed(self):
        return origins.read_sidecar(PROTOTYPE)

    def test_the_fixture_is_present_and_whole(self, parsed):
        records, _ = parsed
        assert len(records) == 152, (
            "the calibration claim in the module docstring is about THIS corpus; if "
            "the fixture changes size the claim is no longer about what was measured")

    def test_every_hard_rule_fires_ZERO_times_on_it(self, parsed):
        # The bar: every precheck detector first written as hard fired 104/49/48 times
        # on documents that had just passed 83 and 74 audit cycles. A gate calibrated
        # only against fixtures it was written beside has not been calibrated.
        _, problems = parsed
        assert problems == [], f"detector fires on already-good data: {problems[:5]}"

    def test_the_headline_numbers_match_the_hand_count(self, parsed):
        records, _ = parsed
        agg = origins.aggregate(records)
        assert agg["fix_introduced"] == 51
        assert agg["self_caught"] == 27
        assert agg["rejected"] == 0
        assert origins.share(agg["fix_introduced"], agg["accepted"]) == "51/152 (33.6%)"

    def test_rejected_is_absent_from_the_corpus(self, parsed):
        # Pinned so the "no real-data coverage" note in the docstring stays true or
        # fails loudly when someone adds a rejected record to the fixture.
        records, _ = parsed
        assert origins.aggregate(records)["rejected"] == 0

    def test_every_seeded_origin_in_the_corpus_carries_its_by_cycle(self, parsed):
        records, _ = parsed
        seeded = [r for r in records if r["origin"] in origins.BY_CYCLE_REQUIRED]
        assert len(seeded) == 68
        assert all(isinstance(r.get("by_cycle"), int) for r in seeded)

    def test_the_per_cycle_trend_is_available(self, parsed):
        # H7's whole purpose: a rate per cycle, not one number at handoff.
        records, _ = parsed
        per_cycle = origins.aggregate(records)["per_cycle"]
        assert sorted(per_cycle) == [98, 99, 100, 101, 102, 103]
        assert per_cycle[98]["fix-introduced"] == 3
        assert per_cycle[103]["fix-introduced"] == 9
