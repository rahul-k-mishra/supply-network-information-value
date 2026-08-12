"""Statistics that survive referees: paired tests, Holm correction, bootstrap
CIs, Cohen's d for paired differences, win rates, and the moderator analysis
(advantage vs chokepoint census) across real chains."""
import numpy as np
from scipy import stats as st


def bootstrap_ci(x, n_boot=2000, alpha=0.05, seed=0):
    rng = np.random.default_rng(seed)
    x = np.asarray(x, float)
    means = rng.choice(x, size=(n_boot, len(x)), replace=True).mean(axis=1)
    lo, hi = np.quantile(means, [alpha / 2, 1 - alpha / 2])
    return float(x.mean()), float(lo), float(hi)


def paired_compare(ref, method):
    ref, method = np.asarray(ref, float), np.asarray(method, float)
    d = ref - method                       # positive = method better (lower CVaR)
    if np.allclose(d, 0):
        return {"adv": 0.0, "p": 1.0, "cohens_d": 0.0, "win": 0.0}
    try:
        p = st.wilcoxon(ref, method, zero_method="zsplit").pvalue
    except ValueError:
        p = 1.0
    cd = d.mean() / d.std(ddof=1) if d.std(ddof=1) > 0 else 0.0
    win = float((d > 0).mean())
    return {"adv": float(d.mean()), "p": float(p), "cohens_d": float(cd), "win": win}


def holm(pvals):
    """Holm-Bonferroni adjusted p-values, order preserved."""
    p = np.asarray(pvals, float)
    order = np.argsort(p)
    adj = np.empty_like(p)
    m = len(p)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * p[i])
        adj[i] = min(1.0, running)
    return adj


def moderator(adv_per_net, choke_per_net):
    """Pre-registered prediction: advantage increases with chokepoint census."""
    x = np.asarray(choke_per_net, float)
    y = np.asarray(adv_per_net, float)
    if len(x) < 3 or x.std() == 0:
        return {"spearman_rho": float("nan"), "p": float("nan"), "n": len(x)}
    rho, p = st.spearmanr(x, y)
    return {"spearman_rho": float(rho), "p": float(p), "n": len(x)}
