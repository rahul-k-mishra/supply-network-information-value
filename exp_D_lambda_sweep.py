"""
exp_D_lambda_sweep.py
=====================
Runs the dispersion parameter across a grid instead of the two points
(0 and 0.8) the paper currently has, and aggregates the result into the
figure Corollary 2 deserves.

WHY THIS SCRIPT EXISTS
----------------------
Corollary 2 says the identification premium is nondecreasing in lambda.
Two points cannot show a monotone relationship; they can only show that
one point is higher than another.  A grid can.  This is the cheapest
experiment in the whole package and the one that most improves the
paper's empirical section.

TWO MODES
---------
1. DRIVE: calls your existing runner once per lambda value.  The flags in
   RUNNER_CMD were checked against run_experiment.py --help and use
   --overlay-seeds and --seeds-per-net, not --seeds.  The runner also
   requires --willems-file, so pass it here; the script checks the path
   exists before launching anything.  Start with --only to time a single
   lambda before committing to a grid.
2. AGGREGATE: if the per-lambda folders already exist, skip the runs with
   --aggregate-only and just build the table and figure.

  python exp_D_lambda_sweep.py --willems-file <path> --only 0.4   (time one)
  python exp_D_lambda_sweep.py --grid coarse           (6 lambda values)
  python exp_D_lambda_sweep.py --grid fine             (11 lambda values)
  python exp_D_lambda_sweep.py --grid fine --aggregate-only

WHAT COUNTS AS A PASS (state this before you look at the output)
----------------------------------------------------------------
  - Spearman(lambda, summary) >= 0.7 -> Corollary 3 is illustrated on real
    chains; put the curve in the paper
  - non-monotone or flat             -> report the curve anyway and say
    plainly that the monotone prediction is not visible at these budgets;
    that is a finding, not a failure

  WHICH SUMMARY COUNTS, decided before any run: the median is exactly zero
  on most of these chains and will probably be zero at every lambda, so a
  rank correlation on medians would be undefined.  The mean ceiling is the
  registered summary; the fraction above 0.02 is reported alongside it.  The
  median is printed but is not the criterion.

Output: exp_D_lambda_sweep.csv + fig6_lambda_curve.png
"""
import argparse
import os
import subprocess
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import spearmanr

COARSE = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
FINE = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

# Flags verified against run_experiment.py --help on 2026-08-12.
RUNNER_CMD = ("python run_experiment.py --dataset willems --pilot "
              "--willems-file \"{wfile}\" {wmap}"
              "--lam {lam} --chains {chains} --overlay-seeds {overlays} "
              "--seeds-per-net {seeds} --min-nodes 20 --skip-voi "
              "--n-jobs {jobs} --out {out}")


def load_ceilings(path):
    df = pd.read_csv(path, keep_default_na=False)
    df["s"] = df["seed"] % 1000
    piv = df.pivot_table(index=["network", "s"], columns="policy",
                         values="cvar")
    return (piv["None"] - piv["Oracle"]).groupby(level="network").mean()


def find_raw(folder):
    for name in ("results_raw.csv", "results_raw_willems.csv"):
        p = os.path.join(folder, name)
        if os.path.exists(p):
            return p
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chains", default="7,9,11,14,17,18,19,21")
    ap.add_argument("--seeds", type=int, default=8,
                    help="passed to --seeds-per-net")
    ap.add_argument("--overlays", type=int, default=3,
                    help="passed to --overlay-seeds")
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--grid", choices=["coarse", "fine"], default="coarse")
    ap.add_argument("--only", type=float, default=None,
                    help="run a single lambda (use this to time one point "
                         "before committing to the whole grid)")
    ap.add_argument("--willems-file",
                    help="path to the public MSOM workbook; required unless "
                         "--aggregate-only")
    ap.add_argument("--willems-map", default=None,
                    help="optional mapping file, if your pilot used one")
    ap.add_argument("--aggregate-only", action="store_true")
    a = ap.parse_args()

    # Pre-flight: fail in one second rather than once per lambda value.
    if not a.aggregate_only:
        if not a.willems_file:
            sys.exit("--willems-file is required (the runner asks for it). "
                     "Use the same workbook path your pilot run used.")
        if not os.path.exists(a.willems_file):
            sys.exit(f"workbook not found: {a.willems_file}")
        if a.willems_map and not os.path.exists(a.willems_map):
            sys.exit(f"map file not found: {a.willems_map}")

    grid = [a.only] if a.only is not None else (
        COARSE if a.grid == "coarse" else FINE)

    rows = []
    for lam in grid:
        out = f"results_sweep_lam{int(round(lam * 100)):03d}"
        # Resume on the RAW FILE, not the folder: a failed run can leave an
        # empty folder behind, and skipping on folder presence would then
        # silently skip every lambda for ever.
        if not a.aggregate_only and find_raw(out) is None:
            wmap = (f'--willems-map "{a.willems_map}" '
                    if a.willems_map else "")
            cmd = RUNNER_CMD.format(lam=lam, chains=a.chains,
                                    overlays=a.overlays, seeds=a.seeds,
                                    jobs=a.jobs, out=out,
                                    wfile=a.willems_file, wmap=wmap)
            print(f"\n=== lambda={lam} ===\n{cmd}")
            rc = subprocess.call(cmd, shell=True)
            if rc != 0:
                print(f"runner returned {rc} for lambda={lam}; "
                      "check the flag names in RUNNER_CMD", file=sys.stderr)
                continue
        raw = find_raw(out)
        if not raw:
            print(f"[skip] lambda={lam}: no raw csv in {out} even after the "
                  "run -- read the runner output above for the reason")
            continue
        per = load_ceilings(raw)
        rows.append(dict(lam=lam, n=len(per), median=float(per.median()),
                         mean=float(per.mean()),
                         frac_gt02=float((per > 0.02).mean()),
                         mx=float(per.max())))
        print(f"lambda={lam}: n={len(per)} median={per.median():+.5f} "
              f"mean={per.mean():+.5f} frac>0.02={(per > 0.02).mean():.3f}")

    if not rows:
        print("nothing aggregated")
        return
    df = pd.DataFrame(rows).sort_values("lam")
    df.to_csv("exp_D_lambda_sweep.csv", index=False)

    # The median is often exactly zero at every lambda, which makes a rank
    # correlation on medians undefined.  Report all three summaries and let
    # the one with variation carry the statement; this choice is stated in
    # the header before any run, not after seeing the numbers.
    print()
    for col, label in (("median", "median ceiling"),
                       ("mean", "mean ceiling"),
                       ("frac_gt02", "fraction above 0.02")):
        if df[col].nunique() < 2:
            print(f"Spearman(lambda, {label}) = undefined "
                  f"(constant at {df[col].iloc[0]:.5f})")
        else:
            rho, p = spearmanr(df["lam"], df[col])
            print(f"Spearman(lambda, {label}) = {rho:+.3f}  p={p:.4f}")

    fig, ax = plt.subplots(figsize=(5.4, 3.2))
    ax.plot(df["lam"], df["median"], "o-", label="median ceiling")
    ax.plot(df["lam"], df["mean"], "s--", label="mean ceiling")
    ax.plot(df["lam"], df["mx"], "^:", label="maximum")
    ax.axhline(0.02, color="crimson", ls="--", lw=1, label="0.02 reference")
    ax.set_xlabel("dispersion $\\lambda$")
    ax.set_ylabel("EVPI ceiling")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig("fig6_lambda_curve.png", dpi=200)
    print("wrote fig6_lambda_curve.png and exp_D_lambda_sweep.csv")


if __name__ == "__main__":
    main()
