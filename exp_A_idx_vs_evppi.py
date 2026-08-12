"""
exp_A_idx_vs_evppi.py
=====================
Benchmarks the identification-premium index (IDX) against EXACT EVPPI,
computed by brute-force enumeration on miniature instances of the
disjoint-category setting of Theorem 2a.

WHY THIS SCRIPT EXISTS
----------------------
The paper calls IDX "a cheap surrogate for EVPPI".  That sentence is not
allowed to stand on assertion.  This script measures three things that a
referee will ask for:

  (1) Conservativeness.  Is IDX_k >= EVPPI_k on every instance?  The theory
      says IDX is an UPPER BOUND, not an estimate, so a single case with
      IDX_k < EVPPI_k falsifies the claim as stated.
  (2) Agreement.  Pearson and Spearman correlation between IDX_k and
      EVPPI_k, plus mean absolute and mean relative error.
  (3) Cost.  Runtime of IDX versus runtime of exact EVPPI.

WHAT COUNTS AS A PASS (state this before you look at the output)
----------------------------------------------------------------
  - violations == 0                      -> the bound claim survives
  - Spearman >= 0.7 and Pearson >= 0.7   -> "surrogate" is a fair word
  - Spearman in [0.3, 0.7)               -> call it "a conservative bound
                                            with moderate rank agreement"
  - Spearman < 0.3                       -> DELETE the word "surrogate"
                                            from the paper; it is a bound
                                            and nothing more

Nothing here reads your result folders; it builds its own instances, so it
runs anywhere with numpy + scipy.

  python exp_A_idx_vs_evppi.py --n-instances 400 --seed 20260812
  python exp_A_idx_vs_evppi.py --n-instances 400 --seed 7   (any seed)

Output: console table + exp_A_idx_vs_evppi.csv (one row per channel).
"""
import argparse
import itertools
import time

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr


# ----------------------------------------------------------------------
# Instance generation.  One instance = K independent focal categories,
# each fed by one latent channel with m candidates, exactly one of which
# is the true supplier.
# ----------------------------------------------------------------------
def make_instance(rng):
    K = int(rng.integers(2, 4))               # 2 or 3 focal categories
    cats = []
    for _ in range(K):
        m = int(rng.integers(2, 4))           # 2 or 3 candidates
        q = np.round(rng.uniform(0.05, 0.60, size=m), 3)   # candidate risks
        c = np.round(rng.uniform(0.5, 2.0, size=m), 2)     # securing costs
        cv = round(float(rng.uniform(1.0, 4.0)), 2)        # consumer-cut cost
        prior = rng.dirichlet(np.ones(m) * float(rng.choice([1.0, 4.0])))
        cats.append(dict(m=m, q=q, c=c, cv=cv, prior=prior))
    B = round(float(rng.uniform(1.0, 5.0)), 2)             # total budget
    return dict(K=K, cats=cats, B=B)


def actions(cat):
    """Every action available for one category: (label, cost, risk_fn).

    risk_fn(theta) is the resulting starvation probability of that category
    when the true supplier is candidate `theta`.
    """
    m, q, c, cv = cat["m"], cat["q"], cat["c"], cat["cv"]
    out = [("none", 0.0, lambda th, q=q: float(q[th]))]
    for i in range(m):
        out.append((f"cand{i}", float(c[i]),
                    lambda th, i=i, q=q: 0.0 if th == i else float(q[th])))
    out.append(("consumer", cv, lambda th: 0.0))
    out.append(("all", float(c.sum()), lambda th: 0.0))
    return out


# ----------------------------------------------------------------------
# Exact quantities by enumeration.  No sampling, no approximation.
# ----------------------------------------------------------------------
def exact_quantities(inst):
    K, cats, B = inst["K"], inst["cats"], inst["B"]
    acts = [actions(c) for c in cats]
    thetas = list(itertools.product(*[range(c["m"]) for c in cats]))
    pri = np.array([np.prod([cats[k]["prior"][t[k]] for k in range(K)])
                    for t in thetas])

    plans = [p for p in itertools.product(*acts)
             if sum(a[1] for a in p) <= B + 1e-12]

    # j(plan, theta) = mean starvation probability over categories
    J = np.empty((len(plans), len(thetas)))
    for pi, plan in enumerate(plans):
        for ti, th in enumerate(thetas):
            J[pi, ti] = sum(plan[k][2](th[k]) for k in range(K)) / K

    prior_val = float((J @ pri).min())                 # A  = min_S E_theta j
    full_val = float((J.min(axis=0) * pri).sum())      # EM = E_theta min_S j
    evpi = prior_val - full_val

    # EVPPI for channel k: learn theta_k only, everything else stays prior
    evppi = []
    for k in range(K):
        tot = 0.0
        for tk in range(cats[k]["m"]):
            mask = np.array([t[k] == tk for t in thetas])
            w = pri[mask]
            if w.sum() <= 0:
                continue
            cond = w / w.sum()
            tot += w.sum() * float((J[:, mask] @ cond).min())
        evppi.append(prior_val - tot)
    return evpi, np.array(evppi), prior_val, full_val


def index_premiums(inst):
    """IDX_k = I_k / K, with I_k the Theorem 2a identification premium.

    Uses only prior-available information: candidate risk population,
    costs, prior weights.  It never looks at the realised theta except
    through the prior expectation, exactly as the paper claims.
    """
    K, cats, B = inst["K"], inst["cats"], inst["B"]
    idx = []
    for cat in cats:
        acts = actions(cat)
        breaks = sorted({a[1] for a in acts if a[1] <= B + 1e-12})
        prior = cat["prior"]
        prem = 0.0
        for th in range(cat["m"]):
            best = 0.0
            for b in breaks:
                feas = [a for a in acts if a[1] <= b + 1e-12]
                v_inv = min(sum(prior[t] * a[2](t) for t in range(cat["m"]))
                            for a in feas)
                v_full = min(a[2](th) for a in feas)
                best = max(best, v_inv - v_full)
            prem += prior[th] * best
        idx.append(prem / K)
    return np.array(idx)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-instances", type=int, default=400)
    ap.add_argument("--seed", type=int, default=20260812)
    a = ap.parse_args()

    rng = np.random.default_rng(a.seed)
    rows = []
    t_idx = t_exact = 0.0

    for n in range(a.n_instances):
        inst = make_instance(rng)

        t0 = time.perf_counter()
        evpi, evppi, prior_val, full_val = exact_quantities(inst)
        t_exact += time.perf_counter() - t0

        t0 = time.perf_counter()
        idx = index_premiums(inst)
        t_idx += time.perf_counter() - t0

        for k in range(inst["K"]):
            rows.append(dict(instance=n, channel=k, K=inst["K"],
                             m=inst["cats"][k]["m"], budget=inst["B"],
                             evppi=evppi[k], idx=idx[k],
                             evpi_total=evpi, bound_total=idx.sum()))

    df = pd.DataFrame(rows)
    df["violation"] = df["idx"] < df["evppi"] - 1e-9
    tot = df.groupby("instance").first()
    tot_viol = int((tot["bound_total"] < tot["evpi_total"] - 1e-9).sum())

    print(f"instances                : {a.n_instances}  (seed {a.seed})")
    print(f"channels                 : {len(df)}")
    print(f"per-channel violations   : {int(df['violation'].sum())}"
          "   (IDX_k < EVPPI_k; must be 0)")
    print(f"whole-instance violations: {tot_viol}"
          "   (sum IDX < EVPI; must be 0)")

    nz = df[(df["evppi"] > 1e-9) | (df["idx"] > 1e-9)]
    if len(nz) > 2:
        pr, pp = pearsonr(nz["idx"], nz["evppi"])
        sr, sp = spearmanr(nz["idx"], nz["evppi"])
        mae = float((nz["idx"] - nz["evppi"]).abs().mean())
        rel = float(((nz["idx"] - nz["evppi"]) /
                     nz["evppi"].clip(lower=1e-6)).median())
        print(f"non-degenerate channels  : {len(nz)}")
        print(f"Pearson  r={pr:+.4f}  p={pp:.2e}")
        print(f"Spearman r={sr:+.4f}  p={sp:.2e}")
        print(f"MAE                      : {mae:.5f}")
        print(f"median relative slack    : {rel:+.3f}  "
              "(0 = tight, >0 = conservative)")
    else:
        print("too few non-degenerate channels to correlate")

    print(f"runtime exact EVPPI      : {t_exact:.2f}s")
    print(f"runtime IDX              : {t_idx:.2f}s"
          f"   speedup x{t_exact / max(t_idx, 1e-9):.1f}")

    df.to_csv("exp_A_idx_vs_evppi.csv", index=False)
    print("wrote exp_A_idx_vs_evppi.csv")


if __name__ == "__main__":
    main()
