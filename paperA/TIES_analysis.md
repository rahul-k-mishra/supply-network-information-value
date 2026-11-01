# Tie-breaking instability: analysis

**Date:** 2026-11-01. **Scope:** report only. `main.tex` was not edited.

**Runs:**
- All runs were in scratch, with `/home/rahul/Research/.venv_aug/bin/python`
  (numpy 1.26.4, scipy 1.11.4, pandas 2.2.3).
- A supplementary legacy-mode run used the project's other environment,
  `sniv/.venv` (numpy 2.5.4, scipy 1.18.1, pandas 3.1.0). It is labelled
  "new env" below.

**Outputs:** a scratch directory outside the project (not archived), one
folder per seed, mode and environment.

---

## 0. Where the ties come from

The instability sits entirely in the EVPPI series. The premium series has no
tied values at all, raw or snapped.

Seed s01 legacy is representative of all ten runs:

| Quantity | Count |
|---|---|
| Non-degenerate channels | 4,986 |
| …of which EVPPI is mathematically zero | 1,352 (27%) |
| …stored as exactly `0.0` | 956 |
| …stored as `±1.11e-16` | 396 (205 of them negative) |
| Other tie groups (true value positive) | 88 small groups, at most 3 values each |

`scipy.stats.spearmanr` gives exact ties their average rank. But a value of
`-1.1e-16` ranks below `0.0`, which ranks below `+1.1e-16`. So about a quarter
of the EVPPI ranks are decided by floating-point residue, not by the
quantity itself.

That residue depends on the order of arithmetic and on the build of the
libraries. The saved outputs `expA_s0*.txt` and `expE_s0*.txt` have Windows
(CRLF) line endings. The usage line in `make_figures.py` uses the `^`
continuation of the Windows command prompt. Both suggest the saved runs were
made on a different platform. That fits the observed gap, but I have not
verified it.

---

## 1. Change made

I added `--tie-tol` (default `1e-12`) to `paperA/exp_A_idx_vs_evppi.py`.

**What it does:**
- It applies only to Spearman.
- Before Spearman, the EVPPI and premium series are each snapped separately.
- Values are sorted. Every value within `tie-tol` of its group's *smallest*
  member is replaced by that member.
- Groups are anchored at their smallest member, so a group can never span
  more than the tolerance.

**What the console shows:**
- The original console line `Spearman r=...` still prints the unsnapped
  value, so the saved outputs remain comparable line for line.
- A separate line prints the snapped value, the difference, the number of
  tie groups before and after snapping, and the largest shift applied.
- The largest shift on every run was `≤ 2.22e-16`.

**How the predictions are evaluated:**
- P-S1 is now evaluated twice:
  - with the registered (unsnapped) statistic;
  - with the snapped Spearman substituted into the Spearman line.
- P-S3 is likewise reported with both values.
- The docstring documents the option. It states that the option was added
  after the first runs of the registered predictions and is not part of the
  registration.

**Sanity checks on the snapping:**

| Check | Result |
|---|---|
| Unit test | `0.1+1e-15` and `0.1+5e-13` → `0.1`; `0.1+2e-12` stays separate |
| Smallest gap between distinct snapped values, all runs | `4.5e-10` |

So no two genuinely different values are merged. The default tolerance sits
more than three orders of magnitude above the largest residue (3.7e-16) and
more than two below the smallest real gap.

---

## 2. Results

### Table A. Spearman (premium vs EVPPI), unsnapped and snapped at tol = 1e-12

| Seed | Saved output | Legacy unsnapped | Legacy snapped | Legacy unsnapped, new env | Legacy snapped, new env | Subsets unsnapped | Subsets snapped |
|---|---|---|---|---|---|---|---|
| s01 (20260812) | 0.5125 | 0.5127 | **0.5142** | 0.5127 | 0.5142 | 0.4994 | **0.5009** |
| s02 (733) | 0.5158 | 0.5162 | **0.5200** | 0.5162 | 0.5200 | 0.5148 | **0.5177** |
| s03 (40427) | 0.5155 | 0.5151 | **0.5205** | 0.5151 | 0.5205 | 0.5106 | **0.5142** |
| s04 (991) | 0.5136 | 0.5139 | **0.5144** | 0.5139 | 0.5144 | 0.5147 | **0.5150** |
| s05 (20260101) | 0.5051 | 0.5048 | **0.5097** | 0.5048 | 0.5097 | 0.5063 | **0.5103** |
| **Pooled** (24,978 channels) | — | 0.5125 | **0.5157** | — | — | 0.5091 | **0.5116** |
| Range over seeds | 0.5051–0.5158 | 0.5048–0.5162 | 0.5097–0.5205 | | | 0.4994–0.5148 | 0.5009–0.5177 |

The snapped value is always higher than the unsnapped one:

| Mode | Snapped − unsnapped, per seed | Pooled |
|---|---|---|
| Legacy | +0.0015, +0.0037, +0.0055, +0.0004, +0.0048 | +0.0032 |
| Subsets | +0.0014, +0.0028, +0.0036, +0.0004, +0.0040 | +0.0025 |

The reason: residue scatters the mathematically tied EVPPI zeros across
adjacent ranks at random, which weakens the measured association.

### Table B. Is the snapped statistic stable?

**Perturbation test.** I added 50 independent draws of relative noise
uniform on ±4e-16 to both series. That is the scale of the residue. Then I
recomputed both statistics each time.

| Seed / mode | Unsnapped: range over 50 draws | Spread | Snapped: range over 50 draws | Spread |
|---|---|---|---|---|
| s01 legacy | 0.5126 – 0.5128 | 0.0002 | 0.514236 – 0.514236 | 0 |
| s02 legacy | 0.5161 – 0.5163 | 0.0002 | 0.519951 – 0.519951 | 0 |
| s03 legacy | 0.5150 – 0.5152 | 0.0002 | 0.520539 – 0.520539 | 0 |
| s04 legacy | 0.5138 – 0.5140 | 0.0002 | 0.514361 – 0.514361 | 0 |
| s05 legacy | 0.5048 – 0.5049 | 0.0002 | 0.509676 – 0.509676 | 0 |
| s01 subsets | 0.4994 – 0.4995 | 0.0001 | 0.500873 – 0.500873 | 0 |
| s02 subsets | 0.5147 – 0.5149 | 0.0002 | 0.517665 – 0.517665 | 0 |
| s03 subsets | 0.5105 – 0.5107 | 0.0001 | 0.514225 – 0.514225 | 0 |
| s04 subsets | 0.5146 – 0.5147 | 0.0001 | 0.515022 – 0.515022 | 0 |
| s05 subsets | 0.5061 – 0.5063 | 0.0002 | 0.510251 – 0.510251 | 0 |

**Tolerance sweep.** The snapped value is identical at the 4th decimal for
every tolerance from `1e-15` to `1e-8`, on all ten seed/mode pairs. A
tolerance of 0 (exact ties only) gives back the unsnapped value. The choice of
`1e-12` is therefore immaterial anywhere inside that window.

---

## 3. Verdicts

### Is the snapped Spearman stable?

**Yes.** It is a function of the mathematical values, not of the residue:
- Residue-scale noise moves it by exactly 0, against 0.0001–0.0002 for the
  unsnapped value.
- It is invariant to the tolerance across seven orders of magnitude.
- It is identical in both environments (numpy 1.26 / scipy 1.11 and numpy 2.5
  / scipy 1.18).

**Across modes.** Legacy and subsets give different snapped values because
they are different experiments, with different action sets. The difference
(subsets − legacy) is:

| Seed | Snapped difference | Unsnapped difference |
|---|---|---|
| s01 | −0.0133 | −0.0133 |
| s02 | −0.0023 | −0.0014 |
| s03 | −0.0063 | −0.0045 |
| s04 | +0.0006 | +0.0008 |
| s05 | +0.0006 | +0.0015 |
| Pooled | −0.0041 | −0.0034 |

That difference is now a real effect of the action set, not partly residue.
Both modes stay in a narrow band:
- legacy snapped: 0.510–0.521;
- subsets snapped: 0.501–0.518.

### Does the snapped statistic reproduce the saved outputs?

**No.** Snapped minus saved, per seed:

| Seed | s01 | s02 | s03 | s04 | s05 |
|---|---|---|---|---|---|
| Snapped − saved | +0.0017 | +0.0042 | +0.0050 | +0.0008 | +0.0046 |

That is larger than the unsnapped gap of 0.0002–0.0004. The saved values are
themselves one arbitrary resolution of the same ties: whatever residue pattern
the original platform produced. A tie-correct statistic cannot reproduce a
tie-broken one.

**So P-S1 does not pass under the corrected statistic either.** The script
reports `P-S1 with the tie-snapped Spearman substituted: FAIL` on all five
seeds, in both environments.

**What does hold:** the gate's underlying concern, that the switch changed
the instance stream, is answered separately by three pieces of evidence:
1. Every other console line matches the saved outputs exactly: channels,
   both violation counts, non-degenerate count, Pearson, MAE and median
   relative slack.
2. The unmodified root script and the paperA legacy mode produce identical
   output on all five seeds.
3. Both environments agree with each other to the 4th decimal.

As registered, P-S1 fails for exp_A, and it cannot be made to pass, because
the saved Spearman values cannot be regenerated on this machine by any
statistic.

**Options for exp_A** (you decide):
- record P-S1 for exp_A as failed for that cause, with the evidence above; or
- re-baseline with the snapped statistic and archive new console outputs.

P-S1 passes for exp_E as before.

---

## 4. Where rank statistics and exact-zero tests meet floating-point values

### Residue scale in these outputs

| Quantity | Value |
|---|---|
| Largest residue on a mathematically zero quantity, across all CSVs | `3.7e-16` |
| Exception: `verify_theorem.py` generic ratios | down to `−1.04e-14`, because a residue numerator is divided by a small bound |

Smallest genuinely nonzero magnitudes:

| Quantity | Smallest real value |
|---|---|
| exp_A EVPPI | `3.2e-7` |
| exp_A premium − EVPPI | `4.8e-7` |
| exp_E EVPI | `6.1e-8` |
| `verify_theorem.py` EVPI | `2.2e-6` |
| `verify_theorem.py` bound − EVPI | `4.3e-4` |

Each of the few values in the band `(1e-14, 1e-6)` was inspected
individually. All are real small values: 3 to 4 EVPPI values, 1 premium−EVPPI
gap and 1 exp_E EVPI, all ≥ `6.1e-8`. None is residue.

So any threshold between about `1e-13` and `1e-8` cleanly separates zero
from nonzero. Every tolerance used in these scripts (`1e-12`, `1e-9`) lies in
that window.

### Inventory

"Exposed" means the result can change with floating-point residue alone.

**`paperA/exp_A_idx_vs_evppi.py`**

| Line | What | Applied to | Exposed? |
|---|---|---|---|
| 319 | `spearmanr(nz["idx"], nz["evppi"])` | EVPPI, 27% mathematically zero with ± residue | **YES.** Moves the 4th decimal. This is the line behind the P-S1 failure and the paper's "Spearman 0.505 to 0.516". |
| 322 | `spearmanr` on tie-snapped series | same | No. Invariant to residue (Table B). |
| 304 | violation `idx < evppi − 1e-9` | premium − EVPPI | No. Residue ≤ 1.1e-16; smallest real gap 4.8e-7. |
| 306 | instance violation `bound_total < evpi_total − 1e-9` | totals | No. Same margins. |
| 315 | non-degenerate filter `(evppi > 1e-9) \| (idx > 1e-9)` | EVPPI, premium | No. Smallest real EVPPI 3.2e-7, smallest real premium 7.3e-6. |
| 328–330 | median of `(idx − evppi)/evppi.clip(lower=1e-6)` | relative slack | **Not to residue** (the clip maps 0 and ±1.1e-16 alike to 1e-6). **But see the zero-handling problem below.** |
| 231 | `w.sum() <= 0` | prior weights from a Dirichlet draw | No. Positive by construction. |
| 212, 250, 256 | budget feasibility `cost <= B + 1e-12` | costs rounded to 2 dp | No. |

**Zero-handling problem in the median relative slack (not residue).** The
27% of channels whose EVPPI is zero (25.5% under subsets) enter the median
with a relative slack of about `idx / 1e-6`. That is an arbitrary huge number
fixed by the clip, so these channels are pushed into the upper tail.

| Mode | Median, all non-degenerate channels | Median, channels with EVPPI > 1e-9 only |
|---|---|---|
| Legacy, pooled | +1.693 (the bound is about 2.7× EVPPI) | +0.835 (about 1.8×) |
| Subsets, pooled | +1.758 | +0.944 |

The paper's "the bound typically about 2.7 times the quantity it bounds"
comes from the first column. It is a property of how zero-EVPPI channels are
handled, not of the bound's typical slack where there is something to bound.
This is unaffected by snapping. I flag it because it bears on a sentence in
the paper.

**`paperA/exp_E_conjecture1.py`**

No rank statistic.

| Line | What | Exposed? |
|---|---|---|
| 257 | violation `slack < −1e-9` | No. Residue ≤ 8.3e-17; smallest real slack 8.5e-6. |
| 252, 262, 278 | `bound > 1e-12` (ratio and diagnostic) | No. Smallest real bound 1.1e-4. |
| 261 | `min slack` printed `%+.6f` | No for the decision. The printed "−0.000000" is residue (−5.6e-17 to −8.3e-17) rounded for display. |
| 301 | P-S5 `abs(min_slack) <= 1e-9` | No. |
| 175, 202, 207 | budget feasibility `<= B + 1e-12` | No. |

The exp_E mean and max ratio (0.337 / 1.000) are means and maxima, not
ranks. Residue changes them below the printed precision.

**`paperA/verify_theorem.py`**

No rank statistic.

| Line | What | Exposed? |
|---|---|---|
| 192 | violation `evpi > bound + 1e-9` | No. |
| 196 | Theorem 4 regime "nonzero EVPI" `evpi > 1e-9` | No. Residue ≤ 3.7e-16. |
| 198 | dilution closed form `abs(bound − closed) > 1e-9` | No. |
| 164 | closed-form branch `cu < cv − 1e-12` vs solver `<= b + 1e-12` | No. Costs are continuous draws, so a coincidence within 1e-12 has probability ≈ 0. |
| 127–128 | `.min()` over action values | No. A minimum's value does not depend on which tied action attains it. |
| 200 | `ratio = evpi / bound if bound > 1e-12` | Not in the decision. Feeds the next row. |
| 226–227 | **Figure 4 histogram, `range=(0, 1)`** | **YES, mildly.** See below. |

**The Figure 4 exposure.** In the generic batch, 124 of 6,000 ratios (119
under legacy) are tiny negative residues, with true value 0 and minimum
−1.04e-14. `np.histogram` with `range=(0,1)` silently drops them. So the
current Figure 4 shows 5,876 instances, while its title says "6000 generic
instances (0 with zero bound excluded)". The zero bar is undercounted by 124
(about 4% of that bar).

The dilution batch has 40 ratios equal to `1.000000000000003` and 41 tiny
negatives. They do not enter Figure 4. The printed "max 1.000" and the
violation test are unaffected, but any exact `ratio <= 1` check would see 40
"exceedances" of 3e-15.

**`make_figures.py`** (project root, not in `paperA/`; Section 8 material)

| Line | What | Applied to | Exposed? |
|---|---|---|---|
| 43 | split-half `spearmanr(ca, cb)` | per-network mean H in each half | **YES.** On the frozen Willems file, 30 and 31 of the 96 half-means are exactly zero, and 2 networks carry 1e-17 residue instead of 0. Raw ρ = −0.0365; with \|x\| < 1e-12 set to 0, ρ = −0.0407. The header's own record of a rerun moving this from 0.014 to −0.037, "instance-level values shifted at epsilon scale", is this effect, though other changes may have contributed. |
| 48 | `zeros = int((per == 0).sum())` | per-network mean H | **YES.** Frozen Willems: `== 0` gives 24/96; within 1e-12 gives 26/96. The 2 extra networks are mathematically zero (\|H\| ≈ 1e-17). The header's record of 25 zeros in the overwritten 10-Aug run fits this. The synthetic file is unaffected (5 either way, smallest nonzero 1.3e-3). |
| 46 | `median=per.median()` | per-network mean H | No in practice. The median is 0 or residue-sized either way. |
| 84 | split-half Spearman p-value (`--per-net`) | same as line 43 | YES, same cause. |

**Text in `paperA/main.tex` that rests on exposed computations** (not
edited):
- l.1351, "a quarter of the instances give exactly zero": counts `== 0`. It
  is 26/96, not 24/96, with a tolerance. Section 8 material.
- The split-half reliability statements built on `make_figures.py` line 43.
  Section 8 material.
- The EVPPI paragraph in the verification section, "Spearman 0.505 to 0.516"
  and "typically about 2.7 times". The first uses the exposed exp_A line 319.
  The second uses the zero-handling issue above.
- The Figure 4 caption, "over 6000 enumerated instances. No value exceeds
  one." 124 of the 6,000 are not plotted. "No value exceeds one" is true for
  the generic batch the figure shows (max 0.985).
- l.67 and l.339, "median of exactly zero" for H and H·K₀: a median, so not
  materially exposed.

**Other root scripts that compute rank statistics** (outside `paperA/`, not
examined here): `exp_F_planner_gaps.py`, `exp_H_reaggregate.py`,
`run_experiment.py`, `exp_D_lambda_sweep.py`, `p1b_eval.py`,
`exp_I_clustered.py`, `exp_J_theta_oracle.py`, `stats.py`. Audit findings
F-04, F-06 and F-11 (environment-dependent Table 9 ρ and p-values) may share
this cause. That is untested.

---

## 5. Summary

1. **The cause:** the instability comes from roughly 27% of EVPPI values
   that are mathematically zero but stored as 0 or ±1.1e-16.
2. **The fix works:** snapping at any tolerance from 1e-15 to 1e-8 removes
   it completely. Spread under residue-scale noise is 0, and both
   environments agree.
3. **Snapped values:**
   - legacy: 0.510–0.521 per seed, 0.516 pooled;
   - subsets: 0.501–0.518 per seed, 0.512 pooled.
4. **P-S1:** the snapped statistic does not reproduce the saved outputs, and
   cannot: they are a different, tie-broken resolution. P-S1 for exp_A
   therefore fails under both the registered and the corrected statistic.
   The instance stream is shown unchanged by independent evidence (§3).
5. **Other exposures:**
   - Figure 4's histogram silently drops 124 residue-negative ratios.
   - `make_figures.py`'s exact-zero count and split-half Spearman are
     exposed: 24 against 26 zeros on the frozen file.
   - The "about 2.7 times" in the EVPPI paragraph is driven by how zero-EVPPI
     channels enter the median, not by residue: about 1.8× where EVPPI > 0.
6. **Not exposed:** every violation test, threshold and minimum in
   `verify_theorem.py`, `exp_E_conjecture1.py` and `exp_A_idx_vs_evppi.py`.
   The margins span about 8 orders of magnitude.
