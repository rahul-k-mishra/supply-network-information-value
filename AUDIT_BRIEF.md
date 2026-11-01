# Audit brief — SNIV manuscript, pre-transfer

Target: paper/springer/annals_of_operation_research/asdr_paper_springer/main.tex
and its main.pdf. Evidence: the four *_FROZEN folders (read-only — never
write into them). Scripts: exp_*.py, make_*.py, verify_theorem.py.

## Your role

You are an adversarial referee, not a co-author. The paper has been
desk-handled at three venues with zero referee reports. Assume something is
wrong and find it. "No issues found" in any section is only acceptable with
the evidence that establishes it.

Do NOT edit main.tex or any script in this pass. Report only.

## Output

Write AUDIT_FINDINGS.md. One entry per finding:

  ID | severity (BLOCKER / MAJOR / MINOR) | location (file + line or section)
  what is claimed | what the evidence says | how you checked (exact command
  or file) | proposed fix

BLOCKER = would justify rejection or a correction after publication.
Order by severity. Do not pad with trivia.

## Scope, in priority order

1. NUMBER TRACING. Every numeral in the text, tables and abstract must trace
   to a file in a *_FROZEN folder or a logs/*.txt console capture. List any
   number you cannot trace. Flag any mismatch, however small.

2. UNDIAGNOSED REPRODUCIBILITY DEFECT. make_figures.py reports zeros=9 for
   pilot_willems under numpy 2.5.4 / pandas 3.1.0 and zeros=10 under numpy
   1.26.4 / pandas 2.2.3, from identical input. Find the exact line and
   mechanism. A count of exact zeros must not depend on library version.
   Also confirm whether pilot_syn max 0.0437 vs 0.0438 is only display
   rounding of the exact value 0.04375.

3. MATHEMATICS. Re-derive every proof line by line: Propositions 1, 2, 5, 8,
   9, 11; Theorems 4 and 6 including steps S1-S10; Corollaries 2, 3, 7, 8;
   Conjecture 1. State where each step uses an assumption and whether that
   assumption is stated. Check EVPI, the bound U and the measured advantage H
   are never conflated — H is neither an upper nor a lower bound on EVPI.

4. REFERENCES. All 31. Verify each against a live publisher page: authors,
   title, journal, volume, pages, year. Then read enough of each to confirm
   the sentence citing it is fair in context. Flag any citation used to
   support something the source does not say. Known problems to settle:
   - Ziemba & Butterworth has conflicting volume records
     (Stochastics 1 (1975) 361-378 vs Stochastics IV (1974) 1-18)
   - Claims about convexity requirements in the bound literature are asserted
     for sources that were never read. Verify or withdraw them.
   - Check the Caridi/Cermeno positioning, the Javdani "closest precedent"
     claim, the Strong nested-simulation justification, and the one-line
     characterisations of the Snyder and Wagner surveys.

5. KNOWN OPEN ITEMS. Confirm each is closed in the current PDF or still open:
   - Table 1 stream (C) cell asserts something about unread literature that
     the prose already withdrew
   - A K0 identity stated generally that holds only for multi-sink
     virtual-focal chains (8 of 32), with a vague adjective where a range
     would be defensible
   - (H2) has two witnesses: one needs a cost condition Definition 2 makes
     false, the other is outside the action space. Neither is instantiated.
   - Instance-level p-values where the covariate is chain-level
     (pseudo-replication)

6. REPRODUCIBILITY CLAIMS. requirements.txt omits matplotlib, so no figure
   script runs from a clean clone, and it pins no versions while three
   reported rank statistics depend on scipy 1.11 vs 1.18. Check every
   sentence in the data-availability section against what the repository
   actually does. The repository manifest currently fails on 78 of 106 files
   because of CRLF/LF conversion, and none of the four digests in Appendix A
   match the repository copies.

7. OVERCLAIM AND LANGUAGE. Flag every sentence stronger than its evidence,
   every causal verb where only association was measured, any "state of the
   art" or equivalent, and formulaic or boilerplate phrasing.

## What you must not do

Do not fix anything. Do not soften a finding because it is awkward. Do not
report a section clean without saying how you established it.
