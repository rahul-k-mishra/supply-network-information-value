"""
exp_G_h2_witness.py
===================
Counts how often the checkable witness for (H2) holds on the benchmark
topologies. No simulation, no seeds, no overlays: a graph traversal and a
cost comparison on data already on disk.

THE CONDITION (Proposition 5 of the paper)
------------------------------------------
For a latent category (v,k) with candidate set C, |C| >= 2:
  (i)  every candidate u in C has v as its ONLY consumer, and
  (ii) node_cost[v] <= min_{u in C} node_cost[u].
Then securing v is an identification-free replacement satisfying both clauses
of (H2) for every u in C, so by Theorem 3 that category contributes exactly
zero to the value of structural information.

Both conditions are read off the public graph and the public cost vector.
Nothing latent is used.

BOUND TO THE ACTUAL NETWORK OBJECT (confirmed by --inspect, 2026-08-12)
----------------------------------------------------------------------
  net.n              int, number of nodes
  net.focal          int, the focal node
  net.node_cost      ndarray of securing costs, indexed by node
  net.suppliers      list of length n; net.suppliers[v] is a dict mapping a
                     category index k to a tuple of candidate nodes
  net.name           str
Consumers are derived: u supplies v iff u appears in some net.suppliers[v][k].

WHAT IT PRINTS
--------------
Per chain and in total: the number of latent categories (those with at least
two candidates), how many satisfy (i), how many satisfy (ii), and how many
satisfy both. Single-candidate categories are counted separately and excluded
from the census, since there is nothing to identify in them.

Categories of the focal node are reported both inside and outside the total,
because "securing the focal node" is a degenerate consumer cut: the focal has
no consumers, so guaranteeing its output guarantees the whole objective. The
headline number to quote is the non-focal one.

  python exp_G_h2_witness.py --willems-file data\\chain_data.xlsx --min-nodes 30
  python exp_G_h2_witness.py --willems-file data\\chain_data.xlsx --inspect
"""
import argparse
import sys

import numpy as np


def describe(net):
    print("Network attributes:")
    for a in sorted(dir(net)):
        if a.startswith("_"):
            continue
        v = getattr(net, a)
        if callable(v):
            print(f"  {a:24s} <callable>")
            continue
        t = type(v).__name__
        try:
            print(f"  {a:24s} {t:12s} len={len(v)}  {repr(v[:2])[:90]}")
        except Exception:                                  # noqa: BLE001
            print(f"  {a:24s} {t:12s} {repr(v)[:90]}")


def consumer_map(net):
    """u -> set of nodes u supplies."""
    cons = {}
    for v in range(net.n):
        cats = net.suppliers[v]
        if not cats:
            continue
        for _k, cands in cats.items():
            for u in cands:
                cons.setdefault(int(u), set()).add(int(v))
    return cons


def census(net):
    cons = consumer_map(net)
    cost = np.asarray(net.node_cost, dtype=float)
    focal = int(getattr(net, "focal", -1))
    out = dict(single=0, latent=0, sole=0, cheap=0, both=0,
               f_latent=0, f_both=0)
    for v in range(net.n):
        cats = net.suppliers[v]
        if not cats:
            continue
        for _k, cands in cats.items():
            cands = [int(u) for u in cands]
            if len(cands) < 2:
                out["single"] += 1
                continue
            is_focal = (v == focal)
            sole = all(cons.get(u, set()) == {v} for u in cands)
            cheap = cost[v] <= min(cost[u] for u in cands) + 1e-12
            if is_focal:
                out["f_latent"] += 1
                out["f_both"] += int(sole and cheap)
                continue
            out["latent"] += 1
            out["sole"] += int(sole)
            out["cheap"] += int(cheap)
            out["both"] += int(sole and cheap)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--willems-file", required=True)
    ap.add_argument("--min-nodes", type=int, default=30)
    ap.add_argument("--inspect", action="store_true")
    a = ap.parse_args()

    import data_willems as W
    nets = W.load_all_chains(a.willems_file, min_nodes=a.min_nodes)
    if a.inspect:
        describe(nets[0])
        return 0

    tot = dict(single=0, latent=0, sole=0, cheap=0, both=0,
               f_latent=0, f_both=0)
    print(f"\n{'chain':24s} {'latent':>7s} {'(i)':>7s} {'(ii)':>7s} "
          f"{'both':>7s} {'share':>7s}")
    for net in nets:
        c = census(net)
        for k in tot:
            tot[k] += c[k]
        share = c["both"] / c["latent"] if c["latent"] else float("nan")
        print(f"{str(getattr(net,'name','?')):24s} {c['latent']:7d} "
              f"{c['sole']:7d} {c['cheap']:7d} {c['both']:7d} {share:7.1%}")

    L = tot["latent"]
    print("\n" + "=" * 66)
    print(f"chains                                : {len(nets)}")
    print(f"single-candidate categories (excluded): {tot['single']}")
    print(f"latent categories, non-focal          : {L}")
    if L:
        print(f"  satisfy (i) sole consumer           : {tot['sole']:6d}  "
              f"{tot['sole'] / L:6.1%}")
        print(f"  satisfy (ii) cut no dearer          : {tot['cheap']:6d}  "
              f"{tot['cheap'] / L:6.1%}")
        print(f"  satisfy BOTH, witness holds         : {tot['both']:6d}  "
              f"{tot['both'] / L:6.1%}")
    print(f"focal-node latent categories          : {tot['f_latent']} "
          f"(witness on {tot['f_both']}; see header)")
    if L:
        print(f"\nQuote as: across the retained benchmark chains, "
              f"{tot['both'] / L:.1%} of latent categories provably\nhave zero "
              f"decision value under public data alone, by Proposition 5.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
