"""IDX: the EVPPI-surrogate index, implemented from theory v4 (S9/S11) and the
frozen operationalization below. BLIND BY CONSTRUCTION: this script reads
NETWORKS only -- it contains no path to any results file and no chain-specific
logic. The join against measured ceilings happens only in p1b_eval.py.

Frozen operationalization (documented deviations from the ideal bound; on
general graphs IDX is the registered ranking statistic, the certified bound
lives on the theorem's class):
- Candidate risk q_u = region_p[region(u)]  (public attribute; lambda=0).
- Costs: c_u = node_cost[u]; consumer cut c_v = node_cost[v]; secure-all sum.
- Per-channel premium: I_raw(v,k) = sum_u b_u * max over budget breakpoints
  {c_v, all c_u, sum c_u} inter [0,B] of (v_inv(b) - v_full(b;u))^+ ,
  exactly the S9 algebra with v_full(b;u) = q_u if min(c_v,c_u) > b else 0,
  v_inv(b) = min(nothing, consumer, best diluted candidate, secure-all).
- Weight: for each focal category f, tail weight w_f = min(1, p_f/(1-a))/K0
  (p_f estimated by Monte Carlo on prior-sampled networks, no plan), spread
  EQUALLY over the latent channels that reach f (prevents channel-count
  domination); channel weight = sum over reachable f of w_f / N_f.
- Prior belief (decoys) is stochastic: IDX averaged over --draws independent
  belief constructions seeded by crc32(network name) -- independent of any
  evaluation seed stream.
Usage:
  python compute_index.py --willems-file data\\chain_data.xlsx --out index_willems.csv
"""
import argparse, zlib
import numpy as np
import pandas as pd
from config import make_profile
from simcore import build_belief, sample_node_failures, PHANTOM
import data_willems as W


def per_focal_cat_starvation(net, bel, sim, rng, n_samples=4, n_scen=150):
    """P(focal category f starved) under the prior, no plan. Light re-implementation
    of the cascade returning per-category indicators."""
    K0 = len(net.suppliers[net.focal])
    tot = np.zeros(K0)
    for _ in range(n_samples):
        sup, phr = bel.sample_suppliers(rng)
        fail = sample_node_failures(net, n_scen, sim.p_disrupt, sim.rho_within, rng)
        op = np.ones((net.n, n_scen), dtype=bool)
        focal_ok = []
        for v in net.topo_order():
            cat_ok = []
            for cat, ss in sup[v].items():
                if len(ss) == 0:
                    continue
                any_sup = np.zeros(n_scen, bool)
                for u in ss:
                    if u == PHANTOM:
                        z = phr.get((v, cat))
                        any_sup |= (~fail[:, z]) if z is not None else np.ones(n_scen, bool)
                    else:
                        any_sup |= op[u]
                cat_ok.append(any_sup)
            if v == net.focal:
                focal_ok = cat_ok
                continue
            ok = ~fail[:, v]
            for c in cat_ok:
                ok = ok & c
            op[v] = ok
        for f, okv in enumerate(focal_ok):
            tot[f] += (~okv).mean()
    return tot / n_samples


def focal_reach(net, bel):
    """Bitmask per node: which focal categories this node can feed (on the
    prior mean network, decoys included -- the prior's own view)."""
    sup = bel.mean_suppliers()
    K0 = len(net.suppliers[net.focal])
    reach = [0] * net.n
    for f, (cat, ss) in enumerate(sorted(net.suppliers[net.focal].items())):
        for u in ss:
            reach[u] |= (1 << f)
    order = sorted(range(net.n), key=lambda v: net.tier[v])   # downstream first
    for v in order:
        if v == net.focal:
            continue
        m = reach[v]
        if m:
            for cat, ss in sup[v].items():
                for u in ss:
                    if u >= 0:
                        reach[u] |= m
    return reach, K0


def index_one_draw(net, sim, draw_seed, B):
    rng = np.random.default_rng(draw_seed)
    bel = build_belief(net, sim, rng)
    p_f = per_focal_cat_starvation(net, bel, sim, rng)
    K0 = len(p_f)
    w_f = np.minimum(1.0, p_f / (1.0 - sim.alpha)) / K0
    reach, _ = focal_reach(net, bel)
    pr = (net.region_p[net.region] if net.region_p is not None
          else np.full(net.n, sim.p_disrupt))

    # channels + reachable-f channel counts
    channels = []
    n_ch_per_f = np.zeros(K0)
    for v, idxs in bel.in_idx.items():
        for cat, ii in bel.cat_candidates(v).items():
            fs = [f for f in range(K0) if reach[v] >> f & 1]
            if not fs:
                continue
            channels.append((v, cat, ii, fs))
            for f in fs:
                n_ch_per_f[f] += 1

    idx_val = 0.0
    for v, cat, ii, fs in channels:
        cand = [bel.edges[i][2] for i in ii]
        b0 = np.array([bel.b0[i] for i in ii], dtype=float)
        b0 = b0 / b0.sum() if b0.sum() > 0 else np.full(len(ii), 1.0 / len(ii))
        q = np.array([pr[u] for u in cand], dtype=float)
        c_u = np.array([max(0.05, float(net.node_cost[u])) for u in cand])
        c_v = max(0.05, float(net.node_cost[v]))
        bps = sorted({c for c in [c_v, *c_u, float(c_u.sum())] if c <= B + 1e-12})
        if not bps:
            continue
        qbar = float(b0 @ q)
        prem = 0.0
        for j, u in enumerate(cand):
            best = 0.0
            for b in bps:
                # v_inv(b)
                opts = [qbar]
                if c_v <= b + 1e-12:
                    opts.append(0.0)
                aff = c_u <= b + 1e-12
                if aff.any():
                    opts.append(qbar - float(np.max(b0[aff] * q[aff])))
                if c_u.sum() <= b + 1e-12:
                    opts.append(0.0)
                v_inv = min(opts)
                v_full = 0.0 if min(c_v, c_u[j]) <= b + 1e-12 else q[j]
                best = max(best, max(0.0, v_inv - v_full))
            prem += b0[j] * best
        weight = sum(w_f[f] / max(1.0, n_ch_per_f[f]) for f in fs)
        idx_val += weight * prem
    return idx_val, len(channels)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--willems-file", required=True)
    ap.add_argument("--out", default="index_willems.csv")
    ap.add_argument("--overlay-seeds", type=int, default=3)
    ap.add_argument("--min-nodes", type=int, default=30)
    ap.add_argument("--draws", type=int, default=10)
    args = ap.parse_args()

    cfg = make_profile("full")
    rows = []
    for os_seed in range(args.overlay_seeds):
        nets = W.load_all_chains(args.willems_file, n_regions=cfg.sim.n_regions,
                                 overlay="community", overlay_seed=os_seed,
                                 min_nodes=args.min_nodes)
        for net in nets:
            base = zlib.crc32(net.name.encode())
            vals, nch = [], 0
            for d in range(args.draws):
                v, nch = index_one_draw(net, cfg.sim, base + 7919 * d,
                                        float(cfg.sim.mitigation_budget))
                vals.append(v)
            rows.append({"network": net.name, "IDX": float(np.mean(vals)),
                         "IDX_std": float(np.std(vals)), "n_channels": nch})
            print(f"  {net.name}: IDX={np.mean(vals):.5f} (+-{np.std(vals):.5f}) "
                  f"channels={nch}", flush=True)
    pd.DataFrame(rows).to_csv(args.out, index=False)
    print(f"done -> {args.out}")


if __name__ == "__main__":
    main()
