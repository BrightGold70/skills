"""Throwaway differential: old docsections heading regex vs the CommonMark ATX selector, over the repo's docs."""
import re, sys, pathlib
OLD = re.compile(r"^(?P<marks>#+) (?P<text>.*?)\s*$")             # docsections.titled_section's shape, any heading text
NEW = re.compile(r"^ {0,3}(?P<marks>#{1,6})(?:[ \t]+(?P<text>.*?))?(?:[ \t]+#+)?[ \t]*$")
def fence_lines(text):
    """Set of line numbers inside a fence (CommonMark: run>=3 of ` or ~, 0-3 indent, closer same char >= len, blank tail)."""
    inside=set(); fence=None
    for i,line in enumerate(text.split("\n")):
        m=re.match(r"^( {0,3})(`{3,}|~{3,})(.*)$", line)
        if fence is None:
            if m and not (m.group(2)[0]=="`" and "`" in m.group(3)):
                fence=(m.group(2)[0], len(m.group(2))); inside.add(i)
        else:
            inside.add(i)
            if m and m.group(2)[0]==fence[0] and len(m.group(2))>=fence[1] and m.group(3).strip()=="":
                fence=None
    return inside
both=old_only=new_only=0; ex_old=[]; ex_new=[]
files=[p for d in ("h-mad","handoff") for p in pathlib.Path(d).rglob("*.md") if "archive" not in p.parts]
for p in files:
    text=p.read_text(errors="replace"); fenced=fence_lines(text)
    for i,line in enumerate(text.split("\n")):
        o=bool(OLD.match(line)); n=bool(NEW.match(line)) and i not in fenced
        if o and n: both+=1
        elif o and not n: old_only+=1; len(ex_old)<6 and ex_old.append((str(p),i+1,line[:60]))
        elif n and not o: new_only+=1; len(ex_new)<6 and ex_new.append((str(p),i+1,line[:60]))
print(f"files={len(files)} both={both} old_only={old_only} new_only={new_only}")
for t in ex_old: print("OLD-ONLY", *t)
for t in ex_new: print("NEW-ONLY", *t)
