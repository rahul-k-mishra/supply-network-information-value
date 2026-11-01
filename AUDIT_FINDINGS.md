# AUDIT_FINDINGS — SNIV manuscript, pre-transfer

Target: `paper/springer/annals_of_operation_research/asdr_paper_springer/main.tex` (2038 lines) and its `main.pdf` (34 pp., built 2026-08-12 19:40). The root-level `main.tex` is a different, older draft (1361 lines) and was **not** audited.
Audit date: 2026-11-01. Nothing in main.tex, the scripts or the `*_FROZEN` folders was modified. All re-runs were done in a scratch directory outside the project, via symlinks to the read-only evidence.

## Preliminary notes on the brief itself

- **No project instruction file exists** in the project. The audit followed AUDIT_BRIEF.md alone.
- **There is no `logs/` folder in the working directory.** Console captures exist as root-level `exp*_s0*.txt`, `expB_100m.txt`, `witness.txt` and others. A `logs/` folder (34 files) exists only inside `asdr_repo.zip` and the GitHub clone, and even there it is incomplete (see F-15). Under the brief's strict standard, every number not in a `*_FROZEN` file is therefore untraceable. Below I trace to the best available capture and flag the gap.
- **The brief's theorem numbering does not match the PDF.** The PDF uses one shared counter:
  - Prop 1 = H relation; Lemma 2 = garbling; Prop 3 = Bernoulli CVaR; Thm 4 = zero value; Cor 5 = law-invariant; Thm 6 = premium bound (S1–S10); Cor 7 = dilution; Prop 8 = witness; Cor 9 = per-channel; Prop 10 = dispersion; Prop 11 = CVaR transfer; Conjecture 12 = shared subtrees.
  - "Propositions 2, 5, 9" and "Corollaries 2, 3, 8" in the brief do not exist under those labels. I audited **every** numbered result by name (§3).
- Environments used:
  - "new": the project `.venv`, numpy 2.5.4 / pandas 3.1.0 / scipy 1.18.1 (= `env_ubuntu_20261031.txt`).
  - "old": a scratch venv, numpy 1.26.4 / pandas 2.2.3 / scipy 1.11.4 / matplotlib 3.8.4.
- Scope 4 (references) was carried out as a separate check using Crossref, PMLR, arXiv, MIT CTL, RePEc, JAIR and the author PDFs. Taylor & Francis, Springer, Wiley and INFORMS pages returned 403, so several full texts were **not** read (stated per item in §4).

---

## Findings, ordered by severity

### F-01 | BLOCKER | §3 l.99–101, l.299–302, l.356–365, l.1158–1161; Table 2; `run_experiment.py:60`, `policies.py:224–233`, `simcore.py:303–315`
- **Claimed:** H compares "the plans returned by the implemented planner given the prior and given θ". "The informed planner is handed θ outright." "Neither EVPI nor H involves probing … no probe parameter enters any number reported below."
- **Evidence:** the policy subtracted in every reported H (`piv["None"] - piv["Oracle"]`) is `OraclePolicy`. It is a **probing** policy. It spends `probe_budget = 9` probes (config.py:22), chosen in a truth-informed order (`_oracle_rank`). Each probe returns an observation through the noisy asymmetric channel (`rho_p = 0.9`, `FP_RATE = 0.02`, simcore.py:151–175). The plan is then built by `plan_mitigation` from the **posterior** belief. θ is never passed to the planner. So the reported "H" is the value of a particular, infeasible, truth-guided 9-probe acquisition policy, not the oracle advantage of eq. (H). B_v, ρ_p and the false-positive rate all enter every measured number.
- **Consequences:**
  - Prop 1's identity does not apply to the measured quantity.
  - The §8.7 calibration (where the enumeration's informed planner really is handed θ) does not transfer, even before the CVaR/expected-loss caveat.
  - By Lemma 2, an exact planner with this policy would be ≤ EVPI. With the heuristic, the sign is unknown in a different way from the one stated.
- **How checked:** read `run_experiment.py:36–61,128–133`, `policies.py:224–233`, `simcore.py:140–175,303–320`, `config.py:20–23`. `results_willems_FROZEN/REPORT.md` header "profile: … Bv=9".
- **Fix:** either re-run with a planner that receives the true structure (`plan_mitigation` on `net.suppliers`, `rate_known` = truth), or redefine and rename the measured quantity as the value of the Oracle *probing* policy. Then rewrite §3.1, Table 2, §8.1–8.8, the abstract and the conclusion accordingly, and delete every "no probe parameter enters" sentence.

### F-02 | BLOCKER | §3 "Network"/"Uncertainty" l.281–296; §10 item (10); `simcore.py:263–297, 74–112, 183–209`
- **Claimed:** "exactly one candidate actually supplies the category". "The model therefore contains no concurrently multi-sourced category, and dual sourcing … lies outside it." θ selects one candidate in C_{v,k}, under a prior π over that choice.
- **Evidence:** in the implemented model:
  - The true networks carry 1,664 non-focal categories with ≥2 true suppliers (exp_G census, below). `cascade_loss` ORs over all of them (`any_sup |= op[u]`), so these are concurrently multi-sourced.
  - The belief is **independent Bernoulli edge-existence** over true suppliers plus `n_decoys = 2` decoys per (node, category) (build_belief, l.273–284). There is no single-supplier prior.
  - Posterior samples draw 1 **or 2** suppliers per category (`k = 1 if rng.random() < q1 … else 2`, l.201).
  - `PHANTOM` suppliers are added for unprobed nodes.
  - None of this is the model in §3, so no theorem in §4–5 is about the measured problem.
- **How checked:** code reading as cited, plus `exp_G_h2_witness.py` output (`witness.txt`, reproduced in scratch `run/G.txt`): "latent categories, non-focal: 1664".
- **Fix:** describe the implemented model accurately (multi-sourcing, decoys, edge-wise prior, phantom suppliers), or re-implement the model the paper states. Either way, the claimed scope ("dual sourcing outside the model") must change.

### F-03 | BLOCKER | Abstract l.67–70; §8.3 l.1250–1285; Prop 8 discussion; Table 5 row Prop 8; §10 item (8); `exp_G_h2_witness.py`, `exp_H_reaggregate.py:q2`
- **Claimed:** "88.9% of their categories have a single possible supplier, which bounds how much there was to find". These categories "carry nothing to identify … zero by construction". The witness conditions are "read off the public graph and cost vector"; 47 categories (2.8%) satisfy them.
- **Evidence:** the census counts `len(net.suppliers[v][k])`, the **true** supplier list, not the candidate pool the planner faces.
  - In the pipeline, every non-focal category of a single-supplier node has that supplier plus 2 decoys in the belief. All 13,313 "single possible supplier" categories therefore *do* carry an identification problem for the measured planners (is the edge real, or a decoy?).
  - The 1,664 "latent" categories are the truly multi-sourced ones, i.e. real redundancy, not epistemic candidate sets.
  - Condition (i) "sole consumer" is evaluated on true consumers (`cons` built from `net.suppliers`), which by the paper's own model is latent, not public.
  - The abstract's "which bounds how much there was to find" and §8.3's explanation of the zero mass ("What does explain a large part of the observed concentration is candidate multiplicity") are therefore unsupported. The second is also a causal claim drawn from a census, with no analysis linking it to H.
- **How checked:** `exp_G_h2_witness.py` and `exp_H_reaggregate.py` re-run (scratch `run/G.txt`, `run/H.txt`); output identical to `witness.txt` (13,313 / 1,664 / 106 / 210 / 47). Read `simcore.py:263–284` for the decoy construction.
- **Fix:** recompute the census on the belief's candidate pools (`bel.cat_candidates`), and evaluate (i) on the public candidate graph. Withdraw the abstract sentence and the "explains the concentration" paragraph unless a new analysis supports them.

### F-04 | BLOCKER | §8.6 Table 9 and prose l.1495–1536; §10 item (8); `exp_H_reaggregate.py`, `exp_I_clustered.py`
- **Claimed:**
  - Table 9 values, e.g. chain-level chokepoint census at λ=0, ρ = −0.331, p = 0.065.
  - "None of the pre-specified three reaches significance at either level."
  - K0 chain ρ = −0.329, p = 0.066; H·K0 chain ρ = −0.258, p = 0.154.
  - Instance-level rows as tabulated.
- **Evidence:** the table is **library-version dependent**. Only the old environment reproduces the paper. Under the project's own current environment (`env_ubuntu_20261031.txt`):

  | λ=0 row | paper (= old env) | new env | parse-independent (true zeros snapped) |
  |---|---|---|---|
  | census, chain | −0.331, p=0.065 | **−0.356, p=0.046** | −0.344, p=0.054 |
  | size, chain | −0.147, 0.421 | −0.185, 0.309 | −0.167, 0.362 |
  | depth, chain | −0.183, 0.315 | −0.192, 0.293 | −0.188, 0.303 |
  | K0, chain | −0.329, 0.066 | −0.347, 0.051 | −0.339, 0.058 |
  | H·K0, chain | −0.258, 0.154 | −0.276, 0.126 | −0.265, 0.143 |
  | census, inst | −0.176, 0.086 | −0.175, 0.087 | −0.182, 0.075 |
  | λ=0.8 size, inst | +0.269, 0.085 | +0.249, 0.112 | +0.272, 0.082 |
  | λ=0.8 H·K0, inst | +0.349, 0.024 | +0.334, 0.031 | +0.347, 0.024 |

  Under the current environment, a pre-specified test reaches p < 0.05, which contradicts the sentence quoted above. The mechanism is F-06: 1-ulp parse noise turns true zeros into ±1e-17 values, which breaks ties in the Spearman ranks.

  Chain-level λ=0.8 rows and the clustered ratios (1.92, 1.96 → two-sided p 0.064, 0.072) are version-stable and verified.
- **How checked:** ran `exp_H_reaggregate.py` and `exp_I_clustered.py` under both environments (scratch `run/H.txt`, `H_old.txt`, `I.txt`, `I_old.txt`). Wrote an independent exact-decimal recomputation (scratch `canon.py`).
- **Fix:** compute H with an explicit tolerance (or exact rational arithmetic) before ranking, pin versions, and re-report Table 9 from the canonical computation. Rewrite "none reaches significance" to report the canonical p = 0.054 honestly as borderline, under six uncorrected tests.

### F-05 | BLOCKER | §8.2 "The two regimes" l.1095–1106; §8.4 sweep l.1344–1418; Table 8 vs Table 6 comparisons; `netgen.py:11–27`, `simcore.py:45–60`, `data_willems.py:284–290`
- **Claimed:** λ only adds a hidden mean-preserving two-point attribute, and the sweep varies λ "with everything else held constant".
- **Evidence:**
  - At λ = 0, node failure rates are the public regional rates `region_p`: 0.015, and 0.08–0.11 in fragile regions.
  - For any λ > 0, `assign_latent_rates` sets `net.node_rate` (base `p_bar = 0.04` for every node, two-point around 0.04 at tier ≥ 2). That **overrides** `region_p` (precedence in `sample_node_failures`). So λ = 0 → 0.2 also removes all regional rate heterogeneity and changes the baseline rate.
  - The two-point law is asymmetric (P(hi) = 1/3, p_hi = p̄(1+2λ), p_lo = p̄(1−λ)), not the equal-probability ± family of Def. 4 / §8.2 wording. At λ = 1, p_lo is clamped to 1e−4, so the law is not exactly mean-preserving.
  - This is a plausible explanation of the "dip from 0.0063 at λ=0 to 0.0020 at λ=0.2, which we leave unexplained". The paired tests vs λ = 0 compare different disruption models, and the λ=0 vs λ=0.8 contrasts of §8.3–8.4 are confounded.
- **How checked:** code reading as cited.
- **Fix:** re-run the sweep with λ = 0 implemented as `assign_latent_rates(lam=0)`, using the same p̄ and no regional override, or make the λ>0 overlay preserve `region_p`. Describe the asymmetric two-point law accurately. Until then, withdraw all λ=0 vs λ>0 comparisons.

### F-06 | MAJOR (scope 2) | `make_figures.py:34,37,40,47` (same pattern in `exp_H_reaggregate.py:64–69`, `exp_I_clustered.py`); Table 6 "exact zeros 24"; §8.3 "A quarter … exactly zero"; §8.8 "24 of 96"
- **Mechanism (exact):**
  - Line 34, `pd.read_csv(path, keep_default_na=False)`, uses the default C float parser.
  - Under pandas 2.2.3 that parser is not correctly rounded (`xstrtod`): 4,144 of 7,680 cvar values in `results_willems_FROZEN/results_raw.csv` (and 759/1,344, 102/384, 177/768 in the other three files) parse 1 ulp away from Python's `float()`.
  - Under pandas 3.1.0 all values parse correctly rounded (0 differences).
  - Line 37 subtracts `None − Oracle` per seed. Line 40 averages over seeds (`groupby().mean()`). Line 47 tests `per == 0` **exactly**.
  - For instances whose true advantage is 0, the per-seed differences carry representation residue in either case. Whether that residue cancels exactly in the mean then depends on which ulp each value parsed to. numpy itself is not the cause; the pandas parser is.
- **Concrete case (pilot_willems):** `willems_chain24_seed2`. The 16 per-seed differences are, in units of 1/168: −1.5, −1.25, −1, +1.75, 0, 0, +1.75, 0, +0.25, +0.75, +0.25, 0, 0, −1, 0, 0. Their exact sum is 0.
  - pandas 3.1.0: mean = −3.47e−18, so `zeros = 9`.
  - pandas 2.2.3: mean = 0.0, so `zeros = 10`.
  - Even exact-decimal arithmetic on the stored strings gives −3.75e−18, because the generator already wrote residue. Exact `==` is wrong under every version.
- **Same defect in the headline count:** two λ=0 benchmark instances, `willems_chain13_seed1` (+4.2e−18) and `willems_chain33_seed1` (+5.6e−18), are true zeros. Their per-seed differences sum to 0 in exact units, e.g. 0.0125 + 0.00625 − 0.03125 + 0.0125 − 0.00625 + 0.00625 = 0. With a 1e−12 tolerance the counts are **26/96** (not 24) at λ=0 and **10/42** at λ=0.8. There is a clean gap: the smallest genuine nonzero |H| is many orders above 1e−12. The 24 is an artefact under both environments.
- **pilot_syn max:** `synthetic_scalefree_03` has exact value 0.04375 (rational mean 0.04375). The new env parses to 0.043749999999999997 and prints 0.0437. The old env parses 1 ulp high and prints 0.0438. So **yes, it is display rounding only**. 0.0438 (round-half-up of the exact value) is the correct 4-dp figure, and Table 8 is right. The script's `.4f` output simply cannot be trusted at a tie.
- **How checked:** scratch `zeros.py`, `parse.py`, `exact.py`; make_figures.py run under both environments (outputs above).
- **Fix:** replace `per == 0` with `np.isclose(per, 0, atol=1e-12)`, or compute differences in exact rationals (`Fraction`, from the known 1/(16·K0) grid). Pass `float_precision="round_trip"` to read_csv. Correct Table 6 to 26 (27.1%) and §8.8 to "26 of 96", and check the "quarter" wording. Report the λ=0.8 zero count if it is used anywhere.

### F-07 | MAJOR | §3.1 eq. (H), §3.2 "instance is the unit at which H is computed", Prop 1 usage throughout §8
- **Claimed:** H = E_π[j(Ŝ_π;θ)] − E_π[j(Ŝ_θ;θ)], with the expectation over θ ~ π.
- **Evidence:** each instance is one overlay, i.e. one realised θ. The per-instance number is a single-θ difference averaged over seeds and scenarios, not E_π. For a single θ the prior-side gap can be negative, which is why negative instance values (−0.0521, −0.0085, …) appear, and Prop 1's ε_π ≥ 0 does not hold per instance. Instance-level statements of the form "H ≥/≤ EVPI" are not defined.
- **How checked:** `run_experiment.py:310–316` (overlay seeds = instances); results files (negative per-instance H, make_figures `--per-net` output).
- **Fix:** define the per-instance estimand, θ-conditional, separately from eq. (H). State that only averages over overlays estimate H, and with 3 overlays per chain only very noisily.

### F-08 | MAJOR | Table 8 caption l.1300–1304; `results_willems_FROZEN/diagnostics.csv`
- **Claimed:** "the 14 chains with at least four tiers and at most 350 nodes (7, 8, 9, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21, 24)".
- **Evidence:** chain 22 has 254 nodes and max_tier 9, so it satisfies both criteria, but it is absent from `results_pilot_willems_FROZEN`. The stated rule does not reproduce the selection, so either the rule is misdescribed or chain 22 was dropped for an unstated reason.
- **How checked:** diagnostics.csv rows; `cut -d, -f1 results_pilot_willems_FROZEN/results_raw_willems.csv | sort -u`.
- **Fix:** state the true selection rule (and when it was fixed), or run chain 22 and include it.

### F-09 | MAJOR | Abstract l.61 "where it is attained"; Contributions l.142–143; Table 5 row Cor 7 "bound attained"; §6 l.1026–1028; Conclusion l.1765
- **Claimed:** in the dilution special case the bound is attained.
- **Evidence:** Cor 7 gives the exact **premium** I_k, not EVPI = U.
  - In the enumerated dilution (c1) batch, EVPI/U has mean **0.221** (max 1.000). `verify_theorem.py` prints this, but Table 4 omits the mean.
  - Remark 1 states that in the same regime, with c_v ≤ B, the premium is positive while EVPI is zero.
  - So the bound is attained on *some* dilution instances (single affordable interval, cut unaffordable), not in the special case as such. The abstract and conclusion contradict Remark 1.
- **How checked:** re-ran `verify_theorem.py` in scratch (`[c1] … tightness mean=0.221 max=1.000`).
- **Fix:** state the sub-case in which equality holds (e.g. c_u ≤ B < c_v for every category) and report the c1 mean in Table 4.

### F-10 | MAJOR | (H1) sufficient condition l.521–523; Conclusion l.1758–1760, l.1782
- **Claimed:** a sufficient condition for (H1) is that "within every latent category the candidates are exchangeable in operability law, in securing cost and under the prior". "Verifying (H1) reduces to an exchangeability check on candidate sets."
- **Evidence:** read marginally, this is not sufficient for *law* invariance of L. Example: candidates u1 and u2 for (v,k) have the same marginal failure law, but u1 also supplies another category (or sits in a different copula cluster, or has a different upstream subtree). Then the joint law of the starvation indicators, hence the law of L (and under the conjunctive cascade even E L), depends on θ. Sufficiency needs a network automorphism exchanging the candidates together with their upstream subtrees, consumers and cluster labels. "Under the prior" is irrelevant to (H1), which is stated pointwise in θ. The conclusion's first sentence restates the insufficient condition as the theorem's hypothesis.
- **How checked:** derivation (T5 uses (H1) for every ID-free plan; a counterexample can be built with two candidates differing only in a shared downstream consumer).
- **Fix:** state the condition as invariance of the joint law under candidate permutations (an automorphism of the public structure), and correct the conclusion.

### F-11 | MAJOR | Table 9 instance-level rows (λ=0 K0, λ=0 H·K0, λ=0.8 K0)
- **Claimed:**
  - λ=0 K0: ρ = −0.157, p = 0.130
  - λ=0 H·K0: ρ = −0.079, p = 0.440
  - λ=0.8 K0: ρ = +0.218, p = 0.170
- **Evidence:** no environment reproduces these p-values.
  - Old env (`exp_H` Q3): p = 0.125, 0.442 and 0.165.
  - New env: −0.157 / 0.127, −0.075 / 0.467, +0.202 / 0.199.
  - Canonical: −0.166 / 0.106, −0.094 / 0.363, +0.219 / 0.163.
  - These three cells are **untraceable**.
- **How checked:** as F-04.
- **Fix:** regenerate from a single logged run and archive its console output.

### F-12 | MAJOR | §8.2 l.1156–1157 "A leakage audit confirms that the uninformed planner's output does not change when the hidden ground truth is permuted"
- **Evidence:** no code, flag or log implements this. `grep -rni "leak\|permut"` over all `*.py` finds only community-colouring permutations in `data_willems.py`; nothing is in `logs/` or the FROZEN folders.
- **Fix:** add the audit script and its log, or delete the sentence.

### F-13 | MAJOR | §8.9 "Predictions were registered before the corresponding data existed"; §8.4 "registered summary, fixed before the sweep"; App. A "pass criteria … stated in their headers before execution"
- **Evidence:** the only "registration" is the docstrings of editable scripts. They carry no timestamp, hash or external registry, and the script headers have demonstrably been edited after runs. For example, `exp_I_clustered.py` is written around placeholders filled after the run, and `make_figures.py` "re-canonicalized on 2026-08-12". `exp_G_h2_witness.py` still instructs "Quote as: … 2.8% of latent categories provably have zero decision value … by Proposition 5" and "by Theorem 3 that category contributes exactly zero", which is exactly what the paper (correctly) disclaims. Script theorem numbers (Thm 3/5, Cor 7, Prop 5) are stale against the PDF.
- **Fix:** say "pre-specified in the analysis script header" without "registered", or deposit the headers with timestamps (OSF / a git tag dated before the run). Correct the stale headers.

### F-14 | MAJOR (scope 6) | Data and code availability l.1810–1825; App. A "Frozen result files", "Regeneration", "Determinism"
Each sentence was checked against `asdr_repo.zip` and a fresh clone of `github.com/rahul-k-mishra/supply-network-information-value` (single commit `4161907`, no tags):

| Sentence | Finding |
|---|---|
| "…the archived result files from which every reported measurement was computed" | **False.** The sweep inputs (`results_sweep_lam*`) are not frozen and have no digest. The census and correlation numbers depend on the Willems workbook through scripts that are not in the repo (row below). |
| "…the console output of each reported run" | **False.** `logs/` has no output for `verify_theorem.py` (Table 4), `make_figures.py` (Tables 6–8), `exp_G/H/I` (census, Table 9, clustered ratios, paired sweep, H·K0) or the Remark 1 numbers. |
| "…the figure scripts" | **Incomplete.** `make_paper_figures.py`, which writes fig1a/fig1b/fig2_lambda_pilots/fig3 (its own header, l.12), is not in the repo. `exp_G_h2_witness.py`, `exp_H_reaggregate.py` and `exp_I_clustered.py` are also absent. |
| "…a manifest giving the SHA-256 digest of every file in it" | **Fails.** In the GitHub clone, `sha256sum -c MANIFEST.sha256` gives **77 mismatches of 105 entries**; the brief's "78 of 106" is off by one (the repo has 107 files; `LICENSE` is not in the manifest). Cause: CRLF → LF normalisation on push; `tr -d '\r' < local file` reproduces the GitHub digest exactly (e.g. `5266448c…` for results_willems). In the zip (CRLF preserved) the manifest passes 105/105. |
| Appendix A digests | Match the local FROZEN files and the zip copies exactly, but match **none** of the four GitHub copies (GitHub: 5266448c…, d373c1cb…, a951f09b…, 2f921da2…). |
| "Every reported number regenerates deterministically … at the pinned revision" | **False on three counts.** (1) There is no pinned revision: no tag, and the paper gives no commit hash. (2) Results are library-version dependent (F-04, F-06; also the split-half ρ in the make_figures header is −0.037 but reproduces as −0.0365 old / −0.0304 new; the Wilcoxon p at λ=0.4 is 0.021 old / 0.020 new; λ=1.0 is 0.062 / 0.064). (3) Numbers in F-11 regenerate under no environment. |
| `requirements.txt` | Unpinned (`>=` only) and **omits matplotlib**, which `make_figures.py`, `make_fig7.py`, `make_fig8.py`, `verify_theorem.py`, `exp_B`, `exp_D` and `exp_E` all import, so no figure script runs from a clean clone. scipy is also unpinned. The brief's "scipy 1.11 vs 1.18" attribution is only partly right: the dominant cause is the pandas parser (F-06). |
| "One script regenerates every table and figure in Sections 6 and 8 … and prints the values that must be reproduced" | **False.** `make_figures.py` prints only the Table 6/8 summaries and writes fig1a/1b/2a/2b. fig2a/2b are not in the paper; the paper uses `fig2_lambda_pilots.png` from the missing script. It does not produce Tables 4, 7, 9, 10 or 11, or figs 3, 4, 7 and 8. |
| "The verification pipeline reproduced identical reported outputs on an independent machine" (l.1005–1007, l.1870–1871) | Unsupported. There is no log of that run, and this audit shows outputs are not identical across environments. |
| "Re-executing the experiments from scratch reproduces the reported aggregate statistics" | **Not tested** in this audit (hours of compute). `expD_fine.txt` shows that runner invocations previously failed (`--willems-file required`). There is no evidence either way. |
| "Seeds derive from a stable checksum of the instance identifier" | Plausible: zlib.crc32 is used in `train.py` and `compute_index.py`, and per-instance seeds are fixed integers (e.g. 541000+s). Not exhaustively verified. |

- **How checked:** `unzip asdr_repo.zip`; `git clone`; `sha256sum -c`; `grep -c $'\r'`; listings of `logs/`.
- **Fix:** add `.gitattributes` with `* -text` (or regenerate the manifest after LF normalisation and quote LF digests). Tag a release and cite its hash or DOI (e.g. Zenodo). Pin every package, including matplotlib, from `env_ubuntu_20261031.txt`. Commit the missing scripts and every console log, and correct each sentence above.

### F-15 | MAJOR (scope 1) | Numbers not traceable to `*_FROZEN` or a `logs/*.txt` capture
All of these trace only to root-level captures or my re-runs of unarchived scripts:
- Table 4 (6000/0.143/0.985; 2000/0; 2000/0/1.000): reproduced by re-running `verify_theorem.py`, but there is no log. The CSV's first line differs from the archived `verify_tightness.csv` (CRLF).
- Remark 1 (0.112, 66%, 0.216, 40%): **no script prints these.** I reproduced them by replaying `verify_theorem.gen` at seed 20260810: all-cuts-affordable n = 4481, mean 0.112, 66.0% < 0.05; none affordable n = 474, mean 0.216, 39.7%. They are correct, but untraceable. Note also that 1,045 mixed instances (mean 0.240) are omitted from the comparison.
- Census numbers (14,977; 13,313; 88.9%; 1,664; 106; 210; 47; 6.4/12.6/2.8%): root `witness.txt` only; not in the repo `logs/`.
- Clustered ratios 1.92, 1.96, p 0.064, 0.072; instance ratios 2.8, 2.2; SE 0.00038: from exp_I/exp_H output, which is not archived.
- Table 9 entirely; H·K0 statistics in §3 Units (0.020/0/1.012; 0.146/0.018/2.379): from exp_H Q3, not archived.
- Table 10 (sweep) and the paired tests (−0.0043, p 0.028 / 0.108; −0.0036, 0.021 / 0.021; Holm 0.105; Spearman −0.086, p 0.87; max +0.771, p 0.072): reproduced from the non-frozen `results_sweep_lam*`. Root `exp_D_lambda_sweep.csv` matches; there is no paired-test log.
- Table 11 (`exp_F` aggregate over 5 seeds): only per-seed txt captures exist; the 5-seed aggregate (0.0436, 0.0440, 0.00241/0.00205, 0.83/0.54, 0.477, 0.148/0.376, +0.00036, 0.083, −0.0091/+0.0148, 0.971; K-trend +0.0008 → −0.0001 and 0.12 → 0.63) is printed nowhere. I recomputed it from `expF_s0*.csv`: **all match**, but only with a 1e−12 equality tolerance. That tolerance is the opposite of the exact-zero convention used for Table 6 (F-06).
- Remark/§6 EVPPI paragraph (24,981; 0.505–0.516; 0.597–0.615; "≈2.7×") and Conjecture search (100,000; zero minimum slack): match the root `expA_s0*.txt` / `expE_s0*.txt`, which are present in the repo `logs/`. These are traceable.
- Table 12 (money): matches `expB_100m.txt` (0.00/0.42/2.12; 0.04/0.81/9.15). Traceable.
- K0 statistics (2–672, median 52, three chains with K0 = 2): from `witness.txt` sinks counts, not in a FROZEN file.
- "Synthetic n ≈ 977": every one of the 12 synthetic networks has exactly 977 nodes (`results_scalefree_v2_FROZEN/diagnostics.csv`). "About" is unnecessary.
- "Poisson … P(X ≥ 6) about 0.025": computed value 0.0242 → "about 0.024". Expected count 2.18 ✓.
- Conjecture "minimum slack was zero": the observed minimum is −8.3e−17 (91 instances with slack below zero at float level, none below −1e−12). This is fine as float noise but should be stated as "zero to machine precision".

**Verified against FROZEN files (both environments unless noted):**
- Table 6: means, medians, >0.01, frac >0.02, max 0.0212, "six > 2SE". Exact-zero count: see F-06.
- Table 8 (n, medians, means, fracs, maxima; 0.0438 per F-06).
- Chain 09 (0.0152; 0.0212/0.0192/0.0053; 0.034; 0.0915).
- Synthetic 03/07/06/02/08 claims; "more than four times" (4.3×); 0.0557/0.0212 = 2.6.
- Table 3 parameters (config.py: α 0.9, B 9.0, 160, 200, 6 regions).
- Table 7 counts (`witness.txt`: 38 → 32; cones 9/14/18/23/28/29; smallest retained 39).
- Units arithmetic (1/52 = 0.019, 1/672 = 0.0015).
- Prop 1 residual 2.8e−17 (max 2.78e−17).

Not as stated: Table 3 "seeded evaluations 10 / 16 / 8" omits that the synthetic λ=0 run uses **8** seeds per network, not 10 (MINOR, see F-27).

### F-16 | MAJOR (scope 4) | §2 (D) l.223–231; Table 1 row D; `cermeno2026`
- **Claimed:** Cermeño & Rodas is student work that "maps visibility improvements to operational and strategic benefits, typically through causal models of performance indicators".
- **Evidence:** the MIT CTL capstone (May 2026, 21 pp., read in full during the reference check) computes a **decision-based value of information** for tier-2/3 visibility: the reduction in expected disruption cost under the cost-minimising resilience strategy. It reports **exact zero VoI** in several settings and explains them by the chosen policy staying optimal. That is close to this paper's own question, and it undermines Table 1 row D "zero-value condition: no" unless the column is restricted to *formal* sufficient conditions. "Causal models of KPIs" fits Caridi et al. only.
- **Fix:** characterise it accurately; restrict the KPI sentence to Caridi; distinguish on formality (they give no stated condition or bound); and change the D-row cell to "no formal condition".

### F-17 | MAJOR (scope 4) | §2 (A′) l.179–183; Table 1 row A′ "convexity-free: not in those examined"
- **Claimed:** "That family of bounds rests on convexity or concavity", asserted for Madansky, Avriel–Williams, Ziemba–Butterworth, Hausch–Ziemba, Huang–Vertinsky–Ziemba and Birge.
- **Evidence:**
  - **Verified** from the abstract only for Huang–Vertinsky–Ziemba (concave utility; Jensen / Edmundson–Madansky). The paper's paraphrase of it is accurate.
  - Consistent with, but not stated in, the abstracts of Madansky (LP, random RHS) and Avriel–Williams ("linear or convex program").
  - **Not verified at all** for Ziemba–Butterworth, Hausch–Ziemba and Birge: full texts not accessible (403), no abstract read.
  - The Table 1 phrase "in those examined" is false for sources that were not examined.
  - Separately, Madansky (1960) gives conditions for **equality** between the expected-value and stochastic solutions. It is also textbook (Birge–Louveaux) that EVPI = 0 when one decision is optimal for almost every scenario. That makes Table 1's A′ "gives a zero-value condition: no" contestable; a stochastic-programming referee will raise it.
- **Fix:** read the three full texts, or restrict the convexity sentence to Huang–Vertinsky–Ziemba (and, with "in the LP/convex setting", Madansky and Avriel–Williams). Acknowledge the classical EVPI = 0 conditions and say how the structural, per-category condition differs.

### F-18 | MAJOR (scope 4) | Prop 3 proof (P4) l.493–495 cites `artzner1999` for CVaR subadditivity
- **Evidence:** Artzner et al. define coherence and prove it for WCE. TCE/TailVaR is not subadditive for atomic laws, and Prop 3 concerns Bernoulli (atomic) variables, exactly where TCE ≠ CVaR. CVaR coherence for general laws is Acerbi & Tasche (2002), Pflug (2000) or Rockafellar & Uryasev (2002). Relatedly, Prop 11 (V1) cites Rockafellar–Uryasev 2000, which assumes a continuous loss distribution, whereas L here is discrete (MINOR, F-28).
- **Fix:** cite Acerbi & Tasche 2002 or Rockafellar & Uryasev 2002 at P4 and V1.

### F-19 | MAJOR (scope 4) | §2 (E) l.235–236 "topological measures of network vulnerability are well established [wagner2010, simchi2015]"
- **Evidence:** Simchi-Levi et al. 2015 is a risk-exposure / time-to-recover optimisation model, not topological. Wagner & Neshat is a graph-based index over vulnerability *drivers*, not a topology of the supply network (full text not read).
- **Fix:** "graph-theoretic and risk-exposure measures of supply-chain vulnerability", or cite a genuinely topological source.

### F-20 | MAJOR | Conjecture 12 l.949–954
- **Claimed:** the bound holds "under a single-cut regime … and with replacement slack".
- **Evidence:** "replacement slack" is defined nowhere in the paper (or in `exp_E_conjecture1.py`'s header). "Single-cut regime" is defined through properties of *optimal* plans, so the hypothesis cannot be checked in advance. The conjecture is not well-posed, and the 100,000-instance search tests an unstated operationalisation.
- **Fix:** define both terms formally, and state the exact class the enumeration searched (K ≤ 3, C ≤ 3 confirmed from `expE_s0*.csv`).

### F-21 | MAJOR (scope 7) | Strong statements unsupported by the evidence
- l.1277–1279: "What does explain a large part of the observed concentration is candidate multiplicity". This is a causal verb from a census with no linking analysis, and the census is mismeasured (F-03).
- l.761: "This accounts for a substantial part of the mass near zero in Figure 4". This is a stratified mean, not an accounting; 1,045 mixed instances are omitted.
- l.1646: "H is a faithful ordering". This was established only for the expected-loss miniature pair, whose informed planner is handed θ; it is not the measured planner pair (F-01).
- l.1781: "conditions under which the answer is provably nothing". The paper itself gives no procedure for verifying (H2).
- l.1189–1192: "the excluded chains would, if anything, be expected to show less value". Unsupported speculation.
- l.1153–1156: "a near-zero advantage therefore cannot be explained by the planner having overfitted". Out-of-sample evaluation rules out in-sample overfit, not planner noise; overstated.
- l.1187: "the partition does not depend on the exact value chosen". It holds only for thresholds in (29, 39].
- l.228: "its answer sharper". Comparative claim with no comparison.
- l.1005–1007 and l.1870: "reproduced identical reported outputs on an independent machine" (F-14).
- No "state of the art" or equivalent phrasing found (grep over main.tex).

---

### MINOR

- **F-22 | Thm 6 statement.** The hypothesis "θ_k independent across categories" is not used in S1–S10. S3 and S9 need only marginals, by linearity of expectation. It *is* needed for Cor 9 (P1, where E_{θ−k} must not depend on θ_k). Fix: move the hypothesis to Cor 9, or note it is only needed there.
- **F-23 | Cor 5.** "Monotone with respect to almost sure dominance" is never used: (H2) is assumed directly for J_ρ, and C1–C3 use only law invariance. Also, CVaR-EVPI (prior objective E_θ ρ(L), not ρ of the mixture) is first defined in Prop 11's proof (V4). Lemma 2 is proved for j only, while the abstract applies it under CVaR. Fix: define EVPI_ρ once in §3, and state Lemma 2 for E_θ J_ρ (the proof carries over pointwise).
- **F-24 | Prop 10.** "Constant for λ ≤ D/δ and strictly increasing above" requires D < δ. If D/δ ≥ 1, I_k is constant on all of [0,1]. Add the condition.
- **F-25 | Thm 4 (T3).** "The status of no other element changes" relies on Definition 1 being read as quantifying over *all* plans containing the action. Definition 1's wording ("given a plan containing that action") is ambiguous. Fix: make the quantifier explicit.
- **F-26 | Pseudo-replication residue (scope 5d).**
  - The Poisson calculation (l.1221–1225) and the 2-SE rule treat the 96 instances as independent.
  - The sweep's paired t / Wilcoxon tests (l.1391–1402) treat 24 instances from 8 chains as independent.
  - Fig. 3 caption has the same issue.
  - Fix: report chain-clustered versions, or flag them like Table 9.
- **F-27 | Table 3** "10 / 16 / 8" mislabels the synthetic λ=0 run, which uses 8 seeds (`results_scalefree_v2_FROZEN`: 8 per network).
- **F-28 | References (scope 4):**
  - `vayanos2025`: Mgmt Sci 72(2) 1509–1528 is the **Feb 2026** issue. Cite (2026) or "Articles in Advance 2025".
  - `raiffa1961` publisher: "Division of Research, Graduate School of Business Administration, Harvard University".
  - Missing issue numbers: birge1982 24(1); goel2006 108(2–3); hausch1983 10(3–4); ziemba1975 1(4).
  - `artstein1994`: add the series "Contributions to Statistics". The source says the problem "resembles" a three-stage program, so "recasts" is slightly strong.
  - `strong2014` itself proposes the non-nested regression estimator. Add "addressed by regression-based estimators".
  - `brintrup2018` pages "1–12" unverified; cite the article number only.
  - `cermeno2026` type: "Capstone project, MASc SCM, MIT, May 2026".
  - Rockafellar–Uryasev 2000 assumes continuous losses (V1); add the 2002 paper.
- **F-29 | Scope 4 settled item, Ziemba & Butterworth.** The bib entry "Stochastics **1**, 361–378 (1975)" is **correct** (doi:10.1080/17442507508833117). Crossref's 1973 date is a whole-volume placeholder; the DOI year code "75" and the page range place the paper in the 1975 part of vol. 1, issue 4. No record of "Stochastics IV (1974) 1–18" exists anywhere searched; treat it as spurious. Hausch & Ziemba II is confirmed as 10(3–4) 181–217 (1983).
- **F-30 | Table 1 row C (scope 5a).** It says "gives an EVPI bound: no", yet the prose (l.215–216) says Ma et al. use "the perfect-information bound" as the benchmark. Separately, the A′ cell asserts a property of unread works (F-17).
- **F-31 | Language (scope 7), formulaic or rhetorical constructions to cut:**
  - "Two things follow, and the second is unwelcome" (l.1273)
  - "The hypothesis v≠0 is not cosmetic" (l.743)
  - "That count is a resolution statement and should be read as one" (l.1218)
  - "that is one fact rather than five" (l.1395)
  - "It would be wrong to claim" (l.222)
  - "We must be explicit that" (l.169)
  - "Everything else in the paper supports that claim" (l.118)
  - "in our view, the more useful one" (l.102)
  - "The column that separates it is the third" (l.249)
  - "Nothing in the theory requires otherwise" (l.1404)
  - Recurrent self-referential hedging ("we do not claim … in either direction") appears 6+ times; consolidate it in §10.
- **F-32 | Vague quantifiers (scope 5b).**
  - l.1078 "most chains lie far above that range" → "29 of 32 have K0 between 6 and 672".
  - l.1515 "close to collinear" → "chain-level Spearman 0.83 between census and K0 (p = 4e−9)".
  - l.1112 "realised sizes of about 977" → "977".

---

## §3 Mathematics: line-by-line status (scope 3)

| Result | Steps | Verdict | Assumptions used, and stated? |
|---|---|---|---|
| Prop 1 (H vs EVPI) | E1–E3 | **Correct as algebra.** "Neither gap dominates" is an assertion with no example in the proof, but the §8.7 data supply one. | Needs Ŝ_π and Ŝ_θ deterministic and j exact. Not stated: in the measurements, Ŝ are random and j is estimated (F-07). The measured quantity is not this H (F-01). |
| Lemma 2 | L1–L4 | Correct. | Finite plan set (stated, Table 5). Same feasible set after acquisition (unstated; holds if probing does not consume B_m). Expected loss only (F-23). |
| Prop 3 (Bernoulli CVaR) | P1–P4 | Correct. | Subadditivity of CVaR (true; citation wrong, F-18). |
| Def 1 / (H1) / (H2) | — | (H1) sufficient condition insufficient (F-10). The (H2) remark that "secure all candidates" can never witness the cost clause under positive costs is correct. | — |
| Thm 4 | T1–T9 | Correct given (H1) and (H2). T5 uses (H1); T2–T3 use (H2); T6 uses feasibility of S*; T9 uses EVPI ≥ 0. | Additive costs implicit in T2 (unstated). Definition-1 quantifier ambiguity (F-25). |
| Cor 5 | C1–C3 | Correct. | Monotonicity unused; CVaR-EVPI undefined until Prop 11 (F-23). |
| Thm 6 | S1–S10 | **Correct.** S1: correspondence ✓. S2–S4: separation (needs node-disjoint subtrees and additive cost; independence not needed). S6: step-function / breakpoint claim ✓ (b = 0 is a breakpoint via no-action). S7–S8: min over splits with split-independent correction ✓. S9: E over θ ✓. S10 ✓. Re-ran `verify_theorem.py`: 0 violations in 6000. | Independence superfluous (F-22). |
| Cor 7 (dilution) | D1–D4 | **Correct for I_k**, including when "secure all" (cost m·c_u) is cheaper than c_v: the max is still attained on [c_u, min(c_v, m·c_u)). The proof ignores that action but the result survives. 2000-instance c1 batch: 0 mismatches. | "Bound attained" overclaim (F-09). |
| Prop 8 (witness) | W1–W4 | Correct for the paper's stated model. In the implementation, (i) is evaluated on latent truth (F-03). | v ≠ 0, (i), (ii), conjunctive cascade, additive costs. |
| Cor 9 | P1–P4 | Correct. P2 follows from the definition of D_k as a supremum, not from S6 as cited. | Uses independence (stated via Thm 6). |
| Prop 10 | R1–R7 | Correct. | Needs D < δ for the threshold statement (F-24). R7 is not a proof but a remark. |
| Prop 11 | V1–V6 | Correct (algebra re-derived: EVPI_CVaR ≤ (EVPI + E M)/(1−α) − E M). | L ≥ 0. R–U 2000 assumes continuous L (F-28). |
| Conjecture 12 | — | Not well-posed (F-20). | — |

**EVPI / U / H separation:** the text keeps them apart consistently. It never uses H as a bound on EVPI (l.71–72, l.377–381, Table 2, l.1549–1550, l.1572–1575, l.1776–1777 all say so) and never applies U to a CVaR measurement (l.407–408, l.936–942). The one leak is in the opposite direction. "H is a faithful ordering" of EVPI (l.1646) is a property of a different H (handed θ, expected loss) from the one measured (F-01, F-21). Table 2's "H = EVPI + ε_π − ε_θ" row likewise describes a quantity the empirical sections do not compute.

---

## §5 Known open items (scope 5)

| Item | Status | Evidence |
|---|---|---|
| (a) Table 1 stream (C) cell vs withdrawn prose | **OPEN, reframed.** I found no prose withdrawal specific to row C. The remaining unread-literature assertion is in row A′ ("not in those examined"), for three sources not examined (F-17). Row C has a separate inconsistency: "EVPI bound: no" vs Ma et al. (F-30). | main.tex l.169–189, l.213–217, l.265–268 |
| (b) K0 identity "holds only for 8 of 32 multi-sink chains" | **Premise not supported by current loader output; identity holds 32/32.** `witness.txt` and my re-run show every one of the 32 retained chains with `focal=__market__`, sinks 2–672. So "K0 = number of sinks" holds for all 32, and l.1074 ("every one of which the loader reports as multi-sink") is consistent with evidence. The single-sink clause (l.1072–1073) is dead text for this collection. The vague adjectives remain **OPEN** (F-32). If "8 of 32" came from an earlier loader version, that version is not in evidence. | `witness.txt`; scratch `run/G.txt` |
| (c) (H2) witnesses not instantiated | **OPEN.** The conclusion (l.1792) still offers "a shared downstream stage that can be dual-sourced or buffered once" as the *in-model* example, though l.287 places dual sourcing outside the model (and the implementation includes it, F-02). The contractual remedy is correctly flagged as outside V. Neither is instantiated on any benchmark network; only the miniature t1 batch instantiates (H1)+(H2) by construction (c_v = c_u·U(0.3,1)). Prop 8 is checked on 47 categories, but on latent truth (F-03). | l.1782–1799; `verify_theorem.py:gen` |
| (d) Instance-level p-values with chain-level covariates | **Largely CLOSED for Table 9** (chain-level column added; text says to read it) but its values are version-dependent (F-04, F-11). **Residual OPEN** in the Poisson/2-SE count and the paired sweep tests (F-26). | Table 9; l.1215–1238, l.1391–1402 |

---

## §4 References: per-item summary (scope 4)

Metadata checked against Crossref / publisher records during the reference check. "Read" means abstract unless stated.

| Key | Metadata vs bib | Citing sentence |
|---|---|---|
| artstein1993 | ✓ | Fair |
| artstein1994 | ✓ (series missing) | Fair; "recasts" slightly strong (abstract seen via snippet only) |
| artstein1999 | ✓ | Fair (TLDR only; not verified in depth) |
| artzner1999 | ✓ | **Overstated at P4** (F-18); fair at l.246 |
| avriel1970 | ✓ | Fair; convexity requirement unverified beyond abstract |
| birge1982 | issue missing | Fair as VSS bounds; convexity **unverified** |
| blackwell1953 | ✓ | Fair (Lemma needs only the elementary direction) |
| brintrup2018 | pages unverified | Fair |
| caridi2014 | ✓ | Fair |
| cermeno2026 | exists; type imprecise | **Mischaracterised** (F-16) |
| goel2006 | issue missing | Fair |
| golovin2011 | ✓ | Fair |
| hausch1983 | issue missing | Topic fair; convexity **unverified** |
| heath2024 | ✓ | Fair |
| howard1966 | ✓ | Fair |
| huang1977 | ✓ | **Fair, verified** (concave utility, Jensen / E–M) |
| javdani2014 | ✓ PMLR 33:430–438 | Fair: drives uncertainty into a single decision region. "Closest precedent" is a judgement, defensible. |
| jonsbraten1998 | ✓ | Fair |
| kosasih2022 | ✓ | Fair |
| ma2024 | ✓ (still arXiv-only) | Fair (perfect-information bound as benchmark; branching on probing sets) |
| madansky1960 | ✓ | Fair on bounds; its equality conditions bear on Table 1 (F-17) |
| raiffa1961 | publisher loose | Fair |
| rockafellar2000 | ✓ | Continuous-loss assumption vs discrete L (F-28) |
| simchi2015 | ✓ | **Unsupported as "topological"** (F-19) |
| snyder2016 | ✓ | Fair (OR/MS disruption review) |
| strong2014 | ✓ | Fair; better framed as the solution to nested MC |
| tomlin2006 | ✓ | Fair |
| vayanos2025 | **year should be 2026** | Fair |
| wagner2010 | ✓ | Overstated as "topological" (partly verified) |
| willems2008 | ✓ (38 chains confirmed) | Fair |
| ziemba1975 | ✓ vol 1 (1975) 361–378 | Topic fair; convexity **unverified** |

Not read in full (paywall or 403): Ziemba–Butterworth, Hausch–Ziemba, Birge, Avriel–Williams, Madansky, Artstein 1994/1999, Wagner–Neshat. The pre-existing `citation_audit.md` is an unfilled checklist: every verdict is blank, it omits the A′ group, and it quotes superseded wording. It should not be relied on.

---

## Scratch artefacts (for reproduction of this audit)
All in the scratch directory used for the audit, which was not archived:
- `zeros.py`, `parse.py`, `exact.py`: zeros mechanism.
- `canon.py`: version-independent Table 9.
- `snap.py`: parse-snapping wrapper.
- `run/{G,H,I,H_old,I_old}.txt`: script outputs under both environments.
- `vt/`: `verify_theorem.py` re-run.
- `oldenv/`: numpy 1.26.4 / pandas 2.2.3 / scipy 1.11.4.
- `repo/`: unzipped asdr_repo.zip.
- `gh/`: GitHub clone.
