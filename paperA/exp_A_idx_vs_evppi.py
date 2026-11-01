"""
exp_A_idx_vs_evppi.py
=====================
Benchmarks the identification-premium index (IDX) against EXACT EVPPI,
computed by brute-force enumeration on miniature instances of the
disjoint-category setting of Theorem 2a.

WHY THIS SCRIPT EXISTS
----------------------
The paper calls IDX "a cheap surrogate for EVPPI".  That sentence is not
allowed to stand on assertion.  This script measures three things that a
referee will ask for:

  (1) Conservativeness.  Is IDX_k >= EVPPI_k on every instance?  The theory
      says IDX is an UPPER BOUND, not an estimate, so a single case with
      IDX_k < EVPPI_k falsifies the claim as stated.
  (2) Agreement.  Pearson and Spearman correlation between IDX_k and
      EVPPI_k, plus mean absolute and mean relative error.
  (3) Cost.  Runtime of IDX versus runtime of exact EVPPI.

WHAT COUNTS AS A PASS (state this before you look at the output)
----------------------------------------------------------------
  - violations == 0                      -> the bound claim survives
  - Spearman >= 0.7 and Pearson >= 0.7   -> "surrogate" is a fair word
  - Spearman in [0.3, 0.7)               -> call it "a conservative bound
                                            with moderate rank agreement"
  - Spearman < 0.3                       -> DELETE the word "surrogate"
                                            from the paper; it is a bound
                                            and nothing more

Nothing here reads your result folders; it builds its own instances, so it
runs anywhere with numpy + scipy.

  python exp_A_idx_vs_evppi.py --n-instances 400 --seed 20260812
  python exp_A_idx_vs_evppi.py --n-instances 400 --seed 7   (any seed)

Output: console table + exp_A_idx_vs_evppi.csv (one row per channel).

SUBSET-ALGEBRA PREDICTIONS, registered 2026-11-01 before any run
-----------------------------------------------------------------
  P-S1 (both scripts) legacy mode reproduces the saved console outputs
       expA_s01..s05.txt and expE_s01..s05.txt exactly. This is a correctness
       gate: if it fails, the switch changed the instance stream and nothing
       else means anything.
  P-S2 (exp_A) under subsets, zero cases of premium < EVPPI across all five
       seeds. Corollary 9 proves the bound, so a violation means a defect.
  P-S3 (exp_A) under subsets, Spearman(premium, EVPPI) stays above 0.4 on
       every seed. A drop below that is a reportable weakening of the rank
       agreement the paper claims.
  P-S4 (exp_E) under subsets, zero violations of the Conjecture 12 bound
       across all five seeds. A violation is a COUNTEREXAMPLE and a welcome
       result: report it, do not suppress it, and save the instance.
  P-S5 (exp_E) under subsets, the minimum slack remains zero to machine
       precision, so the bound is still attained.

EVALUATION NOTES (implementation, not part of the registration)
---------------------------------------------------------------
  --actions subsets (default) | legacy. Legacy is the algebra the saved
  outputs were produced with: none / one named candidate / consumer cut /
  all candidates. Subsets: none / consumer cut / any nonempty subset T of
  the candidates at cost sum_{i in T} c_i. The action algebra consumes no
  random numbers, so both modes see the same instances.
  P-S1 is evaluated in legacy mode when --reference names the saved output.
  The two "runtime" lines report wall-clock time and cannot reproduce, so
  they are excluded from the comparison; every other line must match.
  P-S2 and P-S3 are evaluated per run in subsets mode; the registered
  prediction holds only if it passes on all five seeds. Tolerance for a
  violation is 1e-9, as in the original script.

  --tie-tol (added 2026-11-01, after the first runs of the predictions
  above). Many EVPPI and premium values are mathematically equal but differ
  by floating-point residue of order 1e-16, and Spearman breaks such ties by
  the residue, so its 4th decimal depends on arithmetic order and library
  version. Before Spearman, each of the two series is snapped separately:
  values are sorted, and every value within --tie-tol (absolute, default
  1e-12) of the current group's smallest member is replaced by that member.
  Groups are anchored at their smallest member, so they cannot chain beyond
  the tolerance. The original console line ("Spearman r=...") stays the
  unsnapped statistic, so the saved outputs remain comparable; the snapped
  value is printed on a separate line, and P-S1 and P-S3 are evaluated with
  both, labelled.

  SLACK STATISTICS (added 2026-11-01). The original "median relative slack"
  line divides by EVPPI clipped at 1e-6, so the roughly one quarter of
  channels whose EVPPI is zero enter with an arbitrary, clip-determined
  ratio; the statistic is not well defined on them. A separate block reports:
  the count and fraction of channels with |EVPPI| <= --tie-tol; the median
  and quartiles of premium/EVPPI over channels with EVPPI > --tie-tol only;
  and the median and quartiles of premium - EVPPI over all channels, which is
  defined everywhere. The original line is kept, unchanged, for comparison
  with the saved outputs, and is relabelled in the block as not well defined.
"""
import argparse
import itertools
import sys
import time

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr


# ----------------------------------------------------------------------
# Instance generation.  One instance = K independent focal categories,
# each fed by one latent channel with m candidates, exactly one of which
# is the true supplier.
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# Registered predictions: printed at startup, evaluated at the end.
# ----------------------------------------------------------------------
_PRED_HEAD = "SUBSET-ALGEBRA PREDICTIONS, registered 2026-11-01 before any run"
_CORE = []                     # the console lines the original script printed


def out(line):
    """Print a line of the original console output and record it, so that
    legacy mode can be compared line by line with the saved outputs."""
    print(line, flush=True)
    _CORE.append(line)


def print_predictions():
    doc = __doc__
    start = doc.index(_PRED_HEAD)
    end = doc.index("EVALUATION NOTES", start)
    print(doc[start:end].rstrip() + "\n", flush=True)


def snap(x, tol):
    """Replace every value within `tol` of its group's smallest member by
    that member. Groups are formed in sorted order and anchored at their
    first (smallest) value, so they never span more than `tol`."""
    x = np.asarray(x, dtype=float)
    order = np.argsort(x, kind="stable")
    out_ = x.copy()
    anchor = None
    for i in order:
        if anchor is None or x[i] - anchor > tol:
            anchor = x[i]
        out_[i] = anchor
    return out_


def n_tie_groups(x):
    """Number of distinct values shared by more than one element."""
    _, counts = np.unique(np.asarray(x), return_counts=True)
    return int((counts > 1).sum()), int(counts[counts > 1].sum())


def compare_reference(path, skip_prefixes=(), lines=None):
    """P-S1: compare the recorded core lines with a saved console output,
    ignoring lines whose content is wall-clock time."""
    with open(path) as fh:
        ref = fh.read().splitlines()
    keep = lambda lines: [l for l in lines
                          if not any(l.startswith(p) for p in skip_prefixes)]
    got, want = keep(_CORE if lines is None else lines), keep(ref)
    diffs = [(i, w, g) for i, (w, g) in
             enumerate(zip(want + [None] * (len(got) - len(want)),
                           got + [None] * (len(want) - len(got))))
             if w != g]
    return (not diffs), diffs

def make_instance(rng):
    K = int(rng.integers(2, 4))               # 2 or 3 focal categories
    cats = []
    for _ in range(K):
        m = int(rng.integers(2, 4))           # 2 or 3 candidates
        q = np.round(rng.uniform(0.05, 0.60, size=m), 3)   # candidate risks
        c = np.round(rng.uniform(0.5, 2.0, size=m), 2)     # securing costs
        cv = round(float(rng.uniform(1.0, 4.0)), 2)        # consumer-cut cost
        prior = rng.dirichlet(np.ones(m) * float(rng.choice([1.0, 4.0])))
        cats.append(dict(m=m, q=q, c=c, cv=cv, prior=prior))
    B = round(float(rng.uniform(1.0, 5.0)), 2)             # total budget
    return dict(K=K, cats=cats, B=B)


def actions(cat, algebra="subsets"):
    """Every action available for one category: (label, cost, risk_fn).

    risk_fn(theta) is the resulting starvation probability of that category
    when the true supplier is candidate `theta`.

    algebra="legacy" is the original list, unchanged in content and order:
    none / one named candidate / consumer cut / all candidates.
    algebra="subsets": none / consumer cut / any nonempty subset of the
    candidates, at the summed cost.
    """
    m, q, c, cv = cat["m"], cat["q"], cat["c"], cat["cv"]
    acts = [("none", 0.0, lambda th, q=q: float(q[th]))]
    if algebra == "legacy":
        for i in range(m):
            acts.append((f"cand{i}", float(c[i]),
                         lambda th, i=i, q=q: 0.0 if th == i else float(q[th])))
        acts.append(("consumer", cv, lambda th: 0.0))
        acts.append(("all", float(c.sum()), lambda th: 0.0))
    elif algebra == "subsets":
        acts.append(("consumer", cv, lambda th: 0.0))
        for r in range(1, m + 1):
            for T in itertools.combinations(range(m), r):
                acts.append(("cand" + "".join(map(str, T)),
                             float(sum(c[i] for i in T)),
                             lambda th, T=frozenset(T), q=q:
                             0.0 if th in T else float(q[th])))
    else:
        raise ValueError(f"unknown action algebra {algebra!r}")
    return acts


# ----------------------------------------------------------------------
# Exact quantities by enumeration.  No sampling, no approximation.
# ----------------------------------------------------------------------
def exact_quantities(inst, algebra="subsets"):
    K, cats, B = inst["K"], inst["cats"], inst["B"]
    acts = [actions(c, algebra) for c in cats]
    thetas = list(itertools.product(*[range(c["m"]) for c in cats]))
    pri = np.array([np.prod([cats[k]["prior"][t[k]] for k in range(K)])
                    for t in thetas])

    plans = [p for p in itertools.product(*acts)
             if sum(a[1] for a in p) <= B + 1e-12]

    # j(plan, theta) = mean starvation probability over categories
    J = np.empty((len(plans), len(thetas)))
    for pi, plan in enumerate(plans):
        for ti, th in enumerate(thetas):
            J[pi, ti] = sum(plan[k][2](th[k]) for k in range(K)) / K

    prior_val = float((J @ pri).min())                 # A  = min_S E_theta j
    full_val = float((J.min(axis=0) * pri).sum())      # EM = E_theta min_S j
    evpi = prior_val - full_val

    # EVPPI for channel k: learn theta_k only, everything else stays prior
    evppi = []
    for k in range(K):
        tot = 0.0
        for tk in range(cats[k]["m"]):
            mask = np.array([t[k] == tk for t in thetas])
            w = pri[mask]
            if w.sum() <= 0:
                continue
            cond = w / w.sum()
            tot += w.sum() * float((J[:, mask] @ cond).min())
        evppi.append(prior_val - tot)
    return evpi, np.array(evppi), prior_val, full_val


def index_premiums(inst, algebra="subsets"):
    """IDX_k = I_k / K, with I_k the Theorem 2a identification premium.

    Uses only prior-available information: candidate risk population,
    costs, prior weights.  It never looks at the realised theta except
    through the prior expectation, exactly as the paper claims.
    """
    K, cats, B = inst["K"], inst["cats"], inst["B"]
    idx = []
    for cat in cats:
        acts = actions(cat, algebra)
        breaks = sorted({a[1] for a in acts if a[1] <= B + 1e-12})
        prior = cat["prior"]
        prem = 0.0
        for th in range(cat["m"]):
            best = 0.0
            for b in breaks:
                feas = [a for a in acts if a[1] <= b + 1e-12]
                v_inv = min(sum(prior[t] * a[2](t) for t in range(cat["m"]))
                            for a in feas)
                v_full = min(a[2](th) for a in feas)
                best = max(best, v_inv - v_full)
            prem += prior[th] * best
        idx.append(prem / K)
    return np.array(idx)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-instances", type=int, default=400)
    ap.add_argument("--seed", type=int, default=20260812)
    ap.add_argument("--actions", choices=("subsets", "legacy"),
                    default="subsets",
                    help="per-category action algebra (see docstring)")
    ap.add_argument("--tie-tol", type=float, default=1e-12,
                    help="absolute tolerance for snapping near-tied values "
                         "before Spearman (see docstring)")
    ap.add_argument("--reference", default=None,
                    help="saved console output to compare against (P-S1)")
    a = ap.parse_args()
    print_predictions()
    print(f"action algebra: {a.actions}\n", flush=True)

    rng = np.random.default_rng(a.seed)
    rows = []
    t_idx = t_exact = 0.0

    for n in range(a.n_instances):
        inst = make_instance(rng)

        t0 = time.perf_counter()
        evpi, evppi, prior_val, full_val = exact_quantities(inst, a.actions)
        t_exact += time.perf_counter() - t0

        t0 = time.perf_counter()
        idx = index_premiums(inst, a.actions)
        t_idx += time.perf_counter() - t0

        for k in range(inst["K"]):
            rows.append(dict(instance=n, channel=k, K=inst["K"],
                             m=inst["cats"][k]["m"], budget=inst["B"],
                             evppi=evppi[k], idx=idx[k],
                             evpi_total=evpi, bound_total=idx.sum()))

    df = pd.DataFrame(rows)
    df["violation"] = df["idx"] < df["evppi"] - 1e-9
    tot = df.groupby("instance").first()
    tot_viol = int((tot["bound_total"] < tot["evpi_total"] - 1e-9).sum())

    out(f"instances                : {a.n_instances}  (seed {a.seed})")
    out(f"channels                 : {len(df)}")
    out(f"per-channel violations   : {int(df['violation'].sum())}"
          "   (IDX_k < EVPPI_k; must be 0)")
    out(f"whole-instance violations: {tot_viol}"
          "   (sum IDX < EVPI; must be 0)")

    nz = df[(df["evppi"] > 1e-9) | (df["idx"] > 1e-9)]
    sr = srs = rel = None
    if len(nz) > 2:
        pr, pp = pearsonr(nz["idx"], nz["evppi"])
        sr, sp = spearmanr(nz["idx"], nz["evppi"])
        idx_s = snap(nz["idx"].to_numpy(), a.tie_tol)
        evppi_s = snap(nz["evppi"].to_numpy(), a.tie_tol)
        srs, sps = spearmanr(idx_s, evppi_s)
        tie_info = dict(
            raw_evppi=n_tie_groups(nz["evppi"]), raw_idx=n_tie_groups(nz["idx"]),
            snap_evppi=n_tie_groups(evppi_s), snap_idx=n_tie_groups(idx_s),
            max_shift=float(max(np.abs(idx_s - nz["idx"].to_numpy()).max(),
                                np.abs(evppi_s - nz["evppi"].to_numpy()).max())))
        mae = float((nz["idx"] - nz["evppi"]).abs().mean())
        rel = float(((nz["idx"] - nz["evppi"]) /
                     nz["evppi"].clip(lower=1e-6)).median())
        out(f"non-degenerate channels  : {len(nz)}")
        out(f"Pearson  r={pr:+.4f}  p={pp:.2e}")
        out(f"Spearman r={sr:+.4f}  p={sp:.2e}")
        out(f"MAE                      : {mae:.5f}")
        out(f"median relative slack    : {rel:+.3f}  "
              "(0 = tight, >0 = conservative)")
    else:
        out("too few non-degenerate channels to correlate")

    out(f"runtime exact EVPPI      : {t_exact:.2f}s")
    out(f"runtime IDX              : {t_idx:.2f}s"
          f"   speedup x{t_exact / max(t_idx, 1e-9):.1f}")

    df.to_csv("exp_A_idx_vs_evppi.csv", index=False)
    out("wrote exp_A_idx_vs_evppi.csv")

    if srs is not None:
        print(f"\nSpearman, tie-snapped (tol={a.tie_tol:g}): r={srs:+.4f}  "
              f"p={sps:.2e}   [unsnapped r={sr:+.4f}; "
              f"difference {srs - sr:+.4f}]")
        print(f"  tie groups (groups/values) EVPPI: raw "
              f"{tie_info['raw_evppi'][0]}/{tie_info['raw_evppi'][1]} -> snapped "
              f"{tie_info['snap_evppi'][0]}/{tie_info['snap_evppi'][1]}; "
              f"premium: raw {tie_info['raw_idx'][0]}/{tie_info['raw_idx'][1]}"
              f" -> snapped {tie_info['snap_idx'][0]}/{tie_info['snap_idx'][1]};"
              f" largest value shift {tie_info['max_shift']:.2e}", flush=True)

    # ------------------------------------------------------------------
    # Slack statistics that are well defined on every channel they cover.
    # Printed outside the original console block, which is unchanged.
    # ------------------------------------------------------------------
    e = df["evppi"].to_numpy()
    prem = df["idx"].to_numpy()
    tol = a.tie_tol
    zero = np.abs(e) <= tol
    pos = e > tol
    neg = e < -tol
    print(f"\nSLACK STATISTICS (all {len(df)} channels; 'EVPPI zero' means "
          f"|EVPPI| <= tie-tol = {tol:g})")
    print(f"  channels with EVPPI zero          : {int(zero.sum())} "
          f"({zero.mean():.3f} of all channels)")
    if neg.any():
        print(f"  WARNING: {int(neg.sum())} channels with EVPPI < -tie-tol "
              "(negative beyond residue; EVPPI should be >= 0)")
    if pos.any():
        ratio = prem[pos] / e[pos]
        q1, med, q3 = np.percentile(ratio, [25, 50, 75])
        print(f"  premium/EVPPI, EVPPI > 0 only     : median {med:.3f}  "
              f"quartiles [{q1:.3f}, {q3:.3f}]  (n={int(pos.sum())})")
    diff = prem - e
    d1, dmed, d3 = np.percentile(diff, [25, 50, 75])
    print(f"  premium - EVPPI, all channels     : median {dmed:.5f}  "
          f"quartiles [{d1:.5f}, {d3:.5f}]  (n={len(diff)})")
    if rel is not None:
        n_zero_nz = int((nz["evppi"].abs() <= tol).sum())
        print(f"  OLD STATISTIC, NOT WELL DEFINED   : median relative slack "
              f"{rel:+.3f} (premium/EVPPI {1 + rel:.3f}) over {len(nz)} "
              f"non-degenerate channels, {n_zero_nz} of which have EVPPI zero "
              "and enter with EVPPI clipped to 1e-6", flush=True)

    # ------------------------------------------------------------------
    # Evaluation of the registered predictions for this run.
    # ------------------------------------------------------------------
    n_chan_viol = int(df["violation"].sum())
    print("\nPREDICTION EVALUATION (this run: seed "
          f"{a.seed}, actions {a.actions})", flush=True)
    if a.actions == "legacy":
        if a.reference:
            ok, diffs = compare_reference(a.reference,
                                          skip_prefixes=("runtime",))
            print(f"  P-S1: {'PASS' if ok else 'FAIL'}  (vs {a.reference};"
                  " runtime lines excluded)")
            for i, want, got in diffs:
                print(f"        line {i}: saved   {want!r}")
                print(f"                 now     {got!r}")
            if srs is not None:
                alt = [f"Spearman r={srs:+.4f}  p={sps:.2e}"
                       if l.startswith("Spearman r=") else l for l in _CORE]
                ok2, diffs2 = compare_reference(a.reference,
                                                skip_prefixes=("runtime",),
                                                lines=alt)
                print(f"  P-S1 with the tie-snapped Spearman substituted: "
                      f"{'PASS' if ok2 else 'FAIL'}")
                for i, want, got in diffs2:
                    print(f"        line {i}: saved   {want!r}")
                    print(f"                 now     {got!r}")
        else:
            print("  P-S1: NOT EVALUATED (no --reference given)")
        print("  P-S2, P-S3: not applicable in legacy mode")
    else:
        print("  P-S1: not applicable in subsets mode")
        print(f"  P-S2: {'PASS' if n_chan_viol == 0 else 'FAIL'}  "
              f"(per-channel premium < EVPPI cases: {n_chan_viol}; "
              f"whole-instance: {tot_viol})")
        if sr is None:
            print("  P-S3: FAIL  (too few non-degenerate channels to compute"
                  " Spearman)")
        else:
            print(f"  P-S3: {'PASS' if sr > 0.4 else 'FAIL'}  "
                  f"(Spearman {sr:+.4f}; threshold 0.4)")
            print(f"  P-S3 with the tie-snapped Spearman: "
                  f"{'PASS' if srs > 0.4 else 'FAIL'}  (Spearman {srs:+.4f})")
    print("  P-S4, P-S5: belong to exp_E_conjecture1.py")
    print("  The cross-seed predictions hold only if every seed passes.",
          flush=True)


if __name__ == "__main__":
    main()
