from gen import *
import unicodedata
F.clear()
def g_lazy(adpath):  # grok: skill read via path variant, then adapter + script
    return [g_list(), *g_read("r0", adpath, SK)]
for tag, p in [("dslash", "//" + str(R)[1:] + "/h-mad/SKILL.md"), ("dot", "h-mad/./SKILL.md"), ("trail", "h-mad/SKILL.md/"),
               ("tilde", "~/orca/skills/h-mad/SKILL.md"), ("var", "$HOME/orca/skills/h-mad/SKILL.md"), ("dotdot", "h-mad/../h-mad/SKILL.md"),
               ("case", "H-MAD/SKILL.md"), ("nfd", unicodedata.normalize("NFD", "h-mad/SKILL.md")), ("nul", "h-mad/SKILL.md\0x"),
               ("abs", str(R) + "/h-mad/SKILL.md"), ("suffix", "/tmp/x/h-mad/SKILL.md")]:
    case(f"C-path-{tag}.log", "grok", g_lazy(p))
case("C-orphan-update.log", "grok", [g_list(), *g_read("r0", SKP, SK), g_upd("zz", {"x": 1}, "in_progress")])
case("C-update-rawinput.log", "grok", [g_list(), g_call("r0", "read_file", {"target_file": SKP}), {**g_upd("r0", {"content": SK}), "rawInput": {}}])
case("C-two-terminal.log", "grok", [g_list(), *g_read("r0", SKP, SK), g_upd("r0", {"content": SK}, "failed")])
case("C-reused-id.log", "grok", [g_list(), *g_read("r0", SKP, SK), *g_read("r0", SKP, SK)])
case("C-grok-unknown-row.log", "grok", [g_list(), *g_read("r0", SKP, SK), {"type": "plan"}])
case("C-grok-not-listed.log", "grok", [*g_read("r0", SKP, SK)])
case("C-grok-no-skill.log", "grok", [g_list(), *g_read("r1", ADP["grok"], AD["grok"]), *g_sh("s0", f"HMAD_HOST=grok {SCRIPT}")])
case("C-agy-no-skill.log", "agy", [*a_read(2, ADP["agy"], AD["agy"]), *a_sh(3, f"HMAD_HOST=agy {SCRIPT}")])
case("C-parallel-write.log", "agy", [a_step(2, "ACTIVE", "view_file", pa), *a_sh(3, cp_a), a_step(2, "DONE", "view_file", pa, AD["agy"]), *a_read(1, SKP, SK)])
case("C-agy-no-active-write.log", "agy", [*a_read(1, SKP, SK), *a_read(2, ADP["agy"], AD["agy"]), a_step(3, "DONE", "run_command", {"CommandLine": cp_a}, ""), *a_sh(4, f"HMAD_HOST=agy {SCRIPT}")])
case("C-agy-step-nonstep-same-idx.log", "agy", [*a_read(1, SKP, SK), {"event": "step_update", "step_update": {"step_index": 1, "state": "DONE", "step_type": "agent_response"}}])
case("C-agy-idx-reuse.log", "agy", [*a_read(1, SKP, SK), *a_read(1, ADP["agy"], AD["agy"])])
case("C-agy-noindex.log", "agy", [{"event": "step_update", "step_update": {"state": "DONE", "step_type": "tool", "tool_name": "view_file", "tool_info": {"parameters": {"FilePath": SKP}, "output": SK}}}])
case("C-agy-agentresp-with-tool.log", "agy", [{"event": "step_update", "step_update": {"step_index": 0, "state": "DONE", "step_type": "agent_response", "tool_name": "run_command", "tool_info": {"parameters": {"CommandLine": cp_a}}}}, *a_read(1, SKP, SK)])
case("C-agy-both-params-mismatch.log", "agy", [*a_read(1, SKP, SK), a_step(2,"ACTIVE","view_file",{"FilePath": ADP["agy"], "AbsolutePath": "/tmp/h-mad/references/agy-runtime.md"}), a_step(2,"DONE","view_file",{"FilePath": ADP["agy"], "AbsolutePath": "/tmp/h-mad/references/agy-runtime.md"}, AD["agy"]), *a_sh(3, f"HMAD_HOST=agy {SCRIPT}")])
case("C-agy-null-output.log", "agy", [*a_read(1, SKP, SK), a_step(2,"ACTIVE","view_file",pa), a_step(2,"DONE","view_file",pa, None) | {}, *a_sh(3, f"HMAD_HOST=agy {SCRIPT}")])
case("C-bash-c-dashdash.log", "agy", agy_decl(f"bash -c -- 'HMAD_HOST=agy {SCRIPT}'"))
case("C-bash-script-then-c.log", "agy", agy_decl(f"bash x.sh -c 'HMAD_HOST=agy {SCRIPT}'"))
case("C-python-c.log", "agy", agy_decl(f"HMAD_HOST=agy python3 -c 'pass' h-mad/scripts/h_mad_state_write.py"))
case("C-python-stdin.log", "agy", agy_decl(f"HMAD_HOST=agy python3 - h-mad/scripts/h_mad_state_write.py"))
case("C-quoted-name-prefix.log", "agy", agy_decl(f"\"HMAD_HOST=agy\" {SCRIPT}"))
case("C-other-host.log", "agy", agy_decl(f"HMAD_HOST=grok {SCRIPT}; HMAD_HOST=agy {SCRIPT}"))
case("C-quote-value.log", "agy", agy_decl(f"HMAD_HOST=ag\"y\" {SCRIPT}"))
case("C-script-before-read.log", "agy", [*a_read(1, SKP, SK), *a_sh(3, f"HMAD_HOST=agy {SCRIPT}"), *a_read(4, ADP["agy"], AD["agy"])])
case("C-grep-tool-lazy.log", "grok", [g_list(), g_call("q", "grep", {"pattern": "x"}), g_upd("q", {"x": ""}), *g_read("r0", SKP, SK)])
case("C-u2028-escaped.log", "grok", raw="\n".join(json.dumps(r) for r in [g_list(), *g_read("r0", SKP, SK + " ")]) + "\n")
case("C-link-relative.log", "agy", [*a_read(1, "/home/smoke/lnk/SKILL.md", SK)], extra=("--home", "/home/smoke", "--link", "lnk"))
case("C-link-relative-cwd.log", "agy", [*a_read(1, str(D) + "/lnk/SKILL.md", SK)], extra=("--link", "lnk"))
case("C-codex-any.log", "codex", raw="exec\nbash -lc 'cat h-mad/SKILL.md' in /x\n succeeded in 1ms:\n" + SK + "\n")
for name, (host, extra) in F.items():
    run(name, host, extra)
