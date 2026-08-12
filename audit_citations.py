"""
audit_citations.py
==================
Builds a checklist for the source read-through: every \\cite in main.tex,
paired with the sentence that cites it. You read each source once and tick
whether the sentence is fair in context.

    python audit_citations.py

Writes citation_audit.md, one block per reference with every sentence that
cites it, and a VERDICT line to fill in with FAIR / OVERSTATED / WRONG.
"""
import re
from collections import defaultdict

tex = open("main.tex", encoding="utf-8").read()

# Strip the bibliography so bibitem lines don't count as citing sentences
body = tex.split("\\begin{thebibliography}")[0]

# Collect the reference list for labels
bib = dict(re.findall(r"\\bibitem\{([^}]+)\}\s*\n(.+?)(?=\n\n)", tex, re.S))

# Split body into sentences, keeping cites attached
flat = re.sub(r"\s+", " ", body)
sentences = re.split(r"(?<=[.!?]) ", flat)

uses = defaultdict(list)
for s in sentences:
    for m in re.finditer(r"\\cite\{([^}]+)\}", s):
        for key in m.group(1).split(","):
            uses[key.strip()].append(s.strip())

out = ["# Citation audit checklist", "",
       "For each reference: open the source, read the sentence(s) below,",
       "and replace the VERDICT line with FAIR, OVERSTATED or WRONG plus a",
       "note. A reference cited only in a positioning table still needs the",
       "table row checked.", ""]
for key in sorted(bib):
    entry = re.sub(r"\s+", " ", bib[key]).strip()
    out.append(f"## {key}")
    out.append(f"*{entry}*")
    out.append("")
    if key in uses:
        for s in uses[key]:
            out.append(f"- cited in: {s}")
    else:
        out.append("- NOT CITED IN THE BODY -- either cite it or remove it")
    out.append("")
    out.append("VERDICT: ____")
    out.append("")

open("citation_audit.md", "w", encoding="utf-8").write("\n".join(out))
print(f"{len(bib)} references, {sum(len(v) for v in uses.values())} citing "
      f"sentences -> citation_audit.md")
uncited = [k for k in bib if k not in uses]
if uncited:
    print("NOT CITED IN BODY:", ", ".join(uncited))
