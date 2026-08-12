"""Mechanical verification of Theorem 2a, Theorem 1, and C1 on the exact
miniature model matching the theorem's hypotheses (disjoint categories,
expected loss, finite action sets). Brute-force EVPI vs the frozen index bound.
A single violation falsifies the theorem as stated."""
import numpy as np
from itertools import product

def actions_for_cat(cat):
    """Return list of (cost, pvec) where pvec[i] = starvation prob if candidate
    i is true. Action algebra: nothing / consumer cut / secure candidate j /
    secure all candidates."""
    m, q, c_u, c_v = cat["m"], cat["q"], cat["c_u"], cat["c_v"]
    acts = [(0.0, q.copy())]                       # nothing
    acts.append((c_v, np.zeros(m)))                # consumer cut
    for j in range(m):                             # secure candidate j
        p = q.copy(); p[j] = 0.0
        acts.append((float(c_u[j]), p))
    acts.append((float(c_u.sum()), np.zeros(m)))   # secure all
    return acts

def solve_instance(cats, B):
    K = len(cats)
    A_list = [actions_for_cat(c) for c in cats]
    costs = [np.array([a[0] for a in acts]) for acts in A_list]
    pvecs = [np.stack([a[1] for a in acts]) for acts in A_list]   # (nA, m)
    priors = [c["b"] for c in cats]
    E_k = [pv @ b for pv, b in zip(pvecs, priors)]                # (nA,)

    # enumerate feasible plans
    plans = [pl for pl in product(*[range(len(a)) for a in A_list])
             if sum(costs[k][pl[k]] for k in range(K)) <= B + 1e-12]
    assert plans, "no feasible plan (nothing always feasible)"
    # prior planner
    A_val = min(sum(E_k[k][pl[k]] for k in range(K)) for pl in plans)
    # full information: expectation over theta of min over plans
    thetas = list(product(*[range(c["m"]) for c in cats]))
    EM = 0.0
    for th in thetas:
        w = np.prod([priors[k][th[k]] for k in range(K)])
        M = min(sum(pvecs[k][pl[k], th[k]] for k in range(K)) for pl in plans)
        EM += w * M
    EVPI = (A_val - EM) / K

    # frozen index bound: per category, breakpoints = action costs (<=B) + B
    bound = 0.0
    for k in range(K):
        bps = sorted({float(c) for c in costs[k] if c <= B + 1e-12} | {float(B)})
        I_k = 0.0
        for i in range(cats[k]["m"]):
            best = 0.0
            for b in bps:
                feas = costs[k] <= b + 1e-12
                v_inv = E_k[k][feas].min()
                v_full = pvecs[k][feas, i].min()
                best = max(best, max(0.0, v_inv - v_full))
            I_k += priors[k][i] * best
        bound += I_k / K
    return EVPI, bound

def gen(rng, mode="generic"):
    K = int(rng.integers(2, 4))
    cats = []
    for _ in range(K):
        m = int(rng.integers(2, 4))
        q = rng.uniform(0.05, 0.95, m)
        c_u = rng.uniform(0.4, 3.0, m)
        c_v = float(rng.uniform(0.4, 4.0))
        b = rng.dirichlet(np.ones(m))
        if mode in ("t1", "c1"):
            q[:] = q[0]; c_u[:] = c_u[0]; b = np.full(m, 1.0/m)
        if mode == "t1":
            c_v = float(c_u[0] * rng.uniform(0.3, 1.0))   # consumer dominates
        cats.append(dict(m=m, q=q, c_u=c_u, c_v=c_v, b=b))
    B = float(rng.uniform(0.8, 9.0))
    return cats, B

def c1_closed_form(cats, B):
    tot = 0.0
    for c in cats:
        m, qb, cu, cv = c["m"], c["q"][0], float(c["c_u"][0]), c["c_v"]
        I = qb*(1-1/m) if (cu <= B + 1e-12 and cu < cv - 1e-12) else 0.0
        tot += I / len(cats)
    return tot

rng = np.random.default_rng(20260810)
report = {}
for mode, n in (("generic", 6000), ("t1", 2000), ("c1", 2000)):
    viol, t1_nonzero, c1_mismatch, ratios = 0, 0, 0, []
    worst = None
    for _ in range(n):
        cats, B = gen(rng, mode)
        EVPI, bound = solve_instance(cats, B)
        if EVPI > bound + 1e-9:
            viol += 1
            if worst is None or EVPI - bound > worst[0]:
                worst = (EVPI - bound, cats, B, EVPI, bound)
        if mode == "t1" and EVPI > 1e-9:
            t1_nonzero += 1
        if mode == "c1" and abs(bound - c1_closed_form(cats, B)) > 1e-9:
            c1_mismatch += 1
        if bound > 1e-12:
            ratios.append(EVPI / bound)
    report[mode] = dict(n=n, violations=viol, t1_nonzero=t1_nonzero,
                        c1_mismatch=c1_mismatch,
                        mean_tightness=float(np.mean(ratios)) if ratios else None,
                        max_tightness=float(np.max(ratios)) if ratios else None)
    print(f"[{mode}] n={n} violations={viol} "
          + (f"T1-nonzero-EVPI={t1_nonzero} " if mode=="t1" else "")
          + (f"C1-formula-mismatch={c1_mismatch} " if mode=="c1" else "")
          + (f"tightness mean={report[mode]['mean_tightness']:.3f} "
             f"max={report[mode]['max_tightness']:.3f}" if ratios else ""), flush=True)
    if worst:
        print("  WORST VIOLATION:", worst[0], "instance:", worst[1], "B=", worst[2],
              "EVPI=", worst[3], "bound=", worst[4])
print("\nDONE")
