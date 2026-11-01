"""
remark1_analysis.py
===================
Reproduces the figures quoted in Remark 1 of the paper ("The premium is loose
where the theorem bites"): the tightness ratio EVPI / U on the generic batch
of verify_theorem.py, split by whether the consumer cut is affordable.

  - instances in which EVERY category has an affordable consumer cut
    (c_v <= B for all categories);
  - instances in which NO category has one (c_v > B for all categories).

For each group it prints the number of instances, the mean ratio, and the
fraction of instances with ratio below 0.05. Instances with a zero bound have
no ratio and are excluded (there are none at the default seed).

It replays exactly the instance stream of verify_theorem.py: the same seed,
and the generic batch is drawn first, so the 6000 generic instances are
identical to those behind Table 3 and Figure 1.

  python remark1_analysis.py                 # subsets action set (the paper)
  python remark1_analysis.py --actions legacy

Expected output at the default seed, subsets action set:
  every category has an affordable cut : n=4481  mean 0.102  below 0.05: 0.671
  no category has an affordable cut    : n=474   mean 0.203  below 0.05: 0.405
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify_theorem import gen, solve_instance   # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20260810,
                    help="must equal verify_theorem.py's seed")
    ap.add_argument("--n-generic", type=int, default=6000)
    ap.add_argument("--actions", choices=("subsets", "legacy"),
                    default="subsets")
    a = ap.parse_args()

    rng = np.random.default_rng(a.seed)
    all_cut, no_cut = [], []
    for _ in range(a.n_generic):
        cats, B = gen(rng, "generic")
        evpi, bound = solve_instance(cats, B, a.actions)
        if bound <= 1e-12:
            continue
        ratio = evpi / bound
        affordable = [c["c_v"] <= B + 1e-12 for c in cats]
        if all(affordable):
            all_cut.append(ratio)
        elif not any(affordable):
            no_cut.append(ratio)

    print(f"action algebra: {a.actions}   seed: {a.seed}   "
          f"generic instances: {a.n_generic}")
    for label, r in (("every category has an affordable cut", all_cut),
                     ("no category has an affordable cut   ", no_cut)):
        r = np.asarray(r)
        print(f"{label} : n={len(r)}  mean {r.mean():.3f}  "
              f"below 0.05: {(r < 0.05).mean():.3f}")


if __name__ == "__main__":
    main()
