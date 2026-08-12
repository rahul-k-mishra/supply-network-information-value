# Zero-value conditions and identification-premium bounds

Code and archived results for the paper *The Decision Value of Hidden
Supply-Network Structure: Zero-Value Conditions and Identification-Premium
Bounds*.

Every number in the paper regenerates from this repository together with the
public Willems dataset (see `data/README_DATA.md`). `MANIFEST.sha256` lists
every file with its digest.

## Layout

    *.py                       model, planner, runner, verifier
    exp_*.py, make_*.py        the paper's experiments and figures
    results_*_FROZEN/          the archived result files every reported
                               measurement was computed from
    results_sweep_lam*/        the dispersion sweep, one folder per lambda
    logs/                      console output of each reported run
    figures/                   figures as generated
    data/                      where to place the third-party dataset

## Reproducing the paper

Install dependencies, then:

    python make_figures.py --lam0-willems results_willems_FROZEN/results_raw.csv --lam0-syn results_scalefree_v2_FROZEN/results_raw.csv --pilot-willems results_pilot_willems_FROZEN/results_raw_willems.csv --pilot-syn results_pilot_syn_FROZEN/results_raw.csv --per-net
    python exp_A_idx_vs_evppi.py --n-instances 2000 --seed 20260812
    python exp_E_conjecture1.py --n-instances 20000 --seed 20260812
    python exp_F_planner_gaps.py --n-instances 2000 --seed 20260812
    python exp_B_breakeven.py --ceilings results_willems_FROZEN/results_raw.csv --pilot results_pilot_willems_FROZEN/results_raw_willems.csv --value 100e6

Each script states, in its header and before any output, the values its run
must reproduce or the criteria its result must meet. `exp_A`, `exp_E` and
`exp_F` are self-contained and need no data download.

Re-running the network experiments from scratch additionally requires the
Willems workbook:

    python run_experiment.py --dataset willems --willems-file data/chain_data.xlsx --pilot --lam 0.8 --chains 7,9,11,14,17,18,19,21 --overlay-seeds 3 --seeds-per-net 8 --min-nodes 30 --skip-voi --out results_new

## Determinism

Seeds derive from a stable checksum of the instance identifier rather than
from a process-salted hash, so reported figures regenerate exactly. The
verification pipeline was reproduced on an independent machine.

## Preprocessing

`logs/excluded3.txt` shows the six benchmark chains excluded by the
minimum-cone-size rule and their sizes, which is the provenance for the
preprocessing table in the paper.
