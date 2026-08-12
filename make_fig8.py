"""Figure 8: how far the measured advantage H sits from the exact EVPI.

Left: pooled distribution of H - EVPI over the five seeds of Experiment F.
Right: the mean discrepancy and the frequency of understatement against the
number of focal categories, which is the trend that matters for
extrapolating to real networks.
"""
import glob
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

df = pd.concat([pd.read_csv(p) for p in sorted(glob.glob("expF_s0*.csv"))],
               ignore_index=True)
df["diff"] = df["H"] - df["evpi"]
tol = 1e-12

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
fig.savefig("fig8_H_vs_evpi.png", dpi=200)
print("wrote fig8_H_vs_evpi.png")
