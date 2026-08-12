"""
exp_F_planner_gaps.py
=====================
Measures the two planner optimality gaps in Proposition 2 and, with them,
how far the empirically reported quantity H sits from the exact EVPI.

WHY THIS SCRIPT EXISTS
----------------------
The paper reports H, the advantage an IMPLEMENTED planner gains from being
handed the true structure.  Proposition 2 gives the exact identity

        H = EVPI + eps_pi - eps_theta

where eps_pi and eps_theta are the planner's optimality gaps with and
without theta.  Both are non-negative and neither dominates, so as an
identity alone it says only that the sign of H - EVPI is undetermined.  That
is honest but weak: a referee is entitled to ask how large the discrepancy
actually is and in which direction it usually falls.

This script answers that on miniature instances where the exact optimum can
be enumerated, so EVPI, eps_pi, eps_theta and H are all computed exactly --
no sampling anywhere.  The heuristic is a cost-budgeted greedy that mirrors
the planner used in the network pipeline: it repeatedly takes the affordable
action with the best objective reduction per unit cost, never backtracks,
and never looks ahead.

REGISTERED PREDICTION (written before the script was ever run; do not edit
this block after seeing output)
-------------------------------------------------------------------------
  P-F1  The identity must hold to machine precision:
        max |H - (EVPI + eps_pi - eps_theta)| < 1e-12.
        This is a correctness gate on the code, not a finding.  If it
        fails, STOP -- something is wrong with the implementation and no
        other number in the output means anything.

  P-F2  eps_theta < eps_pi on a majority of instances, hence
        median(H - EVPI) >= 0 and P(H >= EVPI) >= 0.5.
        Reasoning stated in advance: given theta the greedy faces a
        deterministic target and is more often exactly optimal, so its gap
        should be the smaller of the two.
        IF P-F2 HOLDS, it matters for the paper: H would typically OVERSTATE
        EVPI, so the small measured advantages imply the exact EVPI is
        smaller still, and the paper's negative conclusion is strengthened
        rather than weakened by the planner being heuristic.
        IF P-F2 FAILS, that is reported as-is: H understates EVPI, the
        measured advantages are conservative, and the paper must say so.

  P-F3  Spearman(H, EVPI) >= 0.7 across instances, i.e. H ranks instances
        much as EVPI does even where it misstates the level.  A lower value
        would mean H is not even a faithful ordering, which would have to be
        stated in the limitations.

  No result below is to be reinterpreted after the fact.  Whatever comes
  out, it goes in the paper in the direction it came out.

  python exp_F_planner_gaps.py --n-instances 2000 --seed <seed>

Output: console summary + exp_F_planner_gaps.csv (one row per instance).
"""
import argparse
import itertools

import numpy as np
import pandas as pd
from scipy.stats import spearmanr


# ----------------------------------------------------------------------
# Instances: K independent focal categories, each fed by one latent channel.
# Slightly wider than exp_A so the greedy has budget trade-offs to get wrong.
# ----------------------------------------------------------------------
def make_instance(rng):
    K = int(rng.integers(2, 5))
    cats = []
    for _ in range(K):
        m = int(rng.integers(2, 4))
        cats.append(dict(
            m=m,
            q=np.round(rng.uniform(0.05, 0.60, size=m), 3),
            c=np.round(rng.uniform(0.5, 2.0, size=m), 2),
            cv=round(float(rng.uniform(1.0, 4.0)), 2),
            prior=rng.dirichlet(np.ones(m) * float(rng.choice([1.0, 4.0]))),
        ))
    B = round(float(rng.uniform(1.0, 6.0)), 2)
    return dict(K=K, cats=cats, B=B)


def actions(cat):
    """(label, cost, risk_fn) for one category; risk_fn(theta) is that
    category's starvation probability when the supplier is candidate theta."""
    m, q, c, cv = cat["m"], cat["q"], cat["c"], cat["cv"]
    out = [("none", 0.0, lambda th, q=q: float(q[th]))]
    for i in range(m):
        out.append((f"cand{i}", float(c[i]),
                    lambda th, i=i, q=q: 0.0 if th == i else float(q[th])))
    out.append(("consumer", cv, lambda th: 0.0))
    out.append(("all", float(c.sum()), lambda th: 0.0))
    return out


# ----------------------------------------------------------------------
# Exact optima by enumeration.
# ----------------------------------------------------------------------
def enumerate_all(inst):
    K, cats, B = inst["K"], inst["cats"], inst["B"]
    acts = [actions(c) for c in cats]
    thetas = list(itertools.product(*[range(c["m"]) for c in cats]))
    pri = np.array([np.prod([cats[k]["prior"][t[k]] for k in range(K)])
                    for t in thetas])
    plans = [p for p in itertools.product(*acts)
             if sum(a[1] for a in p) <= B + 1e-12]
    Jmat = np.empty((len(plans), len(thetas)))
    for pi_, plan in enumerate(plans):
        for ti, th in enumerate(thetas):
            Jmat[pi_, ti] = sum(plan[k][2](th[k]) for k in range(K)) / K
    return acts, thetas, pri, plans, Jmat


# ----------------------------------------------------------------------
# The heuristic: cost-budgeted greedy, best improvement per unit cost.
# `value(k, action)` returns that category's contribution under the
# evaluation regime (prior expectation, or the realised theta).
# ----------------------------------------------------------------------
def greedy(inst, acts, value):
    K, B = inst["K"], inst["B"]
    chosen = [0] * K                      # index 0 is always "none", cost 0
    spent = 0.0
    while True:
        best, best_ratio = None, 1e-12
        for k in range(K):
            cur_cost = acts[k][chosen[k]][1]
            cur_val = value(k, acts[k][chosen[k]])
            for ai, a in enumerate(acts[k]):
                extra = a[1] - cur_cost
                if extra <= 0 or spent + extra > B + 1e-12:
                    continue
                gain = cur_val - value(k, a)
                if gain <= 0:
                    continue
                ratio = gain / extra
                if ratio > best_ratio + 1e-15:
                    best, best_ratio = (k, ai, extra), ratio
        if best is None:
            return chosen
        k, ai, extra = best
        chosen[k] = ai
        spent += extra


def plan_value(inst, acts, chosen, th):
    return sum(acts[k][chosen[k]][2](th[k])
               for k in range(inst["K"])) / inst["K"]


def analyse(inst):
    acts, thetas, pri, plans, Jmat = enumerate_all(inst)
    K = inst["K"]

    # exact quantities
    A = float((Jmat @ pri).min())                  # min_S E_theta j
    EM = float((Jmat.min(axis=0) * pri).sum())     # E_theta min_S j
    evpi = A - EM

    # heuristic without theta: evaluate each category under the prior
    prior_marg = []
    for k in range(K):
        pk = inst["cats"][k]["prior"]
        prior_marg.append(lambda a, pk=pk: sum(pk[t] * a[2](t)
                                               for t in range(len(pk))) / K)
    hat_pi = greedy(inst, acts, lambda k, a: prior_marg[k](a))
    val_hat_pi = sum(pri[ti] * plan_value(inst, acts, hat_pi, th)
                     for ti, th in enumerate(thetas))

    # heuristic with theta: re-run the same greedy for each theta
    val_hat_theta = 0.0
    for ti, th in enumerate(thetas):
        hat_th = greedy(inst, acts,
                        lambda k, a, th=th: a[2](th[k]) / K)
        val_hat_theta += pri[ti] * plan_value(inst, acts, hat_th, th)

    H = val_hat_pi - val_hat_theta
    eps_pi = val_hat_pi - A
    eps_theta = val_hat_theta - EM
    return dict(K=K, budget=inst["B"], evpi=evpi, H=H,
                eps_pi=eps_pi, eps_theta=eps_theta,
                residual=H - (evpi + eps_pi - eps_theta))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-instances", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20260812)
    a = ap.parse_args()

    rng = np.random.default_rng(a.seed)
    rows = [analyse(make_instance(rng)) for _ in range(a.n_instances)]
    df = pd.DataFrame(rows)
    df["diff"] = df["H"] - df["evpi"]

    print(f"instances                 : {a.n_instances}  (seed {a.seed})")
    print("--- P-F1: identity gate ---")
    print(f"max |residual|            : {df['residual'].abs().max():.3e}"
          "   (must be < 1e-12)")
    if df["residual"].abs().max() >= 1e-12:
        print("IDENTITY GATE FAILED -- stop here, nothing below is meaningful")
        df.to_csv("exp_F_planner_gaps.csv", index=False)
        return

    print("--- gaps ---")
    print(f"mean eps_pi               : {df['eps_pi'].mean():.5f}")
    print(f"mean eps_theta            : {df['eps_theta'].mean():.5f}")
    print(f"P(eps_theta < eps_pi)     : {(df['eps_theta'] < df['eps_pi']).mean():.3f}")

    print("--- P-F2: direction of H vs EVPI ---")
    print(f"mean EVPI                 : {df['evpi'].mean():.5f}")
    print(f"mean H                    : {df['H'].mean():.5f}")
    print(f"median (H - EVPI)         : {df['diff'].median():+.5f}")
    print(f"P(H >= EVPI)              : {(df['diff'] >= -1e-12).mean():.3f}")
    print(f"P(H = EVPI exactly)       : {(df['diff'].abs() < 1e-12).mean():.3f}")
    print(f"5th/95th pct of H - EVPI  : {df['diff'].quantile(0.05):+.5f}"
          f" / {df['diff'].quantile(0.95):+.5f}")

    print("--- P-F3: does H rank like EVPI ---")
    r, p = spearmanr(df["H"], df["evpi"])
    print(f"Spearman(H, EVPI)         : {r:+.4f}  p={p:.2e}")

    print("--- by number of categories ---")
    g = df.groupby("K").agg(n=("H", "size"), evpi=("evpi", "mean"),
                            H=("H", "mean"), diff=("diff", "median"),
                            eps_pi=("eps_pi", "mean"),
                            eps_theta=("eps_theta", "mean"))
    print(g.round(5).to_string())

    df.to_csv("exp_F_planner_gaps.csv", index=False)
    print("wrote exp_F_planner_gaps.csv")


if __name__ == "__main__":
    main()
