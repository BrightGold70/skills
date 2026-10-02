import importlib.util,sys
def load(n,p):
    s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
O=load("old","old_gate.py");N=load("new",__import__("pathlib").Path(__file__).resolve().parents[4]/"h-mad/scripts/h_mad_audit_gate.py")
K=["verdict","must_count","must_build","must_measurement","should_count","should_build","should_measurement","ack_refused"]
def doc(must,should="None"): return "## Must-fix\n"+must+"\n## Should-fix\n"+should+"\n"
def cmp(name,text,ack=set()):
    o=O.classify_detail(text,ack);n=N.classify_detail(text,ack)
    f=lambda d:" ".join(f"{k[:6]}={d.get(k)}" for k in K)
    bad=[]
    if o["verdict"]!=n["verdict"]: bad.append("V")
    if o["must_build"]>0 and n["must_count"]>0 and n["must_build"]==0: bad.append("MEAS-ONLY")
    if o["ack_refused"]>n["ack_refused"]: bad.append("ACKREF↓")
    print(("BROKEN "+",".join(bad) if bad else "ok"),name);print("  old",f(o));print("  new",f(n))
