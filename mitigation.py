"""Mitigation planner. Held FIXED across all compared policies so that observed
differences are attributable to the acquisition policy alone (same rule as v1,
but implemented as greedy expected-tail-loss reduction over posterior samples,
i.e. a well-defined approximation of pi*_m(b))."""
import numpy as np
from simcore import cascade_loss, sample_node_failures, cvar


def plan_mitigation(bel, cfg, rng):
    net = bel.net
    K, M = cfg.mit_posterior_samples, cfg.mit_scenarios
    samples = []
    for _ in range(K):
        sup, phr = bel.sample_suppliers(rng)
        rates = bel.sample_rates(rng)          # None at λ=0 (public rates)
        fail_s = sample_node_failures(net, M, cfg.p_disrupt, cfg.rho_within,
                                      rng, rates=rates)
        samples.append((sup, phr, fail_s))

    pool = _candidate_pool(bel, cfg.mit_pool)
    secured = set()
    budget = float(cfg.mitigation_budget)          # COST budget, not a count
    # current losses per posterior sample under the running plan
    def losses_all(sec):
        return [cascade_loss(net, sup, fail_s, secured=sec, phantom_region=phr)
                for sup, phr, fail_s in samples]
    def mean_cvar(ls):
        return float(np.mean([cvar(l, cfg.alpha) for l in ls]))
    cur = losses_all(secured)
    base = mean_cvar(cur)
    n_tail = max(6, int(np.ceil(0.15 * M)))
    while True:
        # screen candidates on the CURRENT plan's tail scenarios only (cheap),
        # then verify the winner on the full batch (unbiased accept/reject)
        tails = [np.argsort(-l)[:n_tail] for l in cur]
        cand_scores = {}
        for v in pool:
            c = float(net.node_cost[v])
            if v in secured or c > budget + 1e-9:
                continue
            red = 0.0
            for (sup, phr, fail_s), l, t in zip(samples, cur, tails):
                lt = cascade_loss(net, sup, fail_s[t], secured=secured | {v},
                                  phantom_region=phr)
                red += float((l[t] - lt).sum())
            if red > 0:
                cand_scores[v] = red / c
        if not cand_scores:
            break
        picked = False
        for v in sorted(cand_scores, key=cand_scores.get, reverse=True)[:3]:
            new = losses_all(secured | {v})
            val = mean_cvar(new)
            if (base - val) / float(net.node_cost[v]) > 1e-9:
                secured.add(v)
                budget -= float(net.node_cost[v])
                cur, base = new, val
                picked = True
                break
        if not picked:
            break
    return secured


def _mean_cvar(net, samples, fail, secured, alpha):
    vals = []
    for sup, phr in samples:
        losses = cascade_loss(net, sup, fail, secured=secured, phantom_region=phr)
        vals.append(cvar(losses, alpha))
    return float(np.mean(vals))


def _candidate_pool(bel, k):
    """Tier-stratified pool. Tier-1/2 nodes (the big affordable cuts) are always
    eligible -- ranked within tier by risk-coverage per cost -- plus the top
    prescored deep nodes. Rationale: the prescore's coverage term lives on the
    posterior-mean graph, which THINS where probing resolves decoys; a pure
    top-k pool therefore demotes exactly the nodes probing just identified.
    Stratification makes pool membership robust to belief sharpness."""
    net = bel.net
    sup = bel.mean_suppliers(use_prior=True)       # PRIOR graph: same pool for all
    children = {}
    for w in range(net.n):
        for cat, ss in sup[w].items():
            for u in ss:
                if u >= 0:
                    children.setdefault(u, []).append((w, cat))
    pr = (net.region_p[net.region] if net.region_p is not None
          else np.full(net.n, 0.05))
    desc = np.zeros(net.n)
    for v in sorted(range(net.n), key=lambda x: -net.tier[x]):
        desc[v] = sum(pr[u] + desc[u] for cat, ss in sup[v].items()
                      for u in ss if u >= 0)
    b_pool = bel.b0 if hasattr(bel, "b0") else bel.b
    p_single_cat = {}
    for v in bel.in_idx:
        for cat, ii in bel.cat_candidates(v).items():
            p_single_cat[(v, cat)] = _p_exactly_one(b_pool[ii])
    scores = {}
    for v in range(1, net.n):
        served = children.get(v, [])
        if not served and v not in bel.in_idx:
            continue
        crit = max([p_single_cat.get(wc, 0.3) for wc in served], default=0.2)
        scores[v] = (pr[v] + desc[v]) * (0.2 + crit) / max(0.05, float(net.node_cost[v]))
    def top(tsel, m):
        c = [v for v in scores if tsel(net.tier[v])]
        return sorted(c, key=scores.get, reverse=True)[:m]
    pool = (top(lambda t: t == 1, k) + top(lambda t: t == 2, k)
            + top(lambda t: t >= 3, max(4, k // 2)))
    return pool


def _p_exactly_one(b):
    b = np.asarray(b, dtype=float)
    if len(b) == 0:
        return 0.0
    total = 0.0
    for i in range(len(b)):
        total += b[i] * np.prod(np.delete(1.0 - b, i))
    return float(total)
