"""
exp_I_clustered.py
==================
Computes the seven numbers the manuscript still carries as placeholders.
Re-aggregation only: no simulation, no new runs.

WHAT IS MISSING FROM main.tex
-----------------------------
  [XX] [YY]   ratio of the mean advantage to its standard error, computed
              over the 32 (and 14) CHAIN means rather than over instances.
              The instance-level ratios 2.8 and 2.2 are already in the text
              and are inflated by treating clustered overlays as independent.
  [..] x 6    chain-level rho and p for K0 and for H*K0, at both lambda.
  [RR] [PP]   the chain-level rho and p for H*K0 against K0 at lambda=0.8,
              quoted twice in the prose of Section 8.6.

K0 is constant within a chain, so its instance-level correlation triples the
sample without adding information. Only the chain-level row means anything.

PRE-STATED READING (before the run)
-----------------------------------
  The clustered ratios [XX] [YY] will be smaller than 2.8 and 2.2. If either
  falls below 2, the corresponding mean is not separable from zero once
  clustering is respected, and Section 8.3 must say so rather than claim the
  aggregate is resolved.
  [PP] will be larger than 0.024. If it exceeds 0.05 the paper's current
  wording, that the effect "does not reach significance once the clustering
  is respected", is correct as written. If it stays below 0.05 that sentence
  is wrong and must be rewritten.

  python exp_I_clustered.py

Run from the folder holding the FROZEN result directories and the Willems
workbook path used elsewhere.
"""
import argparse
import os

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

FROZEN = {
    "lambda=0": "results_willems_FROZEN/results_raw.csv",
    "lambda=0.8": "results_pilot_willems_FROZEN/results_raw_willems.csv",
}


def per_instance(path):
    df = pd.read_csv(path, keep_default_na=False)
    df["s"] = df["seed"] % 1000
    piv = df.pivot_table(index=["network", "s"], columns="policy",
                         values="cvar")
    return (piv["None"] - piv["Oracle"]).groupby(level="network").mean()


def chain_of(name):
    return name.split("_seed")[0]


def k0_map(willems_file, min_nodes):
    import data_willems as W
    nets = W.load_all_chains(willems_file, min_nodes=min_nodes)
    out = {}
    for net in nets:
        focal = int(getattr(net, "focal", 0))
        out[chain_of(str(getattr(net, "name", "?")))] = len(net.suppliers[focal])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--willems-file", required=True)
    ap.add_argument("--min-nodes", type=int, default=30)
    a = ap.parse_args()

    k0 = k0_map(a.willems_file, a.min_nodes)

    print("\n=== [XX] [YY]  mean / SE at instance level and at chain level ===")
    for label, path in FROZEN.items():
        if not os.path.exists(path):
            print(f"  {label}: file not found, skipped")
            continue
        inst = per_instance(path)
        ch = inst.groupby([chain_of(i) for i in inst.index]).mean()
        r_i = abs(inst.mean()) / (inst.std() / np.sqrt(len(inst)))
        r_c = abs(ch.mean()) / (ch.std() / np.sqrt(len(ch)))
        print(f"  {label:11s} instances n={len(inst):3d} mean={inst.mean():+.5f} "
              f"SE={inst.std()/np.sqrt(len(inst)):.5f} ratio={r_i:5.2f}")
        print(f"  {'':11s} chains    n={len(ch):3d} mean={ch.mean():+.5f} "
              f"SE={ch.std()/np.sqrt(len(ch)):.5f} ratio={r_c:5.2f}   <-- "
              f"{'[XX]' if label == 'lambda=0' else '[YY]'}")

    print("\n=== [..] and [RR] [PP]  K0 and H*K0 against K0, chain level ===")
    for label, path in FROZEN.items():
        if not os.path.exists(path):
            continue
        inst = per_instance(path)
        ch = inst.groupby([chain_of(i) for i in inst.index]).mean()
        kk = pd.Series({c: k0.get(c, np.nan) for c in ch.index})
        ok = kk.notna()
        if ok.sum() < 3:
            print(f"  {label}: too few chains matched to K0")
            continue
        H, K = ch[ok], kk[ok]
        r1, p1 = spearmanr(H, K)
        r2, p2 = spearmanr(H * K, K)
        print(f"  {label:11s} n={int(ok.sum()):3d} chains")
        print(f"    Spearman(H, K0)      rho={r1:+.3f}  p={p1:.3f}")
        print(f"    Spearman(H*K0, K0)   rho={r2:+.3f}  p={p2:.3f}"
              + ("   <-- [RR] [PP]" if label == "lambda=0.8" else ""))

    print("\nPaste the whole output. The chain-level ratios replace [XX] and "
          "[YY];\nthe four chain-level rho/p pairs fill the [..] cells and "
          "[RR] [PP].")


if __name__ == "__main__":
    main()
