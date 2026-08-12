"""
exp_E_conjecture1.py
====================
Exhaustive test of Conjecture 1 (the general-graph extension of the
identification-premium bound) on miniature instances where category
subtrees SHARE channels -- the exact case Theorem 2a does not cover.

WHY THIS SCRIPT EXISTS
----------------------
Theorem 2a is proved only when the focal categories' subtrees are
node-disjoint.  The paper currently carries the shared-node case as
Conjecture 1: the same bound holds if each shared channel's premium is
counted once per focal category it feeds.  A conjecture sitting in the
theoretical centre of a paper is a liability.  This script does not prove
it, but it does something a referee will accept as evidence: it enumerates
EXACT EVPI on thousands of shared-channel instances and checks whether the
conjectured bound is ever violated.

WHAT COUNTS AS A PASS (state this before you look at the output)
----------------------------------------------------------------
  - violations == 0 over >= 5000 instances
      -> Conjecture 1 keeps its label but gains mechanical support on the
         same footing as Theorem 2a's verification; say exactly that
  - violations > 0
      -> BETTER OUTCOME THAN IT LOOKS.  The script prints the smallest
         counterexample.  A counterexample turns a conjecture into a
         negative result you can state precisely: the multiplicity rule
         fails, here is the structure that breaks it.  Send it to me and
         the paper says so.

  python exp_E_conjecture1.py --n-instances 5000 --seed 20260812

Output: console summary + exp_E_conjecture1.csv, and, if any violation
occurs, exp_E_counterexample.txt with the full instance written out.
"""
import argparse
import itertools

import numpy as np
import pandas as pd


def make_instance(rng):
    """K focal categories fed by C channels; sharing is forced by
    assigning at least one channel to more than one category."""
    K = int(rng.integers(2, 4))
    C = int(rng.integers(2, 4))
    chans = []
    for _ in range(C):
        m = int(rng.integers(2, 4))
        chans.append(dict(
            m=m,
            q=np.round(rng.uniform(0.05, 0.55, size=m), 3),
            c=np.round(rng.uniform(0.5, 2.0, size=m), 2),
            cv=round(float(rng.uniform(1.0, 4.0)), 2),
            prior=rng.dirichlet(np.ones(m) * float(rng.choice([1.0, 4.0]))),
        ))
    # feed map: every category gets >=1 channel, and channel 0 feeds >=2
    feeds = [set() for _ in range(C)]
    for k in range(K):
        for c in range(C):
            if rng.random() < 0.55:
                feeds[c].add(k)
    for k in range(K):                       # no orphan category
        if not any(k in f for f in feeds):
            feeds[int(rng.integers(0, C))].add(k)
    feeds[0] = set(range(K)) if K > 1 else feeds[0]   # force real sharing
    B = round(float(rng.uniform(1.0, 5.0)), 2)
    return dict(K=K, C=C, chans=chans, feeds=feeds, B=B)


def actions(ch):
    m, q, c, cv = ch["m"], ch["q"], ch["c"], ch["cv"]
    out = [("none", 0.0, lambda th, q=q: float(q[th]))]
    for i in range(m):
        out.append((f"cand{i}", float(c[i]),
                    lambda th, i=i, q=q: 0.0 if th == i else float(q[th])))
    out.append(("cut", cv, lambda th: 0.0))
    return out


def exact_evpi(inst):
    K, C, chans, feeds, B = (inst["K"], inst["C"], inst["chans"],
                             inst["feeds"], inst["B"])
    acts = [actions(c) for c in chans]
    thetas = list(itertools.product(*[range(c["m"]) for c in chans]))
    pri = np.array([np.prod([chans[c]["prior"][t[c]] for c in range(C)])
                    for t in thetas])
    plans = [p for p in itertools.product(*acts)
             if sum(a[1] for a in p) <= B + 1e-12]

    J = np.empty((len(plans), len(thetas)))
    for pi, plan in enumerate(plans):
        for ti, th in enumerate(thetas):
            f = [plan[c][2](th[c]) for c in range(C)]
            tot = 0.0
            for k in range(K):
                surv = 1.0
                for c in range(C):
                    if k in feeds[c]:
                        surv *= (1.0 - f[c])
                tot += 1.0 - surv
            J[pi, ti] = tot / K
    A = float((J @ pri).min())
    EM = float((J.min(axis=0) * pri).sum())
    return A - EM


def conjectured_bound(inst):
    """(1/K) * sum_c |F(c)| * I_c, with I_c the isolated-channel premium."""
    K, C, chans, feeds, B = (inst["K"], inst["C"], inst["chans"],
                             inst["feeds"], inst["B"])
    total = 0.0
    per = []
    for c in range(C):
        ch, acts = chans[c], actions(chans[c])
        breaks = sorted({a[1] for a in acts if a[1] <= B + 1e-12})
        prem = 0.0
        for th in range(ch["m"]):
            best = 0.0
            for b in breaks:
                feas = [a for a in acts if a[1] <= b + 1e-12]
                v_inv = min(sum(ch["prior"][t] * a[2](t)
                                for t in range(ch["m"])) for a in feas)
                v_full = min(a[2](th) for a in feas)
                best = max(best, v_inv - v_full)
            prem += ch["prior"][th] * best
        per.append(prem)
        total += len(feeds[c]) * prem
    return total / K, per


def dump(inst, evpi, bound, path):
    with open(path, "w") as fh:
        fh.write(f"EVPI = {evpi!r}\nbound = {bound!r}\n")
        fh.write(f"K={inst['K']} C={inst['C']} B={inst['B']}\n")
        fh.write(f"feeds={[sorted(f) for f in inst['feeds']]}\n")
        for i, ch in enumerate(inst["chans"]):
            fh.write(f"channel {i}: m={ch['m']} q={list(ch['q'])} "
                     f"c={list(ch['c'])} cv={ch['cv']} "
                     f"prior={[round(float(x), 4) for x in ch['prior']]}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-instances", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=20260812)
    a = ap.parse_args()

    rng = np.random.default_rng(a.seed)
    rows, worst, worst_inst = [], None, None
    for n in range(a.n_instances):
        inst = make_instance(rng)
        evpi = exact_evpi(inst)
        bound, per = conjectured_bound(inst)
        slack = bound - evpi
        rows.append(dict(instance=n, K=inst["K"], C=inst["C"],
                         shared=sum(1 for f in inst["feeds"] if len(f) > 1),
                         evpi=evpi, bound=bound, slack=slack,
                         ratio=evpi / bound if bound > 1e-12 else np.nan))
        if worst is None or slack < worst:
            worst, worst_inst = slack, inst

    df = pd.DataFrame(rows)
    viol = df[df["slack"] < -1e-9]
    print(f"instances          : {a.n_instances}  (seed {a.seed})")
    print(f"shared-channel inst: {int((df['shared'] > 0).sum())}")
    print(f"bound violations   : {len(viol)}")
    print(f"min slack          : {df['slack'].min():+.6f}")
    nz = df[df["bound"] > 1e-12]
    if len(nz):
        print(f"tightness EVPI/bound: mean {nz['ratio'].mean():.3f}  "
              f"max {nz['ratio'].max():.3f}")
    if len(viol):
        dump(worst_inst, exact_evpi(worst_inst),
             conjectured_bound(worst_inst)[0], "exp_E_counterexample.txt")
        print("COUNTEREXAMPLE written to exp_E_counterexample.txt -- send it")
    df.to_csv("exp_E_conjecture1.csv", index=False)
    print("wrote exp_E_conjecture1.csv")


if __name__ == "__main__":
    main()
