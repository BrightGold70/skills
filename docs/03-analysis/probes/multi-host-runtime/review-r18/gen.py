#!/usr/bin/env python3
"""Build r18 fixtures and run smoke_assert.py v111 on each; print cmd + output."""
import json, subprocess, sys
from pathlib import Path

R = Path("/Users/kimhawk/orca/skills")
D = Path(__file__).resolve().parent
CHK = R / "docs/03-analysis/probes/multi-host-runtime/smoke_assert.py"

def head(p):
    return next(l for l in (R / p).read_text().splitlines() if l.startswith("# "))

SK = head("h-mad/SKILL.md")
AD = {"agy": head("h-mad/references/agy-runtime.md"), "grok": head("h-mad/references/grok-runtime.md")}
SKP, ADP = "h-mad/SKILL.md", {h: f"h-mad/references/{h}-runtime.md" for h in ("agy", "grok")}
SCRIPT = "python3 h-mad/scripts/h_mad_state_write.py --status"

# ---------- grok helpers
def g_list():
    return {"type": "available_commands", "commands": ["h-mad"]}
def g_call(i, tool, raw):
    return {"type": "tool_call", "toolCallId": i, "toolName": tool, "rawInput": raw}
def g_upd(i, out, status="completed"):
    return {"type": "tool_call_update", "toolCallId": i, "status": status, "rawOutput": out}
def g_read(i, path, text):
    return [g_call(i, "read_file", {"target_file": path}), g_upd(i, {"content": text})]
def g_sh(i, cmd):
    return [g_call(i, "run_terminal_command", {"command": cmd}), g_upd(i, {"output": ""})]

# ---------- agy helpers
def a_step(idx, state, tool, params, out=None, step_type="tool"):
    info = {"name": tool, "parameters": params}
    if out is not None:
        info["output"] = out
    return {"event": "step_update", "step_update": {"step_index": idx, "state": state, "step_type": step_type,
                                                    "tool_name": tool, "tool_info": info}}
def a_read(idx, path, text, key="FilePath"):
    p = {key: path}
    return [a_step(idx, "ACTIVE", "view_file", p), a_step(idx, "DONE", "view_file", p, text)]
def a_sh(idx, cmd):
    p = {"CommandLine": cmd}
    return [a_step(idx, "ACTIVE", "run_command", p), a_step(idx, "DONE", "run_command", p, "")]

def write(name, rows=None, raw=None):
    p = D / name
    if raw is not None:
        p.write_bytes(raw if isinstance(raw, bytes) else raw.encode())
    else:
        p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    return p

def run(name, host, extra=()):
    cmd = ["python3", str(CHK), "v111", "--host", host, "--log", str(D / name), "--root", str(R), *extra]
    r = subprocess.run(cmd, capture_output=True, text=True)
    out = (r.stdout.strip() or "") + (("  STDERR-LAST: " + r.stderr.strip().splitlines()[-1]) if r.stderr.strip() else "")
    print(f"{name} | rc={r.returncode} | {out}")
    return out

F = {}
def case(name, host, rows=None, raw=None, extra=()):
    write(name, rows, raw); F[name] = (host, extra)

# ===== H1: phantom declarations (text that never executes counted as a declared script run)
def grok_decl(cmd):
    return [g_list(), *g_read("r0", SKP, SK), *g_read("r1", ADP["grok"], AD["grok"]), *g_sh("s0", cmd)]
def agy_decl(cmd):
    return [*a_read(1, SKP, SK), *a_read(2, ADP["agy"], AD["agy"]), *a_sh(3, cmd)]
case("H1a-comment.log", "agy", agy_decl(f"{SCRIPT} #; HMAD_HOST=agy {SCRIPT}"))
case("H1b-heredoc.log", "agy", agy_decl(f"{SCRIPT}; cat <<EOF\nHMAD_HOST=agy {SCRIPT}\nEOF"))
case("H1c-false-and.log", "agy", agy_decl(f"{SCRIPT}; false && HMAD_HOST=agy {SCRIPT}"))
case("H1d-python-X.log", "agy", agy_decl(f"{SCRIPT}; HMAD_HOST=agy python3 -X h-mad/scripts/h_mad_state_write.py </dev/null"))
case("H1e-bash-o-c.log", "agy", agy_decl(f"{SCRIPT}; bash -o -c 'HMAD_HOST=agy {SCRIPT}'"))
case("H1f-grok-comment.log", "grok", grok_decl(f"{SCRIPT} #; HMAD_HOST=grok {SCRIPT}"))
case("H1-control.log", "agy", agy_decl(f"{SCRIPT}; HMAD_HOST=agy {SCRIPT}"))
case("H1-control-neg.log", "agy", agy_decl(f"{SCRIPT}"))

# ===== H2: quoted HMAD_HOST spelling escapes the raw-text mention count
case("H2a-quoted-export.log", "agy", agy_decl(f"export HMA\"\"D_HOST=codex; {SCRIPT}; HMAD_HOST=agy {SCRIPT}"))
case("H2b-function-override.log", "agy",
     agy_decl(f"python3() {{ env HMA\"\"D_HOST=codex /usr/bin/python3 \"$@\"; }}; HMAD_HOST=agy {SCRIPT}"))
case("H2c-var-built-name.log", "agy", agy_decl(f"n=HMAD; export ${{n}}_HOST=codex; {SCRIPT}; HMAD_HOST=agy {SCRIPT}"))
case("H2-control.log", "agy", agy_decl(f"export HMAD_HOST=codex; {SCRIPT}; HMAD_HOST=agy {SCRIPT}"))

# ===== H3: completion row before issue row
cp_g = "cp /tmp/evil.md h-mad/references/grok-runtime.md"
case("H3a-grok-update-before-call.log", "grok", [
    g_list(), *g_read("r0", SKP, SK),
    g_upd("r1", {"content": AD["grok"]}),            # completion of r1 ...
    *g_sh("w", cp_g),                                 # ... a write issued ...
    g_call("r1", "read_file", {"target_file": ADP["grok"]}),  # ... then r1 issued
    *g_sh("s0", f"HMAD_HOST=grok {SCRIPT}")])
case("H3a-control.log", "grok", [
    g_list(), *g_read("r0", SKP, SK), *g_sh("w", cp_g), *g_read("r1", ADP["grok"], AD["grok"]),
    *g_sh("s0", f"HMAD_HOST=grok {SCRIPT}")])
cp_a = "cp /tmp/evil.md h-mad/references/agy-runtime.md"
pa = {"FilePath": ADP["agy"]}
case("H3b-agy-done-before-active.log", "agy", [
    *a_read(1, SKP, SK),
    a_step(2, "DONE", "view_file", pa, AD["agy"]),
    *a_sh(3, cp_a),
    a_step(2, "ACTIVE", "view_file", pa),
    *a_sh(4, f"HMAD_HOST=agy {SCRIPT}")])
case("H3b-control.log", "agy", [
    *a_read(1, SKP, SK), *a_sh(3, cp_a), *a_read(2, ADP["agy"], AD["agy"]), *a_sh(4, f"HMAD_HOST=agy {SCRIPT}")])

# ===== H4: agy step_update payload that is not a dict is dropped silently
case("H4a-agy-nondict-step-lazy.log", "agy", [
    {"event": "step_update", "step_update": [{"step_index": 0, "state": "DONE", "step_type": "tool",
                                              "tool_name": "run_command",
                                              "tool_info": {"parameters": {"CommandLine": cp_a}}}]},
    *a_read(1, SKP, SK)])
case("H4b-agy-nondict-step-write.log", "agy", [
    {"event": "step_update", "step_update": "run_command: " + cp_a},
    *a_read(1, SKP, SK), *a_read(2, ADP["agy"], AD["agy"]), *a_sh(3, f"HMAD_HOST=agy {SCRIPT}")])
case("H4-control.log", "agy", [
    {"event": "step_update", "step_update": {"step_index": 0, "state": "DONE", "step_type": "planner_action"}},
    *a_read(1, SKP, SK)])
case("H4-control-lazy.log", "agy", [*a_read(1, SKP, SK)])

# ===== H5: view_file with a non-string FilePath beside a matching AbsolutePath
abs_ad = str(R / ADP["agy"])
pbad = {"FilePath": ["/tmp/evil.md"], "AbsolutePath": abs_ad}
case("H5a-filepath-list.log", "agy", [
    *a_read(1, SKP, SK),
    a_step(2, "ACTIVE", "view_file", pbad), a_step(2, "DONE", "view_file", pbad, AD["agy"]),
    *a_sh(3, f"HMAD_HOST=agy {SCRIPT}")])
pbad2 = {"FilePath": "/tmp/evil.md", "AbsolutePath": abs_ad}
case("H5-control.log", "agy", [
    *a_read(1, SKP, SK),
    a_step(2, "ACTIVE", "view_file", pbad2), a_step(2, "DONE", "view_file", pbad2, AD["agy"]),
    *a_sh(3, f"HMAD_HOST=agy {SCRIPT}")])

# ===== H6: duplicate JSON keys (last wins)
dup_rows = [json.dumps(g_list()), json.dumps({"type": "tool_call", "toolCallId": "r0", "toolName": "read_file", "rawInput": {"target_file": SKP}}),
            json.dumps(g_upd("r0", {"content": SK}))]
dup_rows.append('{"type":"tool_call","toolCallId":"w","toolName":"run_terminal_command","rawInput":{"command":"%s"},"toolName":"read_file","rawInput":{"target_file":"README.md"}}' % cp_g)
dup_rows.append(json.dumps(g_upd("w", {"content": "x"})))
dup_rows += [json.dumps(r) for r in g_read("r1", ADP["grok"], AD["grok"])]
dup_rows += [json.dumps(r) for r in g_sh("s0", f"HMAD_HOST=grok {SCRIPT}")]
case("H6-duplicate-keys.log", "grok", raw="\n".join(dup_rows) + "\n")
ctl = dup_rows[:3] + ['{"type":"tool_call","toolCallId":"w","toolName":"run_terminal_command","rawInput":{"command":"%s"}}' % cp_g] + dup_rows[4:]
case("H6-control.log", "grok", raw="\n".join(ctl) + "\n")

# ===== M: crashes / wrong-direction verdicts
case("M1a-grok-list-id.log", "grok", [g_list(), g_call(["r0"], "read_file", {"target_file": SKP}), g_upd(["r0"], {"content": SK})])
case("M1b-agy-list-index.log", "agy", [a_step([1], "ACTIVE", "view_file", {"FilePath": SKP}), a_step([1], "DONE", "view_file", {"FilePath": SKP}, SK)])
case("M1-control.log", "grok", [g_list(), g_call("r0", "read_file", {"target_file": SKP}), g_upd("r0", {"content": SK})])
case("M2-deep-nesting.log", "grok", raw=json.dumps(g_list()) + "\n" + '{"type":"text","x":' + "[" * 100000 + "]" * 100000 + "}\n")
case("M3-u2028-in-output.log", "grok", [g_list(), *g_read("r0", SKP, SK + "\nline more"), *g_read("r1", ADP["grok"], AD["grok"]), *g_sh("s0", f"HMAD_HOST=grok {SCRIPT}")])
case("M3b-u0085-in-output.log", "agy", [*a_read(1, SKP, SK + "\u0085x"), *a_read(2, ADP["agy"], AD["agy"]), *a_sh(3, f"HMAD_HOST=agy {SCRIPT}")])
case("M3-control.log", "grok", [g_list(), *g_read("r0", SKP, SK + "\nline more"), *g_read("r1", ADP["grok"], AD["grok"]), *g_sh("s0", f"HMAD_HOST=grok {SCRIPT}")])

# ===== L: drift
case("L1-bad-utf8.log", "agy", raw=b'{"event":"init","x":"\xff"}\n' + json.dumps(a_read(1, SKP, SK)[0]).encode() + b"\n")
case("L2-int-limit.log", "agy", raw='{"event":"init","x":' + "9" * 5000 + "}\n")

if __name__ == "__main__":
    only = sys.argv[1:]
    for name, (host, extra) in F.items():
        if not only or any(name.startswith(o) for o in only):
            run(name, host, extra)
