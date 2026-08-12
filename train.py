"""Training and tuning.

- ASDR variants trained by a compact Differential Evolution (DE/rand/1/bin,
  absolute population -- pop x gens x n_train episode evaluations, so compute
  budget is explicit and identical across trainees).
- TUNING PARITY: Decoupled and UCB hyperparameters are tuned with the SAME DE
  budget, killing the "unequal tuning effort" objection from v1's Discussion.
- Optional learning curve over N_train in {4, 8, 16, 32}.
"""
import zlib
import numpy as np
from concurrent.futures import ProcessPoolExecutor
from simcore import run_episode
from mitigation import plan_mitigation
import policies as P

_G = {}

def _worker_init(instances, sim_cfg):
    _G["instances"], _G["sim"] = instances, sim_cfg

def _factory(kind, params):
    if kind == "asdr":     return P.ASDRLinear(params)
    if kind == "interact": return P.ASDRInteract(params)
    if kind == "decoupled":return P.DecoupledPolicy(w=params)
    if kind == "ucb":      return P.UCBPolicy(c=params[0], lam=max(params[1], 1e-3))
    raise ValueError(kind)

def _eval_candidate(task):
    kind, params, seed0 = task
    vals = [run_episode(net, _factory(kind, params), plan_mitigation, _G["sim"],
                        seed0 + 31 * i)["cvar"]
            for i, net in enumerate(_G["instances"])]
    return float(np.mean(vals))


def de_minimize(kind, bounds, instances, cfg, label):
    # zlib.crc32 is deterministic across processes; Python's hash() is
    # salted per process and silently breaks run-to-run reproducibility
    rng = np.random.default_rng(cfg.train.seed + zlib.crc32(kind.encode()) % 1000)
    lo = np.array([b[0] for b in bounds]); hi = np.array([b[1] for b in bounds])
    d, pop, gens = len(bounds), cfg.train.de_popsize, cfg.train.de_maxiter
    X = lo + rng.random((pop, d)) * (hi - lo)
    seed0 = cfg.train.seed

    def eval_batch(vecs):
        tasks = [(kind, v, seed0) for v in vecs]
        if cfg.n_jobs > 1:
            with ProcessPoolExecutor(cfg.n_jobs, initializer=_worker_init,
                                     initargs=(instances, cfg.sim)) as ex:
                return list(ex.map(_eval_candidate, tasks))
        _worker_init(instances, cfg.sim)
        return [_eval_candidate(t) for t in tasks]

    fit = np.array(eval_batch(list(X)))
    for g in range(gens):
        trials = []
        for i in range(pop):
            a, b, c = rng.choice([j for j in range(pop) if j != i], 3, replace=False)
            mut = np.clip(X[a] + 0.7 * (X[b] - X[c]), lo, hi)
            mask = rng.random(d) < 0.9
            mask[rng.integers(d)] = True
            trials.append(np.where(mask, mut, X[i]))
        tf = np.array(eval_batch(trials))
        better = tf < fit
        X[better] = np.array(trials)[better]
        fit[better] = tf[better]
        print(f"  [train] {label} gen {g+1}/{gens} best={fit.min():.4f}", flush=True)
    i = int(np.argmin(fit))
    return X[i], float(fit[i])


def _make_instances(gen_fn, n_train, base_seed):
    return [gen_fn(base_seed + 10_000 + i) for i in range(n_train)]


def train_all(gen_fn, cfg, want=("asdr", "interact")):
    instances = _make_instances(gen_fn, cfg.train.n_train, cfg.train.seed)
    out = {}
    if "asdr" in want:
        out["asdr_theta"], _ = de_minimize("asdr", [(-2, 2)] * 8, instances, cfg, "ASDR")
    if "interact" in want:
        out["interact_params"], _ = de_minimize("interact", [(-2, 2)] * 24,
                                                instances, cfg, "ASDR-Interact")
    if cfg.train.tune_baselines:
        out["decoupled_w"], _ = de_minimize("decoupled", [(0, 2)] * 3, instances,
                                            cfg, "Decoupled")
        out["ucb_params"], _ = de_minimize("ucb", [(0, 3), (0.01, 3)], instances,
                                           cfg, "UCB")
    return out


def learning_curve(gen_fn, cfg, sizes=(4, 8, 16, 32)):
    import copy
    curve = {}
    for n in sizes:
        c = copy.deepcopy(cfg); c.train.n_train = n
        instances = _make_instances(gen_fn, n, cfg.train.seed)
        theta, val = de_minimize("asdr", [(-2, 2)] * 8, instances, c,
                                 f"ASDR n_train={n}")
        curve[n] = {"theta": list(map(float, theta)), "train_cvar": val}
    return curve
