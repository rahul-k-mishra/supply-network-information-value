"""Figure 8: how far the measured advantage H sits from the exact EVPI.

Left: pooled distribution of H - EVPI over the five seeds of Experiment F.
Right: the mean discrepancy and the frequency of understatement against the
number of focal categories, which is the trend that matters for
extrapolating to real networks.

PAPER A CHANGES (2026-11-01). Takes the CSV glob and output path as
arguments, and prints every quantity in the paper's Table of planner gaps
(tab:gaps) and the per-K trend, all with the same tolerance: a quantity is
"zero" if |x| < 1e-12, and H > EVPI means H - EVPI > 1e-12. Spearman is
printed unsnapped and after merging near-ties within --tie-tol, the
statistic the paper reports.

  python make_fig8.py --csv-glob 'runs/expF_s0*_subsets/exp_F_planner_gaps.csv'
"""
import argparse
import glob
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

ap = argparse.ArgumentParser()
ap.add_argument("--csv-glob", default="expF_s0*.csv")
ap.add_argument("--out", default="fig8_H_vs_evpi.png")
ap.add_argument("--tie-tol", type=float, default=1e-12)
args = ap.parse_args()
paths = sorted(glob.glob(args.csv_glob))
assert paths, f"no CSV matches {args.csv_glob!r}"
df = pd.concat([pd.read_csv(p) for p in paths], ignore_index=True)
df["diff"] = df["H"] - df["evpi"]
tol = 1e-12


def snap(x, t):
    x = np.asarray(x, dtype=float)
    out_ = x.copy()
    anchor = None
    for i in np.argsort(x, kind="stable"):
        if anchor is None or x[i] - anchor > t:
            anchor = x[i]
        out_[i] = anchor
    return out_


from scipy.stats import spearmanr
d = df["diff"]
print(f"files                          : {len(paths)}  instances {len(df)}")
print(f"max |residual|                 : {df['residual'].abs().max():.2e}")
print(f"mean EVPI / mean H             : {df['evpi'].mean():.4f} / {df['H'].mean():.4f}")
print(f"mean eps_pi / mean eps_theta   : {df['eps_pi'].mean():.5f} / {df['eps_theta'].mean():.5f}")
print(f"P(eps_pi=0) / P(eps_theta=0)   : {(df['eps_pi'].abs() < tol).mean():.3f} / {(df['eps_theta'].abs() < tol).mean():.3f}")
print(f"P(H=EVPI)                      : {(d.abs() < tol).mean():.3f}")
print(f"P(H>EVPI) / P(H<EVPI)          : {(d > tol).mean():.3f} / {(d < -tol).mean():.3f}")
print(f"P(eps_pi>eps_theta) / reverse  : {((df['eps_pi'] - df['eps_theta']) > tol).mean():.3f} / {((df['eps_theta'] - df['eps_pi']) > tol).mean():.3f}")
print(f"mean H-EVPI                    : {d.mean():+.5f}")
print(f"mean |H-EVPI| / mean EVPI      : {d.abs().mean() / df['evpi'].mean():.3f}")
print(f"5th / 95th pct of H-EVPI       : {d.quantile(0.05):+.4f} / {d.quantile(0.95):+.4f}")
r_raw = spearmanr(df["H"], df["evpi"])[0]
r_snap = spearmanr(snap(df["H"], args.tie_tol), snap(df["evpi"], args.tie_tol))[0]
print(f"Spearman(H,EVPI) unsnapped     : {r_raw:.4f}")
print(f"Spearman(H,EVPI) tie-snapped   : {r_snap:.4f}  (tol {args.tie_tol:g})")
print("by K: n, mean H-EVPI, P(H<EVPI), P(H>EVPI), P(H=EVPI)")
for k, gk in df.groupby("K"):
    dk = gk["diff"]
    print(f"  K={k}: {len(gk):5d}  {dk.mean():+.5f}  {(dk < -tol).mean():.3f}  "
          f"{(dk > tol).mean():.3f}  {(dk.abs() < tol).mean():.3f}")

fig, ax = plt.subplots(1, 2, figsize=(7.6, 2.9))

nz = df.loc[df["diff"].abs() >= tol, "diff"]
ax[0].hist(nz, bins=60, color="#7aa6c2", edgecolor="k", linewidth=0.3)
ax[0].axvline(0, color="k", lw=0.8)
ax[0].set_xlabel("$H-\\mathrm{EVPI}$ (instances where they differ)")
ax[0].set_ylabel("instances")
ax[0].set_title(f"{(df['diff'].abs()<tol).mean():.0%} of instances give "
                "$H=\\mathrm{EVPI}$ exactly", fontsize=8.5)

g = df.groupby("K")
ks = list(g.groups)
md = [g.get_group(k)["diff"].mean() for k in ks]
pl = [(g.get_group(k)["diff"] < -tol).mean() for k in ks]
ax[1].axhline(0, color="grey", lw=0.8, ls=":")
ax[1].plot(ks, md, "o-", color="#e07b39", label="mean $H-\\mathrm{EVPI}$")
ax[1].set_xlabel("focal categories $K$")
ax[1].set_ylabel("mean $H-\\mathrm{EVPI}$")
ax[1].set_xticks(ks)
a2 = ax[1].twinx()
a2.plot(ks, pl, "s--", color="#31688e", label="$P(H<\\mathrm{EVPI})$")
a2.set_ylabel("$P(H<\\mathrm{EVPI})$")
a2.set_ylim(0, 1)
h1, l1 = ax[1].get_legend_handles_labels()
h2, l2 = a2.get_legend_handles_labels()
ax[1].legend(h1 + h2, l1 + l2, fontsize=7.5, loc="center left")
ax[1].set_title("the sign is not stable in $K$", fontsize=8.5)

fig.tight_layout()
fig.savefig(args.out, dpi=200)
print("wrote", args.out)
