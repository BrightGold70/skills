import random,itertools,sys
from h import O,N
random.seed(int(sys.argv[1]))
ind=["","  "," ","   ","    ","\t","      ","\t  "]
mk=["- ","* ","• ","-  "]
pl=["A","B","C","D","None","**None**","Build defects:","[k1] A","A.","a"]
cl=["class: measurement","class: build","class: cosmetic","Class: BUILD","**class: measurement**","`class: Measurement.`","class:measurement","class: build-ish"]
pr=["prose","1. numbered","> quote","None"]
def line():
    r=random.random()
    if r<.55: s=random.choice(ind)+random.choice(mk)+random.choice(pl)
    elif r<.85: s=random.choice(ind)+random.choice(cl)
    else: s=random.choice(ind)+random.choice(pr)
    if random.random()<.1: s+="\r"
    return s
def sec(): return "\n".join(line() for _ in range(random.randint(0,7)))
acks=["A","B","C","D","Build defects:","[k1] whatever","a.","prose"]
bad={};C=0
for i in range(int(sys.argv[2])):
    t="## Must-fix\n"+sec()+"\n## Should-fix\n"+sec()+"\n"
    ack=set(random.sample(acks,random.randint(0,3)))
    o=O.classify_detail(t,ack);n=N.classify_detail(t,ack)
    C+=(n["must_count"]+n["should_count"]<o["must_count"]+o["should_count"]);tags=[]
    if o["verdict"]!=n["verdict"]: tags.append("V")
    if o["must_build"]>0 and n["must_count"]>0 and n["must_build"]==0: tags.append("MEAS")
    if o["must_build"]==0 and o["must_count"]>0 and n["must_build"]>0: tags.append("rev-meas")
    if o["ack_refused"]>n["ack_refused"]: tags.append("ACKREF")
    if n["must_count"]>o["must_count"] or n["should_count"]>o["should_count"]: tags.append("UP")
    for tg in tags:
        if tg not in bad or len(t)<len(bad[tg][0]): bad[tg]=(t,ack,o,n)
for k,(t,a,o,n) in bad.items():
    print("==",k,a);print(repr(t));print(" old",{x:o[x] for x in o if o[x]});print(" new",{x:n[x] for x in n if n[x]})
print("done",list(bad),"collapsed",C)
