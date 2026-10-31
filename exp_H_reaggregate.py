"""
exp_H_reaggregate.py
====================
Five questions answered by re-aggregating files already on disk. No new
simulation, no seeds, no runs of the pipeline.

  Q1  The three correlations of Section 8.6 recomputed at CHAIN level, next
      to the instance-level values the paper currently reports. The paper
      says the instance-level p-values overstate precision; this measures by
      how much.
  Q2  Audit of the 47 witness categories for v = 0. Proposition 5 requires
      v != 0, since plans exclude the focal node. Any witness at v = 0 must
      be struck from the count.
  Q3  The K0-scaled advantage H * K0 per instance, with its dispersion, and
      the correlation of H with K0. This says how many focal categories
      perfect knowledge rescues, and whether the small advantage is a
      property of the problem or of the 1/K0 normalisation.
  Q4  Standard errors for every mean in Tables 7, 8 and 9, computed across
      the seeded evaluations within each instance and then across instances.
  Q5  The paired within-instance analysis of the lambda sweep: 144 paired
      observations instead of a six-point Spearman.

PRE-STATED READINGS (written before the run; do not edit afterwards)
--------------------------------------------------------------------
  Q1  Chain-level p-values will be larger than the instance-level ones.
      If any instance-level p below 0.10 rises above 0.30 at chain level,
      the paper's "neither outcome licenses a claim" wording is confirmed
      and should quote the chain-level number.
  Q2  Expected: zero witnesses at v = 0, since focal categories in these
      chains all have a candidate pool of size one. If any appear, the 47
      and the 2.8% in Section 8.3 are both wrong and must be corrected.
  Q3  If H * K0 is roughly constant across chains, the advantage is a real
      property of the decision problem and should be reported in units of
      focal categories. If H * K0 grows with K0, the headline is partly a
      normalisation artefact and the paper must say so.
  Q4  If the standard error of the mean advantage is of the same order as
      the mean itself, Tables 7 to 9 cannot support level comparisons and
      the text must be reduced to the sign and the zeros.
  Q5  A paired test over 144 observations either finds a lambda effect the
      six-point Spearman could not detect, or closes the question with
      power the registered statistic never had.

  python exp_H_reaggregate.py --willems-file data\\chain_data.xlsx

Run from the folder holding the FROZEN result directories.
"""
import argparse
import glob
import os

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr, ttest_rel, wilcoxon

FROZEN = {
    "lam0": "results_willems_FROZEN/results_raw.csv",
    "pilot": "results_pilot_willems_FROZEN/results_raw_willems.csv",
}
DIAG = "results_willems_FROZEN/diagnostics.csv"


def per_instance(path):
    """instance -> mean advantage, and the standard error across seeds."""
    df = pd.read_csv(path, keep_default_na=False)
    df["s"] = df["seed"] % 1000
    piv = df.pivot_table(index=["network", "s"], columns="policy",
                         values="cvar")
    d = piv["None"] - piv["Oracle"]
    g = d.groupby(level="network")
    return g.mean(), g.std() / np.sqrt(g.size()), g.size()


def chain_of(name):
    return name.split("_seed")[0]


def k0_map(willems_file, min_nodes):
    """chain name -> K0, taken as the number of sinks the loader reports."""
    import data_willems as W
    nets = W.load_all_chains(willems_file, min_nodes=min_nodes)
    out = {}
    for net in nets:
        cats = net.suppliers[int(getattr(net, "focal", 0))]
        out[str(getattr(net, "name", "?")).split("_seed")[0]] = len(cats)
    return out


def q1(mean_lam0, mean_pilot):
    print("\n=== Q1  correlations at instance level and chain level ===")
    if not os.path.exists(DIAG):
        print("  diagnostics.csv not found; skipped")
        return
    dg = pd.read_csv(DIAG)
    dg["chain"] = dg["name"].map(chain_of)
    feat = dg.groupby("chain").first()
    for label, m in (("lambda=0", mean_lam0), ("lambda=0.8", mean_pilot)):
        if m is None:
            continue
        inst = pd.DataFrame({"H": m})
        inst["chain"] = [chain_of(i) for i in inst.index]
        j = inst.join(feat, on="chain")
        for col, nice in (("n_chokepoints_tier2plus", "chokepoint census"),
                          ("n_nodes", "network size"),
                          ("max_tier", "tier depth")):
            if col not in j:
                continue
            a = j.dropna(subset=[col])
            r_i, p_i = spearmanr(a["H"], a[col])
            c = a.groupby("chain").agg(H=("H", "mean"), x=(col, "first"))
            r_c, p_c = spearmanr(c["H"], c["x"])
            print(f"  {label:11s} {nice:20s} instance n={len(a):3d} "
                  f"rho={r_i:+.3f} p={p_i:.3f}   chain n={len(c):3d} "
                  f"rho={r_c:+.3f} p={p_c:.3f}")


def q2(willems_file, min_nodes):
    print("\n=== Q2  witness audit for v = 0 ===")
    import data_willems as W
    nets = W.load_all_chains(willems_file, min_nodes=min_nodes)
    at_focal = latent = both = 0
    for net in nets:
        focal = int(getattr(net, "focal", 0))
        cost = np.asarray(net.node_cost, float)
        cons = {}
        for v in range(net.n):
            for _k, cands in (net.suppliers[v] or {}).items():
                for u in cands:
                    cons.setdefault(int(u), set()).add(int(v))
        for v in range(net.n):
            for _k, cands in (net.suppliers[v] or {}).items():
                cands = [int(u) for u in cands]
                if len(cands) < 2:
                    continue
                latent += 1
                sole = all(cons.get(u, set()) == {v} for u in cands)
                cheap = cost[v] <= min(cost[u] for u in cands) + 1e-12
                if sole and cheap:
                    both += 1
                    if v == focal:
                        at_focal += 1
    print(f"  latent categories {latent}, witness holds {both}, "
          f"of which at the focal node {at_focal}")
    print("  " + ("CLEAN: no witness at v = 0" if at_focal == 0 else
                  f"CORRECTION NEEDED: {at_focal} witnesses sit at v = 0 and "
                  "must be removed from the count in Section 8.3"))


def q3_q4(mean_lam0, se_lam0, mean_pilot, se_pilot, k0):
    print("\n=== Q3  K0-scaled advantage ===")
    for label, m in (("lambda=0", mean_lam0), ("lambda=0.8", mean_pilot)):
        if m is None:
            continue
        ch = pd.Series([chain_of(i) for i in m.index], index=m.index)
        kk = ch.map(k0)
        ok = kk.notna()
        if ok.sum() == 0:
            print(f"  {label}: no K0 match"); continue
        scaled = m[ok] * kk[ok]
        r, p = spearmanr(m[ok], kk[ok])
        r2, p2 = spearmanr(scaled, kk[ok])
        print(f"  {label:11s} H*K0 mean={scaled.mean():+.3f} "
              f"median={scaled.median():+.3f} max={scaled.max():+.3f} "
              f"(units: focal categories rescued)")
        print(f"              Spearman(H,K0)={r:+.3f} p={p:.3f}   "
              f"Spearman(H*K0,K0)={r2:+.3f} p={p2:.3f}")

    print("\n=== Q4  standard errors on the reported means ===")
    for label, m, se in (("lambda=0", mean_lam0, se_lam0),
                         ("lambda=0.8", mean_pilot, se_pilot)):
        if m is None:
            continue
        across = m.std() / np.sqrt(len(m))
        print(f"  {label:11s} mean={m.mean():+.5f}  SE across instances="
              f"{across:.5f}  ratio={abs(m.mean())/across:5.2f}")
        print(f"              median within-instance SE={se.median():.5f}")


def q5():
    print("\n=== Q5  paired within-instance analysis of the sweep ===")
    frames = {}
    for d in sorted(glob.glob("results_sweep_lam*")):
        raw = None
        for n in ("results_raw.csv", "results_raw_willems.csv"):
            if os.path.exists(os.path.join(d, n)):
                raw = os.path.join(d, n)
        if raw is None:
            continue
        lam = int(d.split("lam")[-1]) / 100.0
        m, _se, _n = per_instance(raw)
        frames[lam] = m
    if len(frames) < 2:
        print("  fewer than two sweep folders found; skipped")
        return
    lams = sorted(frames)
    common = set(frames[lams[0]].index)
    for l in lams[1:]:
        common &= set(frames[l].index)
    common = sorted(common)
    print(f"  {len(lams)} lambda values, {len(common)} instances in common, "
          f"{len(lams) * len(common)} paired observations")
    base = frames[lams[0]][common]
    for l in lams[1:]:
        d = frames[l][common] - base
        t, pt = ttest_rel(frames[l][common], base)
        try:
            _w, pw = wilcoxon(frames[l][common], base)
        except ValueError:
            pw = float("nan")
        print(f"  lambda={l:.1f} vs {lams[0]:.1f}: mean diff={d.mean():+.5f} "
              f"paired t p={pt:.3f}  Wilcoxon p={pw:.3f}")
    long = pd.DataFrame({l: frames[l][common] for l in lams})
    rows = [(l, i, long.loc[i, l]) for l in lams for i in common]
    df = pd.DataFrame(rows, columns=["lam", "inst", "H"])
    r, p = spearmanr(df["lam"], df["H"])
    print(f"  pooled Spearman(lambda, H) over {len(df)} observations: "
          f"rho={r:+.3f} p={p:.4f}  (not independent; paired tests above "
          f"are the ones to quote)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--willems-file", required=True)
    ap.add_argument("--min-nodes", type=int, default=30)
    a = ap.parse_args()

    mean_lam0 = se_lam0 = mean_pilot = se_pilot = None
    if os.path.exists(FROZEN["lam0"]):
        mean_lam0, se_lam0, _ = per_instance(FROZEN["lam0"])
    if os.path.exists(FROZEN["pilot"]):
        mean_pilot, se_pilot, _ = per_instance(FROZEN["pilot"])

    q1(mean_lam0, mean_pilot)
    q2(a.willems_file, a.min_nodes)
    k0 = k0_map(a.willems_file, a.min_nodes)
    q3_q4(mean_lam0, se_lam0, mean_pilot, se_pilot, k0)
    q5()
    print("\nSend the whole output. Every number above either goes into the "
          "paper or corrects something already in it.")


if __name__ == "__main__":
    main()
