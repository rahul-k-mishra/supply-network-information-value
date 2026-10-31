# ASDR v2 results

profile: seeds=8, n_train=32, Bv=9, Bm=9.0

## What each block checks and what the result means

**Policy table** -- lower mean CVaR is better; `adv` is the paired advantage over Decoupled; `p_holm` is the Holm-corrected paired Wilcoxon p-value. A publishable positive result = ASDR variants significantly below Decoupled AND UCB after correction.

       policy  mean_cvar    ci_lo    ci_hi       adv        p  cohens_d      win   p_holm
         ASDR   0.419922 0.398240 0.441346  0.006684 0.713909  0.100697 0.125000 1.000000
       Oracle   0.422917 0.401931 0.444922  0.003689 0.643033  0.055819 0.083333 1.000000
       Random   0.423329 0.401562 0.445391  0.003277 0.752193  0.052675 0.083333 1.000000
         None   0.425705 0.402830 0.447410  0.000901 0.152316  0.013803 0.062500 0.913893
    Decoupled   0.426606 0.402474 0.452214  0.000000 1.000000  0.000000 0.000000      NaN
ASDR-Interact   0.427431 0.406084 0.448181 -0.000825 0.391707 -0.012636 0.072917 1.000000
     Coverage   0.429275 0.407551 0.450493 -0.002669 0.065747 -0.039893 0.093750 0.460232
          UCB   0.429698 0.406288 0.453311 -0.003092 0.383115 -0.059183 0.072917 1.000000

**Coupling decomposition** -- fraction of the ASDR advantage attributable to coupling (vs adaptivity alone). v1 reported ~2:1; here: {
  "total_adv": 0.0066840277777777775,
  "coupling_abs": 0.009776475694444444,
  "adaptivity_abs": -0.0030924479166666674,
  "coupling_frac": 1.4626623376623378
}

**Moderator (pre-registered)** -- prediction: advantage rises with the ground-truth chokepoint census and vanishes at zero. Spearman rho=0.072, p=0.8248, n=12 networks. If rho>0 and significant, this is mechanism evidence, not just a win.

**Diagnostics per network** (chokepoint census: if 0, expect a null on that network -- that is the resolution-threshold hypothesis doing its job):

                  name  n_nodes  n_edges  max_tier  n_chokepoints_tier2plus
synthetic_scalefree_00      977      641         4                        8
synthetic_scalefree_01      977      624         4                        9
synthetic_scalefree_02      977      633         4                        3
synthetic_scalefree_03      977      633         4                        8
synthetic_scalefree_04      977      640         4                        6
synthetic_scalefree_05      977      636         4                        7
synthetic_scalefree_06      977      633         4                        6
synthetic_scalefree_07      977      632         4                        5
synthetic_scalefree_08      977      608         4                        6
synthetic_scalefree_09      977      652         4                        7
synthetic_scalefree_10      977      621         4                        5
synthetic_scalefree_11      977      634         4                        7
