# F-10 analysis: the sufficient condition for (H1)

Scope: mathematics only. `paperA/main.tex` was not edited. Line numbers refer to
`paperA/main.tex` as of 2026-11-01. The counterexamples below were worked by hand and then
checked by exact rational enumeration (Python `fractions`; a scratch script that is not part
of the repo). Every number agrees.

---

## 1. Where the condition is stated and restated

**The statement (inside (H1)), l.520–523:**

```
520  \item[(H1)] \emph{Loss-law invariance.} For every identification-free plan
521  $S$, the law of $L(S;\theta,\cdot)$ is the same for all $\theta$. A
522  sufficient condition is that within every latent category the candidates are
523  exchangeable in operability law, in securing cost and under the prior. The
```

l.527–529 add the justification "That is why the sufficient condition is stated over every
latent category rather than over the plan's."

**The conclusion's restatement, l.1758–1760 and l.1782:**

```
1758  When candidates within a supply category are exchangeable \emph{and}
1759  identification-free actions of no greater cost uniformly dominate, the
1760  decision value of hidden supply-network structure is exactly zero, ...
...
1782  would be. Verifying (H1) reduces to an exchangeability check on candidate sets.
```

**Other places that rely on the same claim** (not named in F-10, but they rest on it):

| Line | Text | Dependence |
|---|---|---|
| l.104–106 | "the first, exchangeability of candidates within a category, directly from prior and public data" | Introduction's version of the same claim |
| l.509–510 | "and, when the candidates are exchangeable in operability law as (H1) assumes, take no action" | Definition 1 says no-action is identification-free under the marginal condition. Example 1 below shows this is false. |
| l.971 | Table `tab:applic`: "(H1) checkable in advance" | True only under the corrected condition, and the check is a different one |
| l.1241–1242 | "At $\lambda=0$ the construction makes candidates within a category approximately exchangeable, which is (H1)" | §8 text, due to be removed, but it equates marginal exchangeability with (H1) |
| l.1797 | "the enumerated batch of Table~\ref{tab:verify} instantiates (H1) and (H2) by construction" | Survives; see §4.5 |

---

## 2. Counterexamples

### Model conventions used (as in the paper, l.280–312)

- Each node $v$ has a failure indicator $F_v$.
- Operability is defined recursively: $O_v = 1$ if $v\in S$. Otherwise
  $O_v = (1-F_v)\cdot\prod_{k\in K_v} O_{s_{v,k}(\theta)}$, where $s_{v,k}(\theta)$ is the
  supplier of category $(v,k)$. That supplier is $\theta_{v,k}$ if the category is latent and
  the public supplier if it is not.
- Focal category $k$ is starved when its supplier is inoperable: $Z_k = 1-O_{s_{0,k}}$.
- The loss is $L = K_0^{-1}\sum_k Z_k$.

### Example 1 (consumer asymmetry). The law, the mean and EVPI all depend on θ.

**Graph.** The nodes are $0$ (focal), $w$, $x$, $u_1$ and $u_2$.

| consumer | category | supplier |
|---|---|---|
| $0$ | focal cat 1 | $w$ (public) |
| $0$ | focal cat 2 | $x$ (public) |
| $w$ | $a$ (**latent**) | $C_{w,a}=\{u_1,u_2\}$ |
| $w$ | $b$ | $u_1$ (public) |

$x$, $u_1$ and $u_2$ have no inputs. $K_0=2$. There is one latent category, so
$\theta=\theta_{w,a}\in\{u_1,u_2\}$.

**Rates.** Failures are independent: each node is its own cluster, or equivalently the copula
correlation is 0.

- $P(F_{u_1}=1)=P(F_{u_2}=1)=q=0.1$
- $P(F_x=1)=r=0.15$
- $F_w=F_0=0$

**Costs, prior, budget.** $c_{u_1}=c_{u_2}=c_w=c_x=1$. The prior is uniform on
$\{u_1,u_2\}$. The budget is $B=1$, so the feasible plans are $\emptyset$, $\{w\}$, $\{x\}$,
$\{u_1\}$ and $\{u_2\}$.

**The stated sufficient condition holds.** The only latent category is $(w,a)$.

- $u_1$ and $u_2$ are both sourceless nodes failing with probability $0.1$, independently, so
  their operability laws are identical.
- Their securing costs are equal.
- The prior is uniform.

The only asymmetry is that $u_1$ also publicly supplies $(w,b)$. The marginal condition does
not see this.

**The plan.** $S=\emptyset$. It is identification-free vacuously, since it has no elements.
l.509–510 also asserts explicitly that no-action is identification-free under this condition.

**Loss law under $\emptyset$, worked line by line.** $Z_2 = F_x$ in both states.

*θ = u₁.*
- $O_w = (1-F_{u_1})(1-F_{u_1}) = 1-F_{u_1}$, so $Z_1 = F_{u_1}$ and $P(Z_1=1)=0.1$.
- $Z_1$ and $Z_2$ are independent.
- $P(L=0) = 0.9\cdot0.85 = 0.765$
- $P(L=\tfrac12) = 0.1\cdot0.85 + 0.9\cdot0.15 = 0.085+0.135 = 0.220$
- $P(L=1) = 0.1\cdot0.15 = 0.015$
- $E L = (0.1+0.15)/2 = 0.125$

*θ = u₂.*
- $O_w = (1-F_{u_2})(1-F_{u_1})$, so $P(Z_1=1) = 1-0.9^2 = 0.19$.
- $P(L=0) = 0.81\cdot0.85 = 0.6885$
- $P(L=\tfrac12) = 0.19\cdot0.85 + 0.81\cdot0.15 = 0.1615+0.1215 = 0.2830$
- $P(L=1) = 0.19\cdot0.15 = 0.0285$
- $E L = (0.19+0.15)/2 = 0.170$

The two laws differ, so (H1) fails while its stated sufficient condition holds. The mean
differs as well, so even expected-loss invariance fails.

**The defect reaches Theorem 4's conclusion.** $(w,a)$ is the only latent category.
Proposition 8's hypotheses hold for it:
- $w\neq0$;
- $w$ is the only consumer of $u_1$ and of $u_2$;
- $c_w = 1 \le \min_u c_u = 1$.

I also checked (H2) directly. The identification-dependent elements are $u_1$ and $u_2$.
Their influence on $L$ runs only through $w$. Securing $w$ forces $Z_1=0$ in every scenario,
so $L(S\setminus\{u\}\cup\{w\};\theta,\omega)\le L(S;\theta,\omega)$ pointwise, and the cost
is no larger. $\{w\}$ is identification-free: under it $L=Z_2/2$ whatever θ is.

Proposition 8's proof says at (W3) that "the only such category is $(v,k)$". Here $u_1$ also
serves $(w,b)$, so that sentence is literally false, but (W4)'s conclusion still holds
because $(w,b)$ has the same consumer $w$.

Values $j(S;\theta)=E L$:

| plan | θ = u₁ | θ = u₂ | prior mean |
|---|---|---|---|
| ∅ | 0.125 | 0.170 | 0.1475 |
| {w} | 0.075 | 0.075 | 0.0750 |
| {x} | 0.1/2 = **0.050** | 0.19/2 = 0.095 | **0.0725** |
| {u₁} | 0.075 | (0.1+0.15)/2 = 0.125 | 0.1000 |
| {u₂} | 0.125 | 0.125 (w still needs u₁ via b) | 0.1250 |

- $\min_S j(S;u_1) = 0.050$, attained at $\{x\}$.
- $\min_S j(S;u_2)=0.075$, attained at $\{w\}$.
- $E_\theta\min_S j = 0.0625$.
- The prior optimum is $\{x\}$, with value $0.0725$.

$$\mathrm{EVPI} = 0.0725-0.0625 = 0.01 > 0.$$

So the paper's sufficient condition for (H1), combined with (H2) certified by the paper's
own Proposition 8, does **not** give EVPI = 0. Theorem 4 itself is not refuted, because its
hypothesis (H1) fails here. What is refuted is the sentence at l.522–523 and the conclusion's
restatement at l.1758 and l.1782. The failing step is (T5). The two θ-optimal plans are both
identification-free, but $j(\{x\};\theta)$ is 0.050 at one state and 0.095 at the other.

### Example 2 (upstream-subtree asymmetry). The mean is invariant; the law is not.

This example shows why Corollary 5 needs *law* invariance, and that the marginal condition
fails even when the means happen to agree.

**Graph.** Focal $0$ takes cat 1 from $w$ and cat 2 from $x$, both public. $w$ consumes one
latent category with $C=\{u_1,u_2\}$. $s$ publicly supplies both $u_1$ and $x$. $u_2$ has no
inputs.

**Rates.**
- $P(F_s=1)=0.1$
- $P(F_{u_2}=1)=0.1$
- $F_{u_1}=F_x=F_w=0$
- Failures are independent.

**Marginal exchangeability holds.**
- $P(O_{u_1}=0)=P(F_s=1)=0.1$ and $P(O_{u_2}=0)=0.1$.
- Equal costs and a uniform prior are added as before.

**Plan.** $\emptyset$.

*θ = u₁.* $Z_1=Z_2=F_s$.
- $P(L=0)=0.9$, $P(L=1)=0.1$
- $EL=0.1$
- $\mathrm{CVaR}_{0.9}(L)=1$

*θ = u₂.* $Z_1=F_{u_2}$ and $Z_2=F_s$, independent.
- $P(L=0)=0.81$
- $P(L=\tfrac12)=0.18$
- $P(L=1)=0.01$
- $EL = 0.09+0.01=0.1$
- $\mathrm{CVaR}_{0.9}(L)$: the top 10 % of mass is $0.01$ at $1$ plus $0.09$ at $\tfrac12$,
  so the value is $(0.01+0.045)/0.1 = 0.55$.

The means are equal, but the laws and the CVaR differ (1 against 0.55).

### Example 3 (cluster asymmetry), stated without numbers

Take Example 2, but delete $s$. Give $u_1$ and $u_2$ their own failure probability $0.1$, and
put $u_1$ in the same copula cluster as $x$ with correlation $\rho>0$, while $u_2$ is in a
singleton cluster. Then $P(Z_1=Z_2=1\mid\theta=u_1)=\Phi_2(\Phi^{-1}(0.1),\Phi^{-1}(0.15);\rho)$.
For $\rho>0$ this exceeds $0.015 = P(Z_1=Z_2=1\mid\theta=u_2)$. The law of $L$ differs and
the mean does not, as in Example 2.

The three examples match the three channels F-10 names: consumers, upstream subtree and
cluster. In each one the candidates have identical marginals, costs and prior.

**The prior clause.** (H1) is a statement pointwise in θ. Its condition is "for all θ", and
no expectation over θ is taken. Prior exchangeability therefore plays no role in (H1). Cost
exchangeability plays none either, because (H1) compares laws for a *fixed* plan.

---

## 3. Corrected sufficient condition and proof

### 3.1 Setting

The **public structure** is
$\mathcal P=(V,0,(K_v),\text{public suppliers},(C_{v,k}),(p_v),\kappa,(\rho_g))$:
- the nodes, with focal node $0$;
- the consumed category labels at each node;
- for each category, either a public supplier or a latent candidate set;
- the marginal failure probabilities $p_v$;
- the cluster labels $\kappa:V\to\mathcal G$, with one copula loading per cluster.

The failure vector follows the one-factor Gaussian copula:
$F_v=\mathbf 1\{\sqrt{\rho_g}Y_g+\sqrt{1-\rho_g}\,\varepsilon_v\le\Phi^{-1}(p_v)\}$, where
$g=\kappa(v)$ and $(Y_g)$ and $(\varepsilon_v)$ are i.i.d. $N(0,1)$.

The state space is $\Theta=\prod_{(v,k)\text{ latent}}C_{v,k}$. Each θ is assumed to give an
acyclic supplier graph, as the paper's DAG model already requires.

### 3.2 Definition (structure automorphism)

A **structure automorphism** is a bijection $\sigma:V\to V$, together with bijections
$\sigma_v:K_v\to K_{\sigma v}$ for every $v$ and a bijection $\beta:\mathcal G\to\mathcal G$,
such that:

- (A0) $\sigma(0)=0$.
- (A1) **Consumers / public edges.** If $(v,k)$ has public supplier $s$, then
  $(\sigma v,\sigma_v k)$ has public supplier $\sigma s$.
- (A2) **Candidate sets.** $(v,k)$ is latent if and only if $(\sigma v,\sigma_v k)$ is latent,
  and in that case $C_{\sigma v,\sigma_v k}=\sigma(C_{v,k})$.
- (A3) **Marginals and clusters.** $p_{\sigma v}=p_v$, $\kappa(\sigma v)=\beta(\kappa(v))$,
  and $\rho_{\beta g}=\rho_g$.

Because σ preserves every edge and candidate relation, it carries the whole upstream subtree
and every consumer of a node along with the node. That is the content F-10 asks for.

σ acts on states and plans as follows:
- $(\sigma\theta)_{\sigma v,\sigma_v k}=\sigma(\theta_{v,k})$, which lies in $\Theta$ by (A2);
- $\sigma S=\{\sigma u:u\in S\}$.

### 3.3 Corrected condition

> **(H1′) Automorphic exchangeability.** For every identification-free plan $S$ and every
> $\theta,\theta'\in\Theta$ there is a structure automorphism σ with $\sigma\theta=\theta'$
> and $\sigma S=S$.
>
> Equivalently: for each identification-free $S$, the stabiliser $\Gamma_S=\{\sigma:\sigma S=S\}$
> acts transitively on Θ.

**Checkable local form (H1′-loc).** (H1′) holds if, for every latent category $(v,k)$ and
every $u,u'\in C_{v,k}$, there is a structure automorphism $\tau$ with these properties:
- it maps $u\mapsto u'$;
- it fixes $v$ and the label $k$;
- it fixes pointwise every node of every other candidate set, and every other latent
  category's consumer and label;
- it fixes every identification-free plan setwise.

The usual instance is the **private-cone swap**. Suppose each candidate $u$ has an upstream
cone $\mathrm{cone}(u)$, meaning $u$ and its ancestors, such that:
- the cones of different candidates are disjoint;
- the only edge leaving a cone is $u\to v$ for category $(v,k)$;
- any two cones are isomorphic by a map that preserves $p$ and cluster labels.

Then $\tau$ = "swap the two cones and fix everything else" satisfies (A0)–(A3), with
$\beta=\mathrm{id}$, provided paired nodes share a cluster label. τ fixes $S$ whenever $S$
meets the two cones symmetrically: for example $\emptyset$, $\{v\}$, all candidates, or any
plan that avoids the cones.

All three examples violate (H1′):
- Example 1: any automorphism moving $u_1\mapsto u_2$ must, by (A1), map the public edge
  $u_1\to(w,b)$ to an edge $u_2\to(\cdot)$. No such edge exists.
- Example 2: $u_1$ has a parent $s$ and $u_2$ does not.
- Example 3: (A3) fails for clusters, because β would have to map $u_1$'s cluster, which
  also contains $x$, onto the singleton cluster of $u_2$.

### 3.4 Lemma (equivariance of the cascade)

Let σ be a structure automorphism and let $F$ be any failure vector. Put
$G_{w}=F_{\sigma^{-1}w}$, so that $G_{\sigma v}=F_v$. Then for every plan $S$, every θ and
every node $v$:
$$O_{\sigma v}(\sigma S,\sigma\theta,G)=O_v(S,\theta,F).$$

*Proof.* Induction on the depth $d_\theta(v)$ of $v$ in the supplier DAG of θ. That depth is
the length of the longest supplier chain ending at $v$, and nodes without inputs have depth 0.

1. σ maps the supplier DAG of θ isomorphically onto that of σθ.
   - For a public category this is (A1): $s_{\sigma v,\sigma_v k}(\sigma\theta)=\sigma(s_{v,k})$.
   - For a latent category it is the definition of σθ:
     $s_{\sigma v,\sigma_v k}(\sigma\theta)=(\sigma\theta)_{\sigma v,\sigma_v k}=\sigma(\theta_{v,k})=\sigma(s_{v,k}(\theta))$.
   - Hence $d_{\sigma\theta}(\sigma v)=d_\theta(v)$, and the induction is well founded.
2. **Membership.** $\sigma v\in\sigma S\iff v\in S$, because σ is a bijection.
3. **Own failure.** $G_{\sigma v}=F_v$ by definition of $G$.
4. **Inputs.** $K_{\sigma v}=\sigma_v(K_v)$. By step 1 the input of $\sigma v$ in category
   $\sigma_v k$ is $\sigma(s_{v,k}(\theta))$. Its depth is $<d_\theta(v)$, so the induction
   hypothesis gives
   $O_{\sigma(s_{v,k}(\theta))}(\sigma S,\sigma\theta,G)=O_{s_{v,k}(\theta)}(S,\theta,F)$.
5. Substitute steps 2–4 into the recursion:
   $O_{\sigma v}(\sigma S,\sigma\theta,G)=\mathbf 1\{v\in S\}\vee\big[(1-F_v)\prod_{k\in K_v}O_{s_{v,k}(\theta)}(S,\theta,F)\big]=O_v(S,\theta,F)$.
6. **Base case.** For $d_\theta(v)=0$ the product is empty, and steps 2–3 alone give the
   equality. ∎

### 3.5 Lemma (failure law is σ-invariant)

Under (A3), $G\overset d= F$.

*Proof.*
1. $G_w=F_{\sigma^{-1}w}=\mathbf 1\{\sqrt{\rho_{g'}}Y_{g'}+\sqrt{1-\rho_{g'}}\,\varepsilon_{\sigma^{-1}w}\le\Phi^{-1}(p_{\sigma^{-1}w})\}$,
   where $g'=\kappa(\sigma^{-1}w)$.
2. By (A3), $p_{\sigma^{-1}w}=p_w$ and $g'=\beta^{-1}(\kappa(w))$, so
   $\rho_{g'}=\rho_{\kappa(w)}$.
3. Set $Y'_g=Y_{\beta^{-1}g}$ and $\varepsilon'_w=\varepsilon_{\sigma^{-1}w}$. These are
   re-indexings of i.i.d. families by bijections, so $(Y',\varepsilon')\overset d=(Y,\varepsilon)$.
4. Then $G_w=\mathbf 1\{\sqrt{\rho_{\kappa(w)}}Y'_{\kappa(w)}+\sqrt{1-\rho_{\kappa(w)}}\,\varepsilon'_w\le\Phi^{-1}(p_w)\}$.
   This is the same measurable function of $(Y',\varepsilon')$ that $F$ is of $(Y,\varepsilon)$.
   Hence $G\overset d=F$. ∎

The proof uses only that the failure law is invariant under σ. It holds for any copula family
with that invariance.

### 3.6 Theorem. (H1′) ⟹ (H1). In fact, for each identification-free $S$, the joint law of $(Z_1,\dots,Z_{K_0})$ is θ-invariant up to a fixed permutation of the focal coordinates.

*Proof.* Fix an identification-free $S$ and $\theta,\theta'$. Take σ from (H1′), so
$\sigma\theta=\theta'$ and $\sigma S=S$.

1. **Focal coordinates.** By (A0), σ fixes $0$, and $\sigma_0$ permutes $\{1,\dots,K_0\}$.
2. **Starvation indicators.** By (A1)/(A2) and the definition of σθ, the supplier of focal
   category $\sigma_0k$ under σθ is $\sigma(s_{0,k}(\theta))$. Lemma 3.4 then gives
   $Z_{\sigma_0 k}(\sigma S,\sigma\theta,G)=1-O_{\sigma(s_{0,k}(\theta))}(\sigma S,\sigma\theta,G)=1-O_{s_{0,k}(\theta)}(S,\theta,F)=Z_k(S,\theta,F)$.
3. **Vector form.** So $Z(\sigma S,\sigma\theta,G)=\Pi_{\sigma_0}Z(S,\theta,F)$ pointwise in
   $F$, where $\Pi_{\sigma_0}$ is a coordinate permutation.
4. **Replace G by F.** By Lemma 3.5, $G\overset d=F$, and $Z(\sigma S,\sigma\theta,\cdot)$ is
   a fixed measurable map. Hence
   $Z(\sigma S,\sigma\theta,F)\overset d=Z(\sigma S,\sigma\theta,G)=\Pi_{\sigma_0}Z(S,\theta,F)$.
5. **Use the hypotheses on σ.** Substituting $\sigma S=S$ and $\sigma\theta=\theta'$:
   $Z(S,\theta',F)\overset d=\Pi_{\sigma_0}Z(S,\theta,F)$. This is the joint-law statement.
6. **From Z to L.** $L=K_0^{-1}\sum_kZ_k$ is invariant under coordinate permutations, so
   $L(S;\theta',\cdot)\overset d=L(S;\theta,\cdot)$.
7. θ, θ′ and $S$ were arbitrary, so (H1) holds. ∎

*Proof that (H1′-loc) ⟹ (H1′).* Fix $S$, θ and θ′. Enumerate the latent categories as
$\ell_1,\dots,\ell_n$. Set $\theta^{(0)}=\theta$. For each $i$:
1. Let $u=\theta^{(i-1)}_{\ell_i}$ and $u'=\theta'_{\ell_i}$. Take $\tau_i$ from (H1′-loc),
   or the identity if $u=u'$.
2. $\tau_i$ fixes $\ell_i$ and maps $u\mapsto u'$, so $(\tau_i\theta^{(i-1)})_{\ell_i}=u'$.
3. For every other latent $\ell=(w,j)$, $\tau_i$ fixes $w$, $j$ and $\theta^{(i-1)}_\ell\in C_\ell$.
   So $(\tau_i\theta^{(i-1)})_\ell=\theta^{(i-1)}_\ell$.
4. Set $\theta^{(i)}=\tau_i\theta^{(i-1)}$. It agrees with θ′ on $\ell_1,\dots,\ell_i$.

After $n$ steps $\theta^{(n)}=\theta'$. Let $\sigma=\tau_n\circ\cdots\circ\tau_1$.
- Compositions of structure automorphisms are structure automorphisms, because (A0)–(A3) are
  closed under composition.
- $\sigma\theta=\theta'$.
- $\sigma S=S$, because each $\tau_i$ fixes $S$. ∎

**Caveats.**
- (H1′) is sufficient, not necessary. (H1) can hold by numerical coincidence without any
  automorphism.
- If two candidate sets share a node, (H1′-loc) cannot hold. Moving that node in one set
  while fixing it in the other is impossible. This is correct behaviour, not a defect of the
  condition.

---

## 4. Is (H1′) strong enough everywhere (H1) is used?

The key point: **the hypothesis (H1) itself is not wrong.** Only the sentence offering a
sufficient condition for it is wrong. Every proof step that invokes (H1) uses the hypothesis
as stated. Replacing the sufficient condition by (H1′) therefore weakens no theorem. What it
narrows is the *applicability and checkability* claims.

### 4.1 Theorem 4, step (T5)

- (T5) needs: for every identification-free plan, $j(S;\theta)$ does not depend on θ.
- (H1′) ⟹ (H1) gives law invariance, which implies mean invariance. ✓
- (T5) also asserts a θ-independent minimiser $S^\star$. The set of identification-free
  feasible plans does not depend on θ, because costs are θ-free. ✓
- (T6)–(T9) are unchanged. **Theorem 4 holds verbatim under (H1′)+(H2).**

### 4.2 Corollary 5, step (C2)

- (C2) needs law invariance of $L$ for every identification-free plan. Theorem 3.6 delivers
  it, and more: joint invariance of $Z$ up to a permutation.
- **Corollary 5 holds verbatim.**
- This is the place where the marginal condition is weakest. Example 2 has equal means and
  CVaR values of 1 against 0.55.

### 4.3 Definition 1, l.509–510 ("take no action" is identification-free)

- This is a use of the sufficient condition, not of (H1).
- Under the marginal reading it is false: Example 1 has a θ-dependent law under $\emptyset$.
- Under (H1′) it is true, since $\emptyset$ is fixed by every σ.
- The sentence must be re-pointed to (H1′).

### 4.4 Proposition 10 (R2), and the implicit structure behind Corollary 7

- (R2) uses "exchangeable candidates" only for the *prior planner's* indifference among
  named candidates. That is prior exchangeability inside the single-category family
  $\mathcal D(\lambda)$, not (H1). It is unaffected by F-10.
- **Related defect, outside F-10's letter but the same flaw:** Corollary 7 (and the setup of
  Proposition 10) states its hypothesis marginally: "$m$ equal-cost, equal-risk candidates".
  The proof (D1)–(D2) silently assumes more. A candidate must influence focal category $k$
  only through $(v,k)$, and nothing else in the subtree may fail.

Counterexample, using focal category 1 of Example 1 with $c_u<c_v$ and $B\ge c_u$:

| budget | $v^{\rm inv}$ | $v^{\rm full}(u_1)$ | $v^{\rm full}(u_2)$ |
|---|---|---|---|
| $b<c_u$ | 0.145 | 0.10 | 0.19 |
| $c_u\le b<\min(c_v,2c_u)$ | 0.05 | 0 | 0.10 |

So $D(u_1)=\max(0.045,0.05)=0.05$, and $D(u_2)=0$ because both deficits are negative. Hence
$I_k=0.025$, but Corollary 7 gives $\bar q(1-1/m)=0.05$.

- Theorem 6 is unaffected, since it never assumes exchangeability.
- Corollary 7's *closed form* is wrong unless its hypothesis is read as the private-cone /
  miniature model, which is what `verify_theorem.py` implements.
- Recommend stating that structure explicitly in Cor 7 and Def 2. This is not a change to
  (H1).

### 4.5 The Table 4 batch (l.1797, `verify_theorem.py` mode `t1`)

- `actions_for_cat` models each category as a star: the true candidate's failure starves the
  category unless that candidate, all candidates, or the consumer is secured.
- Categories are separate.
- With `q`, `c_u` equal and `b` uniform, the cone swap of two candidates is a structure
  automorphism. So (H1′-loc) holds, and "instantiates (H1) by construction" survives.
- The batch evaluates only expected loss, so it checks Theorem 4 and does not test
  Corollary 5's law-level claim. No independence or copula assumption enters that check.

### 4.6 What *is* weakened: scope and checkability claims

- **l.522–523:** the sufficient condition must be replaced by (H1′). The "under the prior"
  clause should go. The cost clause is not needed for (H1).
- **l.104–106, l.1782:** "an exchangeability check on candidate sets" becomes "a search for
  automorphisms of the public structure fixing the identification-free plans". This is still
  checkable from public data, so l.971's "checkable in advance" stands. But it is a graph
  check over consumers, upstream cones and cluster labels, not a per-category marginal
  comparison. It is also **global**: a single latent category whose candidates differ in
  consumers or upstream structure breaks it.
- **l.1758:** "candidates within a supply category are exchangeable" should read
  "exchangeable by automorphisms of the public structure" or equivalent.
- **Applicability narrows sharply.** A candidate that has any consumer besides $v$ blocks the
  local swap unless every other candidate has a matching consumer. On the benchmark data only
  6.4 % of latent categories meet the sole-consumer condition (l.1257–1258). I have **not**
  checked how many admit a non-local automorphism, so I make no claim beyond "probably
  rare".
- l.1241–1242 (λ=0 "approximately exchangeable, which is (H1)") is wrong under the corrected
  condition. It is §8 material and due for removal, but it must not migrate into Paper A.
- **Interaction with F-25** (the quantifier ambiguity in Definition 1). (H1′) quantifies over
  identification-free plans and requires $\sigma S=S$. If Definition 1 classifies as
  identification-free some plan that meets two candidates' cones asymmetrically (for example
  $\{v,u_1\}$ under a literal reading), the stabiliser condition can fail. It can fail even
  though $L(\{v,u_1\};\cdot)=L(\{v,u_2\};\cdot)$. A clean fix is to weaken "$\sigma S=S$" in
  (H1′) to "$L(\sigma S;\theta',\cdot)\overset d=L(S;\theta',\cdot)$". The proof of 3.6 goes
  through unchanged, with step 5 using that equality instead. Resolving F-25 first would make
  the simpler form suffice.

### Summary

| Use | Status under (H1′) |
|---|---|
| Thm 4 (T5) | Holds verbatim |
| Cor 5 (C2) | Holds verbatim; it needs exactly the law-level invariance (H1′) provides |
| Def 1, no-action claim | False as written; true under (H1′) |
| Table 4 t1 batch | Satisfies (H1′); checks expected loss only |
| Cor 7 / Prop 10 | Do not use (H1). Cor 7's closed form has a parallel unstated structural hypothesis (§4.4) |
| Intro l.104–106, Table l.971, Conclusion l.1758, l.1782 | Scope wording must change; the check is an automorphism check, global and much rarer |
