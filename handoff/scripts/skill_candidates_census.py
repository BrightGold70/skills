"""Census of the skill-candidate stores.

Two things make a naive grep wrong, both measured 2026-08-20:
  1. Terminal verdicts use TWO conventions -- `candidate: **SUPERSEDED**` (replaces)
     and a trailing `-- **SUPERSEDED** (...)` after an unchanged `candidate: yes`
     (appends). A terminal marker anywhere in the row wins.
  2. Recurrence BUMPS reuse the `- **name**:` syntax of a real candidate but are
     notes on an existing row. They carry no verdict of their own, and one of them
     says "Still candidate: yes" as PROSE -- which a verdict regex reads as a vote.
     Excluded by explicit phrase, listed on every run so the exclusion is auditable.
  3. The two stores do not share a row shape, and the failure that caused is worse
     than either of the above. `docs/skill-monitoring.md` records entries as
     `- <severity> **J<n> -- title.**` bullets closed by a `Status: `WORD`` line,
     and `rows()` ends a row on any line starting with `|` -- which that file is
     full of. Measured 2026-08-25: this script reported `candidates=3 OPEN=0`
     against 1946 lines carrying 46 real entries. Not an error, not an empty
     result: a CLEAN registry, which is the one answer nothing prompts you to
     re-check. So each store is parsed by its own reader, and every run prints a
     COVERAGE line -- entries seen versus row-shaped lines present -- because the
     generalisable bug was never "pipe tables are unsupported", it was "an
     unsupported shape reads as an empty backlog".
"""
import re, collections, sys, subprocess
from pathlib import Path
def _label(p):
    parts = Path(p).resolve().parts
    return "/".join(parts[-4:-2]) if len(parts) >= 4 else Path(p).stem


ROW  = re.compile(r'^- \*\*(.+?)\*\*')
# A row STARTS here whether or not its bolded name closes on the same line. `ROW`
# needs the closing `**` on one line, so a row whose name WRAPS was matched by
# neither the reader nor the coverage check -- it was missing from both sides of
# the ratio, which therefore stayed a reassuring `207/207`. Measured 2026-09-07: a
# row was appended (git diff: 18 lines inserted) and the census read `candidates=201`
# before and after; two rows already in the store, at the `.result.terminal.handle`
# J1 entry and the `handover_landed.py` entry, had never been counted by any run.
OPENER = re.compile(r'^- \*\*')
# `re.S` so the name can span the wrap. Non-greedy still stops at the FIRST `**`.
NAME = re.compile(r'^- \*\*(.+?)\*\*', re.S)


def row_name(body):
    """(name, text after the closing `**`) for a row, matched ACROSS a wrap.

    Returns (None, "") when the bold never closes anywhere in the row -- a real
    malformation, and one the caller must report rather than silently drop, since
    dropping it is the defect this whole block exists to close.
    """
    joined = "\n".join(body)
    m = NAME.match(joined)
    if not m:
        return None, ""
    # The tail is the remainder of the LINE the name closed on -- NOT the whole row.
    # Returning the whole row here silently widened `BUMP` from a first-line marker
    # to a body-wide search, which reclassified a LANDED row as a bump and kept the
    # LANDED total looking unchanged. Same semantics as the original first-line
    # slice for an unwrapped name, and its natural analogue for a wrapped one.
    rest = joined[m.end():]
    return " ".join(m.group(1).split()), rest.split("\n", 1)[0]
TERM = re.compile(r'\*\*(LANDED|SUPERSEDED|DECLINED)\b')
# `DECLINED` carries two meanings on purpose -- "idea rejected" and "useful, but
# no tool will be built" -- and the header documents that. A reader who skims
# the marker without the note misreads the second bucket as the first, so the
# bucket is named in the row and counted here rather than left to prose. An
# UNQUALIFIED marker is reported as its own number: it is exactly the row that
# gets misread, and folding it into either bucket would hide it.
# `[^(\n]{0,40}` because the bucket usually sits AFTER the date and the closing
# bold: `**DECLINED 2026-08-25 (triage: useful, not codable)**`. A tighter
# pattern matched only the two rows where it directly follows the marker and
# reported the other 20 as unqualified -- caught by running it over the real
# file, which a fixture built from the tight form would never have shown.
TRIAGE = re.compile(r'DECLINED[^(\n]{0,40}\(triage:\s*([^)]*)\)')
CAND = re.compile(r'candidate:\s*\**([A-Za-z-]+)')
# A bump/back-ref announces itself right after the bold name. `(still open; ...)`
# is NOT here on purpose -- that is the canonical row of live-e2e-pane-janitor.
# `^\s*\(\*already open above` is anchored like `(row ~N)`: HemaSuite's hpw:276
# QUOTES this marker mid-tail while being a real candidate, so an unanchored
# phrase would drop the very row that reports the gap.
BUMP = re.compile(r'recurrence, not a new row|no new recurrence|existing row, recurrence bumped|^\s*\(row ~\d+\)|^\s*\(\*already open above, recurrence raised\*\)')
OPEN = ("yes", "maybe")

def rows(p):
    return _rows(open(p).read())


def _rows(text):
    cur=None; out=[]
    for i,ln in enumerate(text.split("\n"),1):
        if OPENER.match(ln):
            if cur: out.append(cur)
            cur=(i,[ln])
        elif ln.startswith("#") or ln.startswith("|"):
            if cur: out.append(cur); cur=None
        elif cur is not None: cur[1].append(ln)
    if cur: out.append(cur)
    return out

# --- the J registry (`docs/skill-monitoring.md`) --------------------------
#
# Its own header states the contract: "every `J` entry ends with exactly one
# machine-readable status line". So the status is READ, never inferred -- the
# leading emoji is SEVERITY, and the body prose is where a census once found
# "MONITORING" inside a note and reported a fixed entry as open.
JROW = re.compile(r'^-\s*\S*\s*\*\*(J\d+[a-z]?)(?:\*\*)?\s*[\u2014\u2013-]')
JSTATUS = re.compile(r'Status:\s*`([A-Z]+)`')
# The vocabulary table in the file's own header, so used-vs-documented is a diff
# against the source rather than against a copy that drifts.
JVOCAB = re.compile(r'^\|\s*`([A-Z]+)`\s*\|')
JOPEN = ("MONITORING", "PLANNED")


def jrows(text):
    """(id, status|None) per J entry, bounded on the next entry or heading."""
    lines = text.split("\n"); starts = []
    for i, ln in enumerate(lines):
        m = JROW.match(ln.strip())
        if m: starts.append((i, m.group(1)))
    out = []
    for pos, (i, jid) in enumerate(starts):
        end = starts[pos + 1][0] if pos + 1 < len(starts) else len(lines)
        found = JSTATUS.findall("\n".join(lines[i:end]))
        # More than one status in an entry is not a verdict, it is a quotation
        # of another entry's. Refuse to pick.
        out.append((jid, found[0] if len(found) == 1 else None))
    return out


def is_monitoring(text):
    """A store is the J registry when its title says so AND it has J rows.

    `JROW` is `^`-anchored and matched per line; a bare `.search()` over the
    whole text would only ever try position 0 without `re.MULTILINE`, which is
    how the first version of this routing silently never fired.
    """
    # The title is searched over the opening lines, not pinned to line 0: a
    # blank first line or YAML frontmatter would otherwise route the registry to
    # the CANDIDATE reader, straight back into the `TOTAL candidates=0` failure
    # this routing exists to prevent. And the J-row requirement is gone: an
    # empty registry is still a registry, and "no entries yet" must not be the
    # thing that misroutes it.
    return any("Skill Monitoring" in ln for ln in text.split("\n")[:5])


def read_store(path, rev):
    if rev is None:
        return open(path).read()
    p = Path(path).absolute()
    command = ["git", "-C", str(p.parent)]
    root = subprocess.run(command + ["rev-parse", "--show-toplevel"],
                          capture_output=True, text=True, check=True).stdout.strip()
    return subprocess.run(command + ["show", f"{rev}:{p.relative_to(root).as_posix()}"],
                          capture_output=True, text=True, check=True).stdout


def open_candidates(text):
    out = []
    for ln, body in _rows(text):
        name, tail = row_name(body)
        blob = "\n".join(body)
        if name is None or BUMP.search(tail) or TERM.search(blob):
            continue
        match = CAND.search(blob)
        if match and match.group(1).lower() in OPEN:
            out.append((ln, body, name[:104]))
    return out


def apply_table(store, table):
    # Preserve existing bytes, including line endings; only insert new lines.
    with open(store, encoding="utf-8", newline="") as stream:
        text = stream.read()
    candidates = open_candidates(text)
    insertions = collections.defaultdict(list)
    header = True
    for line_number, line in enumerate(Path(table).read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [cell.strip().replace(r"\|", "|")
                 for cell in re.split(r"(?<!\\)\|", line[1:-1])]
        if header:
            header = False
            continue
        if len(cells) != 2 or not line.endswith("|"):
            print(f"APPLY: REFUSED reason=malformed-row line={line_number}")
            return 2
        if all(re.fullmatch(r":?-+:?", cell) for cell in cells):
            continue
        name, status = cells
        matches = [(ln, body) for ln, body, candidate in candidates if candidate == name]
        if len(matches) != 1:
            reason = "no-match" if not matches else "ambiguous"
            print(f"APPLY: REFUSED reason={reason} line={name}")
            return 2
        ln, body = matches[0]
        end = ln - 1
        for part in body:
            if not part.strip():
                break
            end += 1
        insertions[end].append(f"  — {status}\n")

    if not insertions:
        print("APPLY: REFUSED reason=empty-table")
        return 2

    # Split on "\n" only, as `_rows` numbers them: splitlines() also breaks on
    # U+2028/U+2029 and would shift every insertion below such a line.
    lines = re.findall(r"[^\n]*\n|[^\n]+\Z", text)
    for end, additions in sorted(insertions.items(), reverse=True):
        if end and not lines[end - 1].endswith(("\n", "\r")):
            additions = ["\n"] + additions
        lines[end:end] = additions
    updated = "".join(lines)
    Path(store).write_bytes(updated.encode("utf-8"))
    count = sum(len(additions) for additions in insertions.values())
    print(f"APPLY: inserted={count} OPEN {len(candidates)}→{len(open_candidates(updated))}")
    return 0


def main(argv=None):
    """Run the census over the store paths in `argv` (default `sys.argv[1:]`).

    Returns a process exit code. Importing this module runs nothing, so a
    caller that only wants to PARSE a store can do so without setting
    `sys.argv` or redirecting stdout first.
    """
    paths = list(sys.argv[1:] if argv is None else argv)
    if "-h" in paths or "--help" in paths:
        print(
            "usage: skill_candidates_census.py [--list-open] [--rev <rev>] "
            "[--apply <table.md>] <skill-candidates.md> [more...]"
        )
        return 0
    # `--list-open` names the rows behind the OPEN number. Nothing listed them,
    # so every session that wanted to reconcile the backlog re-derived the set
    # with an ad-hoc grep -- and this file has already been measured wrong twice
    # that way (a wrapped bold name counted by neither the reader nor the
    # coverage check, leaving a reassuring 207/207). It is a FLAG and add-only:
    # the default output is byte-identical, because the summary line is parsed
    # by other consumers.
    list_open = "--list-open" in paths
    paths = [a for a in paths if a != "--list-open"]
    rev = table = None
    for flag in ("--rev", "--apply"):
        if flag not in paths:
            continue
        index = paths.index(flag)
        if index + 1 == len(paths) or paths[index + 1].startswith("--"):
            print(f"usage: {flag} requires a value", file=sys.stderr)
            return 1
        value = paths[index + 1]
        del paths[index:index + 2]
        if flag == "--rev":
            rev = value
        else:
            table = value
    if table is not None and (rev is not None or len(paths) != 1):
        print("usage: --apply <table.md> requires one store and cannot combine with --rev",
              file=sys.stderr)
        return 1
    if not paths:
        print("usage: skill_candidates_census.py [--list-open] [--rev <rev>] "
              "[--apply <table.md>] <skill-candidates.md> [more...]",
              file=sys.stderr)
        return 1

    if table is not None:
        return apply_table(paths[0], table)

    grand=collections.Counter(); bumps_all=[]; coverage=[]
    for f in paths:
        tag=_label(f)
        try:
            text = read_store(f, rev)
        except subprocess.CalledProcessError as exc:
            detail = exc.stderr.splitlines()[0]
            print(f"census: cannot read {f} at {rev}: {detail}", file=sys.stderr)
            return 2

        if is_monitoring(text):
            entries=jrows(text)
            c=collections.Counter(s or "<none>" for _, s in entries)
            n=len(entries); op=sum(v for k,v in c.items() if k in JOPEN)
            print(f"{tag:8s} J-entries={n:5d} OPEN({'+'.join(JOPEN)})={op:4d}  "
                  + "  ".join(f"{k}={v}" for k,v in sorted(c.items(),key=lambda x:-x[1])))
            documented={m.group(1) for ln in text.split("\n") if (m:=JVOCAB.match(ln.strip()))}
            used={s for _, s in entries if s}
            if used-documented:
                print(f"  ! status words used but NOT documented in this file's own table: "
                      f"{', '.join(sorted(used-documented))}")
            if documented-used:
                print(f"  ~ documented but unused: {', '.join(sorted(documented-used))}")
            # Coverage compares the strict reader against a deliberately LOOSER
            # entry shape, so a row written slightly differently is visible. It must
            # NOT be measured against J-ids appearing anywhere: this file's own
            # header discusses the deliberate J31-J33 numbering gaps, so that metric
            # reports three phantom misses -- the self-pollution failure in reverse,
            # and a guard that cries wolf on the header is worse than none.
            # ANY id-shaped entry bullet, not just `J`. Hardcoding the prefix here
            # filters the rows the reader missed out of its own denominator, so
            # coverage reports clean while dropping them -- the guard rigged to
            # cover the gap it exists to expose. This file also carries F/G/H/A/V/P
            # entries (33 of them, measured 2026-08-25); they are per-review finding
            # rows rather than the standing registry, and they carry no `Status:`
            # line, so they are not counted as open work -- but they ARE reported.
            loose=sum(1 for ln in text.split("\n")
                      if ln.strip().startswith("- ") and re.search(r'\*\*[A-Z]+\d+', ln))
            seen={j for j, _ in entries}
            referenced={m for m in re.findall(r'\bJ\d+\b', text)}
            dangling=sorted(referenced - seen, key=lambda x: int(x[1:]))
            no_status=[j for j, s in entries if s is None]
            coverage.append((Path(f).name, n, loose, no_status))
            if dangling:
                print(f"  ~ referenced with no entry of their own (cross-links or "
                      f"deliberate gaps): {', '.join(dangling)}")
            continue

        c=collections.Counter(); bumps=[]; declined=collections.Counter(); unclosed=[]
        open_rows=[]
        for ln,body in _rows(text):
            name,tail=row_name(body)                    # matched ACROSS a wrap
            if name is None:
                unclosed.append(f"{tag}:{ln} {body[0][:70]}")
                continue
            blob="\n".join(body)
            if BUMP.search(tail):
                bumps.append(f"{tag}:{ln} {name}"); continue
            t=TERM.search(blob)
            if t:
                c[t.group(1)]+=1
                if t.group(1)=="DECLINED":
                    bucket=TRIAGE.search(blob)
                    if not bucket: declined["unqualified"]+=1
                    elif "not codable" in bucket.group(1): declined["useful-not-codable"]+=1
                    else: declined["not-useful"]+=1
                continue
            m=CAND.search(blob)
            verdict=m.group(1).lower() if m else "<none>"
            c[verdict]+=1
            # Same row object the counter just consumed, so the listing and the
            # number can never disagree -- which a second parser would eventually
            # manage, and silently.
            if verdict in OPEN:
                open_rows.append((ln, verdict, name))
        n=sum(c.values()); op=sum(v for k,v in c.items() if k in OPEN)
        print(f"{tag:8s} candidates={n:4d} OPEN(yes+maybe)={op:4d}  "
              + "  ".join(f"{k}={v}" for k,v in sorted(c.items(),key=lambda x:-x[1]))
              + f"   [+{len(bumps)} bump rows excluded]")
        if c.get("DECLINED"):
            # Printed unconditionally when there are any, `unqualified` included, so
            # a bare marker cannot hide behind a bucket it was never sorted into.
            print(f"  ~ DECLINED split: "
                  f"useful-not-codable={declined['useful-not-codable']}  "
                  f"not-useful={declined['not-useful']}  "
                  f"unqualified={declined['unqualified']}")
        if list_open:
            print(f"  OPEN rows in {tag} ({len(open_rows)}):")
            for ln, verdict, name in open_rows:
                print(f"    {tag}:{ln:<5} {verdict:5} {name[:104]}")
            assert len(open_rows) == op, (
                f"listing shows {len(open_rows)} open rows but the count says {op} — "
                "the two disagree, which is the defect this flag exists to avoid")
        grand.update(c); bumps_all+=bumps
        # Same coverage question for a candidate store: `- **` lines the reader did
        # not turn into a row are lines it did not understand.
        # Counted with OPENER, NOT with ROW. A coverage metric derived from the same
        # pattern as the reader it audits can only ever report agreement with itself;
        # these two numbers must be able to DISAGREE or the check is decoration.
        rowish=sum(1 for ln in text.split("\n") if OPENER.match(ln))
        # `unclosed` is deliberately NOT added to `parsed`: an opener the reader
        # could not turn into a row is a line it did not understand, and counting it
        # as parsed would restore the ratio to N/N — which is the exact tautology
        # this change exists to remove. The two numbers must be able to diverge.
        coverage.append((Path(f).name, n+len(bumps), rowish, []))
        if unclosed:
            print(f"  ~ {len(unclosed)} row(s) whose bold name never closes — NOT counted "
                  f"in any verdict bucket:")
            for u in unclosed: print(f"      {u}")
    print()
    n=sum(grand.values()); op=sum(v for k,v in grand.items() if k in OPEN)
    # A monitoring-only run has no candidates, and printing `TOTAL candidates=0`
    # for it is the same false-clean shape this file now guards against.
    if n or bumps_all:
        print(f"TOTAL candidates={n}  OPEN(yes+maybe)={op}  no={grand.get('no',0)}  "
          f"terminal={sum(v for k,v in grand.items() if k in ('LANDED','SUPERSEDED','DECLINED'))}  "
          f"verdict-less={grand.get('<none>',0)}")
        print(dict(grand))
        print(f"\nBUMP ROWS EXCLUDED ({len(bumps_all)}) -- notes on an existing row, not candidates:")
        for b in bumps_all: print("  " + b)

    # The line that would have caught this script reading a 1946-line registry as
    # three candidates. A count is only trustworthy next to what it did NOT read.
    print("\nCOVERAGE -- entries parsed vs row-shaped lines present:")
    for tag, parsed, present, no_status in coverage:
        # Named, not merely counted. An unexplained "NOT PARSED" reads as a defect
        # in the reader and invites widening it -- which would reclassify 33 closed
        # historical rows as open work in one commit. All 33 were read on
        # 2026-08-26 and none is live; see skill-monitoring.md's own header.
        why = (" (historical F/G/H/A/V/P findings log, pre-dates the `Status:` "
               "lifecycle -- NOT open work; promote to a J entry to track one)"
               if "monitoring" in tag else "")
        flag = "" if parsed >= present else (
            f"   <-- {present - parsed} ROW-SHAPED LINES NOT PARSED{why}")
        print(f"  {tag}: parsed={parsed} row-shaped={present}{flag}")
        if no_status:
            print(f"    ! entries with no single machine-readable status: {', '.join(no_status)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
