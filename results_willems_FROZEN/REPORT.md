# ASDR v2 results

profile: seeds=10, n_train=32, Bv=9, Bm=9.0

## What each block checks and what the result means

**Policy table** -- lower mean CVaR is better; `adv` is the paired advantage over Decoupled; `p_holm` is the Holm-corrected paired Wilcoxon p-value. A publishable positive result = ASDR variants significantly below Decoupled AND UCB after correction.

       policy  mean_cvar    ci_lo    ci_hi       adv        p  cohens_d      win   p_holm
       Oracle   0.206870 0.197277 0.217087  0.001616 0.000559  0.155635 0.266667 0.003916
       Random   0.207516 0.198034 0.217868  0.000970 0.132466  0.085972 0.244792 0.529864
         ASDR   0.207886 0.198169 0.218310  0.000601 0.067699  0.062455 0.242708 0.338495
     Coverage   0.207887 0.198310 0.218179  0.000600 0.018792  0.056740 0.256250 0.112751
         None   0.207925 0.198235 0.218157  0.000561 0.761586  0.046790 0.240625 1.000000
          UCB   0.208082 0.198432 0.218301  0.000405 0.145872  0.030856 0.239583 0.529864
    Decoupled   0.208487 0.198888 0.218907  0.000000 1.000000  0.000000 0.000000      NaN
ASDR-Interact   0.209338 0.199614 0.219513 -0.000851 0.758144 -0.053986 0.245833 1.000000

**Coupling decomposition** -- fraction of the ASDR advantage attributable to coupling (vs adaptivity alone). v1 reported ~2:1; here: {
  "total_adv": 0.0006009882501549435,
  "coupling_abs": 0.00019641405799009185,
  "adaptivity_abs": 0.0004045741921648516,
  "coupling_frac": 0.3268184659840745
}

**Moderator (pre-registered)** -- prediction: advantage rises with the ground-truth chokepoint census and vanishes at zero. Spearman rho=0.009, p=0.9311, n=96 networks. If rho>0 and significant, this is mechanism evidence, not just a win.

**Diagnostics per network** (chokepoint census: if 0, expect a null on that network -- that is the resolution-threshold hypothesis doing its job):

                 name  n_nodes  n_edges  max_tier  n_chokepoints_tier2plus
willems_chain07_seed0       39       84         4                        6
willems_chain08_seed0       41       50         8                       10
willems_chain09_seed0       50       78         5                        3
willems_chain10_seed0       59      189         2                        0
willems_chain11_seed0       69      126         5                       24
willems_chain12_seed0       89      158         5                        7
willems_chain13_seed0      109      462         2                        0
willems_chain14_seed0      117      185         4                       50
willems_chain15_seed0      134      220         4                       56
willems_chain16_seed0      146      284         7                       36
willems_chain17_seed0      153      309         5                       37
willems_chain18_seed0      155      252         8                       72
willems_chain19_seed0      157      278         9                        5
willems_chain20_seed0      157      171        10                        2
willems_chain21_seed0      187      393         7                       66
willems_chain22_seed0      254      376         9                      130
willems_chain23_seed0      272      549         3                        7
willems_chain24_seed0      335     1287         6                       52
willems_chain25_seed0      410     1026         3                      143
willems_chain26_seed0      469      607         6                        0
willems_chain27_seed0      483      953         5                       12
willems_chain28_seed0      578     2352         8                       43
willems_chain29_seed0      618     1118         5                      124
willems_chain30_seed0      627      852         5                      391
willems_chain31_seed0      707     1478         4                       60
willems_chain32_seed0      845     1907         5                      212
willems_chain33_seed0      977     1341         8                      481
willems_chain34_seed0     1207     4116         3                        5
willems_chain35_seed0     1387     1893         6                       62
willems_chain36_seed0     1452     5484         4                      607
willems_chain37_seed0     1480     2628         4                      646
willems_chain38_seed0     2026    16784         4                      646
willems_chain07_seed1       39       84         4                        6
willems_chain08_seed1       41       50         8                       10
willems_chain09_seed1       50       78         5                        3
willems_chain10_seed1       59      189         2                        0
willems_chain11_seed1       69      126         5                       24
willems_chain12_seed1       89      158         5                        7
willems_chain13_seed1      109      462         2                        0
willems_chain14_seed1      117      185         4                       50
willems_chain15_seed1      134      220         4                       56
willems_chain16_seed1      146      284         7                       36
willems_chain17_seed1      153      309         5                       37
willems_chain18_seed1      155      252         8                       72
willems_chain19_seed1      157      278         9                        5
willems_chain20_seed1      157      171        10                        2
willems_chain21_seed1      187      393         7                       66
willems_chain22_seed1      254      376         9                      130
willems_chain23_seed1      272      549         3                        7
willems_chain24_seed1      335     1287         6                       52
willems_chain25_seed1      410     1026         3                      143
willems_chain26_seed1      469      607         6                        0
willems_chain27_seed1      483      953         5                       12
willems_chain28_seed1      578     2352         8                       43
willems_chain29_seed1      618     1118         5                      124
willems_chain30_seed1      627      852         5                      391
willems_chain31_seed1      707     1478         4                       60
willems_chain32_seed1      845     1907         5                      212
willems_chain33_seed1      977     1341         8                      481
willems_chain34_seed1     1207     4116         3                        5
willems_chain35_seed1     1387     1893         6                       62
willems_chain36_seed1     1452     5484         4                      607
willems_chain37_seed1     1480     2628         4                      646
willems_chain38_seed1     2026    16784         4                      646
willems_chain07_seed2       39       84         4                        6
willems_chain08_seed2       41       50         8                       10
willems_chain09_seed2       50       78         5                        3
willems_chain10_seed2       59      189         2                        0
willems_chain11_seed2       69      126         5                       24
willems_chain12_seed2       89      158         5                        7
willems_chain13_seed2      109      462         2                        0
willems_chain14_seed2      117      185         4                       50
willems_chain15_seed2      134      220         4                       56
willems_chain16_seed2      146      284         7                       36
willems_chain17_seed2      153      309         5                       37
willems_chain18_seed2      155      252         8                       72
willems_chain19_seed2      157      278         9                        5
willems_chain20_seed2      157      171        10                        2
willems_chain21_seed2      187      393         7                       66
willems_chain22_seed2      254      376         9                      130
willems_chain23_seed2      272      549         3                        7
willems_chain24_seed2      335     1287         6                       52
willems_chain25_seed2      410     1026         3                      143
willems_chain26_seed2      469      607         6                        0
willems_chain27_seed2      483      953         5                       12
willems_chain28_seed2      578     2352         8                       43
willems_chain29_seed2      618     1118         5                      124
willems_chain30_seed2      627      852         5                      391
willems_chain31_seed2      707     1478         4                       60
willems_chain32_seed2      845     1907         5                      212
willems_chain33_seed2      977     1341         8                      481
willems_chain34_seed2     1207     4116         3                        5
willems_chain35_seed2     1387     1893         6                       62
willems_chain36_seed2     1452     5484         4                      607
willems_chain37_seed2     1480     2628         4                      646
willems_chain38_seed2     2026    16784         4                      646
