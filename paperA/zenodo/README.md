# Code and enumeration results for "The Decision Value of Hidden Supply-Network Structure: Zero-Value Conditions and Identification-Premium Bounds"

Author: Rahul Kumar Mishra (Independent Researcher, Ranchi, India).
Version 1.0.0. Code under the MIT License (see `LICENSE`).

This archive contains everything needed to reproduce every number and the one
figure in the paper. The paper is theoretical. No external data are used.
Every reported number is obtained by exact enumeration of small synthetic
instances drawn from fixed seeds: no sampling happens inside an instance, and
the seeds are used only to draw the instances.

## Contents

```
code/
  verify_theorem.py        enumeration checks of Theorems 4 and 6 and
                           Corollary 7; writes Figure 1 (fig4_tightness.png)
  remark1_analysis.py      the four figures quoted in Remark 1
  exp_A_idx_vs_evppi.py    per-channel premium against exact EVPPI (one seed per run)
  pool_evppi.py            pools the five exp_A seeds into the reported statistics
  exp_E_conjecture1.py     search for counterexamples to Conjecture 12 (one seed per run)
outputs/
  verify/                  console.txt, verify_tightness.csv, fig4_tightness.png
  remark1/                 console.txt
  exp_A/seed_<s>/          console.txt, exp_A_idx_vs_evppi.csv   (five seeds)
  exp_A/pooled.txt         output of pool_evppi.py
  exp_E/seed_<s>/          console.txt, exp_E_conjecture1.csv    (five seeds)
environment.txt            interpreter and library versions used for the outputs
requirements.txt           pinned library versions
run_all.sh                 regenerates outputs/ from code/
SHA256SUMS                 digest of every file in the archive
```

## Where each reported result comes from

| In the paper | Script and output |
|---|---|
| Table 3 (enumeration checks) | `verify_theorem.py`: `outputs/verify/console.txt`, the three lines beginning `[generic]`, `[t1]` and `[c1]` |
| Figure 1 (ratio of EVPI to the bound) | `verify_theorem.py`: `outputs/verify/fig4_tightness.png`; the line beginning `Figure 4:` gives the number plotted |
| Remark 1 | `remark1_analysis.py`: `outputs/remark1/console.txt` |
| Section 6, comparison with exact EVPPI | `exp_A_idx_vs_evppi.py` per seed (Spearman after merging near-ties, Pearson, violations); `pool_evppi.py` for the pooled zero fraction, ratio and gap |
| Section 6, search on Conjecture 12 | `exp_E_conjecture1.py` per seed (violations, minimum slack) |
| Limitation (4), mean ratio 0.132 | `outputs/verify/console.txt`, line `[generic]` |

## Expected values

These are the values computed with the versions in `requirements.txt`:

- **`verify_theorem.py`** (seed 20260810):
  - generic batch: 6000 instances, 0 violations, mean ratio 0.132, max 0.985;
  - Theorem 4 regime: 2000 instances, 0 violations, 0 nonzero-EVPI cases;
  - Corollary 7 regime: 2000 instances, 0 violations, 0 closed-form mismatches, mean ratio 0.212, max 1.000;
  - Figure 1: 6000 of 6000 instances plotted.
- **`remark1_analysis.py`**:
  - every category has an affordable cut: 4481 instances, mean 0.102, 67.1% below 0.05;
  - no category has an affordable cut: 474 instances, mean 0.203, 40.5% below 0.05.
- **`exp_A_idx_vs_evppi.py`** (2000 instances at each of the seeds 20260812, 733, 40427, 991, 20260101):
  - 0 channels with premium below EVPPI;
  - Spearman after merging near-ties 0.501 to 0.518;
  - Pearson 0.573 to 0.589.
- **`pool_evppi.py`** (pooled over the five seeds):
  - 24981 channels;
  - EVPPI zero on 25.6%;
  - premium/EVPPI where EVPPI > 0: median 1.94, interquartile range 1.37 to 3.50;
  - premium − EVPPI over all channels: median 0.023, interquartile range 0.011 to 0.040.
- **`exp_E_conjecture1.py`** (20000 instances at each of the same five seeds):
  - 0 violations;
  - minimum slack zero to machine precision.

## How to run

You need Python 3.12 and the libraries in `requirements.txt`:

```
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
bash run_all.sh            # rewrites outputs/; about 2 to 10 minutes on a laptop
sha256sum -c SHA256SUMS    # compare with the archived digests (see Determinism)
```

To run a single script, call it from the folder where its output files should
go. For example:

```
python code/exp_A_idx_vs_evppi.py --n-instances 2000 --seed 733
```

## Notes on the method

**Action set.** In each category a plan may:
- take no action;
- cut at the consumer;
- secure any nonempty subset of the candidates, at the summed cost.

Every script takes `--actions subsets` (the default, used in the paper) or
`--actions legacy`. The legacy option restricts the plans to one named candidate
or all candidates, and is kept only for comparison with earlier versions.

**Floating-point ties.** Many EVPPI values, and many EVPI and H values, are
mathematically zero but are stored with residue of order 1e-16. Rank statistics
are therefore computed after merging values within `--tie-tol` (default 1e-12)
of each other; the result is the same for any tolerance from 1e-15 to 1e-8. The
unmerged statistic is printed as well. In Figure 1, ratios within 1e-12 of zero
are plotted as zero.

**Registered predictions.** `exp_A_idx_vs_evppi.py` and `exp_E_conjecture1.py`
print, and evaluate, predictions that were registered before their first run.
P-S1 compares legacy mode with console outputs from an earlier archive. Those
outputs are not part of this deposit, so P-S1 reports `NOT EVALUATED` unless
`--reference` is given.

**Determinism.** With the pinned versions, `run_all.sh` reproduces every output
file byte for byte, with one exception. The five `outputs/exp_A/seed_*/console.txt`
files contain two lines (`runtime exact EVPPI`, `runtime IDX`) that report
wall-clock time, so `sha256sum -c` reports those five files as changed. Every
other line of them, and every other file, is identical. With other library
versions, a rank statistic printed without tie merging may differ in its fourth
decimal. The merged statistic, which is the one reported, does not.
