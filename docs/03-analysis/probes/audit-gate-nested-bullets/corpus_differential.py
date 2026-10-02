import sys, re, subprocess, importlib.util, pathlib
repo = pathlib.Path("/Users/kimhawk/orca/skills")
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m; spec.loader.exec_module(m); return m
sys.path.insert(0, str(repo / "h-mad/scripts"))
old = load("old_gate", sys.argv[1]); new = load("new_gate", repo / "h-mad/scripts/h_mad_audit_gate.py")
files = subprocess.run(["git", "-C", str(repo), "ls-files", "*.audit.*.md", "*audit*.md"], capture_output=True, text=True).stdout.split()
files = sorted(set(f for f in files if f.endswith(".md")))
NEST = re.compile(r"^[ \t]{2,}[-*•] ", re.M)
def sect_nested(text):
    # indented bullet anywhere inside a Must-fix / Should-fix section
    out = False
    for m in re.finditer(r"(?ms)^\s*#{1,6}\s*(Must-fix|Should-fix)\b.*?(?=^\s*#{1,6}\s|\Z)", text):
        if NEST.search(m.group(0)): out = True
    return out
scored = changed = bad = acked_any = flips = lower = to_meas_only = 0
for f in files:
    t = (repo / f).read_text(encoding="utf-8", errors="replace")
    if not old.has_gate_sections(t): continue
    ack = old._acknowledged_from_text(t)
    acked_any += bool(ack)
    a, b = old.classify_detail(t, ack), new.classify_detail(t, ack)
    flips += a["verdict"] != b["verdict"]
    # SKILL.md routes measurement-only musts to the sidecar: that decision must never newly fire.
    to_meas_only += a["must_build"] > 0 and b["must_count"] > 0 and b["must_build"] == 0
    lower += b["must_count"] < a["must_count"] or b["should_count"] < a["should_count"]
    scored += 1
    ka = {k: a[k] for k in a if k != "verdict" and not isinstance(a[k], (list, dict))}
    kb = {k: b[k] for k in b if k != "verdict" and not isinstance(b[k], (list, dict))}
    if (a["verdict"], ka) != (b["verdict"], kb):
        changed += 1
        nested = sect_nested(t)
        if not nested: bad += 1
        print(f"CHANGED nested={nested} {f}: {a['verdict']} must={a['must_count']} should={a.get('should_count')} -> {b['verdict']} must={b['must_count']} should={b.get('should_count')}")
print(f"DIFF: scored={scored} with_ack_sidecar={acked_any} changed={changed} changed_without_nested_bullets={bad} verdict_flips={flips} newly_measurement_only_musts={to_meas_only}")
