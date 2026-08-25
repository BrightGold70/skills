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
import re, collections, sys
from pathlib import Path
def _label(p):
    parts = Path(p).resolve().parts
    return "/".join(parts[-4:-2]) if len(parts) >= 4 else Path(p).stem


ROW  = re.compile(r'^- \*\*(.+?)\*\*')
TERM = re.compile(r'\*\*(LANDED|SUPERSEDED|DECLINED)\b')
CAND = re.compile(r'candidate:\s*\**([A-Za-z-]+)')
# A bump/back-ref announces itself right after the bold name. `(still open; ...)`
# is NOT here on purpose -- that is the canonical row of live-e2e-pane-janitor.
BUMP = re.compile(r'recurrence, not a new row|no new recurrence|existing row, recurrence bumped|^\s*\(row ~\d+\)')
OPEN = ("yes", "maybe")

def rows(p):
    cur=None; out=[]
    for i,ln in enumerate(open(p).read().split("\n"),1):
        if ROW.match(ln):
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
JROW = re.compile(r'^-\s*\S*\s*\*\*(J\d+[a-z]?)\s*[\u2014\u2013-]')
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
    lines = text.split("\n")
    if not lines or "Skill Monitoring" not in lines[0]:
        return False
    return any(JROW.match(ln.strip()) for ln in lines)


paths = sys.argv[1:]
if not paths:
    sys.exit("usage: skill_candidates_census.py <skill-candidates.md> [more...]")

grand=collections.Counter(); bumps_all=[]; coverage=[]
for f in paths:
    tag=_label(f)
    text=open(f).read()

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
        loose=sum(1 for ln in text.split("\n")
                  if ln.strip().startswith("- ") and re.search(r'\*\*J\d+', ln))
        seen={j for j, _ in entries}
        referenced={m for m in re.findall(r'\bJ\d+\b', text)}
        dangling=sorted(referenced - seen, key=lambda x: int(x[1:]))
        no_status=[j for j, s in entries if s is None]
        coverage.append((Path(f).name, n, loose, no_status))
        if dangling:
            print(f"  ~ referenced with no entry of their own (cross-links or "
                  f"deliberate gaps): {', '.join(dangling)}")
        continue

    c=collections.Counter(); bumps=[]
    for ln,body in rows(f):
        m0=ROW.match(body[0])
        name=m0.group(1)
        tail=body[0][m0.end():]                     # text AFTER the closing ** of the name
        blob="\n".join(body)
        if BUMP.search(tail):
            bumps.append(f"{tag}:{ln} {name}"); continue
        t=TERM.search(blob)
        if t: c[t.group(1)]+=1; continue
        m=CAND.search(blob)
        c[m.group(1).lower() if m else "<none>"]+=1
    n=sum(c.values()); op=sum(v for k,v in c.items() if k in OPEN)
    print(f"{tag:8s} candidates={n:4d} OPEN(yes+maybe)={op:4d}  "
          + "  ".join(f"{k}={v}" for k,v in sorted(c.items(),key=lambda x:-x[1]))
          + f"   [+{len(bumps)} bump rows excluded]")
    grand.update(c); bumps_all+=bumps
    # Same coverage question for a candidate store: `- **` lines the reader did
    # not turn into a row are lines it did not understand.
    rowish=sum(1 for ln in open(f).read().split("\n") if ROW.match(ln))
    coverage.append((Path(f).name, n+len(bumps), rowish, []))
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
    flag = "" if parsed >= present else f"   <-- {present - parsed} ROW-SHAPED LINES NOT PARSED"
    print(f"  {tag}: parsed={parsed} row-shaped={present}{flag}")
    if no_status:
        print(f"    ! entries with no single machine-readable status: {', '.join(no_status)}")
