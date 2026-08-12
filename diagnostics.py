"""Diagnostics.

chokepoint_census: ground-truth count of latent (tier>=2) nodes whose single
failure brings down the focal node. This is the pre-registered moderator:
ASDR's advantage is predicted to increase with this count and vanish at zero.
"""
import numpy as np
from simcore import cascade_loss


def chokepoint_census(net, min_tier=2):
    fail = np.zeros((1, net.n), dtype=bool)             # no background failures
    choke = []
    for v in range(net.n):
        if net.tier[v] < min_tier or v == net.focal:
            continue
        loss = cascade_loss(net, net.suppliers, fail, node_fail=v)[0]
        if loss > 0:
            choke.append(v)
    # rank by tier depth (deeper chokepoints are the ones probing must find)
    choke.sort(key=lambda v: -net.tier[v])
    return choke


def network_summary(net):
    choke = chokepoint_census(net)
    return {
        "name": net.name, "n_nodes": int(net.n),
        "n_edges": int(sum(len(s) for d in net.suppliers for s in d.values())),
        "max_tier": int(net.tier.max()),
        "n_chokepoints_tier2plus": len(choke),
        "chokepoints": choke[:20],
    }
