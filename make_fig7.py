"""Figure 7: the premium bound and the measured planner advantage, on one axis.

Top panel is Proposition 8's closed formula for the identification premium
under the two-point construction, at illustrative parameters stated in the
caption.  Bottom panel is the measured heuristic oracle advantage from the
fixed-instance-set sweep (exp_D_lambda_sweep.csv).  The point of the figure
is the threshold: the premium is constant until the dispersion term overtakes
the dilution term, and only rises after that.
"""
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

qbar, m, delta = 0.30, 3, 0.30
dil = qbar * (1 - 1 / m)
lam = np.linspace(0, 1, 400)
prem = 0.5 * np.maximum(lam * delta, dil) + 0.5 * dil
thr = dil / delta

df = pd.read_csv("exp_D_lambda_sweep.csv").sort_values("lam")

fig, ax = plt.subplots(2, 1, figsize=(5.6, 4.4), sharex=True)
ax[0].plot(lam, prem, color="#31688e", lw=1.8)
ax[0].axvline(thr, color="grey", ls=":", lw=1)
ax[0].annotate("dilution term dominates", (0.03, dil + 0.008), fontsize=7.5)
ax[0].annotate("dispersion term\ndominates", (thr + 0.03, dil + 0.008),
               fontsize=7.5)
ax[0].set_ylabel("premium $I_k(\\lambda)$")
ax[0].set_title("Identification premium, two-point construction "
                "($\\bar q=0.30$, $m=3$, $\\delta=0.30$)", fontsize=9)

ax[1].plot(df["lam"], df["mean"], "o-", color="#e07b39", lw=1.6,
           label="mean")
ax[1].plot(df["lam"], df["mx"], "^:", color="#7a7a7a", lw=1.2, label="max")
ax[1].set_xlabel("dispersion $\\lambda$")
ax[1].set_ylabel("planner advantage $H$")
ax[1].set_title("Measured heuristic oracle advantage, 24 fixed instances",
                fontsize=9)
ax[1].legend(fontsize=7.5)
for a in ax:
    a.grid(alpha=0.25, lw=0.5)
fig.tight_layout()
fig.savefig("fig7_premium_vs_measured.png", dpi=200)
print("threshold lambda =", round(thr, 3))
