"""Census of the skill-candidate stores.

Two things make a naive grep wrong, both measured 2026-08-20:
  1. Terminal verdicts use TWO conventions -- `candidate: **SUPERSEDED**` (replaces)
     and a trailing `-- **SUPERSEDED** (...)` after an unchanged `candidate: yes`
     (appends). A terminal marker anywhere in the row wins.
  2. Recurrence BUMPS reuse the `- **name**:` syntax of a real candidate but are
     notes on an existing row. They carry no verdict of their own, and one of them
     says "Still candidate: yes" as PROSE -- which a verdict regex reads as a vote.
     Excluded by explicit phrase, listed on every run so the exclusion is auditable.
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

paths = sys.argv[1:]
if not paths:
    sys.exit("usage: skill_candidates_census.py <skill-candidates.md> [more...]")

grand=collections.Counter(); bumps_all=[]
for f in paths:
    tag=_label(f)
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
print()
n=sum(grand.values()); op=sum(v for k,v in grand.items() if k in OPEN)
print(f"TOTAL candidates={n}  OPEN(yes+maybe)={op}  no={grand.get('no',0)}  "
      f"terminal={sum(v for k,v in grand.items() if k in ('LANDED','SUPERSEDED','DECLINED'))}  "
      f"verdict-less={grand.get('<none>',0)}")
print(dict(grand))
print(f"\nBUMP ROWS EXCLUDED ({len(bumps_all)}) -- notes on an existing row, not candidates:")
for b in bumps_all: print("  " + b)
