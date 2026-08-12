"""Synthetic multi-tier supply network generator (four topology families).

Networks are DAGs: focal node 0 at tier 0; suppliers at strictly higher tiers.
Each node consumes 1-3 material categories; each category is served by one
supplier (single-sourced) with probability q_single, else two suppliers.
"""
import numpy as np
from simcore import Network


def assign_latent_rates(net, lam, rng, p_bar=0.04, mu=1.0/3.0):
    """λ>0 attribute layer: deep (tier>=2) nodes draw a hidden two-point rate,
    mean-preserving in λ: p_hi = p_bar(1+2λ), p_lo = p_bar(1-λ), P(hi)=mu=1/3.
    Assignment LATENT; (mu, p_hi, p_lo) public. Shallow nodes: public p_bar.
    λ=0 leaves the network unchanged (backwards compatible)."""
    import numpy as _np
    if lam <= 0:
        return net
    p_hi, p_lo = p_bar * (1 + 2 * lam), max(1e-4, p_bar * (1 - lam))
    latent = net.tier >= 2
    rate = _np.full(net.n, p_bar, dtype=float)
    draw = rng.random(net.n) < mu
    rate[latent & draw] = p_hi
    rate[latent & ~draw] = p_lo
    net.node_rate = rate
    net.attr_meta = {"mu": mu, "p_hi": p_hi, "p_lo": p_lo, "latent": latent}
    return net

FAMILIES = ("scalefree", "sparse", "clustered", "heavytail")


def generate(n_nodes: int, topology: str, n_regions: int, rng: np.random.Generator,
             max_tier: int = 4, q_single: float = 0.6, lam: float = 0.0) -> Network:
    if topology not in FAMILIES:
        raise ValueError(topology)

    # ---- tier layout: geometric growth upstream --------------------------
    sizes = _tier_sizes(n_nodes, max_tier)
    tier = np.concatenate([np.full(s, t) for t, s in enumerate(sizes)])
    n = len(tier)
    ids_by_tier = [np.where(tier == t)[0] for t in range(max_tier + 1)]

    # ---- attachment weights per family -----------------------------------
    if topology == "scalefree":
        gamma = 1.08
    elif topology == "heavytail":
        gamma = 2.5
    else:
        gamma = 0.0  # uniform

    weight = np.ones(n)
    suppliers = [dict() for _ in range(n)]
    # categories taper with tier so deep conjunctive chains stay survivable
    n_cats = np.ones(n, dtype=int)
    n_cats[tier == 1] = rng.integers(1, 3, size=int((tier == 1).sum()))
    n_cats[tier == 2] = rng.integers(1, 3, size=int((tier == 2).sum()))
    n_cats[0] = rng.integers(4, 7)               # focal consumes 4-6 categories

    for t in range(max_tier):                    # consumers at tier t
        pool = ids_by_tier[t + 1]
        if len(pool) == 0:
            continue
        for v in ids_by_tier[t]:
            # deep sourcing is more consolidated: single-sourcing more common
            q_t = q_single if t == 0 else min(0.95, q_single + 0.15)
            for cat in range(n_cats[v]):
                k = 1 if rng.random() < q_t else 2
                w = weight[pool] ** (1.0 + gamma) if gamma > 0 else weight[pool]
                pr = w / w.sum()
                sup = rng.choice(pool, size=min(k, len(pool)), replace=False, p=pr)
                suppliers[v][cat] = tuple(int(u) for u in sup)
                weight[sup] += 1.0               # preferential attachment

    # ---- regions ---------------------------------------------------------
    if topology == "clustered":
        # contiguous blocks of ids -> strong regional clustering of subtrees
        region = _clustered_regions(n, n_regions, tier, suppliers, rng)
    else:
        region = rng.integers(0, n_regions, size=n)

    if topology == "sparse":
        # thin the graph: drop some second suppliers (raises single-sourcing)
        for v in range(n):
            for cat, sup in list(suppliers[v].items()):
                if len(sup) > 1 and rng.random() < 0.5:
                    suppliers[v][cat] = (sup[0],)

    # securing cost falls with tier depth: near-tier capacity is expensive,
    # deep component suppliers are cheap (in Willems this is real stage cost)
    depth_from_top = max_tier - tier
    cost = np.clip(rng.lognormal(0.0, 0.35, size=n), 0.5, 2.0) * (1.8 ** depth_from_top.astype(float))
    cost = cost / cost[tier >= max_tier].min() if (tier >= max_tier).any() else cost

    # public regional fragility: a few risky regions, most safe
    region_p = np.full(n_regions, 0.015)
    frag = rng.choice(n_regions, size=max(1, n_regions // 3), replace=False)
    region_p[frag] = rng.uniform(0.08, 0.11, size=len(frag))
    net = Network(n=n, suppliers=suppliers, region=np.asarray(region, dtype=int),
                  tier=tier.astype(int), n_regions=n_regions, node_cost=cost,
                  focal=0, region_p=region_p)
    return assign_latent_rates(net, lam, rng)


def _tier_sizes(n_nodes: int, max_tier: int):
    raw = np.array([1.0] + [2.2 ** t for t in range(1, max_tier + 1)])
    sizes = np.maximum(1, np.round(raw / raw.sum() * n_nodes)).astype(int)
    sizes[0] = 1
    return sizes


def _clustered_regions(n, n_regions, tier, suppliers, rng):
    region = np.full(n, -1)
    region[0] = 0
    order = np.argsort(tier)                     # downstream first
    for v in order:
        if v == 0:
            continue
        # inherit consumer's region with high probability
        cons = [w for w in range(n) for c in suppliers[w] if v in suppliers[w][c]]
        if cons and rng.random() < 0.8:
            region[v] = region[cons[0]] if region[cons[0]] >= 0 else rng.integers(n_regions)
        else:
            region[v] = rng.integers(0, n_regions)
    region[region < 0] = rng.integers(0, n_regions, size=(region < 0).sum())
    return region
