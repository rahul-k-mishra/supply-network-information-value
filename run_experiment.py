"""ASDR v2 experiment runner.

Synthetic (four families):
  python run_experiment.py --dataset synthetic --topology scalefree --profile smoke
  python run_experiment.py --dataset synthetic --topology scalefree --profile full --n-jobs 8

Willems (2008) real chains (download the MSOM workbook first):
  python run_experiment.py --dataset willems --willems-file "chain data.xlsx" --profile full --n-jobs 8
  python run_experiment.py --dataset willems --willems-file FILE --inspect     # if parsing fails

Outputs (in --out): results_raw.csv, results_summary.csv, moderator.json,
diagnostics.csv, trained_params.json, REPORT.md
"""
import argparse
import json
import os
import numpy as np
import pandas as pd

from config import make_profile
from simcore import run_episode
from mitigation import plan_mitigation
from diagnostics import chokepoint_census, network_summary
from train import train_all, learning_curve
import policies as P
import stats as S
import netgen
from concurrent.futures import ProcessPoolExecutor

_EG = {}

def _eval_init(net, cfg, trained, oracle_rank):
    _EG.update(net=net, cfg=cfg, trained=trained, oracle=oracle_rank)

def _eval_task(task):
    name, seed = task
    net, cfg, trained = _EG["net"], _EG["cfg"], _EG["trained"]
    if name == "None":
        r = none_baseline(net, cfg, seed)
    else:
        pol = build_policies(cfg, trained, _EG["oracle"])[name]()
        r = run_episode(net, pol, plan_mitigation, cfg.sim, seed)
    return {"network": net.name, "policy": name, "seed": seed,
            "cvar": r["cvar"], "mean_loss": r["mean_loss"]}


def build_policies(cfg, trained, oracle_rank):
    dec_w = trained.get("decoupled_w", (1.0, 0.5, 0.5))
    ucb = trained.get("ucb_params", (1.0, 1.0))
    pols = {
        "Random": lambda: P.RandomPolicy(),
        "Coverage": lambda: P.CoveragePolicy(),
        "Decoupled": lambda: P.DecoupledPolicy(w=dec_w),
        "UCB": lambda: P.UCBPolicy(c=ucb[0], lam=max(ucb[1], 1e-3)),
        "ASDR": lambda: P.ASDRLinear(trained["asdr_theta"]),
    }
    if "interact_params" in trained:
        pols["ASDR-Interact"] = lambda: P.ASDRInteract(trained["interact_params"])
    pols["ASDR-VOI"] = lambda: P.ASDRVOI(cfg.voi_prefilter, cfg.voi_outcome_samples)
    pols["Oracle"] = lambda: P.OraclePolicy(oracle_rank)
    return pols


def none_baseline(net, cfg, seed):
    """No acquisition: mitigation from the prior belief alone."""
    import copy
    c = copy.copy(cfg.sim)
    c.probe_budget = 0
    return run_episode(net, P.RandomPolicy(), plan_mitigation, c, seed)


def _truth_greedy(net, sim):
    """Full-information cost-aware greedy plan on the TRUE network, computed
    once per network. Anchors the Oracle's probe ranking to the decision that
    perfect information would support."""
    from simcore import sample_node_failures, cascade_loss, cvar
    rng = np.random.default_rng(4242)
    fail = sample_node_failures(net, 300, sim.p_disrupt, sim.rho_within, rng)
    pr = (net.region_p[net.region] if net.region_p is not None
          else np.full(net.n, sim.p_disrupt))
    desc = np.zeros(net.n)
    for v in np.argsort(-net.tier):
        desc[v] = sum(pr[u] + desc[u] for cat, ss in net.suppliers[v].items()
                      for u in ss)
    score = {v: (pr[v] + desc[v]) / max(0.05, float(net.node_cost[v]))
             for v in range(net.n) if v != net.focal}
    pool = sorted(score, key=score.get, reverse=True)[:60]
    base = cvar(cascade_loss(net, net.suppliers, fail), sim.alpha)
    secured, budget = set(), float(sim.mitigation_budget)
    while True:
        best, bestv, bestr = None, base, 1e-12
        for v in pool:
            c = float(net.node_cost[v])
            if v in secured or c > budget + 1e-9:
                continue
            val = cvar(cascade_loss(net, net.suppliers, fail,
                                    secured=secured | {v}), sim.alpha)
            r = (base - val) / c
            if r > bestr:
                best, bestv, bestr = v, val, r
        if best is None:
            break
        secured.add(best)
        budget -= float(net.node_cost[best])
        base = bestv
    return secured


def _oracle_rank(net, sim):
    """Probing reveals a node's SUPPLIERS, so information about a latent
    chokepoint lives at its CONSUMERS. Plain consumer-of-census ranking
    collapses onto Coverage on distribution-shaped chains (every sink consumes
    a chokepoint), so the Oracle is anchored to the DECISION instead: probe
    what verifies the full-information plan first, then remaining census."""
    choke = set(chokepoint_census(net, min_tier=2))

    def consumers_of(nodes):
        out = set()
        for w in range(net.n):
            if w == net.focal:
                continue
            for cat, sup in net.suppliers[w].items():
                if any(u in nodes for u in sup):
                    out.add(w)
                    break
        return out

    plan = _truth_greedy(net, sim)
    rank, seen = [], set()
    for block in (consumers_of(plan) | plan, consumers_of(choke) | choke):
        for v in sorted(block, key=lambda v: (net.tier[v], v)):
            if v not in seen and v != net.focal:
                seen.add(v)
                rank.append(v)
    if not rank:
        rank = sorted(chokepoint_census(net, min_tier=1),
                      key=lambda v: (net.tier[v], v))
    return rank


def evaluate(nets, cfg, trained, out_dir, skip=()):
    rows = []
    for k, net in enumerate(nets):
        oracle_rank = _oracle_rank(net, cfg.sim)
        names = ["None"] + [n for n in build_policies(cfg, trained, oracle_rank)
                            if n not in skip]
        tasks = [(name, 500_000 + 1000 * k + s)
                 for s in range(cfg.n_seeds) for name in names]
        if cfg.n_jobs > 1:
            with ProcessPoolExecutor(cfg.n_jobs, initializer=_eval_init,
                                     initargs=(net, cfg, trained, oracle_rank)) as ex:
                rows += list(ex.map(_eval_task, tasks))
        else:
            _eval_init(net, cfg, trained, oracle_rank)
            for t in tasks:
                rows.append(_eval_task(t))
        print(f"    net {k+1}/{len(nets)} ({net.name}) done", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(out_dir, "results_raw.csv"), index=False)
    return df


def pilot_verdict(df, cfg):
    """Registered gates, fixed before this run:
    G1-kill: median ceiling < 0.005 AND frac(ceiling>0.02) < 0.20  -> H1 wins.
    G2: split-half Spearman of the per-instance ceiling >= 0.5 required before
        any moderator (index) test may be registered."""
    from scipy.stats import spearmanr
    piv = df.pivot_table(index=["network", "seed"], columns="policy",
                         values="cvar")
    ceil_seed = piv["None"] - piv["Oracle"]
    per = ceil_seed.groupby(level="network").mean()
    seeds = sorted({s for _, s in ceil_seed.index})
    half = set(seeds[:len(seeds) // 2])
    ca = ceil_seed[[s in half for _, s in ceil_seed.index]].groupby(level="network").mean()
    cb = ceil_seed[[s not in half for _, s in ceil_seed.index]].groupby(level="network").mean()
    rho, p = spearmanr(ca.reindex(per.index), cb.reindex(per.index))
    med, frac = float(per.median()), float((per > 0.02).mean())
    print(chr(10) + "=== PILOT VERDICT (registered gates) ===")
    print(f"instances={len(per)}  ceiling: median={med:.4f}  mean={per.mean():.4f}  "
          f"frac>0.02={frac:.2f}  max={per.max():.4f}")
    print(f"split-half reliability of ceiling: spearman={rho:.3f} (p={p:.4f})")
    g1_kill = (med < 0.005) and (frac < 0.20)
    print(f"G1 (ceilings open):     {'KILL -- H1 wins, program dead' if g1_kill else 'PASS'}")
    print(f"G2 (reliability >=0.5): {'PASS -- moderator test may be registered' if rho >= 0.5 else 'FAIL -- no moderator test'}")


def summarise(df, out_dir):
    piv = df.pivot_table(index=["network", "seed"], columns="policy", values="cvar")
    summary, pvals, labels = [], [], []
    ref = piv["Decoupled"]
    for pol in piv.columns:
        m, lo, hi = S.bootstrap_ci(piv[pol].values)
        cmp = S.paired_compare(ref.values, piv[pol].values)
        summary.append({"policy": pol, "mean_cvar": m, "ci_lo": lo, "ci_hi": hi, **cmp})
        if pol not in ("Decoupled",):
            pvals.append(cmp["p"]); labels.append(pol)
    adj = S.holm(pvals)
    adj_map = dict(zip(labels, adj))
    for row in summary:
        row["p_holm"] = adj_map.get(row["policy"], float("nan"))
    sdf = pd.DataFrame(summary).sort_values("mean_cvar")
    sdf.to_csv(os.path.join(out_dir, "results_summary.csv"), index=False)

    # coupling decomposition (ASDR - UCB = coupling; UCB - Decoupled = adaptivity)
    dec = {}
    if {"ASDR", "UCB", "Decoupled"} <= set(piv.columns):
        total = (piv["Decoupled"] - piv["ASDR"]).mean()
        coup = (piv["UCB"] - piv["ASDR"]).mean()
        adap = (piv["Decoupled"] - piv["UCB"]).mean()
        dec = {"total_adv": float(total), "coupling_abs": float(coup),
               "adaptivity_abs": float(adap),
               "coupling_frac": float(coup / total) if total else float("nan")}
    return sdf, piv, dec


def moderator_analysis(piv, nets, out_dir):
    """Pre-registered: per-network ASDR advantage vs chokepoint census."""
    adv, choke, names = [], [], []
    for net in nets:
        sub = piv.xs(net.name, level="network")
        if "ASDR" in sub and "Decoupled" in sub:
            adv.append(float((sub["Decoupled"] - sub["ASDR"]).mean()))
            choke.append(len(chokepoint_census(net)))
            names.append(net.name)
    res = S.moderator(adv, choke)
    res["per_network"] = [{"network": n, "advantage": a, "chokepoints": c}
                          for n, a, c in zip(names, adv, choke)]
    json.dump(res, open(os.path.join(out_dir, "moderator.json"), "w"), indent=2)
    return res


def write_report(out_dir, cfg, sdf, dec, mod, diag):
    lines = ["# ASDR v2 results", "",
             f"profile: seeds={cfg.n_seeds}, n_train={cfg.train.n_train}, "
             f"Bv={cfg.sim.probe_budget}, Bm={cfg.sim.mitigation_budget}", "",
             "## What each block checks and what the result means", "",
             "**Policy table** -- lower mean CVaR is better; `adv` is the paired "
             "advantage over Decoupled; `p_holm` is the Holm-corrected paired "
             "Wilcoxon p-value. A publishable positive result = ASDR variants "
             "significantly below Decoupled AND UCB after correction.", "",
             sdf.to_string(index=False), ""]
    if dec:
        lines += ["**Coupling decomposition** -- fraction of the ASDR advantage "
                  "attributable to coupling (vs adaptivity alone). v1 reported "
                  f"~2:1; here: {json.dumps(dec, indent=2)}", ""]
    if mod and not np.isnan(mod.get("spearman_rho", float("nan"))):
        lines += ["**Moderator (pre-registered)** -- prediction: advantage rises "
                  "with the ground-truth chokepoint census and vanishes at zero. "
                  f"Spearman rho={mod['spearman_rho']:.3f}, p={mod['p']:.4f}, "
                  f"n={mod['n']} networks. If rho>0 and significant, this is "
                  "mechanism evidence, not just a win.", ""]
    lines += ["**Diagnostics per network** (chokepoint census: if 0, expect a "
              "null on that network -- that is the resolution-threshold "
              "hypothesis doing its job):", "", diag.to_string(index=False), ""]
    open(os.path.join(out_dir, "REPORT.md"), "w").write("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", choices=["synthetic", "willems"], default="synthetic")
    ap.add_argument("--topology", default="scalefree", choices=netgen.FAMILIES)
    ap.add_argument("--profile", default="smoke", choices=["smoke", "full"])
    ap.add_argument("--out", default="results")
    ap.add_argument("--n-jobs", type=int, default=1)
    ap.add_argument("--willems-file")
    ap.add_argument("--willems-map")
    ap.add_argument("--chains", help="comma list of chain ids, e.g. 1,5,38")
    ap.add_argument("--overlay", default="community", choices=["community", "classification"])
    ap.add_argument("--overlay-seeds", type=int, default=3)
    ap.add_argument("--strict-conjunctive", action="store_true")
    ap.add_argument("--n-eval-nets", type=int, default=None,
                    help="synthetic: number of evaluation networks per family "
                    "(default: 12 full, 2 smoke). Networks are the replication "
                    "units; seeds are nested within networks.")
    ap.add_argument("--seeds-per-net", type=int, default=None,
                    help="seeds per evaluation network (default: 8 full, 3 smoke)")
    ap.add_argument("--lam", type=float, default=0.0,
                    help="latent attribute dispersion (0 = original public-"
                    "attribute environment; assignment hidden until probed)")
    ap.add_argument("--pilot", action="store_true",
                    help="H1 kill-test: evaluate None + Oracle only, no "
                    "training, prints registered gates G1 (ceilings open) and "
                    "G2 (split-half reliability >= 0.5)")
    ap.add_argument("--min-nodes", type=int, default=30,
                    help="skip Willems chains smaller than this (small chains "
                    "have few latent tiers, so discovery has little to find)")
    ap.add_argument("--inspect", action="store_true")
    ap.add_argument("--learning-curve", action="store_true")
    ap.add_argument("--skip-voi", action="store_true",
                    help="skip the expensive ASDR-VOI lookahead policy")
    args = ap.parse_args()
    print("[asdr2 runner r9 | lambda-latent-attributes | pilot gates]",
          flush=True)

    cfg = make_profile(args.profile)
    cfg.n_jobs = args.n_jobs
    os.makedirs(args.out, exist_ok=True)

    if args.dataset == "willems":
        import data_willems as W
        if args.inspect:
            W.inspect_workbook(args.willems_file, mapping=args.willems_map)
            return
        if not args.willems_file:
            raise SystemExit("--willems-file required (download the public MSOM "
                             "workbook; see README).")
        chains = [int(x) for x in args.chains.split(",")] if args.chains else None
        nets = []
        for os_seed in range(args.overlay_seeds):
            nets += W.load_all_chains(args.willems_file, n_regions=cfg.sim.n_regions,
                                      overlay=args.overlay, overlay_seed=os_seed,
                                      strict_conjunctive=args.strict_conjunctive,
                                      mapping=args.willems_map, chains=chains,
                                      min_nodes=args.min_nodes, lam=args.lam)
        # per-chain seeds are fewer; replication comes from chains x overlays
        cfg.n_seeds = args.seeds_per_net or max(5, cfg.n_seeds // 6)
    else:
        n_ev = args.n_eval_nets or (12 if args.profile == "full" else 2)
        cfg.n_seeds = args.seeds_per_net or (8 if args.profile == "full" else 3)
        nets = []
        for i in range(n_ev):
            net = netgen.generate(cfg.n_nodes, args.topology, cfg.sim.n_regions,
                                  np.random.default_rng(900 + i), lam=args.lam)
            net.name = f"synthetic_{args.topology}_{i:02d}"
            nets.append(net)

    # diagnostics first: know what you are testing on
    diag = pd.DataFrame([network_summary(n) for n in nets]).drop(columns=["chokepoints"])
    diag.to_csv(os.path.join(args.out, "diagnostics.csv"), index=False)
    print(diag.to_string(index=False))

    # training distribution: synthetic, matched family (never the eval networks)
    gen_fn = lambda seed: netgen.generate(
        min(cfg.n_nodes, 400), args.topology, cfg.sim.n_regions,
        np.random.default_rng(seed), lam=args.lam)
    if args.pilot:
        print("[1/3] PILOT: training skipped (None + Oracle need none)")
        trained = {"asdr_theta": [0.0] * 8}
    else:
        print("[1/3] training / tuning (tuning parity enabled)...")
        trained = train_all(gen_fn, cfg)
    json.dump({k: list(map(float, v)) for k, v in trained.items()},
              open(os.path.join(args.out, "trained_params.json"), "w"), indent=2)
    if args.learning_curve:
        json.dump(learning_curve(gen_fn, cfg),
                  open(os.path.join(args.out, "learning_curve.json"), "w"), indent=2)

    print("[2/3] evaluation...")
    pilot_skip = ("Random", "Coverage", "Decoupled", "UCB", "ASDR",
                  "ASDR-Interact", "ASDR-VOI")
    df = evaluate(nets, cfg, trained, args.out,
                  skip=pilot_skip if args.pilot
                  else (("ASDR-VOI",) if args.skip_voi else ()))
    if args.pilot:
        pilot_verdict(df, cfg)
        return

    print("[3/3] statistics...")
    sdf, piv, dec = summarise(df, args.out)
    mod = moderator_analysis(piv, nets, args.out) if len(nets) >= 3 else {}
    write_report(args.out, cfg, sdf, dec, mod, diag)
    print(sdf.to_string(index=False))
    if dec:
        if abs(dec["total_adv"]) > 0.005:
            print("coupling decomposition:", dec)
        else:
            print("coupling decomposition: total advantage within noise "
                  f"({dec['total_adv']:+.4f}); fraction not interpretable")
    print(f"done -> {args.out}/REPORT.md")


if __name__ == "__main__":
    main()
