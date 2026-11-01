"""
pool_evppi.py
=============
Pools the per-seed CSV files written by exp_A_idx_vs_evppi.py and prints the
statistics quoted in the paper's comparison with exact EVPPI (Section 6):

  - channels, and channels with premium < EVPPI (must be 0);
  - the fraction of channels whose EVPPI is zero (|EVPPI| <= --tie-tol);
  - median and quartiles of premium / EVPPI over channels with EVPPI > tie-tol;
  - median and quartiles of premium - EVPPI over all channels.

The per-seed Spearman and Pearson ranges are read from each run's console
output and are not recomputed here.

  python pool_evppi.py outputs/exp_A/seed_*/exp_A_idx_vs_evppi.csv

Expected output for the five seeds of the paper, subsets action set:
  channels 24981, premium < EVPPI: 0
  EVPPI zero: 6383 (0.256)
  premium/EVPPI, EVPPI > 0: median 1.944, quartiles [1.368, 3.501]
  premium - EVPPI, all channels: median 0.0233, quartiles [0.0112, 0.0400]
"""
import argparse

import numpy as np
import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", nargs="+")
    ap.add_argument("--tie-tol", type=float, default=1e-12)
    a = ap.parse_args()

    df = pd.concat([pd.read_csv(p) for p in a.csv], ignore_index=True)
    e = df["evppi"].to_numpy()
    p = df["idx"].to_numpy()
    tol = a.tie_tol

    zero = np.abs(e) <= tol
    pos = e > tol
    viol = int((p < e - 1e-9).sum())
    r1, rm, r3 = np.percentile(p[pos] / e[pos], [25, 50, 75])
    d1, dm, d3 = np.percentile(p - e, [25, 50, 75])

    print(f"files: {len(a.csv)}")
    print(f"channels {len(df)}, premium < EVPPI: {viol}")
    print(f"EVPPI zero: {int(zero.sum())} ({zero.mean():.3f})")
    print(f"premium/EVPPI, EVPPI > 0: median {rm:.3f}, "
          f"quartiles [{r1:.3f}, {r3:.3f}]")
    print(f"premium - EVPPI, all channels: median {dm:.4f}, "
          f"quartiles [{d1:.4f}, {d3:.4f}]")


if __name__ == "__main__":
    main()
