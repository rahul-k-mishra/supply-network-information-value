"""Simulation core for ASDR v2.

Ground-truth network, belief state over latent edges, Bayesian probe updates,
correlated regional disruption scenarios, conjunctive cascade, CVaR, and the
episode runner shared by every policy.
"""
from dataclasses import dataclass, field
import numpy as np
from scipy.stats import norm

PHANTOM = -1  # placeholder supplier when the posterior sample leaves a category empty


@dataclass
class Network:
    n: int
    suppliers: list          # node -> {cat: (supplier ids,)}  ground truth
    region: np.ndarray
    tier: np.ndarray
    n_regions: int
    node_cost: np.ndarray
    focal: int = 0
    name: str = "synthetic"
    region_p: np.ndarray = None     # per-region marginal failure prob (public)
    node_rate: np.ndarray = None    # TRUE per-node failure rate (λ>0: latent
                                    # for deep nodes; population law public)
    attr_meta: dict = None          # {'mu','p_hi','p_lo','latent': bool mask}

    @property
    def frac_single(self):
        """Public aggregate: fraction of single-sourced categories (a summary
        statistic firms know about their own sourcing; not node-level truth)."""
        cats = [len(s) for d in self.suppliers for s in d.values()]
        return float(np.mean([c == 1 for c in cats])) if cats else 0.7

    def topo_order(self):
        """Suppliers before consumers (descending tier works for strict-tier DAGs;
        Willems chains are relabelled to strict topological order at load time)."""
        return np.argsort(-self.tier, kind="stable")


# --------------------------------------------------------------------------
# Scenarios
# --------------------------------------------------------------------------
def sample_node_failures(net, n_scen, p, rho_within, rng, rates=None):
    """Node-level disruptions, correlated within region (public clusters) via a
    Gaussian copula. Marginal rates: `rates` override (planning under sampled
    latent assignments) > net.node_rate (truth, λ>0) > public region_p > p."""
    zr = rng.standard_normal((n_scen, net.n_regions))
    e = rng.standard_normal((n_scen, net.n))
    u = (np.sqrt(rho_within) * zr[:, net.region]
         + np.sqrt(1.0 - rho_within) * e)
    if rates is not None:
        p_node = np.asarray(rates, dtype=float)
    elif net.node_rate is not None:
        p_node = net.node_rate
    elif net.region_p is not None:
        p_node = net.region_p[net.region]
    else:
        p_node = np.full(net.n, p)
    return norm.cdf(u) < p_node[None, :]


def region_wipe(net, r):
    """One deterministic scenario: every node in region r fails (feature calc)."""
    fail = np.zeros((1, net.n), dtype=bool)
    fail[0, net.region == r] = True
    return fail


# --------------------------------------------------------------------------
# Cascade + CVaR
# --------------------------------------------------------------------------
def cascade_loss(net: Network, suppliers, fail, secured=None, node_fail=None,
                 phantom_region=None):
    """Binary loss at the focal node for each scenario.

    suppliers      : structure to evaluate (truth or a posterior sample)
    fail           : bool (n_scen, n) node-level failures
    secured        : set of node ids immune to disruption (guaranteed sources)
    node_fail      : optional node id forced inoperative in all scenarios
    phantom_region : optional dict (v,cat) -> proxy node id whose raw failure
                     column stands in for an unknown PHANTOM supplier
    """
    n_scen = fail.shape[0]
    secured = secured or set()
    op = np.ones((net.n, n_scen), dtype=bool)
    focal_cat_ok = []
    for v in net.topo_order():
        if v == node_fail:
            op[v] = False
            continue
        if v in secured and v != net.focal:
            # securing = qualified backup source: v's output is guaranteed to its
            # consumers regardless of v's own state or its upstream subtree
            op[v] = True
            continue
        cat_ok = []
        for cat, sup in suppliers[v].items():
            if len(sup) == 0:
                continue
            any_sup = np.zeros(n_scen, bool)
            for u in sup:
                if u == PHANTOM:
                    z = phantom_region.get((v, cat)) if phantom_region else None
                    any_sup |= (~fail[:, z]) if z is not None else np.ones(n_scen, bool)
                elif u in secured:
                    any_sup = np.ones(n_scen, bool)   # guaranteed backup source
                    break
                else:
                    any_sup |= op[u]
            cat_ok.append(any_sup)
        if v == net.focal:
            # loss is upstream-driven: focal's own region is not a disruption
            # source; loss = fraction of focal input categories starved
            focal_cat_ok = cat_ok
            continue
        ok = ~fail[:, v]
        cats_ok = np.ones(n_scen, bool)
        for c in cat_ok:
            cats_ok &= c
        op[v] = ok & cats_ok
    if not focal_cat_ok:
        return np.zeros(n_scen)
    served = np.mean(np.stack(focal_cat_ok), axis=0)
    return 1.0 - served


def cvar(losses, alpha):
    k = max(1, int(np.ceil((1.0 - alpha) * len(losses))))
    return float(np.sort(losses)[::-1][:k].mean())


# --------------------------------------------------------------------------
# Belief state
# --------------------------------------------------------------------------
@dataclass
class Belief:
    net: Network
    edges: list                       # (consumer v, cat, supplier u, is_true)
    b: np.ndarray                     # posterior existence probability
    in_idx: dict = field(default_factory=dict)   # v -> [edge indices]
    probed: set = field(default_factory=set)
    obs: dict = field(default_factory=dict)      # edge idx -> last observation (0/1)
    rate_known: dict = field(default_factory=dict)  # node -> revealed true rate

    @property
    def latent_nodes(self):
        return [v for v in self.in_idx if v not in self.probed]

    FP_RATE = 0.02   # false-alarm rate: probes rarely INVENT relationships

    def probe(self, v, rho_p, rng):
        """Asymmetric-channel observation of node v's candidate in-edges:
        P(detect | edge) = rho_p, P(false alarm | no edge) = FP_RATE. A
        symmetric channel lets decoys flip to 'confirmed supplier' often enough
        to hide true single-sourcing behind fake redundancy -- probing must not
        manufacture reassurance."""
        self.probed.add(v)
        # λ>0: auditing v's supply base reveals its candidates' attributes
        if self.net.attr_meta is not None:
            for i in self.in_idx.get(v, []):
                u = self.edges[i][2]
                self.rate_known[u] = float(self.net.node_rate[u])
        fp = self.FP_RATE
        for i in self.in_idx.get(v, []):
            true = self.edges[i][3]
            o = (rng.random() < rho_p) if true else (rng.random() < fp)
            self.obs[i] = int(o)
            b = self.b[i]
            if o:
                self.b[i] = b * rho_p / (b * rho_p + (1 - b) * fp)
            else:
                self.b[i] = b * (1 - rho_p) / (b * (1 - rho_p) + (1 - b) * (1 - fp))
        return _single_source_signal(self, v)

    def cat_candidates(self, v):
        out = {}
        for i in self.in_idx.get(v, []):
            _, cat, u, _ = self.edges[i]
            out.setdefault(cat, []).append(i)
        return out

    def sample_suppliers(self, rng):
        """Draw a structure from the posterior, CALIBRATED to the public
        sourcing-multiplicity marginal: the number of suppliers per category is
        drawn from the known aggregate single-sourcing rate; WHICH candidates
        fill those slots is drawn by belief weight. Independent Bernoulli
        sampling over candidates+decoys understates unprobed single-sourcing
        risk and creates a streetlight bias toward probed areas."""
        q1 = self.net.frac_single
        sup = [dict(self.net.suppliers[v]) if v not in self.in_idx else {}
               for v in range(self.net.n)]
        phantom_region = {}
        for v, idxs in self.in_idx.items():
            cats = {}
            for cat, ii in self.cat_candidates(v).items():
                w = self.b[ii].astype(float)
                if w.sum() < 1e-9:
                    w = np.ones(len(ii))
                w = w / w.sum()
                k = 1 if (rng.random() < q1 or len(ii) < 2) else 2
                pick = rng.choice(len(ii), size=min(k, len(ii)), replace=False, p=w)
                cats[cat] = [self.edges[ii[j]][2] for j in pick]
            if not cats:
                cats = {0: [PHANTOM]}
                phantom_region[(v, 0)] = int(rng.integers(self.net.n))
            sup[v] = {c: tuple(s) for c, s in cats.items()}
        return sup, phantom_region

    def sample_rates(self, rng):
        """Draw a full rate vector from the attribute posterior: revealed nodes
        at truth; unrevealed latent nodes iid from the PUBLIC mixing law."""
        am = self.net.attr_meta
        if am is None:
            return None
        r = self.net.node_rate.copy()
        latent = am["latent"]
        for v in range(self.net.n):
            if latent[v] and v not in self.rate_known:
                r[v] = am["p_hi"] if rng.random() < am["mu"] else am["p_lo"]
            elif v in self.rate_known:
                r[v] = self.rate_known[v]
        return r

    def expected_rates(self):
        am = self.net.attr_meta
        if am is None:
            return None
        r = self.net.node_rate.copy()
        latent = am["latent"]
        mix = am["mu"] * am["p_hi"] + (1 - am["mu"]) * am["p_lo"]
        for v in range(self.net.n):
            if latent[v] and v not in self.rate_known:
                r[v] = mix
            elif v in self.rate_known:
                r[v] = self.rate_known[v]
        return r

    def mean_suppliers(self, thresh=0.5, use_prior=False):
        bb = self.b0 if (use_prior and hasattr(self, "b0")) else self.b
        sup = [dict(self.net.suppliers[v]) if v not in self.in_idx else {}
               for v in range(self.net.n)]
        for v, idxs in self.in_idx.items():
            cats = {}
            for i in idxs:
                _, cat, u, _ = self.edges[i]
                if bb[i] >= thresh:
                    cats.setdefault(cat, []).append(u)
            sup[v] = {c: tuple(s) for c, s in cats.items()}
        return sup


def _single_source_signal(bel, v):
    cc = bel.cat_candidates(v)
    if not cc:
        return 0.0
    sig = [1.0 if sum(bel.obs.get(i, 0) for i in idxs) == 1 else 0.0
           for idxs in cc.values()]
    return float(np.mean(sig))


def build_belief(net: Network, cfg, rng) -> Belief:
    """Tier-1 relationships known; all edges into tier>=1 nodes are latent,
    with decoy candidates so probing carries genuine identification value."""
    edges, in_idx = [], {}
    for v in range(net.n):
        if v == net.focal:
            continue                                  # focal's suppliers known
        if not net.suppliers[v]:
            continue
        idxs = []
        for cat, sup in net.suppliers[v].items():
            for u in sup:
                idxs.append(len(edges)); edges.append((v, cat, int(u), True))
            pool = np.where(net.tier > net.tier[v])[0]
            pool = pool[~np.isin(pool, sup)]
            if len(pool):
                dec = rng.choice(pool, size=min(cfg.n_decoys, len(pool)), replace=False)
                for u in dec:
                    idxs.append(len(edges)); edges.append((v, cat, int(u), False))
        if idxs:
            in_idx[v] = idxs
    b = np.full(len(edges), cfg.prior)
    if cfg.informed_prior:
        for i, (v, cat, u, true) in enumerate(edges):
            # observable, pre-probe features only: tier depth + degree proxy
            depth = net.tier[u] / max(1, net.tier.max())
            b[i] = float(np.clip(cfg.prior + 0.15 * (0.5 - abs(depth - 0.5))
                                 + (0.1 if true else -0.1) * 0.0, 0.05, 0.95))
    bel = Belief(net=net, edges=edges, b=b, in_idx=in_idx)
    bel.b0 = b.copy()          # prior snapshot: pool construction uses this so
    if net.attr_meta is not None:      # non-latent nodes' rates are public
        for v in range(net.n):
            if not net.attr_meta["latent"][v]:
                bel.rate_known[v] = float(net.node_rate[v])
    return bel                 # pool membership is identical across policies


# --------------------------------------------------------------------------
# Episode
# --------------------------------------------------------------------------
def run_episode(net: Network, policy, mitigate_fn, cfg, seed):
    """One full acquire-then-mitigate episode. Returns dict of outcomes."""
    rng = np.random.default_rng(seed)
    bel = build_belief(net, cfg, rng)
    policy.reset(bel, cfg, rng)
    for _ in range(cfg.probe_budget):
        cand = bel.latent_nodes
        if not cand:
            break
        v = policy.select(bel, cand)
        reward = bel.probe(v, cfg.rho_p, rng)
        policy.observe(v, reward, bel)
    secured = mitigate_fn(bel, cfg, rng)
    fail = sample_node_failures(net, cfg.n_scen, cfg.p_disrupt, cfg.rho_within,
                                np.random.default_rng(seed + 777))
    losses = cascade_loss(net, net.suppliers, fail, secured=secured)
    return {"cvar": cvar(losses, cfg.alpha), "mean_loss": float(losses.mean()),
            "secured": sorted(secured), "probes": sorted(bel.probed)}
