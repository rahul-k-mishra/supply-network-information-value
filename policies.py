"""Acquisition policies.

Baselines: None (implicit, B_v=0), Random, Coverage, Decoupled (tunable),
UCB (adaptive, additive, uncoupled -- Bayesian linear bandit on static features).
ASDR variants: linear (8 features, incl. new complementarity feature),
interact (rank-1 quadratic -- can represent pairwise probe complementarity),
voi (one-step lookahead against the mitigation plan -- the theoretically
correct coupled policy that the parametric scorers approximate).
Oracle: probes ground-truth chokepoints (infeasible upper bound).
"""
import numpy as np
from simcore import cascade_loss, cvar
from mitigation import plan_mitigation, _p_exactly_one

N_FEATURES = 8


# --------------------------------------------------------------------------
# Features
# --------------------------------------------------------------------------
def features(bel, cands, region_loss):
    """Feature matrix (len(cands) x 8), all in ~[0,1]."""
    net = bel.net
    max_tier = max(1, int(net.tier.max()))
    mean_sup = bel.mean_suppliers()
    deg = np.zeros(net.n)
    for v in range(net.n):
        for cat, sup in mean_sup[v].items():
            for u in sup:
                if u >= 0:
                    deg[u] += 1
    deg = deg / max(1.0, deg.max())
    crit_region = _critical_region_mass(bel)

    X = np.zeros((len(cands), N_FEATURES))
    for j, v in enumerate(cands):
        idxs = bel.in_idx.get(v, [])
        bvals = bel.b[idxs] if idxs else np.array([0.0])
        cc = bel.cat_candidates(v)
        unresolved = np.mean([all(i not in bel.obs for i in ii) for ii in cc.values()]) if cc else 0.0
        X[j, 0] = float(bvals.mean())                                  # posterior edge prob
        X[j, 1] = unresolved                                           # exclusivity/unknown cats
        X[j, 2] = net.tier[v] / max_tier                               # tier depth
        if net.attr_meta is not None:
            er = features._er_cache if hasattr(features, "_er_cache") else None
            pr = bel.expected_rates()[v]
        elif net.region_p is not None:
            pr = net.region_p[net.region[v]]
        else:
            pr = 0.05
        X[j, 3] = float(pr) / 0.15                              # believed fragility
        X[j, 4] = region_loss.get(int(net.region[v]), 0.0)             # region cascade loss
        X[j, 5] = deg[v]                                               # posterior-mean degree
        X[j, 6] = net.node_cost[v] / max(1e-9, net.node_cost.max())    # mitigation cost
        X[j, 7] = _complementarity(bel, v, cc)                         # NEW: joint identifiability
    return X


def _complementarity(bel, v, cc):
    """High when probing v resolves whether a category is single-sourced (q near
    0.5 -> max uncertainty) and when it completes partially-identified pairs."""
    if not cc:
        return 0.0
    score = 0.0
    for idxs in cc.values():
        q = _p_exactly_one(bel.b[idxs])
        score += 4.0 * q * (1.0 - q)
        # pair-completion bonus: a sibling candidate already probed & confirmed
        if any(bel.obs.get(i, 0) == 1 for i in idxs):
            score += 0.5
    return score / (2.0 * len(cc))


def _critical_region_mass(bel):
    net = bel.net
    mass, tot = {}, 1e-9
    for v, idxs in bel.in_idx.items():
        cc = bel.cat_candidates(v)
        p = np.mean([_p_exactly_one(bel.b[ii]) for ii in cc.values()]) if cc else 0.0
        r = int(net.region[v])
        mass[r] = mass.get(r, 0.0) + p
        tot += p
    return {r: m / tot for r, m in mass.items()}


def region_cascade_losses(bel):
    """Posterior-mean loss when each region fails alone (cached per step)."""
    net = bel.net
    sup = bel.mean_suppliers()
    out = {}
    from simcore import region_wipe
    for r in range(net.n_regions):
        out[r] = float(cascade_loss(net, sup, region_wipe(net, r))[0])
    return out


# --------------------------------------------------------------------------
# Policy base
# --------------------------------------------------------------------------
class Policy:
    name = "base"
    def reset(self, bel, cfg, rng): self.cfg, self.rng = cfg, rng
    def observe(self, v, reward, bel): pass
    def select(self, bel, cands): raise NotImplementedError


class RandomPolicy(Policy):
    name = "Random"
    def select(self, bel, cands):
        return cands[self.rng.integers(len(cands))]


class CoveragePolicy(Policy):
    name = "Coverage"
    def select(self, bel, cands):
        tiers = np.array([bel.net.tier[v] for v in cands])
        low = np.where(tiers == tiers.min())[0]
        counts = np.array([len(bel.in_idx.get(cands[i], [])) for i in low])
        return cands[low[np.argmax(counts)]]


class DecoupledPolicy(Policy):
    """Static risk ranking from the PRIOR belief only (never re-ranked).
    Weights tunable -> tuning parity with ASDR."""
    name = "Decoupled"
    def __init__(self, w=(1.0, 0.5, 0.5)):
        self.w = np.asarray(w, dtype=float)
    def reset(self, bel, cfg, rng):
        super().reset(bel, cfg, rng)
        rl = region_cascade_losses(bel)
        cands = list(bel.in_idx.keys())
        X = features(bel, cands, rl)
        s = self.w[0] * X[:, 0] + self.w[1] * X[:, 2] + self.w[2] * X[:, 3]
        self.rank = [c for _, c in sorted(zip(-s, cands))]
    def select(self, bel, cands):
        for v in self.rank:
            if v in cands:
                return v
        return cands[0]


class UCBPolicy(Policy):
    """Adaptive but additive & uncoupled: Bayesian linear bandit on static
    features, reward = observed single-sourcing signal at the probed node."""
    name = "UCB"
    def __init__(self, c=1.0, lam=1.0):
        self.c, self.lam = float(c), float(lam)
    def reset(self, bel, cfg, rng):
        super().reset(bel, cfg, rng)
        d = N_FEATURES
        self.A = self.lam * np.eye(d)
        self.y = np.zeros(d)
        self._rl = region_cascade_losses(bel)
    def select(self, bel, cands):
        X = features(bel, cands, self._rl)
        Ainv = np.linalg.inv(self.A)
        mu = X @ (Ainv @ self.y)
        var = np.einsum("ij,jk,ik->i", X, Ainv, X)
        return cands[int(np.argmax(mu + self.c * np.sqrt(np.maximum(var, 0))))]
    def observe(self, v, reward, bel):
        x = features(bel, [v], self._rl)[0]
        self.A += np.outer(x, x)
        self.y += reward * x


class ASDRLinear(Policy):
    name = "ASDR"
    def __init__(self, theta):
        self.theta = np.asarray(theta, dtype=float)
    def reset(self, bel, cfg, rng):
        super().reset(bel, cfg, rng)
        self._rl = region_cascade_losses(bel)
    def observe(self, v, reward, bel):
        self._rl = region_cascade_losses(bel)      # coupled: re-plan context each step
    def select(self, bel, cands):
        X = features(bel, cands, self._rl)
        return cands[int(np.argmax(X @ self.theta))]


class ASDRInteract(ASDRLinear):
    """score = theta.phi + (a.phi)(c.phi): rank-1 quadratic, 24 params.
    Can represent pairwise complementarity that no additive rule can."""
    name = "ASDR-Interact"
    def __init__(self, params):
        p = np.asarray(params, dtype=float)
        self.theta, self.a, self.cvec = p[:8], p[8:16], p[16:24]
    def select(self, bel, cands):
        X = features(bel, cands, self._rl)
        s = X @ self.theta + (X @ self.a) * (X @ self.cvec)
        return cands[int(np.argmax(s))]


class ASDRVOI(Policy):
    """One-step lookahead: score each candidate probe by the expected CVaR of the
    mitigation plan that would follow. Coupled by construction; expensive."""
    name = "ASDR-VOI"
    def __init__(self, prefilter=6, outcome_samples=2):
        self.k, self.m = prefilter, outcome_samples
    def reset(self, bel, cfg, rng):
        super().reset(bel, cfg, rng)
        self._rl = region_cascade_losses(bel)
    def observe(self, v, reward, bel):
        self._rl = region_cascade_losses(bel)
    def select(self, bel, cands):
        X = features(bel, cands, self._rl)
        pre = X[:, 0] + X[:, 3] + X[:, 7]                      # cheap prescore
        short = [cands[i] for i in np.argsort(-pre)[:self.k]]
        small = _shrink(self.cfg)
        best_v, best_val = short[0], np.inf
        for v in short:
            vals = []
            for s in range(self.m):
                bel2 = _copy_belief(bel)
                rng2 = np.random.default_rng(self.rng.integers(1 << 30))
                bel2.probe(v, self.cfg.rho_p, rng2)
                sec = plan_mitigation(bel2, small, rng2)
                vals.append(_posterior_cvar(bel2, sec, small, rng2))
            val = float(np.mean(vals))
            if val < best_val:
                best_v, best_val = v, val
        return best_v


class OraclePolicy(Policy):
    """Probes ground-truth chokepoints (single-failure kills focal). Infeasible."""
    name = "Oracle"
    def __init__(self, choke_ranked):
        self.rank = choke_ranked
    def select(self, bel, cands):
        for v in self.rank:
            if v in cands:
                return v
        return min(cands, key=lambda v: bel.net.tier[v])


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def _copy_belief(bel):
    import copy
    b2 = copy.copy(bel)
    b2.b = bel.b.copy()
    b2.probed = set(bel.probed)
    b2.obs = dict(bel.obs)
    return b2


def _shrink(cfg):
    import copy
    c = copy.copy(cfg)
    c.mit_posterior_samples = max(2, cfg.mit_posterior_samples // 2)
    c.mit_scenarios = max(20, cfg.mit_scenarios // 2)
    c.mit_pool = min(cfg.mit_pool, 20)
    return c


def _posterior_cvar(bel, secured, cfg, rng):
    from simcore import sample_node_failures
    net = bel.net
    vals = []
    for _ in range(cfg.mit_posterior_samples):
        sup, phr = bel.sample_suppliers(rng)
        rates = bel.sample_rates(rng)
        fail = sample_node_failures(net, cfg.mit_scenarios, cfg.p_disrupt,
                                    cfg.rho_within, rng, rates=rates)
        vals.append(cvar(cascade_loss(net, sup, fail, secured=secured,
                                      phantom_region=phr), cfg.alpha))
    return float(np.mean(vals))
