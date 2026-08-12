"""Configuration for ASDR v2 experiments.

Two profiles:
  smoke -- minutes; verifies the pipeline runs end to end and orderings are sane.
  full  -- the publication run; hours depending on machine and --n-jobs.
"""
from dataclasses import dataclass, field


@dataclass
class SimConfig:
    # Disruption process
    p_disrupt: float = 0.03         # marginal node failure probability
                                    # (tail = 1-2 region events, so targeted
                                    #  mitigation can rescue the tail)
    rho_within: float = 0.6         # within-region failure correlation (copula)
    alpha: float = 0.9              # CVaR tail level
    n_regions: int = 6

    # Visibility / probing
    rho_p: float = 0.9              # probe reliability
    probe_budget: int = 9           # B_v
    prior: float = 0.5              # uninformed prior on latent edges
    informed_prior: bool = True     # derive prior from observable node features
    n_decoys: int = 2               # decoy candidate suppliers per (node, category)

    # Mitigation
    mitigation_budget: float = 9.0  # B_m -- COST budget for securing
    mit_posterior_samples: int = 10 # K networks sampled from posterior for planning
    mit_scenarios: int = 200        # scenario batch for planning (tail of a
                                    # small batch is noise -> overfit plans)
    mit_pool: int = 16              # candidate pool size for greedy mitigation

    # Evaluation
    n_scen: int = 160               # fresh scenarios for final evaluation


@dataclass
class TrainConfig:
    n_train: int = 32               # training instances (was 4 in v1 -- a review killer)
    de_popsize: int = 16
    de_maxiter: int = 16
    seed: int = 12345
    tune_baselines: bool = True     # tuning parity: same DE budget for Decoupled & UCB
    learning_curve: bool = False    # re-train at n_train in {4,8,16,32} and report


@dataclass
class RunConfig:
    sim: SimConfig = field(default_factory=SimConfig)
    train: TrainConfig = field(default_factory=TrainConfig)
    n_seeds: int = 60
    n_nodes: int = 1000             # synthetic network size
    topology: str = "scalefree"     # scalefree | sparse | clustered | heavytail
    voi_prefilter: int = 6          # candidates evaluated per step by ASDR-VOI
    voi_outcome_samples: int = 2
    n_jobs: int = 1


def make_profile(name: str) -> RunConfig:
    cfg = RunConfig()
    if name == "smoke":
        cfg.n_seeds = 6
        cfg.n_nodes = 150
        cfg.sim.n_scen = 120
        cfg.sim.mit_posterior_samples = 6
        cfg.sim.mit_scenarios = 120
        cfg.sim.mit_pool = 12
        cfg.train.n_train = 3
        cfg.train.de_popsize = 6
        cfg.train.de_maxiter = 3
        cfg.voi_prefilter = 3
        cfg.voi_outcome_samples = 1
    elif name == "full":
        pass  # defaults above are the full profile
    else:
        raise ValueError(f"unknown profile: {name}")
    return cfg
