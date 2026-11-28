import os, subprocess, time
from pathlib import Path
J = os.path.join; N = "docs/.bkit-memory.json"; G = ["git", "--no-optional-locks"]
def git(a, data=None): return subprocess.run(G + a, input=data, capture_output=True, text=True).stdout
def walk(prune):
    level, seen, hits, procs = ["."], 0, 0, 0
    while level:
        if prune == "ignored" and level != ["."]:
            out = set(git(["check-ignore", "-z", "--stdin"], "\0".join(level) + "\0").split("\0")); procs += 1
            level = [d for d in level if d not in out]
        kids = []
        for d in level:
            seen += 1; hits += os.path.lexists(J(d, N))
            kids += [J(d, e.name) for e in os.scandir(d) if e.is_dir(follow_symlinks=False) and e.name != ".git"]
        level = [k for k in kids if not (prune and os.path.lexists(J(k, ".git")))]
    return seen, hits, procs
def listed():
    ds = {"."}
    for f in git(["ls-files", "-z", "-co", "--exclude-standard"]).split("\0"):
        while f := os.path.dirname(f): ds.add(f)
    return len(ds), sum(os.path.lexists(J(d, N)) for d in ds), 1
ways = {"rglob": lambda: ("-", len(list(Path(".").rglob(N))), 0), "all": lambda: walk(""),
        "nested": lambda: walk("nested"), "ignored": lambda: walk("ignored"), "ls-files": listed}
for name, way in ways.items():
    for _ in range(4):
        s = time.perf_counter(); r = way(); print(name, *r, round(time.perf_counter() - s, 2))
