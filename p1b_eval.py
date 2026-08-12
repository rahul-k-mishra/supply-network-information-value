"""P1b verdict: joins IDX (from compute_index.py) with the measured ceiling
(from results_raw.csv). Registered criteria, fixed before this script existed:
  - chain 09 in the TOP 3 chains by mean IDX (aggregated over overlay seeds)
  - Spearman(IDX, ceiling=None-Oracle) > 0 with p < 0.05 over the instances
Usage: python p1b_eval.py --index index_willems.csv --results results_willems/results_raw.csv
"""
import argparse, re
import numpy as np, pandas as pd
from scipy.stats import spearmanr

ap = argparse.ArgumentParser()
ap.add_argument("--index", required=True)
ap.add_argument("--results", required=True)
a = ap.parse_args()

idx = pd.read_csv(a.index)
df = pd.read_csv(a.results, keep_default_na=False)
piv = df.pivot_table(index=["network", "seed"], columns="policy", values="cvar")
pernet = piv.groupby(level="network").mean()
ceil = (pernet["None"] - pernet["Oracle"]).rename("ceiling").reset_index()
m = idx.merge(ceil, on="network")
m["chain"] = [int(re.search(r"chain(\d+)", n).group(1)) for n in m["network"]]

rho, p = spearmanr(m["IDX"], m["ceiling"])
bychain = m.groupby("chain")[["IDX", "ceiling"]].mean().sort_values("IDX", ascending=False)
rank09 = int(np.where(bychain.index == 9)[0][0]) + 1 if 9 in bychain.index else None

print(f"instances joined: {len(m)}")
print(f"Spearman IDX vs ceiling: rho={rho:.3f}  p={p:.5f}")
print(f"chain 09 rank by mean IDX: {rank09} of {len(bychain)}")
print("\ntop 6 chains by IDX:")
print(bychain.head(6).round(5).to_string())
print("\nREGISTERED VERDICT:")
ok1 = rank09 is not None and rank09 <= 3
ok2 = rho > 0 and p < 0.05
print(f"  P1b-1 chain09 top-3:      {'PASS' if ok1 else 'FAIL'}")
print(f"  P1b-2 Spearman>0, p<.05:  {'PASS' if ok2 else 'FAIL'}")
print("  -> " + ("THEORY SURVIVES ITS FIRST REAL-DATA TEST" if ok1 and ok2
      else "THEORY DEFECTIVE ON REAL STRUCTURE -- STOP AND DIAGNOSE, DO NOT WRITE"))
