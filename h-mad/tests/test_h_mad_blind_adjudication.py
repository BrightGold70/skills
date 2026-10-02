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
          negatives=NEGATIVES, extra=("--keep", "text")):
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
    r = build(corpus, out)
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


def test_keep_is_an_allowlist_and_repeatable(corpus, tmp_path):
    out = tmp_path / "out"
    assert build(corpus, out).returncode == 0
    for p in read_payload(out):
        assert set(p) == {"item", "text"}
    out2 = tmp_path / "out2"
    r = build(corpus, out2, extra=("--keep", "text", "--keep", "lane"))
    assert r.returncode == 0, r.stderr
    for p in read_payload(out2):
        assert set(p) == {"item", "text", "lane"}


def test_unlisted_label_field_never_reaches_payload(tmp_path):
    """H1: a corpus field the builder never heard of must not leak by default."""
    path = tmp_path / "corpus.jsonl"
    rows = [{"id": oid, "text": f"t{i}",
             "label": "TP" if oid in POSITIVES else ("FP" if oid in NEGATIVES else "DQ")}
            for i, oid in enumerate(ALL_IDS)]
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    out = tmp_path / "out"
    r = build(path, out)
    assert r.returncode == 0, r.stderr
    raw = (out / "payload.jsonl").read_text()
    for p in read_payload(out):
        assert "label" not in p
    for leak in ('"TP"', '"FP"', '"DQ"', "label"):
        assert leak not in raw


def test_build_without_keep_is_refused(corpus, tmp_path):
    out = tmp_path / "out"
    r = build(corpus, out, extra=())
    assert r.returncode != 0
    assert "--keep" in (r.stderr + r.stdout)
    assert not (out / "payload.jsonl").exists()


def test_strip_is_retired_and_points_at_keep(corpus, tmp_path):
    out = tmp_path / "out"
    r = build(corpus, out, extra=("--keep", "text", "--strip", "lane"))
    assert r.returncode != 0
    assert "--keep" in (r.stderr + r.stdout)
    assert not (out / "payload.jsonl").exists()


@pytest.mark.parametrize("field", ["id", "tag", "item"])
def test_reserved_field_in_keep_is_refused(corpus, tmp_path, field):
    out = tmp_path / "out"
    r = build(corpus, out, extra=("--keep", "text", "--keep", field))
    assert r.returncode != 0
    assert field in (r.stderr + r.stdout)
    assert not (out / "payload.jsonl").exists()


def test_corpus_item_field_cannot_overwrite_assigned_item(tmp_path):
    """M4: a corpus row carrying 'item' must never replace the assigned id."""
    path = tmp_path / "corpus.jsonl"
    rows = [{"id": oid, "text": f"t{i}", "item": f"FORGED-{oid}"}
            for i, oid in enumerate(ALL_IDS)]
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    out = tmp_path / "out"
    r = build(path, out, extra=("--keep", "text", "--keep", "item"))
    assert r.returncode != 0
    assert not (out / "payload.jsonl").exists()
    # with item NOT kept the corpus field is simply never copied
    out2 = tmp_path / "out2"
    assert build(path, out2).returncode == 0
    assert "FORGED" not in (out2 / "payload.jsonl").read_text()
    key = read_key(out2)
    assert sorted(p["item"] for p in read_payload(out2)) == sorted(key)


def test_kept_field_missing_from_a_selected_row_is_refused(tmp_path):
    """The schema difference itself would tell a reader which row is which."""
    path = tmp_path / "corpus.jsonl"
    rows = []
    for i, oid in enumerate(ALL_IDS + ["zq-unused"]):
        row = {"id": oid, "text": f"t{i}", "note": f"n{i}"}
        if oid in ("zq-p1", "zq-unused"):
            del row["note"]
        rows.append(row)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    out = tmp_path / "out"
    r = build(path, out, extra=("--keep", "text", "--keep", "note"))
    assert r.returncode != 0
    assert "REFUSED" in r.stderr and "Traceback" not in r.stderr
    assert "note" in r.stderr
    assert "zq-p1" in r.stderr
    assert not (out / "payload.jsonl").exists()
    # an UNSELECTED row lacking the field does not matter
    out2 = tmp_path / "out2"
    assert build(path, out2).returncode == 0


def test_duplicate_corpus_id_is_refused(corpus, tmp_path):
    with corpus.open("a") as fh:
        fh.write(json.dumps({"id": "zq-n1", "text": "second copy"}) + "\n")
    out = tmp_path / "out"
    r = build(corpus, out)
    assert r.returncode != 0
    assert "REFUSED" in r.stderr and "duplicate" in r.stderr
    assert "zq-n1" in r.stderr
    assert not (out / "payload.jsonl").exists()


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


def _score_key(tmp_path, key_obj, verdict_rows):
    kp = tmp_path / "key.json"
    kp.write_text(json.dumps(key_obj))
    vp = tmp_path / "v.jsonl"
    vp.write_text("".join(json.dumps(r) + "\n" for r in verdict_rows))
    return run("score", "--key", str(kp), "--verdicts", str(vp))


def _assert_incomplete(r):
    assert r.returncode != 0
    assert "Traceback" not in r.stderr
    assert "ADJUDICATION: VALID" not in r.stdout
    tokens = [l for l in r.stdout.splitlines() if l.startswith("ADJUDICATION:")]
    assert len(tokens) == 1, r.stdout + r.stderr
    assert tokens[0].startswith("ADJUDICATION: INCOMPLETE reason="), tokens


def test_empty_key_is_incomplete(tmp_path):
    _assert_incomplete(_score_key(tmp_path, {}, []))


def test_key_with_only_disputed_items_is_incomplete(tmp_path):
    key = {"item-001": {"orig_id": "a", "tag": "disputed"},
           "item-002": {"orig_id": "b", "tag": "disputed"}}
    rows = [{"item": "item-001", "verdict": "upheld"},
            {"item": "item-002", "verdict": "rejected"}]
    _assert_incomplete(_score_key(tmp_path, key, rows))


@pytest.mark.parametrize("missing", ["positive", "negative"])
def test_key_missing_one_control_class_is_incomplete(tmp_path, missing):
    key = {"item-001": {"orig_id": "a", "tag": "disputed"},
           "item-002": {"orig_id": "b", "tag": "positive"},
           "item-003": {"orig_id": "c", "tag": "negative"}}
    key = {k: v for k, v in key.items() if v["tag"] != missing}
    good = {"disputed": "upheld", "positive": "upheld", "negative": "rejected"}
    rows = [{"item": k, "verdict": good[v["tag"]]} for k, v in key.items()]
    r = _score_key(tmp_path, key, rows)
    _assert_incomplete(r)
    assert missing in r.stdout


@pytest.mark.parametrize("key_obj", [
    [],
    "item-001",
    {"item-001": "junk"},
    {"item-001": {"orig_id": "a"}},
    {"item-001": {"orig_id": "a", "tag": "bogus"}},
    {"item-001": {"tag": "positive"}},
])
def test_malformed_key_is_incomplete_with_token(tmp_path, key_obj):
    rows = [{"item": "item-001", "verdict": "upheld"}]
    _assert_incomplete(_score_key(tmp_path, key_obj, rows))


def test_unhashable_verdict_item_is_incomplete_with_token(tmp_path):
    key = {"item-001": {"orig_id": "a", "tag": "positive"},
           "item-002": {"orig_id": "b", "tag": "negative"}}
    rows = [{"item": ["item-001"], "verdict": "upheld"},
            {"item": "item-002", "verdict": "rejected"}]
    _assert_incomplete(_score_key(tmp_path, key, rows))
