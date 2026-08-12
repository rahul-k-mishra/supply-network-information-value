"""
exp_B_breakeven.py
==================
Turns the measured EVPI ceilings into a break-even visibility price, and
so answers the one question the paper's "operationally small" language
invites: small compared with WHAT?

THE LOGIC
---------
The loss is the fraction of focal categories starved.  Let V be the annual
economic value at risk when ONE focal category is starved for the exposure
window the disruption model represents.  Then a measured ceiling of E
(dimensionless) is worth E * K0 * V in money, where K0 is the number of
focal categories -- and since our loss is already normalised by K0, the
focal firm's expected saving from perfect structural information is simply
E * V_total, with V_total the value at risk across the whole focal basket.

A firm should buy visibility only if

        price_of_visibility  <  E * V_total.

So for any V_total the break-even price is a straight line in E, and the
distribution of E across instances turns into a distribution of break-even
prices.  This is the managerial output of the paper: not "visibility is
worthless" but "here is the most it can possibly be worth to you".

  python exp_B_breakeven.py --ceilings results_willems_FROZEN/results_raw.csv ^
      --pilot results_pilot_willems_FROZEN/results_raw_willems.csv ^
      --value 100e6

--value is the annual value at risk across the focal basket, in your own
currency.  Use a number your own business case would defend; the script
prints the whole curve so the paper does not depend on any one choice.

Output: console table + fig5_breakeven.png + exp_B_breakeven.csv
"""
import argparse

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def ceilings(path):
    df = pd.read_csv(path, keep_default_na=False)
    df["s"] = df["seed"] % 1000
    piv = df.pivot_table(index=["network", "s"], columns="policy",
                         values="cvar")
    return (piv["None"] - piv["Oracle"]).groupby(level="network").mean()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ceilings", required=True,
                    help="lambda=0 raw results csv")
    ap.add_argument("--pilot", help="lambda=0.8 pilot raw results csv")
    ap.add_argument("--value", type=float, default=100e6,
                    help="annual value at risk across the focal basket")
    a = ap.parse_args()

    rows = []
    series = {"lambda=0": ceilings(a.ceilings)}
    if a.pilot:
        series["lambda=0.8"] = ceilings(a.pilot)

    for name, per in series.items():
        for q in (0.5, 0.75, 0.9, 0.95, 1.0):
            e = float(per.quantile(q))
            rows.append(dict(regime=name, quantile=q, ceiling=e,
                             breakeven_price=e * a.value))
        print(f"\n{name}: n={len(per)}")
        print(f"  median ceiling {per.median():+.5f} -> break-even price "
              f"{per.median() * a.value:,.0f}")
        print(f"  90th pct       {per.quantile(0.9):+.5f} -> "
              f"{per.quantile(0.9) * a.value:,.0f}")
        print(f"  maximum        {per.max():+.5f} -> "
              f"{per.max() * a.value:,.0f}")

    df = pd.DataFrame(rows)
    df.to_csv("exp_B_breakeven.csv", index=False)

    fig, ax = plt.subplots(figsize=(5.4, 3.2))
    grid = np.linspace(0, max(s.max() for s in series.values()) * 1.05, 200)
    for name, per in series.items():
        frac = [(per > g).mean() for g in grid]
        ax.plot(grid * a.value, frac, label=name)
    ax.set_xlabel(f"visibility price (value at risk = {a.value:,.0f})")
    ax.set_ylabel("fraction of chains where\nbuying is justified")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig("fig5_breakeven.png", dpi=200)
    print("\nwrote fig5_breakeven.png and exp_B_breakeven.csv")


if __name__ == "__main__":
    main()
