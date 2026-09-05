import re, pathlib, subprocess
ROOTS = ["h-mad", "handoff"]
def glob_corpus():
    out = []
    for r in ROOTS:
        for p in sorted(pathlib.Path(r).rglob("*.md")):
            rel = p.as_posix()
            if "/archive/" in rel or rel.startswith(r + "/archive/"):
                continue
            out.append(rel)
    return sorted(out)
tracked = sorted(l for l in subprocess.run(["git","ls-files","--",*ROOTS],capture_output=True,text=True).stdout.split("\n") if l.endswith(".md") and "/archive/" not in l)

FENCE = re.compile(r"^ {0,3}(?P<ch>`{3,}|~{3,})(?P<info>.*)$")
UNDER = re.compile(r"^ {0,3}(=+|-+)[ \t]*$")
NOTPARA = re.compile(r"^(?: {0,3}(?:[-*+>]|\d+[.)])(?: |\t)| {4,}| {0,3}#{1,6}(?: |\t|$)|\s*$| {0,3}\|)")

def census(files):
    total = 0; hits = []
    for rel in files:
        lines = pathlib.Path(rel).read_text(encoding="utf-8", errors="replace").split("\n")
        i = 0
        # skip YAML front matter
        if lines and lines[0].strip() == "---":
            for j in range(1, len(lines)):
                if lines[j].strip() in ("---", "..."):
                    i = j + 1
                    break
        open_ch = None; open_len = 0
        prev_para = False
        while i < len(lines):
            line = lines[i]
            m = FENCE.match(line)
            if open_ch is None:
                if m and (m.group("ch")[0] != "`" or "`" not in m.group("info")):
                    open_ch, open_len = m.group("ch")[0], len(m.group("ch"))
                    prev_para = False; i += 1; continue
            else:
                if m and m.group("ch")[0] == open_ch and len(m.group("ch")) >= open_len and not m.group("info").strip():
                    open_ch = None
                prev_para = False; i += 1; continue
            if prev_para and UNDER.match(line) and line.strip():
                total += 1; hits.append((rel, i + 1, line[:40]))
                prev_para = False
            else:
                prev_para = bool(line.strip()) and not NOTPARA.match(line)
            i += 1
    return total, hits

for name, files in (("glob", glob_corpus()), ("tracked", tracked)):
    t, h = census(files)
    print(f"[{name}] files={len(files)} setext_headings={t}")
    for x in h[:6]:
        print("   ", x)
