import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "h-mad" / "scripts" / "h_mad_blind_adjudication.py"

DISPUTED = ["zq-d1", "zq-d2", "zq-d3"]
POSITIVES = ["zq-p1", "zq-p2"]
NEGATIVES = ["zq-n1", "zq-n2", "zq-n3"]
ALL_IDS = DISPUTED + POSITIVES + NEGATIVES


def run(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=False, capture_output=True, text=True,
    )


@pytest.fixture
def corpus(tmp_path):
    path = tmp_path / "corpus.jsonl"
    rows = []
    for i, oid in enumerate(ALL_IDS + ["zq-unused"]):
        rows.append({
            "id": oid,
            "tag": "LEAKYTAG",
            "lane": "LANE-SECRET",
            "text": f"claim number {i}",
        })
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return path


def build(corpus, out, seed="7", disputed=DISPUTED, positives=POSITIVES,
          negatives=NEGATIVES, extra=()):
    return run(
        "build", "--corpus", str(corpus),
        "--disputed", ",".join(disputed),
        "--positives", ",".join(positives),
        "--negatives", ",".join(negatives),
        "--seed", seed, "--out", str(out), *extra,
    )


def read_payload(out):
    return [json.loads(l) for l in (out / "payload.jsonl").read_text().splitlines() if l.strip()]


def read_key(out):
    return json.loads((out / "key.json").read_text())


def write_verdicts(path, mapping):
    path.write_text("".join(
        json.dumps({"item": item, "verdict": v}) + "\n" for item, v in mapping.items()
    ))
    return path


def verdicts_for(key, decide):
    """decide(orig_id, tag) -> 'upheld' | 'rejected'"""
    return {item: decide(e["orig_id"], e["tag"]) for item, e in key.items()}


def test_round_trip_key_covers_every_selected_row(corpus, tmp_path):
    out = tmp_path / "out"
    r = build(corpus, out)
    assert r.returncode == 0, r.stderr
    payload = read_payload(out)
    key = read_key(out)
    assert len(payload) == len(ALL_IDS)
    assert sorted(p["item"] for p in payload) == sorted(key)
    assert sorted(e["orig_id"] for e in key.values()) == sorted(ALL_IDS)
    tags = {e["orig_id"]: e["tag"] for e in key.values()}
    assert {tags[i] for i in DISPUTED} == {"disputed"}
    assert {tags[i] for i in POSITIVES} == {"positive"}
    assert {tags[i] for i in NEGATIVES} == {"negative"}
    for p in payload:
        assert p["item"].startswith("item-")
    # content survives the blinding
    texts = sorted(p["text"] for p in payload)
    assert len(set(texts)) == len(ALL_IDS)


def test_payload_has_no_tag_and_no_original_ids(corpus, tmp_path):
    out = tmp_path / "out"
    r = build(corpus, out, extra=("--strip", "lane"))
    assert r.returncode == 0, r.stderr
    raw = (out / "payload.jsonl").read_text()
    for p in read_payload(out):
        assert "tag" not in p
        assert "id" not in p
        assert "lane" not in p
    assert "LEAKYTAG" not in raw
    assert "LANE-SECRET" not in raw
    for oid in ALL_IDS:
        assert oid not in raw
    for tag in ("disputed", "positive", "negative"):
        assert tag not in raw


def test_strip_is_repeatable_and_unstripped_fields_stay(corpus, tmp_path):
    out = tmp_path / "out"
    r = build(corpus, out, extra=("--strip", "lane", "--strip", "text"))
    assert r.returncode == 0, r.stderr
    for p in read_payload(out):
        assert set(p) == {"item"}
    out2 = tmp_path / "out2"
    assert build(corpus, out2).returncode == 0
    assert all("lane" in p for p in read_payload(out2))


def _order(out):
    key = read_key(out)
    return [key[p["item"]]["orig_id"] for p in read_payload(out)]


def test_same_seed_same_order_different_seed_different_order(corpus, tmp_path):
    a, b, c = tmp_path / "a", tmp_path / "b", tmp_path / "c"
    assert build(corpus, a, seed="11").returncode == 0
    assert build(corpus, b, seed="11").returncode == 0
    assert build(corpus, c, seed="12").returncode == 0
    assert _order(a) == _order(b)
    assert (a / "payload.jsonl").read_bytes() == (b / "payload.jsonl").read_bytes()
    assert _order(a) != _order(c)
    # and it is actually shuffled, not input order
    assert _order(a) != ALL_IDS


def test_score_reproduces_known_tallies(corpus, tmp_path):
    out = tmp_path / "out"
    assert build(corpus, out).returncode == 0
    key = read_key(out)

    def decide(oid, tag):
        if tag == "positive":
            return "upheld"
        if tag == "negative":
            return "rejected"
        return "upheld" if oid == "zq-d1" else "rejected"

    v = write_verdicts(tmp_path / "v.jsonl", verdicts_for(key, decide))
    r = run("score", "--key", str(out / "key.json"), "--verdicts", str(v))
    assert r.returncode == 0, r.stdout + r.stderr
    lines = r.stdout.splitlines()
    assert "disputed upheld=1/3" in lines
    assert "positives recovered=2/2" in lines
    assert "negatives clean=3/3" in lines
    assert lines[-1] == "ADJUDICATION: VALID"


def test_a_negative_called_upheld_fails_the_controls(corpus, tmp_path):
    out = tmp_path / "out"
    assert build(corpus, out).returncode == 0
    key = read_key(out)

    def decide(oid, tag):
        if tag == "positive":
            return "upheld"
        if oid == "zq-n2":
            return "upheld"
        return "rejected"

    v = write_verdicts(tmp_path / "v.jsonl", verdicts_for(key, decide))
    r = run("score", "--key", str(out / "key.json"), "--verdicts", str(v))
    lines = r.stdout.splitlines()
    assert "negatives clean=2/3" in lines
    assert "positives recovered=2/2" in lines
    assert lines[-1] == "ADJUDICATION: CONTROLS-FAILED"
    assert "ADJUDICATION: VALID" not in r.stdout
    assert r.returncode != 0


def test_a_missed_positive_fails_the_controls(corpus, tmp_path):
    out = tmp_path / "out"
    assert build(corpus, out).returncode == 0
    key = read_key(out)
    v = write_verdicts(tmp_path / "v.jsonl", verdicts_for(
        key, lambda oid, tag: "rejected" if tag != "positive" or oid == "zq-p1" else "upheld"))
    r = run("score", "--key", str(out / "key.json"), "--verdicts", str(v))
    assert "positives recovered=1/2" in r.stdout.splitlines()
    assert r.stdout.splitlines()[-1] == "ADJUDICATION: CONTROLS-FAILED"


def test_missing_verdict_is_incomplete(corpus, tmp_path):
    out = tmp_path / "out"
    assert build(corpus, out).returncode == 0
    key = read_key(out)
    # an otherwise perfect reader who skipped one disputed item
    mapping = verdicts_for(
        key, lambda oid, tag: "upheld" if tag == "positive" else "rejected")
    dropped = next(i for i, e in key.items() if e["tag"] == "disputed")
    del mapping[dropped]
    v = write_verdicts(tmp_path / "v.jsonl", mapping)
    r = run("score", "--key", str(out / "key.json"), "--verdicts", str(v))
    assert "ADJUDICATION: INCOMPLETE" in r.stdout
    assert "ADJUDICATION: VALID" not in r.stdout
    assert r.returncode != 0


def test_verdict_for_unknown_item_is_incomplete(corpus, tmp_path):
    out = tmp_path / "out"
    assert build(corpus, out).returncode == 0
    key = read_key(out)
    mapping = verdicts_for(
        key, lambda oid, tag: "upheld" if tag == "positive" else "rejected")
    mapping["item-999"] = "rejected"
    v = write_verdicts(tmp_path / "v.jsonl", mapping)
    r = run("score", "--key", str(out / "key.json"), "--verdicts", str(v))
    assert "ADJUDICATION: INCOMPLETE" in r.stdout
    assert r.returncode != 0


def test_unknown_verdict_word_is_refused(corpus, tmp_path):
    out = tmp_path / "out"
    assert build(corpus, out).returncode == 0
    key = read_key(out)
    mapping = verdicts_for(
        key, lambda oid, tag: "upheld" if tag == "positive" else "rejected")
    first = next(iter(mapping))
    mapping[first] = "maybe"
    v = write_verdicts(tmp_path / "v.jsonl", mapping)
    r = run("score", "--key", str(out / "key.json"), "--verdicts", str(v))
    assert "ADJUDICATION: VALID" not in r.stdout
    assert r.returncode != 0


def test_overlapping_tag_lists_refused(corpus, tmp_path):
    out = tmp_path / "out"
    r = build(corpus, out, negatives=NEGATIVES + ["zq-p1"])
    assert r.returncode != 0
    assert "zq-p1" in (r.stderr + r.stdout)
    assert not (out / "payload.jsonl").exists()


def test_missing_corpus_id_refused(corpus, tmp_path):
    out = tmp_path / "out"
    r = build(corpus, out, disputed=DISPUTED + ["zq-ghost"])
    assert r.returncode != 0
    assert "zq-ghost" in (r.stderr + r.stdout)
    assert not (out / "payload.jsonl").exists()


@pytest.mark.parametrize("which", ["positives", "negatives"])
def test_empty_control_list_refused(corpus, tmp_path, which):
    out = tmp_path / "out"
    kwargs = {which: []}
    r = build(corpus, out, **kwargs)
    assert r.returncode != 0
    assert which in (r.stderr + r.stdout)
    assert not (out / "payload.jsonl").exists()


def test_help_documents_verdict_vocabulary():
    r = run("score", "--help")
    assert r.returncode == 0
    assert "upheld" in r.stdout and "rejected" in r.stdout
