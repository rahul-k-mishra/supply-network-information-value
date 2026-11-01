"""
exp_E_conjecture1.py
====================
Exhaustive test of Conjecture 1 (the general-graph extension of the
identification-premium bound) on miniature instances where category
subtrees SHARE channels -- the exact case Theorem 2a does not cover.

WHY THIS SCRIPT EXISTS
----------------------
Theorem 2a is proved only when the focal categories' subtrees are
node-disjoint.  The paper currently carries the shared-node case as
Conjecture 1: the same bound holds if each shared channel's premium is
counted once per focal category it feeds.  A conjecture sitting in the
theoretical centre of a paper is a liability.  This script does not prove
it, but it does something a referee will accept as evidence: it enumerates
EXACT EVPI on thousands of shared-channel instances and checks whether the
conjectured bound is ever violated.

WHAT COUNTS AS A PASS (state this before you look at the output)
----------------------------------------------------------------
  - violations == 0 over >= 5000 instances
      -> Conjecture 1 keeps its label but gains mechanical support on the
         same footing as Theorem 2a's verification; say exactly that
  - violations > 0
      -> BETTER OUTCOME THAN IT LOOKS.  The script prints the smallest
         counterexample.  A counterexample turns a conjecture into a
         negative result you can state precisely: the multiplicity rule
         fails, here is the structure that breaks it.  Send it to me and
         the paper says so.

  python exp_E_conjecture1.py --n-instances 5000 --seed 20260812

Output: console summary + exp_E_conjecture1.csv, and, if any violation
occurs, exp_E_counterexample.txt with the full instance written out.

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
  outputs were produced with: none / one named candidate / cut. Subsets:
  none / cut / any nonempty subset T of the candidates at cost
  sum_{i in T} c_i, which includes securing all candidates. The action
  algebra consumes no random numbers, so both modes see the same instances.
  P-S1 is evaluated in legacy mode when --reference names the saved output;
  every console line must match.
  P-S4 and P-S5 are evaluated per run in subsets mode; the registered
  prediction holds only if it passes on all five seeds. A violation is
  slack < -1e-9, as in the original script; P-S5 passes if |min slack| <=
  1e-9. Because an instance with bound 0 and EVPI 0 has slack 0 trivially,
  the minimum slack over instances with a positive bound is also printed,
  as a diagnostic.
"""
import argparse
import itertools
import sys

import numpy as np
import pandas as pd



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


def compare_reference(path, skip_prefixes=()):
    """P-S1: compare the recorded core lines with a saved console output,
    ignoring lines whose content is wall-clock time."""
    with open(path) as fh:
        ref = fh.read().splitlines()
    keep = lambda lines: [l for l in lines
                          if not any(l.startswith(p) for p in skip_prefixes)]
    got, want = keep(_CORE), keep(ref)
    diffs = [(i, w, g) for i, (w, g) in
             enumerate(zip(want + [None] * (len(got) - len(want)),
                           got + [None] * (len(want) - len(got))))
             if w != g]
    return (not diffs), diffs

def make_instance(rng):
    """K focal categories fed by C channels; sharing is forced by
    assigning at least one channel to more than one category."""
    K = int(rng.integers(2, 4))
    C = int(rng.integers(2, 4))
    chans = []
    for _ in range(C):
        m = int(rng.integers(2, 4))
        chans.append(dict(
            m=m,
            q=np.round(rng.uniform(0.05, 0.55, size=m), 3),
            c=np.round(rng.uniform(0.5, 2.0, size=m), 2),
            cv=round(float(rng.uniform(1.0, 4.0)), 2),
            prior=rng.dirichlet(np.ones(m) * float(rng.choice([1.0, 4.0]))),
        ))
    # feed map: every category gets >=1 channel, and channel 0 feeds >=2
    feeds = [set() for _ in range(C)]
    for k in range(K):
        for c in range(C):
            if rng.random() < 0.55:
                feeds[c].add(k)
    for k in range(K):                       # no orphan category
        if not any(k in f for f in feeds):
            feeds[int(rng.integers(0, C))].add(k)
    feeds[0] = set(range(K)) if K > 1 else feeds[0]   # force real sharing
    B = round(float(rng.uniform(1.0, 5.0)), 2)
    return dict(K=K, C=C, chans=chans, feeds=feeds, B=B)


def actions(ch, algebra="subsets"):
    """algebra="legacy" is the original list, unchanged in content and
    order: none / one named candidate / cut. algebra="subsets": none / cut /
    any nonempty subset of the candidates at the summed cost, which includes
    securing all of them."""
    m, q, c, cv = ch["m"], ch["q"], ch["c"], ch["cv"]
    acts = [("none", 0.0, lambda th, q=q: float(q[th]))]
    if algebra == "legacy":
        for i in range(m):
            acts.append((f"cand{i}", float(c[i]),
                         lambda th, i=i, q=q: 0.0 if th == i else float(q[th])))
        acts.append(("cut", cv, lambda th: 0.0))
    elif algebra == "subsets":
        acts.append(("cut", cv, lambda th: 0.0))
        for r in range(1, m + 1):
            for T in itertools.combinations(range(m), r):
                acts.append(("cand" + "".join(map(str, T)),
                             float(sum(c[i] for i in T)),
                             lambda th, T=frozenset(T), q=q:
                             0.0 if th in T else float(q[th])))
    else:
        raise ValueError(f"unknown action algebra {algebra!r}")
    return acts


def exact_evpi(inst, algebra="subsets"):
    K, C, chans, feeds, B = (inst["K"], inst["C"], inst["chans"],
                             inst["feeds"], inst["B"])
    acts = [actions(c, algebra) for c in chans]
    thetas = list(itertools.product(*[range(c["m"]) for c in chans]))
    pri = np.array([np.prod([chans[c]["prior"][t[c]] for c in range(C)])
                    for t in thetas])
    plans = [p for p in itertools.product(*acts)
             if sum(a[1] for a in p) <= B + 1e-12]

    J = np.empty((len(plans), len(thetas)))
    for pi, plan in enumerate(plans):
        for ti, th in enumerate(thetas):
            f = [plan[c][2](th[c]) for c in range(C)]
            tot = 0.0
            for k in range(K):
                surv = 1.0
                for c in range(C):
                    if k in feeds[c]:
                        surv *= (1.0 - f[c])
                tot += 1.0 - surv
            J[pi, ti] = tot / K
    A = float((J @ pri).min())
    EM = float((J.min(axis=0) * pri).sum())
    return A - EM


def conjectured_bound(inst, algebra="subsets"):
    """(1/K) * sum_c |F(c)| * I_c, with I_c the isolated-channel premium."""
    K, C, chans, feeds, B = (inst["K"], inst["C"], inst["chans"],
                             inst["feeds"], inst["B"])
    total = 0.0
    per = []
    for c in range(C):
        ch, acts = chans[c], actions(chans[c], algebra)
        breaks = sorted({a[1] for a in acts if a[1] <= B + 1e-12})
        prem = 0.0
        for th in range(ch["m"]):
            best = 0.0
            for b in breaks:
                feas = [a for a in acts if a[1] <= b + 1e-12]
                v_inv = min(sum(ch["prior"][t] * a[2](t)
                                for t in range(ch["m"])) for a in feas)
                v_full = min(a[2](th) for a in feas)
                best = max(best, v_inv - v_full)
            prem += ch["prior"][th] * best
        per.append(prem)
        total += len(feeds[c]) * prem
    return total / K, per


def dump(inst, evpi, bound, path):
    with open(path, "w") as fh:
        fh.write(f"EVPI = {evpi!r}\nbound = {bound!r}\n")
        fh.write(f"K={inst['K']} C={inst['C']} B={inst['B']}\n")
        fh.write(f"feeds={[sorted(f) for f in inst['feeds']]}\n")
        for i, ch in enumerate(inst["chans"]):
            fh.write(f"channel {i}: m={ch['m']} q={list(ch['q'])} "
                     f"c={list(ch['c'])} cv={ch['cv']} "
                     f"prior={[round(float(x), 4) for x in ch['prior']]}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-instances", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=20260812)
    ap.add_argument("--actions", choices=("subsets", "legacy"),
                    default="subsets",
                    help="per-channel action algebra (see docstring)")
    ap.add_argument("--reference", default=None,
                    help="saved console output to compare against (P-S1)")
    a = ap.parse_args()
    print_predictions()
    print(f"action algebra: {a.actions}\n", flush=True)

    rng = np.random.default_rng(a.seed)
    rows, worst, worst_inst = [], None, None
    for n in range(a.n_instances):
        inst = make_instance(rng)
        evpi = exact_evpi(inst, a.actions)
        bound, per = conjectured_bound(inst, a.actions)
        slack = bound - evpi
        rows.append(dict(instance=n, K=inst["K"], C=inst["C"],
                         shared=sum(1 for f in inst["feeds"] if len(f) > 1),
                         evpi=evpi, bound=bound, slack=slack,
                         ratio=evpi / bound if bound > 1e-12 else np.nan))
        if worst is None or slack < worst:
            worst, worst_inst = slack, inst

    df = pd.DataFrame(rows)
    viol = df[df["slack"] < -1e-9]
    out(f"instances          : {a.n_instances}  (seed {a.seed})")
    out(f"shared-channel inst: {int((df['shared'] > 0).sum())}")
    out(f"bound violations   : {len(viol)}")
    out(f"min slack          : {df['slack'].min():+.6f}")
    nz = df[df["bound"] > 1e-12]
    if len(nz):
        out(f"tightness EVPI/bound: mean {nz['ratio'].mean():.3f}  "
              f"max {nz['ratio'].max():.3f}")
    if len(viol):
        dump(worst_inst, exact_evpi(worst_inst, a.actions),
             conjectured_bound(worst_inst, a.actions)[0],
             "exp_E_counterexample.txt")
        out("COUNTEREXAMPLE written to exp_E_counterexample.txt -- send it")
    df.to_csv("exp_E_conjecture1.csv", index=False)
    out("wrote exp_E_conjecture1.csv")

    # ------------------------------------------------------------------
    # Evaluation of the registered predictions for this run.
    # ------------------------------------------------------------------
    min_slack = float(df["slack"].min())
    pos = df[df["bound"] > 1e-12]
    min_slack_pos = float(pos["slack"].min()) if len(pos) else float("nan")
    print("\nPREDICTION EVALUATION (this run: seed "
          f"{a.seed}, actions {a.actions})", flush=True)
    print("  P-S2, P-S3: belong to exp_A_idx_vs_evppi.py")
    if a.actions == "legacy":
        if a.reference:
            ok, diffs = compare_reference(a.reference)
            print(f"  P-S1: {'PASS' if ok else 'FAIL'}  (vs {a.reference})")
            for i, want, got in diffs:
                print(f"        line {i}: saved   {want!r}")
                print(f"                 now     {got!r}")
        else:
            print("  P-S1: NOT EVALUATED (no --reference given)")
        print("  P-S4, P-S5: not applicable in legacy mode")
    else:
        print("  P-S1: not applicable in subsets mode")
        print(f"  P-S4: {'PASS' if len(viol) == 0 else 'FAIL'}  "
              f"(Conjecture 12 bound violations: {len(viol)})")
        if len(viol):
            print("        COUNTEREXAMPLE: the worst instance is saved in "
                  "exp_E_counterexample.txt; every violating instance is in "
                  "exp_E_conjecture1.csv (slack < -1e-9)")
        print(f"  P-S5: {'PASS' if abs(min_slack) <= 1e-9 else 'FAIL'}  "
              f"(min slack {min_slack:+.3e})")
    print(f"  diagnostic: min slack over instances with bound > 0: "
          f"{min_slack_pos:+.3e} ({len(pos)} instances); "
          f"instances with bound = 0: {len(df) - len(pos)}")
    print("  The cross-seed predictions hold only if every seed passes.",
          flush=True)


if __name__ == "__main__":
    main()
