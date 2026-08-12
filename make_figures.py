"""Regenerate every figure and table in the manuscript from raw result files.
Run on your machine so each number in the paper traces to your own disk.

  python make_figures.py --lam0-willems results_willems_FROZEN/results_raw.csv ^
      --lam0-syn results_scalefree_v2_FROZEN/results_raw.csv ^
      --pilot-willems results_pilot_willems_FROZEN/results_raw_willems.csv ^
      --pilot-syn results_pilot_syn_FROZEN/results_raw.csv

Any file you omit -> its figure/table is skipped with a notice.
CANONICAL SOURCE = the FROZEN folders (SHA-256 hashes recorded in
manuscript Appendix A.3, registered in chat 2026-08-12). The lam0-willems
targets below were re-canonicalized on 2026-08-12 after the 10-Aug raw file
was overwritten in place by an 11-Aug rerun (defect ledger A.2 #8): all
headline stats replicated; instance-level values shifted at epsilon scale.
Pre-stated values the lam0 files MUST reproduce:
  Willems lam0 (96, frozen 11-Aug file, hash 2f9e6883...):
     mean +0.0011, median 0.0000, exact zeros 24/96, >0.01: 3,
     split-half spearman -0.037 / pearson 0.202, >2SE: 6/96, max 0.0212
     [original 10-Aug run, file destroyed: zeros 25, spearman 0.014,
      pearson 0.297 -- kept for the record, no longer reproducible]
  Synthetic lam0 (12): mean +0.0028, >0.01: 3 (nets 03/06/07),
     exact zeros 5, net 05 = -0.052
If your regeneration disagrees with the FROZEN-file targets, STOP:
either the manuscript number is wrong or the frozen evidence was touched
(re-hash and compare against A.3 before anything else).
"""
import argparse
import numpy as np, pandas as pd, re
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import spearmanr, pearsonr

def load(path):
    df = pd.read_csv(path, keep_default_na=False)
    df["s"] = df["seed"] % 1000
    piv = df.pivot_table(index=["network","s"], columns="policy", values="cvar")
    return piv["None"] - piv["Oracle"]

def stats(ceil):
    per = ceil.groupby(level="network").mean()
    ca = ceil[ceil.index.get_level_values("s")%2==0].groupby(level="network").mean()
    cb = ceil[ceil.index.get_level_values("s")%2==1].groupby(level="network").mean()
    rho,p = spearmanr(ca.reindex(per.index), cb.reindex(per.index))
    pr,pp = pearsonr(ca.reindex(per.index), cb.reindex(per.index))
    se = ceil.groupby(level="network").std()/np.sqrt(ceil.groupby(level="network").size())
    return per, dict(n=len(per), mean=per.mean(), median=per.median(),
                     zeros=int((per==0).sum()), gt01=int((per>0.01).sum()),
                     gt02frac=(per>0.02).mean(), mx=per.max(),
                     rel_s=rho, rel_p=pr, sig=int((per.abs()>2*se).sum()))

def fig_hist(per, title, out, thr=None):
    fig,a = plt.subplots(figsize=(5.4,3.0))
    a.hist(per.values, bins=30, color="#7aa6c2", edgecolor="k", linewidth=0.4)
    if thr: a.axvline(thr, color="crimson", ls="--", lw=1)
    a.set_xlabel("EVPI ceiling (None − Oracle CVaR)"); a.set_ylabel("instances")
    a.set_title(title, fontsize=10); fig.tight_layout(); fig.savefig(out, dpi=200)
    print("wrote", out)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    for k in ("lam0-willems","lam0-syn","pilot-willems","pilot-syn"):
        ap.add_argument(f"--{k}")
    ap.add_argument("--per-net", action="store_true",
                    help="also print every per-network mean ceiling, ranked, "
                         "plus split-half p-values -- needed to check the "
                         "per-network claims in manuscript section 7")
    a = ap.parse_args()
    for key, title, out, thr in (
        ("lam0_willems","Fig 1a: λ=0, 96 Willems instances","fig1a_lam0_willems.png",None),
        ("lam0_syn","Fig 1b: λ=0, 12 synthetic n≈977 nets","fig1b_lam0_syn.png",None),
        ("pilot_willems","Fig 2a: λ=0.8 pilot, Willems","fig2a_pilot_willems.png",0.02),
        ("pilot_syn","Fig 2b: λ=0.8 pilot, synthetic","fig2b_pilot_syn.png",0.02)):
        path = getattr(a, key)
        if not path:
            print(f"[skip] --{key.replace('_','-')} not given"); continue
        per, st = stats(load(path))
        print(f"{key}: " + "  ".join(f"{k}={v:.4f}" if isinstance(v,float) else f"{k}={v}"
                                     for k,v in st.items()))
        if a.per_net:
            ceil = load(path)
            ca = ceil[ceil.index.get_level_values("s")%2==0].groupby(level="network").mean()
            cb = ceil[ceil.index.get_level_values("s")%2==1].groupby(level="network").mean()
            cb = cb.reindex(ca.index)
            print(f"  split-half p-values: spearman p={spearmanr(ca,cb)[1]:.4f}"
                  f"  pearson p={pearsonr(ca,cb)[1]:.4f}")
            print("  per-network mean ceiling, ranked (top 8 and bottom 3):")
            r = per.sort_values(ascending=False)
            for name, val in list(r.items())[:8]:
                print(f"    {name:32s} {val:+.5f}")
            print("    ...")
            for name, val in list(r.items())[-3:]:
                print(f"    {name:32s} {val:+.5f}")
        fig_hist(per, title, out, thr)
