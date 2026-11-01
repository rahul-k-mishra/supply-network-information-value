# Slack statistic and Figure 4: analysis

**Date:** 2026-11-01. **Scope:** report only. `main.tex` was not edited, and
the `fig4_tightness.png` in `paperA/` was not replaced.

**Scripts changed:** `paperA/exp_A_idx_vs_evppi.py` and
`paperA/verify_theorem.py`.

**Runs:**
- All runs were in scratch, with `/home/rahul/Research/.venv_aug/bin/python`
  (numpy 1.26.4, scipy 1.11.4, pandas 2.2.3).
- Outputs: a scratch directory outside the project (not archived), one
  folder per run.
- Backups of both scripts as they stood before these changes are in the same
  scratch directory: `exp_A.pre_slack.py` and `verify_theorem.pre_slack.py`.

---

## 1. Script changes

### 1.1 `exp_A_idx_vs_evppi.py`: slack statistics

A new block, `SLACK STATISTICS`, is printed after the tie-snapped Spearman
line. It sits outside the original console block, so that block is unchanged.
P-S1 still fails only on line 6, the Spearman line, exactly as reported in
`TIES_analysis.md`.

The block reports, over all channels, with "EVPPI zero" meaning
|EVPPI| ≤ `--tie-tol` (default 1e-12):

- the count and fraction of channels with EVPPI zero;
- the median and quartiles of **premium / EVPPI**, over channels with
  EVPPI > `--tie-tol` only;
- the median and quartiles of **premium − EVPPI** over all channels. This is
  defined everywhere. It is non-negative because the premium is an upper
  bound;
- the old statistic, the median relative slack with EVPPI clipped at 1e-6,
  labelled `OLD STATISTIC, NOT WELL DEFINED`, with the number of EVPPI-zero
  channels it includes;
- a warning if any channel has EVPPI < −`--tie-tol`. That never happened in
  any run.

The module docstring documents the block. It records that the block was added
on 2026-11-01 and is not part of the registered predictions.

### 1.2 `verify_theorem.py`: Figure 4

- **New option.** `--tie-tol` (default 1e-12) was added.
- **Clamping.** Before plotting, generic-batch ratios with
  |ratio| ≤ `--tie-tol` are set to exactly 0. These are residues of a true
  zero: EVPI is 0 up to about 1e-16, so the ratio is ±1e-14 or smaller.
- **Bins.** The histogram uses explicit edges `linspace(0, 1, 31)`, so 0 is
  the inclusive left edge of the first bin.
- **Console report.** The script prints a line naming the number of generic
  instances, the number with zero bound, the number negative before clamping,
  the number clamped, the number **plotted**, and the number outside [0, 1]
  after clamping. It also prints the size of the zero bin.
- **Title.** The title now states "N of M generic instances plotted". The old
  title printed the number of ratios, not the number plotted. It also takes
  the violation count from the run instead of a hard-coded "0 violations", and
  is split over two lines so it is not clipped.
- **Unchanged.** `verify_tightness.csv` still records raw ratios, and every
  pass/fail check is unchanged.

---

## 2. Results

### 2.1 exp_A: slack statistics, per seed and pooled

The tolerance is 1e-12. "Old ratio" is 1 + the old median relative slack:
the statistic behind the paper's "about 2.7 times".

| Seed | Mode | Channels | EVPPI = 0 | Fraction | EVPPI > 0 | premium/EVPPI Q1 | **median** | Q3 | premium−EVPPI Q1 | **median** | Q3 | Old ratio (not well defined) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| s01 | legacy | 4986 | 1352 | 0.271 | 3634 | 1.307 | **1.851** | 3.225 | 0.01048 | **0.02253** | 0.03907 | 2.692 |
| s02 | legacy | 5012 | 1352 | 0.270 | 3660 | 1.295 | **1.837** | 3.282 | 0.01043 | **0.02182** | 0.03832 | 2.675 |
| s03 | legacy | 5002 | 1360 | 0.272 | 3642 | 1.314 | **1.844** | 3.190 | 0.01068 | **0.02238** | 0.03911 | 2.639 |
| s04 | legacy | 4997 | 1412 | 0.283 | 3585 | 1.291 | **1.834** | 3.249 | 0.01059 | **0.02264** | 0.03857 | 2.836 |
| s05 | legacy | 4984 | 1379 | 0.277 | 3605 | 1.304 | **1.818** | 3.212 | 0.01034 | **0.02298** | 0.03971 | 2.681 |
| **pooled** | legacy | 24981 | 6855 | 0.274 | 18126 | 1.302 | **1.835** | 3.239 | 0.01051 | **0.02246** | 0.03894 | 2.693 |
| s01 | subsets | 4986 | 1287 | 0.258 | 3699 | 1.356 | **1.942** | 3.448 | 0.01103 | **0.02333** | 0.04030 | 2.805 |
| s02 | subsets | 5012 | 1242 | 0.248 | 3770 | 1.384 | **1.945** | 3.547 | 0.01128 | **0.02276** | 0.03977 | 2.740 |
| s03 | subsets | 5002 | 1272 | 0.254 | 3730 | 1.375 | **1.947** | 3.545 | 0.01137 | **0.02320** | 0.03996 | 2.695 |
| s04 | subsets | 4997 | 1298 | 0.260 | 3699 | 1.355 | **1.964** | 3.464 | 0.01123 | **0.02344** | 0.03915 | 2.807 |
| s05 | subsets | 4984 | 1284 | 0.258 | 3700 | 1.371 | **1.933** | 3.521 | 0.01125 | **0.02372** | 0.04111 | 2.765 |
| **pooled** | subsets | 24981 | 6383 | 0.256 | 18598 | 1.368 | **1.944** | 3.501 | 0.01124 | **0.02328** | 0.04001 | 2.758 |

**Checks:**
- No channel had EVPPI < −1e-12, in any run.
- The old-ratio column reproduces the saved `median relative slack` lines
  (+1.692, +1.675, +1.639, +1.836, +1.681) exactly in legacy mode.

**Units.** The premium − EVPPI gap is in objective units (fraction of focal
categories). Both sides carry 1/K₀, as the paper notes.

### 2.2 Why the old statistic is not well defined, and why it lands near 2.7

About a quarter of channels have EVPPI exactly zero but a positive premium:
27.4% under legacy, 25.6% under subsets. The old statistic divides by EVPPI
clipped at 1e-6, so each of these channels gets a ratio of about
premium/1e-6. The median of these clipped ratios is about 3.4×10⁴ and the
smallest is 26, all far above the well-defined interquartile range (upper
quartile 3.2–3.5). The values are fixed by the arbitrary clip, and they put
the whole group in the upper tail.

A median taken with a quarter of the mass pushed into the upper tail lands at
the 69th (legacy) or 67th (subsets) percentile of the well-defined ratios.
That is where 2.7 comes from.

The figure 2.7 is therefore a property of the clip and of the zero fraction,
not of how loose the bound is where there is something to bound. On those
channels the typical ratio is **1.8** (legacy) or **1.9** (subsets).

### 2.3 Spearman, for the same paragraph (from `TIES_analysis.md`, unchanged by this round)

| Mode | Spearman unsnapped, per seed | Spearman snapped (tol 1e-12), per seed | Pooled snapped | Pearson, per seed |
|---|---|---|---|---|
| legacy | 0.5048–0.5162 | 0.5097–0.5205 | 0.5157 | 0.5972–0.6151 |
| subsets | 0.4994–0.5148 | 0.5009–0.5177 | 0.5116 | 0.5733–0.5893 |

### 2.4 verify_theorem.py: Figure 4 and the enumeration checks

| Mode | Generic: violations, mean / max ratio | Thm 4 regime: violations, nonzero-EVPI cases | Dilution regime: violations, mismatches, mean / max ratio | Verdict |
|---|---|---|---|---|
| legacy | 0, 0.143 / 0.985 | 0, 0 | 0, 0, 0.221 / 1.000 | PASS |
| subsets | 0, 0.132 / 0.985 | 0, 0 | 0, 0, 0.212 / 1.000 | PASS |

| Figure 4, generic batch | legacy | subsets |
|---|---|---|
| Generic instances | 6000 | 6000 |
| Zero bound (no ratio) | 0 | 0 |
| Negative before clamping | 119 | 124 |
| Clamped to 0 (\|ratio\| ≤ 1e-12, either sign) | 239 | 247 |
| **Plotted** | **6000** | **6000** |
| Outside [0, 1] after clamping | 0 | 0 |
| Min / max plotted | 0 / 0.984514 | 0 / 0.984514 |
| First bin [0, 1/30) | 3393 | 3437 |
| …of which exactly 0 | 3207 | 3220 |

**Before this fix**, the subsets figure now in `paperA/` plotted 5,876 of
6,000, and the legacy figure 5,881. The 124 or 119 negative residues were
dropped.

**What clamping does not change:**
- The mean and maximum tightness, because residues are smaller than 1e-14.
- Remark 1's fractions (share of instances below 0.05), because a residue
  is below 0.05 whichever side of zero it falls.

The regenerated subsets figure was written to the same scratch directory and
is now `paperA/fig4_tightness.png`.
Its title reads "Bound tightness, 6000 of 6000 generic instances plotted /
(0 with zero bound excluded, 0 violations)".

---

## 3. What the paper must become

### 3.1 The EVPPI paragraph (`main.tex` l.1150–1160)

Current text, l.1154–1160:

> Over five independent seeds and 24,981 channels, $I_k/K_0$ never fell below
> the enumerated $\evppi_k$, and the whole-instance bound was never violated.
> Rank agreement is moderate and stable across seeds (Spearman 0.505 to 0.516;
> Pearson 0.597 to 0.615), with the bound typically about 2.7 times the
> quantity it bounds.

**What is wrong with it:**

1. **"About 2.7 times" is the not-well-defined statistic.** It must go. The
   bound is about 1.8–1.9 times EVPPI on channels where EVPPI is positive, and
   is uninformative on the quarter of channels where EVPPI is zero.
2. **The Spearman range is the tie-broken, platform-dependent statistic.**
   Its 4th decimal is not reproducible (`TIES_analysis.md`).
3. **The numbers come from the legacy action set.** That set is now
   inconsistent with the sentence added earlier to the same section (l.1111),
   which says a plan may secure any nonempty subset of candidates. For
   internal consistency the paragraph should use the subsets numbers. Legacy
   numbers would require qualifying l.1111.

**What it must become (subsets numbers, which are consistent with l.1111 and
Table 4):**

> Over five independent seeds and 24,981 channels, $I_k/K_0$ never fell below
> the enumerated $\evppi_k$, and the whole-instance bound was never violated.
> On 25.6% of channels $\evppi_k$ is zero while the premium is positive, so the
> bound carries no information there. Where $\evppi_k$ is positive, the bound
> is a median 1.94 times it (interquartile range 1.37 to 3.50). Over all
> channels the median gap $I_k/K_0-\evppi_k$ is 0.023 (interquartile range
> 0.011 to 0.040). Rank agreement is moderate and stable across seeds
> (Spearman 0.501 to 0.518, computed with numerically tied values merged;
> Pearson 0.573 to 0.589).

**If the legacy action set is kept instead** (and l.1111 is qualified to
match):
- zero fraction 27.4%;
- ratio median 1.84 (IQR 1.30 to 3.24);
- gap median 0.022 (IQR 0.011 to 0.039);
- Spearman 0.510 to 0.521 with ties merged;
- Pearson 0.597 to 0.615.

**Either way**, the reported Spearman should be the tie-merged statistic, and
the paper or the script header should say how ties are merged (tolerance
1e-12, invariant from 1e-15 to 1e-8).

### 3.2 The Figure 4 caption (`main.tex` l.1145–1146)

Current text:

> Ratio of exact EVPI to the bound of Theorem~\ref{thm:premium} over 6000
> enumerated instances. No value exceeds one.

**What is wrong with it:** as a description of the current figure file, the
caption is false. That figure plots 5,876 instances, because 124 residue
ratios fall below its left edge. Its title likewise says 6000.

**What must change:**

1. **Replace the figure.** `paperA/fig4_tightness.png` must be replaced by the
   regenerated subsets figure, which plots all 6,000. With that figure the
   caption's "6000" is true. "No value exceeds one" is also true: the maximum
   is 0.985.
2. **Disclose the clamping.** The caption should say that ratios are clamped.
   Suggested text:

   > Ratio of exact EVPI to the bound of Theorem~\ref{thm:premium} over 6000
   > enumerated instances; ratios within $10^{-12}$ of zero, floating-point
   > residues of an exact zero, are plotted as zero. No value exceeds one.

3. **Optionally**, the surrounding text ("Most instances lie near zero") can
   be made concrete: 3,437 of 6,000 (57%) fall in the first bin [0, 1/30), and
   3,220 (54%) have EVPI exactly zero.

**Unchanged:** Table 4 (mean 0.132, max 0.985; dilution batch mean 0.212, max
1.000) and Remark 1's figures (0.102 / 67% and 0.203 / 41%).

---

## 4. What was not done

- `main.tex` was not edited.
- `paperA/fig4_tightness.png` was not replaced.
- The root copies of the scripts were not touched.
- P-S1 for exp_A remains failed on the Spearman line alone, for the reason in
  `TIES_analysis.md`. This round does not change that.
